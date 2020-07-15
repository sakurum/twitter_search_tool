# coding: utf-8

import argparse
import os
import json
import time
from requests_oauthlib import OAuth1Session
from pymongo import MongoClient

import api_config
import search_config


# コマンドライン引数の設定
parser = argparse.ArgumentParser()
parser.add_argument("--firsttime", action="store_true", help="初回実行時（DBがないとき）につける")
parser.add_argument("--sinseid", type=int, default=0, help="sinse idを指定する")
args = parser.parse_args()

# APIトークンの読み込み
try:
    AK  = api_config.API_KEY
    AKS = api_config.API_KEY_SECRET
    AT  = api_config.ACCESS_TOKEN
    ATS = api_config.ACCESS_TOKEN_SECRET
except Exception:
    raise

try:
    search_list = search_config.search_list
except Exception:
    raise


class Mongo:
    def __init__(self, db_name, collection_name):
        self.client = MongoClient()
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]

    def insert_many(self, documents):
        return self.collection.insert_many(documents)

    def get_max_id(self):
        return self.collection.find_one(projection={"_id":0, "id": 1}, sort=[("id", -1)])


class TwitterAPI:
    def __init__(self, search_word, collection_name):
        # 変数の用意
        self._collection_name = collection_name
        self._tweet_cnt = 0
        self._tweets = []
        self._since_id = args.sinseid

        # DBの接続
        self._mongo = Mongo(db_name="tweets_data", collection_name=collection_name)
        # idの最大値を取得
        if not args.firsttime:
            self._since_id = self._mongo.get_max_id()["id"]

        # apiためのセットアップ
        self._twitter_api = OAuth1Session(AK, AKS, AT, ATS)
        self._SEARCH_URL = "https://api.twitter.com/1.1/search/tweets.json"
        self._RATE_LIMIT_STATUS_URL = "https://api.twitter.com/1.1/application/rate_limit_status.json"
        self._params = {
            "q": search_word,
            "count": 100,
            "result_type": "recent",
            "exclude": "retweets",
            "lang": "ja",
            "locale": "ja",
            "since_id": self._since_id
        }

        # rate limitのstatusの取得
        status = self._get_rate_limit_status()
        self._LIMIT = status["limit"]
        self._remaining = status["remaining"]


    def _get_response(self):
        return self._twitter_api.get(self._SEARCH_URL, params=self._params)


    def _get_rate_limit_status(self):
        params = {
            "resources_famiily": "family"
        }
        response = self._twitter_api.get(self._RATE_LIMIT_STATUS_URL, params=params, timeout=1)
        return json.loads(response.text)["resources"]["search"]["/search/tweets"]


    def get_tweet(self):
        while True:
            if self._remaining > 0:
                response = self._get_response()
                self._remaining -= 1

                # 正常終了時
                if response.status_code == 200:
                    resp_body = json.loads(response.text)
                    resp_cnt = len(resp_body["statuses"])

                    # 収集結果が0件だったら終了
                    if resp_cnt == 0:
                        break

                    self._tweet_cnt += resp_cnt
                    print("count:{0}, latest:{1}, total:{2} ".format(resp_cnt, resp_body["statuses"][0]["created_at"], self._tweet_cnt))

                    # 収集したうちで最も小さいid-1を、次の収集のmax_idにする
                    self._params["max_id"] = resp_body["statuses"][-1]["id"] - 1

                    # 収集したツイート分を追加（max_idの降順にするように追加）
                    self._tweets[self._tweet_cnt:0] = resp_body["statuses"]

                # 異常終了
                else:
                    print(response)
                    print(json.loads(response.text))
                    break

            # rate limitに達したとき
            else:
                # resetまでの時間を取得して待つ（一応1秒長く待つ）
                status = self._get_rate_limit_status()
                wait_time = int(status["reset"] - time.time() + 1)

                for i in range(1, wait_time+1):
                    print("\rWaiting for rate limit reset: {0} / {1}[sec]".format(i, wait_time), end="")
                    time.sleep(1)

                print("")

                status = self._get_rate_limit_status()
                self._remaining = status["remaining"]


        # 収集が完了して、0件でなかったら保存
        if self._tweets:
            self._mongo.insert_many(self._tweets)

        print("--FINISH--")


def main():
    for search in search_list:
        twitter_api = TwitterAPI(
            search_word=search["search_word"],
            collection_name=search["filename"]
        )
        twitter_api.get_tweet()

def test():
    ta = TwitterAPI(search_word="辻野あかり", collection_name="tujinoakari")
    ta.get_tweet()

if __name__ == "__main__":
    main()
    # test()
