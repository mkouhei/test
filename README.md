dissipate.py (名称未定)
==========================

SYNOPSIS
------------

dissipate.py [-h] [-c [Policy file]] [-f] [-i [SECTION [SECTION ...]]]
        [-x [SECTION [SECTION ...]]] [-l]

```
-f: 実行時確認を行わない
-c: 任意のポリシーファイルを指定する
-i: 未実装(実行するセクションを指定)
-x: 未実装(実行除外するセクションを指定)
-l: 未実装(実行するセクションまたは実行除外するセクションをファイルで指定)
```

Require
------------

+ Python 2.7.x
+ PyYAML 3.10 以上


Operating environment
-----------------------

+ Ubuntu 12.01 以上
+ Fedora 17 以上


DESCRIPTION
------------

ポリシーファイル(YAML)に従ってシテスムを構成する。
パッケージのインストール、テンプレートを利用したファイルの生成、任意のコマンド実行を行う。

ちょっとした構築のみに使用し、インストールが終わったらスクリプトを抹消する。
継続的な利用は想定しない使い捨てツール。

正座しますからもう石投げないでください＞＜


Policy File Syntax (example)
--------------------------------

```
001_ntp:
  install:
    - ntp
  config:
    ntp.conf:
      dir: /etc
      file: ntp.conf
      template: example/ntp.conf.tmpl
      user: root
      group: root
      mode: 400
      attr:
        SERVER1: ntp1.jst.mfeed.ad.jp
        SERVER2: ntp2.jst.mfeed.ad.jp
        SERVER3: ntp3.jst.mfeed.ad.jp
  command:
    - "restorecon -v /etc/ntp.conf"
    - "ls -Zl /etc/ntp.conf"
    - systemctl restart ntpd.service
    - "ntpq -p"
002_httpd:
  install:
  config:
  command:
```

### 大区分
+ 001_ntp: 処理する任意のグループ名(名前の昇順で処理される)
+ install: インストールセクション
+ config :  コンフィグセクション
+ command: コマンドセクション

### インストールセクション

任意のパッケージを列挙する。
```
  - package001
  - package002
  - package003
  - …
```

### コンフィグセクション

+ ntp.conf: ファイル毎に処理を分けるための任意の識別子

+ dir: ファイルの配置先
+ file: ファイル名
+ template: ファイルの元となるテンプレートファイル
+ user: ファイルのユーザ名 または UID
+ group: ファイルのグループ名 または GID
+ mode: ファイルのモード


+ attr: テンプレートファイル内の変数を置換して、ファイルを生成する場合に使用
+   - 置換する任意の変数: 置換する値


### コマンドセクション

任意のコマンドを列挙

```
    - "restorecon -v /etc/ntp.conf"
    - "ls -Zl /etc/ntp.conf"
    - systemctl restart ntpd.service
    - "ntpq -p"
    - ...
```

os.system() にそのまま渡す頭の悪いことをしているので色々注意。
ダブルクォーテーションなどはエスケープする必要がある。
