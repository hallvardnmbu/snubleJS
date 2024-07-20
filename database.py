"""Logic for interacting with the MongoDB database."""

import os
from typing import List

import pymongo
import pandas as pd
from pymongo.results import BulkWriteResult
from pymongo.mongo_client import MongoClient


_CLIENT = MongoClient(
    f"mongodb+srv://{os.environ.get('mongodb_username')}:{os.environ.get('mongodb_password')}"
    f"@vinskraper.wykjrgz.mongodb.net/"
    f"?retryWrites=true&w=majority&appName=vinskraper"
)
MONGODB = _CLIENT['vinskraper']['vinskraper']


def _calculate_discount(record):
    prices = [feat for feat in record if feat.startswith('pris ')]
    prices = sorted(prices, key=lambda x: pd.Timestamp(x.split(" ")[1]))
    if len(prices) > 1:
        prices = prices[-2:]
        if record[prices[0]] in (0.0, None) or record[prices[1]] in (0.0, None):
            return 0.0
        return (record[prices[1]] - record[prices[0]]) / record[prices[0]] * 100
    return 0.0


def db_discounts():
    """
    Calculate the discount for the data in the database.

    Notes
    -----
        The discount is calculated as the percentage difference between the two latest price-columns.
        If there is only one price-column, the discount is set to `'-'`.
        If any of the prices are `NaN` (replaced with `0`'s), the discount is set to `'-'`.
    """
    records = list(MONGODB.find({}))
    operations = [
        pymongo.UpdateOne(
            {'index': record['index']},
            {"$set": {"prisendring": _calculate_discount(record)}},
            upsert=True
        )
        for record in records
    ]
    MONGODB.bulk_write(operations)


def db_upsert(data: List[dict]) -> BulkWriteResult:
    """
    Upsert the given data into the database.

    Parameters
    ----------
    data : List[dict]
        The data to insert into the database.
    """
    operations = [
        pymongo.UpdateOne(
            {'index': record['index']},
            {'$set': record},
            upsert=True
        )
        for record in data
    ]
    result = MONGODB.bulk_write(operations)
    return result


def db_load() -> pd.DataFrame:
    """
    Load the data from the database.

    Returns
    -------
    pd.DataFrame
        The data from the database.
    """
    data = pd.DataFrame(list(MONGODB.find())).set_index('index').drop(columns=['_id'])
    return data
