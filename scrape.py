"""Scrape products from vinmonopolet's website and store the results to a database."""

import os
import enum
import json
from typing import List
import concurrent.futures

import pymongo
import requests
import pandas as pd
from bs4 import BeautifulSoup
from pymongo.errors import BulkWriteError
from pymongo.results import BulkWriteResult
from pymongo.mongo_client import MongoClient


_CLIENT = MongoClient(
    f'mongodb+srv://{os.environ.get("mongodb_username")}:{os.environ.get("mongodb_password")}'
    f'@vinskraper.wykjrgz.mongodb.net/'
    f'?retryWrites=true&w=majority&appName=vinskraper'
)
_DATABASE = _CLIENT['vinskraper']['vin']

_URL = ('https://www.vinmonopolet.no/vmpws/v2/vmp/'
        'search?searchType=product'
        '&currentPage={}'
        '&q=%3Arelevance%3AmainCategory%3A{}')
_SESSION = requests.Session()

_PROXY = None
_PROXIES = None
_PROXY_URL = ('https://api.proxyscrape.com/v3/free-proxy-list/get?request=displayproxies'
              '&proxy_format=protocolipport&format=text&anonymity=Elite,Anonymous&timeout=20000')

_OLD = (pd.Timestamp.now() - pd.DateOffset(months=1)).strftime('%Y-%m-01')
_NOW = pd.Timestamp.now().strftime('%Y-%m-01')
_IMAGE = {'thumbnail': 'https://bilder.vinmonopolet.no/bottle.png',
          'product': 'https://bilder.vinmonopolet.no/bottle.png'}


class CATEGORY(enum.Enum):
    """
    Enum class for the different categories of products available at vinmonopolet.
    Extends the `scrape._URL` with the category value.
    """
    RED_WINE = 'rødvin'
    WHITE_WINE = 'hvitvin'
    SPARKLING_WINE = 'musserende_vin'
    PEARLING_WINE = 'perlende_vin'
    FORTIFIED_WINE = 'sterkvin'
    AROMATIC_WINE = 'aromatisert_vin'
    FRUIT_WINE = 'fruktvin'
    ROSE_WINE = 'rosévin'
    SPIRIT = 'brennevin'
    BEER = 'øl'
    CIDER = 'sider'
    SAKE = 'sake'
    MEAD = 'mjød'


def _upsert(data: List[dict]) -> BulkWriteResult:
    """
    Upsert the given data into the database.
    Calculates the price change percentage based on the previous and current price.

    Parameters
    ----------
    data : List[dict]
        The data to insert into the database.

    Returns
    -------
    BulkWriteResult
    """
    operations = [
        pymongo.UpdateOne(
            {'index': record['index']},
            [
                {'$set': record},
                {'$set': {
                    'prisendring': {'$cond': [
                        {'$gt': [f'$pris {_OLD}', 0]},
                        {'$multiply': [
                            {'$divide': [
                                {'$subtract': [record[f'pris {_NOW}'], f'$pris {_OLD}']},
                                f'$pris {_OLD}'
                            ]},
                            100
                        ]},
                        0
                    ]}
                }}
            ],
            upsert=True
        )
        for record in data
    ]
    result = _DATABASE.bulk_write(operations)

    return result


def _renew_proxy():
    """
    Updates the `_PROXY` with the head of `_PROXIES`.
    Updates the `_PROXIES`-list when it's empty.
    """
    global _PROXY, _PROXIES

    if not _PROXIES:
        _PROXIES = [proxy for proxy in
                    requests.get(_PROXY_URL).text.split('\r\n')
                    if proxy and proxy.startswith('http')]

    _PROXY = {'http': _PROXIES.pop(0)}


def _scrape_page(
        category: CATEGORY,
        page: int
) -> requests.models.Response:
    """
    Scrape a single page of products from the given category.

    Parameters
    ----------
    category : CATEGORY
        The category of products to fetch.
    page : int
        The page number to fetch.

    Returns
    -------
    requests.models.Response
        The response from the page.

    Notes
    -----
        Tries to fetch the page using the `_PROXY`.
        If it fails, it renews the proxy (`_renew_proxy`) and retries.
        Returns code `500` if it fails 10 consecutive times.
    """
    for _ in range(10):
        try:
            response = _SESSION.get(_URL.format(page, category.value),
                                    proxies=_PROXY,
                                    timeout=3)
            break
        except Exception as err:
            print(f'├─ Error: '
                  f'Page {page} (trying another proxy); {err}')
            _renew_proxy()
    else:
        print(f'├─ Error: '
              f'Failed to fetch page {page} after 10 attempts.')
        response = requests.models.Response()
        response.status_code = 500

    return response


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


def _scrape_category(category: CATEGORY) -> bool:
    """
    Fetches all products from the given category.

    Parameters
    ----------
    category : CATEGORY
        The category of products to fetch.

    Returns
    -------
    bool

    Notes
    -----
        Loops through the pages of the category.
        Assumes that there is less than 1000 pages.
        Parses the response and extracts the products.
        Extracts the product information and stores it in the dictionary.
        The price key is suffixed with the current (year-month-)timestamp (%Y-%m-01).
    """

    # ----------------------------------------------------------------------------------------------
    # Loops through the pages of the category.
    # Assuming that there is less than 1000 pages.

    items = []
    for page in range(1000):
        response = _scrape_page(category, page)

        if response.status_code != 200:
            print(f'{category.name} Failed: '
                  f'Page {page} (status code {response.status_code}): '
                  f'{response.text}.')
            continue

        # ------------------------------------------------------------------------------------------
        # Parses the response and extracts the products.

        soup = BeautifulSoup(response.text, 'html.parser')
        if soup.string is None:
            print(f'{category.name} Error: Page {page} (no JSON found).')
            continue
        products = json.loads(soup.string).get('productSearchResult', {}).get('products', [])

        if not products:
            print(f'{category.name} No more products (final page: {page - 1}).')
            break

        # ------------------------------------------------------------------------------------------
        # Extracts the product information and stores it in the list.

        items.extend(_process(products))

    print(f'{category.name} Inserting into database.')
    try:
        result = _upsert(items)
    except BulkWriteError as bwe:
        print(f'{category.name} Error: '
              f'Bulk write operation; {bwe.details}.')
        return False
    print(f'{category.name} Modified {result.modified_count} records')
    print(f'{category.name} Upserted {result.upserted_count} records')
    print(f'{category.name} Success.')
    return True


def scrape(categories=None, max_workers=10):
    if categories is None:
        categories = list(CATEGORY)
    failed = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = {executor.submit(_scrape_category, category): category
                   for category in categories}

        for future in concurrent.futures.as_completed(results):
            try:
                success = future.result()
                if not success:
                    failed.append(results[future])
            except Exception as exc:
                category = results[future]
                print(f'{category.name} FAILED! Concurrency error: {exc}')
                failed.append(category)

    return failed


if __name__ == '__main__':
    scrape()
