"""Code used to refactor the MongoDB database."""

import os

import pymongo
from pymongo.mongo_client import MongoClient
from pymongo.results import BulkWriteResult

import pandas as pd
import pyarrow


# _OLD = MongoClient(
#     f'mongodb+srv://{os.environ.get("MONGO_USR")}:{os.environ.get("MONGO_PWD")}'
#     f'@vinskraper.wykjrgz.mongodb.net/'
#     f'?retryWrites=true&w=majority&appName=vinskraper'
# )['vinskraper']
# _DATABASE = _OLD['vinskraper']['varer']
# _EXPIRED = _OLD['vinskraper']['utgått']
_DATABASE = MongoClient(
    f'mongodb+srv://{os.environ.get("MONGO_USR")}:{os.environ.get("MONGO_PWD")}'
    f'@snublejuice.faktu.mongodb.net/'
    f'?retryWrites=true&w=majority&appName=snublejuice'
)['snublejuice']['products']


def update_prices(records) -> BulkWriteResult:
    raise ValueError("ARE YOU SURE???")

    backup()

    operations = [
        pymongo.UpdateOne(
            {'index': record['index']},
            [
              { "$set": { "oldprice": "$price" } },
              { "$set": record },
              { "$set": { "prices": { "$ifNull": ["$prices", []] } } },
              { "$set": { "prices": { "$concatArrays": ["$prices", ["$price"]] } } },
              {
                  "$set": {
                  "discount": {
                    "$cond": {
                      "if": {
                        "$and": [
                          { "$gt": ["$oldprice", 0] },
                          { "$gt": ["$price", 0] },
                          { "$ne": ["$oldprice", None] },
                          { "$ne": ["$price", None] },
                        ],
                      },
                      "then": {
                        "$multiply": [
                          {
                            "$divide": [{ "$subtract": ["$price", "$oldprice"] }, "$oldprice"],
                          },
                          100,
                        ],
                      },
                      "else": 0,
                    },
                  },
                  "literprice": {
                    "$cond": {
                      "if": {
                        "$and": [
                          { "$gt": ["$price", 0] },
                          { "$gt": ["$volume", 0] },
                          { "$ne": ["$price", None] },
                          { "$ne": ["$volume", None] },
                        ],
                      },
                      "then": {
                        "$multiply": [
                          {
                            "$divide": ["$price", "$volume"],
                          },
                          100,
                        ],
                      },
                      "else": None,
                    },
                  },
                },
              },
              {
                  "$set": {
                  "alcoholprice": {
                    "$cond": {
                      "if": {
                        "$and": [
                          { "$gt": ["$literprice", 0] },
                          { "$gt": ["$alcohol", 0] },
                          { "$ne": ["$literprice", None] },
                          { "$ne": ["$alcohol", None] },
                        ],
                      },
                      "then": {
                        "$divide": ["$literprice", "$alcohol"],
                      },
                      "else": None,
                    },
                  },
                },
              },
            ],
            upsert=True
        )
        for record in records
    ]
    return _DATABASE.bulk_write(operations)


def delete_fields(records, fields) -> BulkWriteResult:
    operations = [
        pymongo.UpdateOne(
            {'index': record['index']},
            {'$unset': {field: '' for field in fields}}
        )
        for record in records
    ]
    return _DATABASE.bulk_write(operations)


def backup():
    data = _DATABASE.find({})
    df = pd.DataFrame(data)
    df = df.drop(columns=["_id"])
    df["year"] = df["year"].apply(lambda x: int(float(x)) if x not in ("None", None, "") and pd.notna(x) else None)
    if not os.path.exists("./backup"):
        path = f"./database/backup/{pd.Timestamp.now().strftime('%Y-%m-%d')}.parquet"
    else:
        path = f"./backup/{pd.Timestamp.now().strftime('%Y-%m-%d')}.parquet"
    df.to_parquet(path)
    print("Saved backup to ", path)


backup()
