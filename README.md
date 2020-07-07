# twitter_search_tool

## Overview

[twitterのSearch API](https://developer.twitter.com/ja) を利用して、ツイートを収集します。

## Description

Search APIでは、7日前までのツイートを、1回のリクエストあたり100件まで取得することができます。
また、このAPIにはレートリミットが存在し、これは15分ごとに設定されています。

このスクリプトでは、ある単語に対して繰り返しSearch APIでの検索を行い、ツイートを収集します。
APIから得られるのは、ツイートの時刻（"create_at"）で降順になったツイートのリストであり、リクエスト毎に得られたリストを連結して、json形式で保存します。

収集中にレートリミットを超過した場合は、pythonのsleep関数で数分待機し、解除を待ってリトライします。

## Usage

このスクリプトを動作させるためには、このリポジトリをcloneした後に、ディレクトリ内に以下のような`config.py`の作成が必要です。
`config.py`に記載するトークンは、Twitter Developerアカウントを作成した上で各自で取得してください。

このサイトが参考になります。:point_right: https://syncer.jp/Web/API/Twitter/REST_API/

```python
API_KEY = "XXXXXXXXXXXXXXXX"
API_KEY_SECRET = "XXXXXXXXXXXXXXXXX"
ACCESS_TOKEN = "XXXXXXXXXXXXXXXXXXX"
ACCESS_TOKEN_SECRET = "XXXXXXXXXXXXXXXXXXXX"

```

`config.py`が作成できたら、ターミナルで`main.py`を実行してください。
`tweets_data`ディレクトリに、収集したツイートがjson形式で保存されます。
（数十MBを超えることがあり、エディタで開こうとするとかなり重い場合があるので注意してください。）

```
$ python3 main.py
```

