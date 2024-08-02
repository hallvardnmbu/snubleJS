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
_DATABASE = _CLIENT['vinskraper']['varer']

STORES: Dict[int, str] = {record['index']: record['navn'] for record in list(
    _CLIENT['vinskraper']['butikk'].aggregate([
        {'$project': {'_id': 0, 'navn': 1, 'index': 1}},
        {'$sort': {'navn': 1}}
    ])
)}


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
) -> Dict[str, Union[list, Dict[str, str]]]:
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
        'utgått': False,
        'kan kjøpes': True,

        **{field: value for field, value in [
            ('tilgjengelig for bestilling', not bool(butikk)),
            ('butikk', {'$all': [int(b) for b in butikk]} if butikk else None)
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

    mapping: Dict[str, Union[list, Dict[str, str]]] = {
        feature: list(set(filtered.distinct(feature)) - {None, '-'})
        for feature in extract
        if feature != 'butikk'
    }

    if 'butikk' not in extract:
        return mapping

    stores = list(set(filtered.distinct('butikk')) - {None, '-'})
    return {
        **mapping,
        **{'butikk': {str(idx): name for idx, name in STORES.items() if idx in stores}}
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
        'utgått': False,
        'kan kjøpes': True,

        **{field: value for field, value in [
            ('tilgjengelig for bestilling', not bool(butikk)),
            ('butikk', {'$all': [int(b) for b in butikk]} if butikk else None)
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
            'utgått': False,
            'kan kjøpes': True,

            **{field: value for field, value in [
                ('tilgjengelig for bestilling', not bool(butikk)),
                ('butikk', {'$all': [int(b) for b in butikk]} if butikk else None)
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
    amount: int = 10,

    filters: bool = False,

    kategori: List[str] = [],
    underkategori: List[str] = [],
    volum: List[str] = [],
    land: List[str] = [],
    distrikt: List[str] = [],
    underdistrikt: List[str] = [],
    butikk: List[str] = [],

    fra: Union[None, float] = None,
    til: Union[None, float] = None,

    sorting: Union[None, str] = None,
    ascending: bool = True,
) -> pd.DataFrame:
    """
    Search for the given name in the database.

    Parameters
    ----------
    name : str
        The name to search for.
    amount : int
        The number of results to return.
    filters : bool
        Whether to apply the filters to the search.
        The filters are the rest of the parameters.
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
    }]

    if filters:
        print(butikk)
        pipeline += [{
            '$match': {
                'utgått': False,
                'kan kjøpes': True,

                **{field: value for field, value in [
                    ('tilgjengelig for bestilling', not bool(butikk)),
                    ('butikk', {'$all': [int(b) for b in butikk]} if butikk else None)
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
        }]
        if sorting:
            pipeline += [{
                '$sort': {
                    sorting: 1 if ascending else -1
                }
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

    pipeline += [{
        '$limit': amount
    }]

    collection = list(_DATABASE.aggregate(pipeline))

    data = pd.DataFrame(collection).set_index('index').drop(columns=['_id']).replace({'-': None})

    return data
