# coding: utf-8

import time
import json
import os
import pickle
from requests_oauthlib import OAuth1Session
from pymongo import MongoClient

# 設定ファイル
import api_config

# APIトークンの読み込み
AK  = api_config.API_KEY
AKS = api_config.API_KEY_SECRET
AT  = api_config.ACCESS_TOKEN
ATS = api_config.ACCESS_TOKEN_SECRET


class Mongo:
    def __init__(self, db_name, collection_name):
        self.client = MongoClient()
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]

    def insert_many(self, documents):
        return self.collection.insert_many(documents)

    def get_max_id(self):
        return self.collection.find_one(projection={"_id":0, "id": 1}, sort=[("id", -1)])

    def __del__(self):
        self.client.close()


class TwitterAPI:
    def __init__(
        self, db_name, collection_name, params):
        # DB接続
        self._db_name = db_name
        self._collection_name = collection_name
        self._db = Mongo(
            db_name=self._db_name,
            collection_name=self._collection_name
        )

        # apiのためのセットアップ
        self._twitter_api = OAuth1Session(AK, AKS, AT, ATS)
        self._SEARCH_URL = "https://api.twitter.com/1.1/search/tweets.json"
        self._RATE_LIMIT_STATUS_URL = "https://api.twitter.com/1.1/application/rate_limit_status.json"
        self._params = params

        # 変数の読み込み
        self._sentinel_path = f"sentinels/{self._collection_name}.pkl"
        if os.path.exists(self._sentinel_path):
            with open(self._sentinel_path, "rb") as f:
                sentinel = pickle.load(f)
                self._params["since_id"] = sentinel.get("next_since_id", None)
                self._params["max_id"] = sentinel.get("next_max_id", None)
        else:
            self._since_id = self._db.get_max_id()

        # rate limit statusを取得
        status = self._get_rate_limit_status()
        self._LIMIT = status["limit"]
        self._remaining = status["remaining"]

        self._tweet_cnt = 0


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
                        self._params["since_id"] = self._db.get_max_id()
                        self._params["max_id"] = None
                        break

                    self._tweet_cnt += resp_cnt
                    print("count:{0}, latest:{1}, total:{2} ".format(resp_cnt, resp_body["statuses"][0]["created_at"], self._tweet_cnt))

                    # 収集したうちで最も小さいid-1を、次の収集のmax_idにする
                    self._params["max_id"] = resp_body["statuses"][-1]["id"] - 1

                    # 収集したツイートをDBに追加
                    self._db.insert_many(resp_body["statuses"])

                # 異常終了
                else:
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

        print("--FINISH--")


    def __del__(self):
        with open(self._sentinel_path, "wb") as f:
            pickle.dump({
                    "next_since_id": self._params.get("since_id", None),
                    "next_max_id": self._params.get("max_id", None)
            }, f)


def main():
    import search_params
    for item in search_params.search_params:
        api = TwitterAPI(
            db_name="tweets_place",
            collection_name=item["collection_name"],
            params=item["params"])
        api.get_tweet()


def test():
    api = TwitterAPI(
        db_name="tweets_place",
        collection_name="test",
        params={
            "q": "四日市",
            "count": 100,
            "result_type": "recent",
            "exclude": "retweets",
            "lang": "ja",
            "locale": "ja"
        })
    api.get_tweet()


if __name__ == "__main__":
    main()
