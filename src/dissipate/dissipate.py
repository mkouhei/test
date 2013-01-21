#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import sys
import pwd
import grp
import argparse
from string import Template
import yaml


parser = argparse.ArgumentParser(
             description='ポリシーファイルに従って何か設定するアレです。')

parser.add_argument('-c',
    nargs='?',
    metavar="Policy file",
    default='./policy.yaml',
    help="Specify the name and path of the policy file, default ./policy.yaml")

parser.add_argument('-f',
    action='store_false',
    help="Assume Yes to all queries and do not prompt")

parser.add_argument('-i',
    nargs='*',
    metavar="SECTION",
    default=[],
    help="Specifies a list of include sections")

parser.add_argument('-x',
    nargs='*',
    metavar="SECTION",
    default=[],
    help="Specifies a list of exclude sections")

parser.add_argument('-l',
    action='store_false',
    help='Use the list file to specify '
                    '"exclude section" or "include section"')

args = parser.parse_args()


class Dissipate:
    def __init__(self):
        # import platform
        # platform.linux_distribution()???
        if os.path.exists('/bin/yum') or os.path.exists('/usr/bin/yum'):
            self.installer = 'yum'
        elif (os.path.exists('/bin/apt-get') or
              os.path.exists('/usr/bin/apt-get')):
            self.installer = 'apt-get'
        else:
            print("Unknown package system.")
            sys.exit(1)

    def do_install(self, packages, installer):
        # パッケージ名、繋がない方がいい？
        # os.system() があるけど、どの道 root で実行するので Escape は敢えてしない方針
        print("\033[32m" + "=== Install Package section ===" + "\033[0m")
        packages = ' '.join(packages)
        install = installer + " -y install " + packages
        print("=== " + install + " ===")
        os.system(install)

    def do_command(self, command):
        # os.system() があるけど、どの道 root で実行するので Escape は敢えてしない方針
        print("\n" + "\033[32m" + "=== Exec command section ===" + "\033[0m")
        for cmd in command:
            print "=== " + cmd
            os.system(cmd)
            print "\n"

    def do_check(self, config):
        print "Check!"

    def set_permission(self, fname, uid, gid, mode=None):
        try:
            os.chown(fname, uid, gid)
        except OverflowError:
            print("\033[33m" +
                  "Warning: (Overflow) Please check user or group. "
                  "Skip owner, group settings." + "\033[0m")

        if mode:
            try:
                os.chmod(fname, mode)
            except (TypeError, OverflowError):
                print("\033[31m" +
                      "Error: Please check mode value. Use umask value."
                      + "\033[0m")

    def do_config(self, config):
        print("\n" + "\033[32m" + "=== Create config section ===" + "\033[0m")

        for x in config:
            # Check param: dir, file, template
            if (not 'dir' in config[x] or
                not os.path.exists(config[x]['dir'])):
                print("\033[31m" +
                      "Error: (dir) parameter is not defined. "
                      "or Directory is not exist." + "\033[0m")
                return 1

            if not 'file' in config[x]:
                print("\033[31m" +
                      "Error: (file) parameter is not defined." + "\033[0m")
                return 1

            if (not 'template' in config[x] or
                not os.path.exists(config[x]['template'])):
                print("\033[31m" +
                      "Error: (template) parameter is not defined. "
                      "r Template file is not exist." + "\033[0m")
                return 1

            # テンプレートからファイルを生成
            fpath = config[x]['dir'] + "/" + config[x]['file']
            of = open(fpath, 'w')
            ot = open(config[x]['template'], 'r').read().decode('utf8')

            if config[x].get('attr'):
                of.write(Template(ot).safe_substitute(config[x]['attr']))
            else:
                of.write(ot)

            of.close()

            print("\n%s" % ("-" * 37))
            print("File: %s" % fpath)
            print("Template: %s" % config[x]['template'])

            if 'user' in config[x]:
                print("User: %s" % str(config[x]['user']))

            if 'group' in config[x]:
                print("Group: %s" % str(config[x]['group']))

            # (FIXME) Set mode
            pat = re.compile(r'[1-7]?[0-7]{3}')
            if ('mode' in config[x] and
                pat.match(str(config[x]['mode'])) is not None):
                if len(str(config[x]['mode'])) == 3:
                    work = "0" + str(config[x]['mode'])
                else:
                    work = str(config[x]['mode'])

                mode = (int(work[0]) * 512 +
                        int(work[1]) * 64 +
                        int(work[2]) * 8 + int(work[3]))
                print("Mode: %s" % oct(mode))
            else:
                mode = None
                print("Mode: Undefined mode or Invalid mode. Use umask value.")

            # Set UID
            dinfo = os.stat(config[x]['dir'])

            if 'user' in config[x]:
                if str(config[x]['user']).isdigit():
                    uid = int(config[x]['user'])
                else:
                    try:
                        uid = pwd.getpwnam(config[x]['user']).pw_uid
                    except KeyError:
                        print("\033[33m" +
                              "Warning: User name not found. "
                              "Use parent directory UID." + "\033[0m")
                        uid = dinfo.st_uid
            else:
                uid = dinfo.st_uid

            # Set GID
            dinfo = os.stat(config[x]['dir'])
            if 'group' in config[x]:
                if str(config[x]['group']).isdigit():
                    gid = config[x]['group']
                else:
                    try:
                        gid = grp.getgrnam(config[x]['group']).gr_gid
                    except KeyError:
                        print("\033[33m" +
                              "Warning: Group name not found. "
                              "Use parent directory GID." + "\033[0m")
                        gid = dinfo.st_gid
            else:
                gid = dinfo.st_gid

            self.set_permission(fpath, uid, gid, mode)

    def do_action(self, name, param):
        print("\033[32m" + "##### " + name + " ######" + "\033[0m")

        if param.get('install') and self.installer:
            self.do_install(param['install'], self.installer)

        if param.get('config'):
            self.do_config(param['config'])

        if param.get('command'):
            self.do_command(param['command'])


