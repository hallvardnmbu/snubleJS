"""Logic for interacting with the MongoDB database."""

import os
from typing import Any, List, Dict

import pandas as pd
from pymongo.mongo_client import MongoClient


_CLIENT = MongoClient(
    f'mongodb+srv://{os.environ.get("mongodb_username")}:{os.environ.get("mongodb_password")}'
    f'@vinskraper.wykjrgz.mongodb.net/'
    f'?retryWrites=true&w=majority&appName=vinskraper'
)
_DATABASE = _CLIENT['vinskraper']['vin']


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
    filtered = _DATABASE.find({
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


def amount(
    kategori: List[str] = [],
    underkategori: List[str] = [],
    volum: List[str] = [],
    land: List[str] = [],
    distrikt: List[str] = [],
    underdistrikt: List[str] = [],
) -> int:
    """
    Extract the maximum amount of records for the given parameters.

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

    Returns
    -------
    int
        The maximum amount of records for the given parameters.
    """
    return _DATABASE.count_documents({
        'tilgjengelig for bestilling': True,
        **{field: {'$in': value} for field, value in [
                    ('kategori', kategori),
                    ('underkategori', underkategori),
                    ('volum', [float(v) for v in volum]),
                    ('land', land),
                    ('distrikt', distrikt),
                    ('underdistrikt', underdistrikt),
                ] if value}
    })


def load(
    kategori: List[str] = [],
    underkategori: List[str] = [],
    volum: List[str] = [],
    land: List[str] = [],
    distrikt: List[str] = [],
    underdistrikt: List[str] = [],

    sorting: str = 'prisendring',
    ascending: bool = True,
    amount: int = 10,
    page: int = 1,
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
    page : int
        The page of the data to load.

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
                        ('underdistrikt', underdistrikt),
                    ] if value}
        }
    },
    {
        '$sort': {
            sorting: 1 if ascending else -1
        }
    },
    {
        '$skip': (page - 1) * amount
    },
    {
        '$limit': amount
    }]

    collection = list(_DATABASE.aggregate(pipeline))

    data = pd.DataFrame(collection).set_index('index').drop(columns=['_id']).replace({'-': None})

    return data


def search(
    name: str,

    kategori: List[str] = [],
    underkategori: List[str] = [],
    volum: List[str] = [],
    land: List[str] = [],
    distrikt: List[str] = [],
    underdistrikt: List[str] = [],

    sorting: str = 'prisendring',
    ascending: bool = True,
    amount: int = 10,
) -> pd.DataFrame:
    """
    Search for the given name in the database.

    Parameters
    ----------
    name : str
        The name to search for.
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
        The number of results to return.

    Returns
    -------
    pd.DataFrame
    """
    if not name:
        return load(
            kategori=kategori, underkategori=underkategori, volum=volum,
            land=land, distrikt=distrikt, underdistrikt=underdistrikt
        )

    pipeline: List[Any] = [{
        '$search': {
            'index': 'navn',
            'text': {
                'query': name,
                'path': 'navn',
            }
        }
    },
    {
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
        '$limit': amount
    }]

    collection = list(_DATABASE.aggregate(pipeline))

    data = pd.DataFrame(collection).set_index('index').drop(columns=['_id']).replace({'-': None})

    return data
