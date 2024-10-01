"""Code used to refactor the MongoDB database."""

import os

import pymongo
from pymongo.mongo_client import MongoClient
from pymongo.results import BulkWriteResult


_OLD = MongoClient(
    f'mongodb+srv://{os.environ.get("MONGO_USR")}:{os.environ.get("MONGO_PWD")}'
    f'@vinskraper.wykjrgz.mongodb.net/'
    f'?retryWrites=true&w=majority&appName=vinskraper'
)['vinskraper']
_NEW = MongoClient(
    f'mongodb+srv://{os.environ.get("MONGO_USR")}:{os.environ.get("MONGO_PWD")}'
    f'@snublejuice.faktu.mongodb.net/'
    f'?retryWrites=true&w=majority&appName=snublejuice'
)['snublejuice']['products']
# _DATABASE = _CLIENT['vinskraper']['varer']
# _EXPIRED = _CLIENT['vinskraper']['utgått']


def update_prices(records) -> BulkWriteResult:
    operations = [
        pymongo.UpdateOne(
            {'index': record['index']},
            [
                {'$rename': {'pris': 'førpris'}},
                {'$set': record},
                {'$set': {'priser': {'$ifNull': ['$priser', []]}}},
                {'$set': {'priser': {'$concatArrays': ['$priser', ['$pris']]}}},
                {'$set': {
                    'prisendring': {'$cond': [
                        {'if': {'and': [
                            {'$gt': ['$førpris', 0]},
                            {'$gt': ['$pris', 0]}
                        ]}},
                        {'$multiply': [
                            {'$divide': [
                                {'$subtract': ['$pris', '$førpris']},
                                '$førpris'
                            ]},
                            100
                        ]},
                        0
                    ]},
                }},
                {'$set': {
                    'literpris': {'$cond': {
                        'if': {'$and': [
                            {'$ne': ['$pris', None]},
                            {'$ne': ['$pris', 0]},
                            {'$ne': ['$volum', None]},
                            {'$ne': ['$volum', 0]},
                        ]},
                        'then': {'$multiply': [
                            {'$divide': ['$pris', '$volum']},
                            100
                        ]},
                        'else': None
                    }}
                }},
                {'$set': {
                    'alkoholpris': {'$cond': {
                        'if': {'$and': [
                            {'$ne': ['$literpris', None]},
                            {'$ne': ['$literpris', 0]},
                            {'$ne': ['$alkohol', None]},
                            {'$ne': ['$alkohol', 0]},
                        ]},
                        'then': {'$divide': ['$literpris', '$alkohol']},
                        'else': None
                    }}
                }}
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


def move(records) -> BulkWriteResult:
    result = _DATABASE.bulk_write([
        pymongo.DeleteOne({'index':
                            {'$in': [record['index'] for record in records]}})
    ])
    print(result)
    return _EXPIRED.bulk_write([
        pymongo.InsertOne(record)
        for record in records
    ])


# HÅNDTER FØLGENDE PRODUKTER:
# "status": "utgått"
# "volum": {"$exists": false}
# "bilde": {"$exists": false}
