# twitter_search_tool

## Overview

[twitterのSearch API](https://developer.twitter.com/ja) を利用して、ツイートを収集します。

ツイートの保存には[mongoDB](https://www.mongodb.com/)を使用します。

## Description

### ツイートの収集について
`search_params`に記述された`collection_name`と`params`を読み取り、ツイートを収集します。
paramsの記載方法については、公式のリファレンス等をご確認ください。

プログラムを実行すると、その時刻から、APIで取得可能な7日前までのツイートを新しいものから順に取得します。
APIのレートリミットの制限（180リクエスト/15分）に達すると、レートリミットがリセットされるまで待機します。

収集が途中で終了された場合（強制終了を含む）、作業状態をpickleに保存します。
プログラムの実行時にpickleに保存された作業状態があれば、自動的にそこから再開します。

### APIについて
twitterのAPIの接続のために、`api_config.py`の値を読み取ります。
Twitter Developerアカウントより、access key, tokenを取得して、`api_config.py`を作成してください。


```python:api_config.py
# your api keys and tokens
API_KEY = ""
API_KEY_SECRET = ""
ACCESS_TOKEN = ""
ACCESS_TOKEN_SECRET = ""
```


**api_configはリポジトリに公開しないようご注意ください。**

## Usage

```bash
# run
pipenv shell
python3 main.py

# exit shell
exit
```

