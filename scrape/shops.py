import os
from typing import Tuple

import pymongo
import requests
import pandas as pd
from bs4 import BeautifulSoup
from pymongo.errors import BulkWriteError
from pymongo.results import BulkWriteResult
from pymongo.mongo_client import MongoClient

from proxy import Proxy


_CLIENT = MongoClient(
    f'mongodb+srv://{os.environ.get("mongodb_username")}:{os.environ.get("mongodb_password")}'
    f'@vinskraper.wykjrgz.mongodb.net/'
    f'?retryWrites=true&w=majority&appName=vinskraper'
)
_PROXY = Proxy()


def stores() -> dict:
    """
    Fetch information about all stores from Vinmonopolet.
    Store the results to a collection named `butikk` in the `vinskraper` database.

    Returns
    -------
    dict

    Extracts
    --------
        * store number : int
        * name : str
        * address : str
        * coordinates : dict of str -> float
        * assortiment type : str
        * click and collect : bool
    """
    url = 'https://www.vinmonopolet.no/vmpws/v2/vmp/stores?fields=FULL&pageSize=1000'

    for _ in range(10):
        try:
            response = requests.get(url,
                                    params={"q": "*"},
                                    proxies=_PROXY.get(),
                                    timeout=3)
            break
        except Exception as err:
            print(f'├─ Error: '
                    f'(Trying another proxy); {err}')
            _PROXY.renew()
    else:
        print(f'├─ Error: '
                f'Failed to fetch store information. Tried 10 times.')
        return {}

    if response.status_code != 200:
        print('Failed to fetch store information.')
        return {}

    stores = response.json()['stores']
    if not stores:
        print('No stores found.')
        return {}

    for store in stores:
        store.pop('openingTimes', None)
        store.pop('formattedDistance', None)

        store['index'] = int(store.pop('name'))
        store['navn'] = store.pop('displayName')
        store['adresse'] = store.pop('address')['formattedAddress']
        store['koordinater'] = store.pop('geoPoint')
        store['sortiment'] = store.pop('assortment', '-')
        store['klikk og hent'] = store.pop('clickAndCollect')
        store['mobilbetaling'] = store.pop('mobileCheckoutEnabled')

    _CLIENT['vinskraper']['butikk'].delete_many({})
    _CLIENT['vinskraper']['butikk'].insert_many(stores)

    return stores


def stock(max_workers=10) -> dict:
    """
    Fetch the stock of all stores from Vinmonopolet.
    Adds the available stores to each product in the `vin` collection.
    Adds the available products to each store in the `butikk` collection.

    Returns
    -------
    dict
        The results of bulk write operations for the `vin` and `butikk` collections.
    """
    url = 'https://www.vinmonopolet.no/vmpws/v2/vmp/search?searchType=product&currentPage={}&q=%3Arelevance%3AavailableInStores%3A{}'

    ids = _CLIENT['vinskraper']['butikk'].distinct('index')
    if not ids:
        ids = [store['index'] for store in stores()]

    # Reset the stock of all stores and products.
    _CLIENT['vinskraper']['butikk'].update_many({}, {'$set': {'produkter': []}})
    _CLIENT['vinskraper']['vin'].update_many({}, {'$set': {'butikker': []}})

    operations = []
    products = {_product: [] for _product in _CLIENT['vinskraper']['vin'].distinct('index')}
    for store in ids:

        _products = []
        for page in range(10000):

            for _ in range(10):
                try:
                    response = requests.get(url.format(page, store),
                                            proxies=_PROXY.get(),
                                            timeout=3)
                    break
                except Exception as err:
                    print(f'├─ Error: '
                            f'Page {page} (trying another proxy); {err}')
                    _PROXY.renew()
            else:
                print(f'├─ Error: '
                        f'Failed to fetch page {page} after 10 attempts.')
                break

            if response.status_code != 200:
                print(f'Failed to fetch products for store {store} (page: {page}).')
                break

            response = response.json()['productSearchResult']['products']
            if not response:
                print(f'Store {store}: {page - 1} pages of products.')
                break

            response = [int(_product['code']) for _product in response]
            _products.extend(response)
            for product in response:
                products[product].append(store) if product in products else None

        operations.append(pymongo.UpdateOne(
            {'index': store},
            {'$set': {'produkter': _products}}
        ))
    result_stores = _CLIENT['vinskraper']['butikk'].bulk_write(operations)
    result_products = _CLIENT['vinskraper']['vin'].bulk_write([
        pymongo.UpdateOne(
            {'index': index},
            {'$set': {'butikker': stores}},
            upsert=True
        )
        for index, stores in products.items()
        if stores
    ])

    return {'stores': result_stores, 'products': result_products}


if __name__ == '__main__':

    # `stores` should be run once to populate the `butikk` collection.
    # _ = stores()

    # `stock` can be run whenever, to update the stock of all stores and products.
    stock()
