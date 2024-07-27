"""Logic for interacting with the MongoDB database."""

import os
import enum
from typing import List, Dict

import pymongo
import pandas as pd
from pymongo.results import BulkWriteResult
from pymongo.mongo_client import MongoClient


_CLIENT = MongoClient(
    f'mongodb+srv://{os.environ.get("mongodb_username")}:{os.environ.get("mongodb_password")}'
    f'@vinskraper.wykjrgz.mongodb.net/'
    f'?retryWrites=true&w=majority&appName=vinskraper'
)
DATABASE = _CLIENT['vinskraper']['vin']


class CATEGORY(enum.Enum):
    """
    Enum class for the different categories of products available at vinmonopolet.
    Extends the `scrape._URL` with the category value.
    """
    RED_WINE = 'rødvin'
    WHITE_WINE = 'hvitvin'
    SPARKLING_WINE = 'musserende_vin'
    PEARLING_WINE = 'perlende_vin'
    FORTIFIED_WINE = 'sterkvin'
    AROMATIC_WINE = 'aromatisert_vin'
    FRUIT_WINE = 'fruktvin'
    ROSE_WINE = 'rosévin'
    SPIRIT = 'brennevin'
    BEER = 'øl'
    CIDER = 'sider'
    SAKE = 'sake'
    MEAD = 'mjød'


def _discount(record, prices):
    """Calculate the discount for the given record."""
    prices = sorted(prices, key=lambda x: pd.Timestamp(x.split(' ')[1]))
    if len(prices) > 1:
        prices = prices[-2:]
        if record[prices[0]] in (0.0, None) or record[prices[1]] in (0.0, None):
            return 0.0
        return (record[prices[1]] - record[prices[0]]) / record[prices[0]] * 100
    return 0.0


def derive() -> BulkWriteResult:
    """
    Calculate the discount for the data in the database.

    Returns
    -------
    BulkWriteResult

    Notes
    -----
        The discount is calculated as the percentage difference between the two latest price-columns.
        If there is only one price-column, the discount is set to `'-'`.
        If any of the prices are `NaN` (replaced with `0`'s), the discount is set to `'-'`.
    """
    records = list(DATABASE.find({}))

    operations = []
    for record in records:
        _prices = [feat for feat in record if feat.startswith('pris ')]
        operations.append(
            pymongo.UpdateOne(
                {'index': record['index']},
                {'$set': {
                    'prisendring': _discount(record, _prices),
                }},
                upsert=True
            )
        )

    results = DATABASE.bulk_write(operations)

    return results


def upsert(data: List[dict]) -> BulkWriteResult:
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
    """
    operations = [
        pymongo.UpdateOne(
            {'index': record['index']},
            {'$set': record},
            upsert=True
        )
        for record in data
    ]
    result = DATABASE.bulk_write(operations)

    return result


def uniques(
    extract: List[str],
    kategori: List[str] = [],
    underkategori: List[str] = [],
    volum: List[str] = [],
    land: List[str] = [],
    distrikt: List[str] = [],
    underdistrikt: List[str] = [],
) -> Dict[str, List[str]]:
    """
    Extract the unique values for the given `extract` features from the database.
    Filters the data based on the given parameters.

    Parameters
    ----------
    extract : list of str
        The features to extract the unique values for.
    kategori : list of str
        The categories to include.
    underkategori : list of str
        The subcategories to include.
    volum : list of str
        The volumes to include.
    land : list of str
        The countries to include.
    distrikt : list of str
        The districts to include.
    underdistrikt : list of str
        The subdistricts to include.

    Returns
    -------
    dict
        A dictionary containing the unique values for the given features.
        Keys are the features and values are a list of the unique values.
    """
    filtered = DATABASE.find({
        'tilgjengelig for bestilling': True,
        **{field: {'$in': value} for field, value in [
                    ('kategori', kategori),
                    ('underkategori', underkategori),
                    ('volum', [float(v) for v in volum]),
                    ('land', land),
                    ('distrikt', distrikt),
                    ('underdistrikt', underdistrikt)
                ] if value}
    })

    return {
        feature: list(set(filtered.distinct(feature)) - {None, '-'})
        for feature in extract
    }


def load(
    kategori: List[str],
    underkategori: List[str],
    volum: List[str],
    land: List[str],
    distrikt: List[str],
    underdistrikt: List[str],

    sorting: str = 'prisendring',
    ascending: bool = True,
    amount: int = 10
) -> pd.DataFrame:
    """
    Load the data from the database.

    Parameters
    ----------
    kategori : list of str
        The categories to include.
    underkategori : list of str
        The subcategories to include.
    volum : list of str
        The volumes to include.
    land : list of str
        The countries to include.
    distrikt : list of str
        The districts to include.
    underdistrikt : list of str
        The subdistricts to include.
    sorting : str
        The feature to sorting by.
    ascending : bool
        Whether to sort the data in ascending order.
    amount : int
        The amount of data to load.

    Returns
    -------
    pd.DataFrame
        The data from the database.

    Raises
    ------
    KeyError
        (Unable to set index.)
        If no data is found for the given parameters.

    Notes
    -----
    Setting up the pipeline for the aggregation.
        The pipeline is used to filter the data from the database.
        The pipeline is constructed based on the given parameters.
        The pipeline is then used to load the data from the database.
    """
    pipeline = [{
        '$match': {
            'tilgjengelig for bestilling': True,
            **{field: {'$in': value} for field, value in [
                        ('kategori', kategori),
                        ('underkategori', underkategori),
                        ('volum', [float(v) for v in volum]),
                        ('land', land),
                        ('distrikt', distrikt),
                        ('underdistrikt', underdistrikt)
                    ] if value}
        }
    },
    {
        '$sort': {
            sorting: 1 if ascending else -1
        }
    },
    {
        '$limit': int(amount)
    }]

    collection = list(DATABASE.aggregate(pipeline))

    data = pd.DataFrame(collection).set_index('index').drop(columns=['_id']).replace({'-': None})

    return data
