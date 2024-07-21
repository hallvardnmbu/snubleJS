"""Scrape products from vinmonopolet's website."""

import json
import logging
from typing import List

import requests
import pandas as pd
from bs4 import BeautifulSoup
from pymongo.errors import BulkWriteError

from category import CATEGORY
from database import upsert, discounts


_LOGGER = logging.getLogger(__name__)
_COLOUR = {
    "RED": "\033[31m",
    "GREEN": "\033[32m",
    "RESET": "\033[0m",
}

_URL = ("https://www.vinmonopolet.no/vmpws/v2/vmp/"
        "search?searchType=product"
        "&currentPage={}"
        "&q=%3Arelevance%3AmainCategory%3A{}")
_SESSION = requests.Session()

_PROXY = None
_PROXIES = None
_PROXY_URL = ("https://api.proxyscrape.com/v3/free-proxy-list/get?request=displayproxies"
              "&proxy_format=protocolipport&format=text&anonymity=Elite,Anonymous&timeout=20000")


def _renew_proxy():
    """
    Updates the `_PROXY` with the head of `_PROXIES`.
    Updates the `_PROXIES`-list when it's empty.
    """
    global _PROXY, _PROXIES

    if not _PROXIES:
        _PROXIES = [proxy for proxy in
                    requests.get(_PROXY_URL).text.split('\r\n')
                    if proxy and proxy.startswith("http")]

    _PROXY = {"http": _PROXIES.pop(0)}


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
            response = _SESSION.get(_URL.format(page, category.value), proxies=_PROXY)
            break
        except Exception as err:
            _LOGGER.error(f"├─ {_COLOUR['RED']}Error{_COLOUR['RESET']}: "
                          f"Page {page} (trying another proxy); {err}")
            _renew_proxy()
    else:
        _LOGGER.error(f"├─ {_COLOUR['RED']}Error{_COLOUR['RESET']}: "
                      f"Failed to fetch page {page} after 10 attempts.")
        response = requests.models.Response()
        response.status_code = 500

    return response


def _scrape_category(category: CATEGORY) -> List[dict]:
    """
    Fetches all products from the given category.

    Parameters
    ----------
    category : CATEGORY
        The category of products to fetch.

    Returns
    -------
    List of dict
        A list containing the products fetched from the given category.

    Notes
    -----
        Loops through the pages of the category.
        Assumes that there is less than 1000 pages.
        Parses the response and extracts the products.
        Extracts the product information and stores it in the dictionary.
        The price key is suffixed with the current (year-month)timestamp (%Y-%m-01).
    """
    items = []
    today = pd.Timestamp.now().strftime('%Y-%m-01')

    # ----------------------------------------------------------------------------------------------
    # Loops through the pages of the category.
    # Assuming that there is less than 1000 pages.

    # TODO: Parallelise the fetching. Each session should use its own proxy.
    for page in range(1000):
        response = _scrape_page(category, page)

        if response.status_code != 200:
            _LOGGER.error(f"├─ {_COLOUR['RED']}Failed{_COLOUR['RESET']}: "
                          f"Page {page} (status code {response.status_code}): "
                          f"{response.text}.")
            continue

        # ------------------------------------------------------------------------------------------
        # Parses the response and extracts the products.

        soup = BeautifulSoup(response.text, "html.parser")
        products = json.loads(soup.string).get("productSearchResult", {}).get("products", [])

        if not products:
            _LOGGER.info(f"├─ No more products (final page: {page - 1}).")
            break

        # ------------------------------------------------------------------------------------------
        # Extracts the product information and stores it in the dictionary.

        for product in products:
            code = product.get("code", None)
            if code is None:
                _LOGGER.error(f"├─ {_COLOUR['RED']}Error{_COLOUR['RESET']}: "
                              f"Product without code: {product}. Skipping.")
                continue

            items.append({
                "index": code,
                "navn": product.get("name", "-"),
                "volum": product.get("volume", {}).get("value", 0.0),

                "land": product.get("main_country", {}).get("name", "-"),
                "distrikt": product.get("district", {}).get("name", "-"),
                "underdistrikt": product.get("sub_District", {}).get("name", "-"),

                "kategori": product.get("main_category", {}).get("name", "-") if category != CATEGORY.COGNAC else "Cognac",
                "underkategori": product.get("main_sub_category", {}).get("name", "-"),

                "meta": json.dumps({
                    "url": f"https://www.vinmonopolet.no{product.get('url', '')}",

                    "status": product.get("status", "-"),
                    "kan kjøpes": product.get("buyable", False),
                    "utgått": product.get("expired", False),
                    "kan bestilles": product.get("storesAvailability", {}).get(
                        "infos", [{}]
                    )[0].get("readableValue", "-"),
                    "produktutvalg": product.get("product_selection", "-"),
                    "bærekraftig": product.get("sustainable", False),

                    "bilde": {img['format']: img['url'] for img in product.get("images", [{
                        "format": "thumbnail",
                        "url": "https://bilder.vinmonopolet.no/bottle.png"
                    }, {
                        "format": "product",
                        "url": "https://bilder.vinmonopolet.no/bottle.png"
                    }])},
                }),

                f"pris {today}": product.get("price", {}).get("value", 0.0),
            })

    return items


def _update_products(category: CATEGORY):
    """
    Fetches all products from the given category and stores (appends) the results to the MongoDB
    collection.

    Parameters
    ----------
    category : CATEGORY
        The category of products to fetch.
        See enumerator `CATEGORY` for available options.

    Raises
    ------
    BulkWriteError
        If there is an issue with the bulk write operation.
        This is printed out in `scrape()`, and retried later.
    """
    _LOGGER.info(f"┌─ Fetching {category.name}")
    items = _scrape_category(category)
    _LOGGER.info(f"├─ Inserting into database.")
    result = upsert(items, category)
    _LOGGER.info(f"│ ├─ Modified {result.modified_count} records")
    _LOGGER.info(f"│ └─ Upserted {result.upserted_count} records")
    _LOGGER.info(f"├─Updating discounts.")
    discounts(category)
    _LOGGER.info(f"└─ {_COLOUR['GREEN']}Success{_COLOUR['RESET']}.")


def scrape():
    """
    Vinmonopolet updates their prices monthly.
    This function should therefore be called at the start of each month to fetch the new prices.
    Retries a category if there is an issue with the bulk write operation. Maximum 10 retries.

    Notes
    -----
    Loops through all categories and updates all products for each category.
    The products are stored in the `directory`, suffixed by the `CATEGORY` names.
    """
    _renew_proxy()

    retries = 0
    categories = [cat for cat in CATEGORY if cat != CATEGORY.ALLE]
    for category in categories:
        try:
            _update_products(category)
        except BulkWriteError as bwe:
            retries += 1
            categories.append(category) if retries < 10 else None
            _LOGGER.error(f"└─ {_COLOUR['RED']}Error{_COLOUR['RESET']}: "
                          f"Bulk write operation; {bwe.details}."
                          f"{'Retrying.' if retries < 10 else ''}")


if __name__ == "__main__":
    scrape()
