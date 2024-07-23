"""Logic for interacting with the MongoDB database."""

import os
from typing import List, Dict

import pymongo
import pandas as pd
import plotly.io as pio
from pymongo.results import BulkWriteResult
from pymongo.mongo_client import MongoClient

from category import CATEGORY
from visualise import graph


CLIENT = MongoClient(
    f'mongodb+srv://{os.environ.get("mongodb_username")}:{os.environ.get("mongodb_password")}'
    f'@vinskraper.wykjrgz.mongodb.net/'
    f'?retryWrites=true&w=majority&appName=vinskraper'
)


def _discount(record, prices):
    """Calculate the discount for the given record."""
    prices = sorted(prices, key=lambda x: pd.Timestamp(x.split(' ')[1]))
    if len(prices) > 1:
        prices = prices[-2:]
        if record[prices[0]] in (0.0, None) or record[prices[1]] in (0.0, None):
            return 0.0
        return (record[prices[1]] - record[prices[0]]) / record[prices[0]] * 100
    return 0.0


def derive(category: CATEGORY) -> Dict[str, BulkWriteResult]:
    """
    Calculate the discount for the data in the database.
    Create the price plot for the data in the database.

    Parameters
    ----------
    category : CATEGORY
        The category of products to calculate the discount for.
        See enumerator `CATEGORY` for available options.
        Modifies the database in-place.

    Returns
    -------
    dict
        A dictionary containing the results of the bulk write operations.
        Keys are `'calculating discounts'` and `'plotting'`.

    Raises
    ------
    ValueError
        If the category is set to `CATEGORY.ALLE`.

    Notes
    -----
        The discount is calculated as the percentage difference between the two latest price-columns.
        If there is only one price-column, the discount is set to `'-'`.
        If any of the prices are `NaN` (replaced with `0`'s), the discount is set to `'-'`.
    """
    if category == CATEGORY.ALLE:
        raise ValueError('Cannot calculate discounts for all categories at once. '
                         'Please specify a single category.')

    collection = CLIENT['vinskraper'][category.name]
    records = list(collection.find({}))

    prices = []
    graphs = []
    for record in records:
        _prices = [feat for feat in record if feat.startswith('pris ')]
        prices.append(
            pymongo.UpdateOne(
                {'index': record['index']},
                {'$set': {
                    'prisendring': _discount(record, _prices),
                }},
                upsert=True
            )
        )
        graphs.append(
            pymongo.UpdateOne(
                {'index': record['index']},
                {'$set': {
                    'plot': graph(record, _prices),
                }},
                upsert=True
            )
        )

    results = {
        'calculating discounts': collection.bulk_write(prices),
        'plotting': CLIENT['vinskraper']['PLOTS'].bulk_write(graphs),
    }

    return results


def upsert(data: List[dict], category: CATEGORY) -> BulkWriteResult:
    """
    Upsert the given data into the database.

    Parameters
    ----------
    data : List[dict]
        The data to insert into the database.
    category : CATEGORY
        The category of products to calculate the discount for.
        See enumerator `CATEGORY` for available options.
        Modifies the database in-place.

    Returns
    -------
    BulkWriteResult

    Raises
    ------
    ValueError
        If the category is set to `CATEGORY.ALLE`.
    """
    if category == CATEGORY.ALLE:
        raise ValueError('Cannot upsert all categories at once. '
                         'Please specify a single category.')

    collection = CLIENT['vinskraper'][category.name]

    operations = [
        pymongo.UpdateOne(
            {'index': record['index']},
            {'$set': record},
            upsert=True
        )
        for record in data
    ]
    result = collection.bulk_write(operations)

    return result


def load(category: CATEGORY) -> pd.DataFrame:
    """
    Load the data from the database.

    Parameters
    ----------
    category : str
        The category of products to load.
    ascending : bool
        Whether to sort the data in ascending order.
    focus : str
        The column to focus on when sorting the data.
    limit : int
        The number of records to return.

    Returns
    -------
    pd.DataFrame
        The data from the database.
    """
    if category == CATEGORY.ALLE:
        return _load_all()

    collection = CLIENT['vinskraper'][category.name]

    data = pd.DataFrame(list(collection.find())).set_index('index').drop(columns=['_id'])

    return data


def plots(indices: List[str]) -> pd.DataFrame:
    collection = CLIENT['vinskraper']['PLOTS']

    data = pd.DataFrame(list(collection.find(
        {'index': {
            '$in': indices
        }}
    ))).set_index('index').drop(columns=['_id'])

    data['plot'] = data['plot'].apply(pio.from_json)

    return data


def _load_all() -> pd.DataFrame:
    """
    Load all data from the database.

    Returns
    -------
    pd.DataFrame
    """
    dfs = []
    for category in [cat for cat in CATEGORY
                     if cat not in (CATEGORY.ALLE, CATEGORY.COGNAC)]:
        df = load(category)
        df['kategori'] = category.value.capitalize().replace('_', ' ')
        dfs.append(df)
    dfs = pd.concat(dfs)

    return dfs
