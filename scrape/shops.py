import os
import concurrent.futures
from functools import partial

import pymongo
import requests
from pymongo.results import BulkWriteResult
from pymongo.mongo_client import MongoClient

from proxy import Proxy


_CLIENT = MongoClient(
    f'mongodb+srv://{os.environ.get("mongodb_username")}:{os.environ.get("mongodb_password")}'
    f'@vinskraper.wykjrgz.mongodb.net/'
    f'?retryWrites=true&w=majority&appName=vinskraper'
)
_PROXY = Proxy()
_STORE = 'https://www.vinmonopolet.no/vmpws/v2/vmp/stores?fields=FULL&pageSize=1000'
_STOCK = ('https://www.vinmonopolet.no/vmpws/v2/vmp/search?'
          'searchType=product&currentPage={}&q=%3Arelevance%3AavailableInStores%3A{}')


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
    for _ in range(10):
        try:
            response = requests.get(_STORE,
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


def _stock(store):
    products = []
    for page in range(10000):
        for _ in range(10):
            try:
                response = requests.get(_STOCK.format(page, store),
                                        proxies=_PROXY.get(),
                                        timeout=3)
                break
            except Exception as err:
                print(f'{store} Error: '
                      f'Page {page} (trying another proxy); {err}')
                _PROXY.renew()
        else:
            print(f'{store} Error: '
                  f'Failed to fetch page {page} after 10 attempts.')
            break

        if response.status_code != 200:
            print(f'{store} Failed to fetch products for store (page: {page}).')
            break

        data = response.json().get('productSearchResult', {}).get('products', [])
        if not data:
            print(f'{store}: {page - 1} pages of products.')
            break

        products.extend([int(_product['code']) for _product in data])

    return store, products


def stock(max_workers=10) -> BulkWriteResult:
    """
    Fetch the stock of all stores from Vinmonopolet.

    Parameters
    ----------
    max_workers : int, optional
        The maximum number of workers to use for concurrent requests (default is 10).

    Returns
    -------
    BulkWriteResult
    """
    ids = _CLIENT['vinskraper']['butikk'].distinct('index')
    if not ids:
        ids = [store['index'] for store in stores()]

    products = {product: [] for product in _CLIENT['vinskraper']['vin'].distinct('index')}
    process = partial(_stock)
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        execution = {executor.submit(process, store): store for store in ids}
        for future in concurrent.futures.as_completed(execution):
            store, _products = future.result()
            for product in _products:
                if product in products:
                    products[product].append(store)

    # Reset the current values.
    _CLIENT['vinskraper']['vin'].update_many({}, {'$set': {'butikk': []}})

    # Add the new values.
    results = _CLIENT['vinskraper']['vin'].bulk_write([
        pymongo.UpdateOne(
            {'index': index},
            {'$set': {'butikk': stores}},
            upsert=True
        )
        for index, stores in products.items()
        if stores
    ])

    return results


if __name__ == '__main__':

    # `stores` should be run once to populate the `butikk` collection.
    # _ = stores()

    # `stock` can be run whenever, to update the stock of all stores and products.
    _ = stock()
