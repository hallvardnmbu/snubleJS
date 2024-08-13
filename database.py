"""Logic for interacting with the MongoDB database."""

import os
from typing import Union, Any, List, Tuple, Dict

import pandas as pd
from pymongo.mongo_client import MongoClient


_CLIENT = MongoClient(
    f'mongodb+srv://{os.environ.get("mongodb_username")}:{os.environ.get("mongodb_password")}'
    f'@vinskraper.wykjrgz.mongodb.net/'
    f'?retryWrites=true&w=majority&appName=vinskraper'
)
_DATABASE = _CLIENT['vinskraper']['varer']
_MAP = {
    'årgang': 'argang',
    'beskrivelse.kort': 'beskrivelse',
    'passer til': 'passer_til',
}


def uniques(
    extract: List[str],
    kategori: List[str] = [],
    underkategori: List[str] = [],
    land: List[str] = [],
    distrikt: List[str] = [],
    underdistrikt: List[str] = [],
    volum: List[str] = [],
    argang: List[str] = [],
    beskrivelse: List[str] = [],
    kork: List[str] = [],
    lagring: List[str] = [],
    butikk: List[str] = [],
    passer_til: List[str] = [],
    **kwargs: Any
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
    land : list of str
        The countries to include.
    distrikt : list of str
        The districts to include.
    underdistrikt : list of str
        The subdistricts to include.
    volum : list of str
        The volumes to include.
    argang : list of str
        The years to include.
    beskrivelse : list of str
        The descriptions to include.
    kork : list of str
        The corks types to include.
    lagring : list of str
        The storage types to include.
    butikk : list of str
        The stores to include.
    passer_til : list of str
        The food pairings to include.
    kwargs : any
        Added to prevent errors when passing the raw state's selection.

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
            ('butikk', {'$all': butikk} if butikk else None),
            ('passer til', {'$all': passer_til} if passer_til else None)
        ] if value},

        **{field: {'$in': value} for field, value in [
            ('kategori', kategori),
            ('underkategori', underkategori),
            ('volum', [float(v) for v in volum]),
            ('land', land),
            ('distrikt', distrikt),
            ('underdistrikt', underdistrikt),
            ('årgang', [int(ar.replace('.0', '')) for ar in argang if ar]),
            ('beskrivelse.kort', beskrivelse),
            ('kork', kork),
            ('lagring', lagring),
        ] if value}
    })

    mapping: Dict[str, Union[list, Dict[str, str]]] = {
        _MAP[feature] if feature in _MAP else feature: list(set(filtered.distinct(feature)) - {None, '-'})
        for feature in extract
    }

    return mapping


def load(
    kategori: List[str] = [],
    underkategori: List[str] = [],
    land: List[str] = [],
    distrikt: List[str] = [],
    underdistrikt: List[str] = [],
    volum: List[str] = [],
    argang: List[str] = [],
    beskrivelse: List[str] = [],
    kork: List[str] = [],
    lagring: List[str] = [],
    butikk: List[str] = [],
    passer_til: List[str] = [],
    alkohol: Union[None, float] = None,
    fra: Union[None, float] = None,
    til: Union[None, float] = None,
    sorting: str = 'prisendring',
    ascending: bool = True,
    amount: int = 10,
    page: int = 1,
    search: str = '',
    filters: bool = False,
    fresh: bool = True,
) -> Tuple[pd.DataFrame, Union[int, None]]:
    """
    Load the data from the database.

    Parameters
    ----------
    kategori : list of str
        The categories to include.
    underkategori : list of str
        The subcategories to include.
    land : list of str
        The countries to include.
    distrikt : list of str
        The districts to include.
    underdistrikt : list of str
        The subdistricts to include.
    volum : list of str
        The volumes to include.
    argang : list of str
        The years to include.
    beskrivelse : list of str
        The descriptions to include.
    kork : list of str
        The corks types to include.
    lagring : list of str
        The storage types to include.
    butikk : list of str
        The stores to include.
    passer_til : list of str
        The food pairings to include.
    alkohol : float
        The minimum alcohol percentage to include.
    fra : float
        The minimum value to include (wrt. `sorting`).
    til : float
        The maximum value to include (wrt. `sorting`).
    sorting : str
        The feature to sort by.
    ascending : bool
        Whether to sort the data in ascending order.
    amount : int
        The amount of data to load.
        Number of items per page.
    page : int
        The page of the data to load.
        I.e., the number of `amount` to skip.
    search : str
        The name to search for.
    filters : bool
        Whether to apply the filters to the search.
    fresh : bool
        Whether to calculate the total amount of records.

    Returns
    -------
    pd.DataFrame
        The data from the database.
    int
        The total amount of records for the given parameters.
        If `fresh` is False, the total amount is not calculated.

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
    pipeline: List[Any] = []

    if search:
        pipeline += [{
            '$search': {
                'index': 'navn',
                'text': {
                    'query': search,
                    'path': 'navn',
                }
            }
        }]

    pipeline += [{
        '$match': {
            'utgått': False,
            'kan kjøpes': True,

            **{field: value for field, value in [
                ('tilgjengelig for bestilling', not bool(butikk and filters)),
                ('butikk', {'$all': butikk} if (butikk and filters) else None),
                ('passer til', {'$all': passer_til} if (passer_til and filters) else None)
            ] if value},

            **{field: {'$in': value} for field, value in [
                ('kategori', kategori),
                ('underkategori', underkategori),
                ('volum', [float(v) for v in volum]),
                ('land', land),
                ('distrikt', distrikt),
                ('underdistrikt', underdistrikt),
                ('årgang', [int(ar.replace('.0', '')) for ar in argang if ar]),
                ('beskrivelse.kort', beskrivelse),
                ('kork', kork),
                ('lagring', lagring),
            ] if (value and filters)}
        }
    }]

    if alkohol:
        pipeline[1 if search else 0]['$match']['alkohol'] = {
            **pipeline[1 if search else 0]['$match'].get('alkohol', {}),
            **{'$gte': alkohol}
        }

    if fra or til:
        between = {op: val for op, val in [
            ('$gte', fra),
            ('$lte', til)
        ] if val}
        if sorting == 'volum':
            pipeline[1 if search else 0]['$match']['volum'] = {
                **pipeline[1 if search else 0]['$match'].get('volum', {}),
                **between
            }
        else:
            pipeline[1 if search else 0]['$match'][sorting] = between
    pipeline[1 if search else 0]['$match'][sorting] = {
        **pipeline[1 if search else 0]['$match'].get(sorting, {}),
        **{'$exists': True,
        '$ne': None}
    }

    if fresh:
        total = list(_DATABASE.aggregate(pipeline + [{'$count': 'amount'}]))
        try:
            total = total[0].get('amount', 0)
        except IndexError:
            raise KeyError('No records found.')
    else:
        total = None

    pipeline += [{
        '$sort': {
            sorting: 1 if ascending else -1
        }
    }, {
        '$skip': (page - 1) * amount
    }, {
        '$limit': amount
    }]

    collection = list(_DATABASE.aggregate(pipeline))

    data = pd.DataFrame(collection).set_index('index').drop(columns=['_id']).replace({'-': None})

    return data, total
