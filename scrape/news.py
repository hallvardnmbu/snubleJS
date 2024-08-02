"""
Fetch new products.

CRON JOB: 0 05 1/7 * *
"""

import os
import time
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
_DATABASE = _CLIENT['vinskraper']['varer']

_PROXY = Proxy()

_NEW = "https://www.vinmonopolet.no/vmpws/v2/vmp/search?searchType=product&currentPage={}&q=%3Arelevance%3AnewProducts%3Atrue"
_DETAILS = 'https://www.vinmonopolet.no/vmpws/v3/vmp/products/{}?fields=FULL'

_NOW = time.strftime('%Y-%m-01')
_IMAGE = {'thumbnail': 'https://bilder.vinmonopolet.no/bottle.png',
          'product': 'https://bilder.vinmonopolet.no/bottle.png'}


def _process_images(images):
    return {img['format']: img['url'] for img in images} if images else _IMAGE


def _process(products) -> List[dict]:
    return [{
        'index': int(product.get('code', 0)),
        'navn': product.get('name', '-'),
        'volum': product.get('volume', {}).get('value', 0.0),
        'land': product.get('main_country', {}).get('name', '-'),
        'distrikt': product.get('district', {}).get('name', '-'),
        'underdistrikt': product.get('sub_District', {}).get('name', '-'),
        'kategori': product.get('main_category', {}).get('name', '-'),
        'underkategori': product.get('main_sub_category', {}).get('name', '-'),
        'url': f'https://www.vinmonopolet.no{product.get("url", "")}',
        'status': product.get('status', '-'),
        'kan kjøpes': product.get('buyable', False),
        'utgått': product.get('expired', False),
        'tilgjengelig for bestilling': product.get('productAvailability', {}).get('deliveryAvailability', {}).get('availableForPurchase', False),
        'bestillingsinformasjon': product.get('productAvailability', {}).get('deliveryAvailability', {}).get('infos', [{}])[0].get('readableValue', '-'),
        'tilgjengelig i butikk': product.get('productAvailability', {}).get('storesAvailability', {}).get('availableForPurchase', False),
        'butikkinformasjon': product.get('productAvailability', {}).get('storesAvailability', {}).get('infos', [{}])[0].get('readableValue', '-'),
        'produktutvalg': product.get('product_selection', '-'),
        'bærekraftig': product.get('sustainable', False),
        'bilde': _process_images(product.get('images')),
        f'pris {_NOW}': product.get('price', {}).get('value', 0.0),
    } for product in products]


def _news(page: int) -> List[dict]:
    """Extract new products from a single page."""
    for _ in range(10):
        try:
            response = requests.get(_NEW.format(page), proxies=_PROXY.get(), timeout=3)
            if response.status_code != 200:
                raise ValueError()

            response = response.json()
            products = response.get('productSearchResult', {}).get('products', [])

            return _process(products)
        except Exception as err:
            print(f'Error: Trying another proxy. {err}')
            _PROXY.renew()
    else:
        raise ValueError('Failed to fetch new products. Tried 10 times.')


def _details(product: int) -> dict:
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


def details(products: List[int] = None, max_workers=5):
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
        print(f'Processing products {i} to {i + step} of {len(products)}.')

        operations = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            results = {executor.submit(_details, product): product for product in products[i:i + step]}
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


def news(max_workers=10):
    response = requests.get(_NEW.format(0), proxies=_PROXY.get(), timeout=3)

    if response.status_code != 200:
        raise ValueError('Failed to fetch new products.')

    response = response.json()
    pages = response.get('contentSearchResult', {}).get('pagination', {}).get('totalPages', 0)

    ids = []
    old = set(_DATABASE.distinct('index'))
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(_news, range(pages)))

        new = list({product['index'] for result in results for product in result} - old)

        operations = [pymongo.UpdateOne(
            {'index': product['index']},
            {'$set': product},
            upsert=True
        ) for result in results for product in result]

        result = _DATABASE.bulk_write(operations)
        print(f'Inserted {result.upserted_count} new products.')
        print(f'Updated {result.modified_count} existing products.')

        ids.extend(new)
    if ids:
        details(ids)


# if __name__ == '__main__':
#     news()
