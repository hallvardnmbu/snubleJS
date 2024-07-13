"""Scrape products from Vinmonopolet's website."""

import os
import enum
import json
import logging

import requests
import pandas as pd
from bs4 import BeautifulSoup


_LOGGER = logging.getLogger(__name__)

_URL = ("https://www.vinmonopolet.no/vmpws/v2/vmp/"
        "search?searchType=product"
        "&currentPage={}"
        "&q=%3Arelevance%3AmainCategory%3A{}")

_PROXIES = None
_PROXY_URL = ("https://api.proxyscrape.com/v3/free-proxy-list/get?request=displayproxies"
              "&proxy_format=protocolipport&format=text&anonymity=Elite,Anonymous&timeout=20000")


class CATEGORY(enum.Enum):
    """
    Enum class for (some of) the different categories of products available at Vinmonopolet.
    Extends the `_URL` with the category value.
    """
    RED_WINE = "rødvin"
    WHITE_WINE = "hvitvin"
    COGNAC = ("brennevin%3AmainSubCategory%3Abrennevin_druebrennevin"
              "%3AmainSubSubCategory%3Abrennevin_druebrennevin_cognac_tradisjonell")

    ROSE_WINE = "rosévin"
    SPARKLING_WINE = "musserende_vin"
    PEARLING_WINE = "perlende_vin"
    FORTIFIED_WINE = "sterkvin"
    AROMATIC_WINE = "aromatisert_vin"
    FRUIT_WINE = "fruktvin"
    SPIRIT = "brennevin"
    BEER = "øl"
    CIDER = "sider"
    SAKE = "sake"
    MEAD = "mjød"


def _get_proxy():
    """Returns a proxy from the list of available proxies. Fetches new if the list is exhausted."""
    global _PROXIES

    if _PROXIES is None:
        _PROXIES = [proxy for proxy in
                    requests.get(_PROXY_URL).text.split('\r\n')
                    if proxy and proxy.startswith("http")]

    return {"http": _PROXIES.pop(0)}


def _get_code(keys: list, code: float) -> float:
    """Iteratively finds the next available code by adding `0.1` if duplicated."""
    _LOGGER.debug(f"Code {code} already exists, finding new code.")
    _code = int(code)
    while code in keys:
        code += 0.1 if code - _code < 0.9 else 0.01
    _LOGGER.debug(f"New code found: {code}.")
    return code


def _scrape_products(category: CATEGORY) -> dict:
    """
    Fetches all products from the given category.

    Parameters
    ----------
    category : CATEGORY
        The category of products to fetch.

    Returns
    -------
    dict
        A dictionary containing the products fetched from the given category.
        The product ID is used as the key, and the product information is stored as a dictionary.
    """
    _LOGGER.info(f"Fetching products from category {category.value}.")

    items = {}
    session = requests.Session()
    proxy = _get_proxy()

    # ----------------------------------------------------------------------------------------------
    # Loops through the pages of the category.
    # Assuming that there is less than 1000 pages.

    for page in range(1000):
        _LOGGER.debug(f"[Page] {page}.")

        # ------------------------------------------------------------------------------------------
        # Tries to fetch the page using the proxy.
        # If it fails, it tries with a new proxy.
        # Breaks if it fails 10 consecutive times.

        i = 0
        response = None
        while i < 10:
            try:
                response = session.get(_URL.format(page, category.value), proxies=proxy)
                break
            except requests.exceptions.ProxyError:
                _LOGGER.debug(" [Proxy] Error, trying another proxy.")
                proxy = _get_proxy()
                i += 1
            except Exception as e:
                _LOGGER.error(f"Error at page {page} (with proxy {proxy} at retry {i}).\n{e}")
                break

        if response is None or response.status_code != 200:
            _LOGGER.error(f"Failed to fetch page {page}.")
            break

        # ------------------------------------------------------------------------------------------
        # Parses the response and extracts the products.

        soup = BeautifulSoup(response.text, "html.parser")
        products = json.loads(soup.string)["productSearchResult"]["products"]
        if not products:
            _LOGGER.info(f"No more products (got to page {page - 1}).")
            break

        # ------------------------------------------------------------------------------------------
        # Extracts the product information and stores it in the dictionary.

        for product in products:
            code = product.get("code", None)

            name = product.get("name", None)
            price = product["price"].get("value", None)
            volume = product["volume"].get("value", None)
            country = product["main_country"].get("name", None)

            district = product["district"].get("name", None)
            sub_district = product["sub_District"].get("name", None)

            items[code if code not in items else _get_code(list(items.keys()), float(code))] = {
                "name": name,
                "price": price,
                "volume": volume,
                "country": country,
                "district": district,
                "sub_district": sub_district
            }

    return items


def update_products(
        category: CATEGORY = CATEGORY.RED_WINE,
        path: str = "./storage/RED_WINE.parquet",
) -> pd.DataFrame:
    """
    Fetches all products from the given category and stores (appends) the results to file `path`.
    The price column is suffixed with the current timestamp.

    Parameters
    ----------
    category : CATEGORY, optional
        The category of products to fetch.
        See enumerator `CATEGORY` for available options.
    path : str, optional
        The name of the `parquet` file to store the products.

    Returns
    -------
    pd.DataFrame
        The (updated) products.
    """
    _LOGGER.info(f"Storing products from category {category.value}.")

    products = _scrape_products(category)
    products = pd.DataFrame(products).T
    products.rename(
        columns={"price": f"price {pd.Timestamp.now().strftime('%Y-%m-%d')}"},
        inplace=True
    )

    if not os.path.exists(path):
        _LOGGER.debug(f"Creating new file: {path}.")
        products.to_parquet(path)
        return products

    old = pd.read_parquet(path)

    updated = pd.concat([old, products], axis=1)
    updated.to_parquet(path)

    return updated