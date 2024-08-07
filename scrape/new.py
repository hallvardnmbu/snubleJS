"""
Fetch new products.
Fetch detailed information about products.

CRON JOB: 0 05 1,14 * *
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

_MONTH = time.strftime('%Y-%m-01')
_IMAGE = {'thumbnail': 'https://bilder.vinmonopolet.no/bottle.png',
          'product': 'https://bilder.vinmonopolet.no/bottle.png'}


def _process_images(images):
    return {img['format']: img['url'] for img in images} if images else _IMAGE


def _process(products) -> List[dict]:
    return [{
        'index': int(product.get('code', 0)),
        'navn': product.get('name', None),
        'volum': product.get('volume', {}).get('value', 0.0),
        'land': product.get('main_country', {}).get('name', None),
        'distrikt': product.get('district', {}).get('name', None),
        'underdistrikt': product.get('sub_District', {}).get('name', None),
        'kategori': product.get('main_category', {}).get('name', None),
        'underkategori': product.get('main_sub_category', {}).get('name', None),
        'url': f'https://www.vinmonopolet.no{product.get("url", "")}',
        'status': product.get('status', None),
        'kan kjøpes': product.get('buyable', False),
        'utgått': product.get('expired', True),

        'produktutvalg': product.get('product_selection', None),
        'bærekraftig': product.get('sustainable', False),
        'bilde': _process_images(product.get('images')),
        f'pris {_MONTH}': product.get('price', {}).get('value', 0.0),
        'literpris': 100 * product.get('price', {}).get('value', 0.0) / product.get('volume', {}).get('value', 1.0),
        'ny': 0,

        'tilgjengelig for bestilling': product.get(
            'productAvailability', {}
        ).get(
            'deliveryAvailability', {}
        ).get(
            'availableForPurchase', False
        ),

        'bestillingsinformasjon': product.get(
            'productAvailability', {}
        ).get(
            'deliveryAvailability', {}
        ).get(
            'infos', [{}]
        )[0].get(
            'readableValue', None
        ),

        'tilgjengelig i butikk': product.get(
            'productAvailability', {}
        ).get(
            'storesAvailability', {}
        ).get(
            'availableForPurchase', False
        ),

        'butikkinformasjon': product.get(
            'productAvailability', {}
        ).get(
            'storesAvailability', {}
        ).get('infos', [{}]
              )[0].get(
            'readableValue', None
        ),
    } for product in products]


def _news(page: int) -> List[dict]:
    """Extract new products from a single page."""
    for _ in range(10):
        try:
            response = requests.get(_NEW.format(page), proxies=_PROXY.get(), timeout=3)
            if response.status_code != 200:
                raise ValueError()
            products = response.json().get('productSearchResult', {}).get('products', [])
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

                'navn': details.get('name', None),
                'volum': details.get('volume', {}).get('value', 0.0),
                'land': details.get('main_country', {}).get('name', None),
                'distrikt': details.get('district', {}).get('name', None),
                'underdistrikt': details.get('sub_District', {}).get('name', None),
                'kategori': details.get('main_category', {}).get('name', None),
                'underkategori': details.get(
                    'main_sub_category', {}
                ).get('name', None),
                'url': f'https://www.vinmonopolet.no{details.get("url", "")}',
                'status': details.get('status', None),
                'kan kjøpes': details.get('buyable', False),
                'utgått': details.get('expired', False),
                'tilgjengelig for bestilling': details.get(
                    'productAvailability', {}
                ).get(
                    'deliveryAvailability', {}
                ).get(
                    'availableForPurchase', False
                ),
                'bestillingsinformasjon': details.get(
                    'productAvailability', {}
                ).get(
                    'deliveryAvailability', {}
                ).get(
                    'infos', [{}]
                )[0].get(
                    'readableValue', None
                ),
                'produktutvalg': details.get('product_selection', None),
                'bærekraftig': details.get('sustainable', False),
                'bilde': _process_images(details.get('images')),
                f'pris {_MONTH}': details.get('price', {}).get('value', 0.0),
                'ny': 0,

                'farge': details.get('color', None),
                'karakteristikk': [characteristic['readableValue'] for characteristic in
                                   details.get('content', {}).get('characteristics', [])],
                'ingredienser': [ingredient['readableValue'] for ingredient in
                                 details.get('content', {}).get('ingredients', [])],
                **{trait["name"].lower(): trait["readableValue"]
                    for trait in details.get('content', {}).get('traits', [])},
                'lukt': details.get('smell', None),
                'smak': details.get('taste', None),
                'allergener': details.get('allergens', None),

                'passer til': [element['name'] for element in details.get('content', {}).get('isGoodFor', [])],
                'lagring': details.get('content', {}).get('storagePotential', {}).get('formattedValue', None),
                'kork': details.get('cork', None),

                'beskrivelse': {'lang': details.get('content', {}).get('style', {}).get('description', None),
                                'kort': details.get('content', {}).get('style', {}).get('name', None)},
                'metode': details.get('method', None),
                'årgang': details.get('year', None),

                'literpris': details.get('litrePrice', {}).get('value', 0.0),
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

                if 'alkohol' in product:
                    try:
                        product['alkohol'] = float(product['alkohol'].replace(' prosent', '').replace(',', '.'))
                    except Exception:
                        product['alkohol'] = 0.0
                else:
                    product['alkohol'] = 0.0
                if product['årgang']:
                    product['årgang'] = int(product['årgang'])

                product = {key: value if value else None for key, value in product.items()}

                operations.append(
                    pymongo.UpdateOne(
                        {'index': product['index']},
                        {'$set': product},
                        upsert=True
                    )
                )
        _DATABASE.bulk_write(operations)


def news(max_workers=5):
    _DATABASE.update_many(
        {},
        {'$inc': {'ny': 1}}  # Increment 'ny' field by 1 for all documents.
    )

    expired = set(_CLIENT['vinskraper']['utgått'].distinct('index'))
    response = requests.get(_NEW.format(0), proxies=_PROXY.get(), timeout=3)

    if response.status_code != 200:
        raise ValueError('Failed to fetch new products.')

    response = response.json()
    pages = response.get('contentSearchResult', {}).get('pagination', {}).get('totalPages', 0)

    ids = list(_DATABASE.find({'oppdater': True}))
    _DATABASE.update_many(
        {'oppdater': True},
        {'$unset': {'oppdater': ''},
         '$set': {'ny': 0}}
    )

    old = set(_DATABASE.distinct('index'))
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(_news, range(pages)))

        new = list({product['index'] for result in results for product in result} - old)

        # If a new product already exists, but is expired, move it back to the main collection.
        _expired = set(new) & expired
        if _expired:
            moving = list(_CLIENT['vinskraper']['utgått'].find({'index': {'$in': list(_expired)}}))
            for record in moving:
                record['ny'] = 1
            _CLIENT['vinskraper']['utgått'].delete_many({'index': {'$in': list(_expired)}})
            _DATABASE.insert_many(moving)
            expired -= _expired

        operations = [pymongo.UpdateOne(
            {'index': product['index']},
            {'$set': product},
            upsert=True
        ) for result in results for product in result if product['index'] in new]

        result = _DATABASE.bulk_write(operations)
        print(f'Inserted {result.upserted_count} new products.')
        print(f'Updated {result.modified_count} existing products.')

        ids.extend(new)
    if ids:
        details(ids)
