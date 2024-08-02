"""Refresh product availability."""

import os
from typing import List
import concurrent.futures

import pymongo
import requests
from pymongo.mongo_client import MongoClient

from proxy import Proxy


_CLIENT = MongoClient(
    f'mongodb+srv://{os.environ.get("mongodb_username")}:{os.environ.get("mongodb_password")}'
    f'@vinskraper.wykjrgz.mongodb.net/'
    f'?retryWrites=true&w=majority&appName=vinskraper'
)
_DATABASE = _CLIENT['vinskraper']['vin']

_PROXY = Proxy()

_AVAILABLE = 'https://www.vinmonopolet.no/vmpws/v3/vmp/products/{}/availability'


def _available(index: int) -> dict:
    for _ in range(10):
        try:
            product = requests.get(_AVAILABLE.format(index), proxies=_PROXY.get(), timeout=3)
            if product.status_code != 200:
                return {}
            product = product.json()

            return {
                'index': index,

                'tilgjengelig for bestilling': product \
                    .get('deliveryAvailability', {}) \
                    .get('availableForPurchase', False),
                'bestillingsinformasjon': product \
                    .get('deliveryAvailability', {}) \
                    .get('infos', [{}])[0] \
                    .get('readableValue', '-'),
                'tilgjengelig i butikk': product \
                    .get('storesAvailability', {}) \
                    .get('availableForPurchase', False),
                'butikkinformasjon': product \
                    .get('storesAvailability', {}) \
                    .get('infos', [{}])[0] \
                    .get('readableValue', '-'),
            }
        except Exception as err:
            print(f'{index}: Trying another proxy. {err}')
            _PROXY.renew()

    raise ValueError('Failed to fetch product availability.')


def available(products: List[int] = None, max_workers=5):
    """
    Update information about product availability.

    Parameters
    ----------
    products : List[int]
        The products to fetch detailed information about.
        If None, all products are fetched.
    max_workers : int
        The maximum number of (parallel) workers to use when fetching products.

    Raises
    ------
    ValueError
        If the product information could not be fetched.

    Notes
    -----
    If `products` is None, all products are fetched.
    The function uses a thread pool to fetch the products in parallel.
    To prevent memory issues, the function fetches the products in batches.
    """
    if not products:
        print('Fetching all products.')
        products = _DATABASE.distinct('index')

    step = max(len(products) // 1000, 500)
    for i in range(0, len(products), step):
        print(f'Processing products {i} to {i + step} of {len(products)}.')

        operations = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            results = {executor.submit(_available, product): product for product in products[i:i + step]}
            for future in concurrent.futures.as_completed(results):
                product = future.result()
                if not product:
                    continue
                operations.append(
                    pymongo.UpdateOne(
                        {'index': product['index']},
                        {'$set': product},
                        upsert=True
                    )
                )
        _DATABASE.bulk_write(operations)


if __name__ == '__main__':
    available()
