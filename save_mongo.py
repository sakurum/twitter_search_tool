# coding: utf-8

from pymongo import MongoClient
import json
import search_config

class Mongo(object):
    def __init__(self, db_name, collection_name):
        self.client = MongoClient()
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]

    def insert_one(self, document):
        return self.collection.insert_one(document)

    def insert_many(self, documents):
        return self.collection.insert_many(documents)

    def get_max_id(self):
        return self.collection.find_one(projection={"_id":0, "id": 1}, sort=[("id", -1)])


def save():
    save_list = search_config.search_list
    # save_list = [{"filename": "itai"}]

    for item in save_list:
        filename = item["filename"]

        print("insert {}.json".format(filename))
        mongo = Mongo(db_name="tweets_data", collection_name=filename)

        with open("tweets_data/{}.json".format(filename), "r") as fp:
            tweets = json.load(fp)
            mongo.insert_many(tweets)

        print("Done")


def get():
    collection_name = "itai"

    mongo = Mongo(db_name="tweets_data", collection_name=collection_name)

    return mongo.get_max_id()


if __name__ == '__main__':
    print(get()["id"])
