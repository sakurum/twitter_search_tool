# coding: utf-8

import config
import os
import json
import time

from requests_oauthlib import OAuth1Session


try:
    AK  = config.API_KEY
    AKS = config.API_KEY_SECRET
    AT  = config.ACCESS_TOKEN
    ATS = config.ACCESS_TOKEN_SECRET
except Exception:
    raise

    
class TwitterAPI:
    def __init__(self, search_word, filename):
        # 変数の用意
        self._filename = filename
        self._tweet_cnt = 0
        self._tweets = []
        self._since_id = 0
        self._rate_limit_cnt = 0
        self._RATE_LIMIT_CNT_MAX = 6

        # 保存ファイルが既にあれば読み込み
        if os.path.isfile(self._filename):
            with open("tweets_data/{}".format(self._filename), "r") as fp:
                self._tweets = json.load(fp)

                # 保存ファイルの中の最新のtweetのidをsince_idにする
                self._since_id = self._tweets[0]["id"]

        # apiためのセットアップ
        self._twitter_api = OAuth1Session(AK, AKS, AT, ATS)
        self._url = "https://api.twitter.com/1.1/search/tweets.json"
        self._params = {
            "q": search_word,
            "count": 100,
            "result_type": "recent",
            "exclude": "retweets",
            "lang": "ja",
            "locale": "ja",
            "since_id": self._since_id
        }


    def _get_response(self):
        return self._twitter_api.get(self._url, params=self._params)


    def get_tweet(self):
        while True:
            response = self._get_response()

            # 正常終了時
            if response.status_code == 200:
                # カウントをリセット
                self._rate_limit_cnt = 0

                resp_body = json.loads(response.text)
                resp_cnt = len(resp_body["statuses"])

                # 収集結果が0件だったら終了
                if resp_cnt == 0:
                    break

                self._tweet_cnt += resp_cnt
                print("count:{0}, latest:{1}, total:{2} ".format(resp_cnt, resp_body["statuses"][0]["created_at"], self._tweet_cnt))

                # 収集したうちで最も小さいid-1を、次の収集のmax_idにする
                self._params["max_id"] = resp_body["statuses"][-1]["id"] - 1

                # 収集したツイート分を追加（max_idの降順にするので先頭に追加）
                self._tweets[0:0] = resp_body["statuses"]

            # レートリミット超過時
            elif response.status_code == 429:
                print(response)
                # n回やっても取得しきれなかったら終了
                if self._rate_limit_cnt > self._RATE_LIMIT_CNT_MAX:
                    print("RATE_LIMIT_CNT_MAX exceeded")
                    break

                self._rate_limit_cnt += 1

                # 5分待つ（あまり良くない(?)対処なので注意）
                # twitter_apiでは、rate_limitは15分で更新
                print("Waiting for rate limit reset...")
                wait_time = 60*5
                for i in range(1, wait_time+1):
                    print("\r{0} / {1}[sec]".format(i, wait_time), end="")
                    time.sleep(1)
                print("")
                print("retry!")

            # その他
            else:
                print(response)
                break

        # 収集が完了したら
        with open("tweets_data/{}.json".format(self._filename), "w") as fp:
            json.dump(self._tweets, fp, indent=4, ensure_ascii=False)


def main():
    search_word = "辻野あかり"
    filename = "tujinoakari"

    twitter_api = TwitterAPI(search_word, filename)
    twitter_api.get_tweet()

    
if __name__ == "__main__":
    main()
