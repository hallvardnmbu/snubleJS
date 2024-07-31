"""Logic for interacting with the MongoDB database."""

import os
from typing import Union, Any, List, Dict

import pandas as pd
from pymongo.mongo_client import MongoClient


_CLIENT = MongoClient(
    f'mongodb+srv://{os.environ.get("mongodb_username")}:{os.environ.get("mongodb_password")}'
    f'@vinskraper.wykjrgz.mongodb.net/'
    f'?retryWrites=true&w=majority&appName=vinskraper'
)
# _STORES: Dict[int, str] = {record['index']: record['navn'] for record in list(
#     _CLIENT['vinskraper']['butikk'].aggregate([
#         {'$project': {'_id': 0, 'navn': 1, 'index': 1}}
#       SORT IT!
#     ])
# )}
_DATABASE = _CLIENT['vinskraper']['vin']


def uniques(
    extract: List[str],
    kategori: List[str] = [],
    underkategori: List[str] = [],
    volum: List[str] = [],
    land: List[str] = [],
    distrikt: List[str] = [],
    underdistrikt: List[str] = [],
    butikk: List[str] = [],
    **kwargs: Dict[str, Union[float, None]]
) -> Dict[str, Union[List[str], Dict[int, str]]]:
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
    butikk : list of str
        The stores to include.
    kwargs : dict
        To prevent errors when passing the state's `valgt` dictionary.

    Returns
    -------
    dict
        A dictionary containing the unique values for the given features.
        Keys are the features and values are a list of the unique values.
    """
    filtered = _DATABASE.find({
        **{field: value for field, value in [
            ('tilgjengelig for bestilling', not bool(butikk)),
            ('butikk', {'$all': butikk} if butikk else None)
        ] if value},

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
    butikk: List[str] = [],

    fra: Union[None, float] = None,
    til: Union[None, float] = None,

    sorting: str = 'prisendring',
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
    butikk : list of str
        The stores to include.
    fra : float
        The minimum value to include (wrt. `sorting`).
    til : float
        The maximum value to include (wrt. `sorting`).
    sorting : str
        The feature to sort the data by.

    Returns
    -------
    int
        The maximum amount of records for the given parameters.
    """
    query = {
        **{field: value for field, value in [
            ('tilgjengelig for bestilling', not bool(butikk)),
            ('butikk', {'$all': butikk} if butikk else None)
        ] if value},

        **{field: {'$in': value} for field, value in [
                    ('kategori', kategori),
                    ('underkategori', underkategori),
                    ('volum', [float(v) for v in volum]),
                    ('land', land),
                    ('distrikt', distrikt),
                    ('underdistrikt', underdistrikt)
                ] if value}
    }

    if fra or til:
        between = {op: val for op, val in [
            ('$gte', fra),
            ('$lte', til)
        ] if val}
        if sorting == 'volum':
            query['volum'] = {
                **query.get('volum', {}),
                **between
            }
        else:
            query[sorting] = between

    return _DATABASE.count_documents(query)


def load(
    kategori: List[str] = [],
    underkategori: List[str] = [],
    volum: List[str] = [],
    land: List[str] = [],
    distrikt: List[str] = [],
    underdistrikt: List[str] = [],
    butikk: List[str] = [],

    fra: Union[None, float] = None,
    til: Union[None, float] = None,

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
    butikk : list of str
        The stores to include.
    fra : float
        The minimum value to include (wrt. `sorting`).
    til : float
        The maximum value to include (wrt. `sorting`).
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
            **{field: value for field, value in [
                ('tilgjengelig for bestilling', not bool(butikk)),
                ('butikk', {'$all': butikk} if butikk else None)
            ] if value},

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
        '$skip': (page - 1) * amount
    },
    {
        '$limit': amount
    }]

    if fra or til:
        between = {op: val for op, val in [
            ('$gte', fra),
            ('$lte', til)
        ] if val}
        if sorting == 'volum':
            pipeline[0]['$match']['volum'] = {
                **pipeline[0]['$match'].get('volum', {}),
                **between
            }
        else:
            pipeline[0]['$match'][sorting] = between

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
    butikk: List[str] = [],

    fra: Union[None, float] = None,
    til: Union[None, float] = None,

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
    butikk : list of str
        The stores to include.
    fra : float
        The minimum value to include (wrt. `sorting`).
    til : float
        The maximum value to include (wrt. `sorting`).
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
            **{field: value for field, value in [
                ('tilgjengelig for bestilling', not bool(butikk)),
                ('butikk', {'$all': butikk} if butikk else None)
            ] if value},

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

    if fra or til:
        between = {op: val for op, val in [
            ('$gte', fra),
            ('$lte', til)
        ] if val}
        if sorting == 'volum':
            pipeline[1]['$match']['volum'] = {
                **pipeline[1]['$match'].get('volum', {}),
                **between
            }
        else:
            pipeline[1]['$match'][sorting] = between

    collection = list(_DATABASE.aggregate(pipeline))

    data = pd.DataFrame(collection).set_index('index').drop(columns=['_id']).replace({'-': None})

    return data