if __name__ == '__main__':
    # 任意のファイルを参照する
    # ここでフォーマットチェックできないかな
    filename = args.c
    try:
        policy = yaml.safe_load(file(filename, 'r').read().decode('utf8'))
        print(yaml.safe_dump(policy, encoding='utf8', allow_unicode=True))
    except IOError:
        print("\033[31m" + "Policy file not found." + "\033[0m")
        sys.exit(1)

    if args.f:
        while True:
            ok = raw_input("exec?[y/N]: ")
            ok = str(ok).lower() or 'n'

            if ok in ('y', 'ye', 'yes'):
                break
            if ok in ('n', 'no'):
                sys.exit(0)

    item = []

    try:
        for x, v in policy.items():
            item.append(x)
            item.sort()
    except AttributeError:
        print("\033[31m" + "Error: Please check YAML format." + "\033[0m")
        sys.exit(1)

    action = Dissipate()

    for x in item:
        action.do_action(x, policy[x])

"""
ツールの名前が決まらない。
英語が致命的過ぎて死にたい
例外処理とか変数名とかを正しく
OrderedDictつかう?

ログ出力
------

* do_config()
* do_check()

  * policy.yaml 内で共通の値を持つものは面倒なので変数したい。
  * policy.yaml の特定セクションを指定するオプション
   -i
  * policy.yaml の特定セクションをスキップするオプシヨン
   -x
  * セクションの指定と除外の指定にリストファイルを使用するオプション
   -l
mode の先頭には 0 をつけない運用回避: o: 755, 1755, x: 0755
* 0 をつけたものが config[x]['mode'] に入ると10進数として格納される。
  そのまま os.chmod 渡せばよい。
* 0 なしの物の場合はそのまま10進数として入る。
  これをそのまま os.chmod に渡すと8進数として見られるため意図しないパーミッションになる。
* 暫定対応として、0で始まらない数値を8進数と見なし、10進数に変換して使用する。
  [1-7]?[0-7]{3} 意外の値は不正な値として扱う。::

   config[x]['mode']=755 : work = "0" + "755" =>
   mode = (int(work[0]) * 512 + int(work[1]) * 64 +
           int(work[2]) * 8 + int(work[3])) =  493 (0755)
   config[x]['mode']=1755:                    =>
   mode = (int(work[0]) * 512 + int(work[1]) * 64 +
           int(work[2]) * 8 + int(work[3])) = 1005(01755)
"""
