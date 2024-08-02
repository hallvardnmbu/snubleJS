"""Fetch detailed information about products."""

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

_DETAILS = 'https://www.vinmonopolet.no/vmpws/v3/vmp/products/{}?fields=FULL'


def _product(product: int) -> dict:
    """Extract detailed information about a single product."""
    for _ in range(10):
        try:
            details = requests.get(_DETAILS.format(product),
                                   proxies=_PROXY.get(),
                                   timeout=3)
            if details.status_code != 200:
                raise ValueError()

            details = details.json()
            return {
                'index': int(details.get('code', 0)),

                'farge': details.get('color', '-'),
                'karakteristikk': [characteristic['readableValue'] for characteristic in
                                   details.get('content', {}).get('characteristics', [])],
                'ingredienser': [ingredient['readableValue'] for ingredient in
                                 details.get('content', {}).get('ingredients', [])],
                'egenskaper': [f'{trait["name"]}: {trait["readableValue"]}' for trait in
                               details.get('content', {}).get('traits', [])],
                'lukt': details.get('smell', '-'),
                'smak': details.get('taste', '-'),

                'passer til': [element['name'] for element in details.get('isGoodFor', [])],
                'lagring': details.get('storagePotential', {}).get('formattedValue', '-'),
                'kork': details.get('cork', '-'),

                'beskrivelse': {'lang': details.get('style', {}).get('description', '-'),
                                'kort': details.get('style', {}).get('name', '-')},
                'metode': details.get('method', '-'),
                'årgang': details.get('year', '-'),
            }
        except Exception as err:
            print(f'{product}: Trying another proxy. {err}')
            _PROXY.renew()

    raise ValueError('Failed to fetch product information.')


def detailed(products: List[int] = None, max_workers=5):
    """
    Fetch detailed information about products and store the results to the database.

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
    The function fetches detailed information about the products in the list `products`.
    If `products` is None, all products are fetched.
    The function uses a thread pool to fetch the products in parallel.
    To prevent memory issues, the function fetches the products in batches.
    """
    if not products:
        print('Fetching all products.')
        products = _DATABASE.distinct('index')

    step = max(len(products) // 1000, 500)
    for i in range(0, len(products), step):
        print(f'Processing products {i} to {i + step}.')

        operations = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            results = {executor.submit(_product, product): product for product in products[i:i + step]}
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
    detailed()
