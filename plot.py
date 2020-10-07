from bson.json_util import loads, dumps
import pandas
from pymongo import MongoClient

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

import pprint

class Mongo:
    def __init__(self, db_name, collection_name):
        self._client = MongoClient()
        self._db = self._client[db_name]
        self._collection = self._db[collection_name]

    def mongo_to_dataframe(self):
        return pandas.DataFrame.from_dict(list(self._collection.find(
            projection={"_id":0, "created_at":1, "text":1, "user.location":1}

        )))

    def __del__(self):
        self._client.close()


def csv():
    df = pandas.read_csv("data.csv", encoding="shift-jis")
    pprint.pprint(df)


def main():
    db = Mongo(
        db_name="tweets_place",
        collection_name="tokyo_r5km"
    )

    df = db.mongo_to_dataframe()
    df["created_at"] = pandas.to_datetime(df["created_at"], format="%a %b %d %H:%M:%S %z %Y")
    df.set_index("created_at", inplace=True)

    df["count"] = df.apply(lambda x: "頭痛" in x["text"], axis=1)
    df["sum"] = 1

    df_time = df.resample("H").sum()

    def key_in_text(x):
        if x["sum"] == 0:
            return 0
        else:
            return x["count"]/x["sum"]

    df_time["per"] = df_time.apply(key_in_text, axis=1)


    # plot
    fig, ax = plt.subplots()

    df_time.plot(subplots=True, sharex=True)
    ax.xaxis.set_minor_locator(mdates.HourLocator(byhour=range(0, 24, 1), tz=None))
    plt.show()


if __name__ == "__main__":
    main()
