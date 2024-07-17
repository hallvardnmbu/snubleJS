"""Scrape products from Vinmonopolet's website."""

import os
import enum
import json
import logging
from memoization import cached

import requests
import pandas as pd
from bs4 import BeautifulSoup
from pyarrow.lib import ArrowTypeError

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


def _renew_proxy():
    """Returns a proxy from the list of available proxies. Fetches new if the list is exhausted."""
    global _PROXY, _PROXIES

    if _PROXIES is None:
        _PROXIES = [proxy for proxy in
                    requests.get(_PROXY_URL).text.split('\r\n')
                    if proxy and proxy.startswith("http")]

    _PROXY = {"http": _PROXIES.pop(0)}


@cached(ttl=60 * 60 * 10)
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
    items = {}
    _renew_proxy()

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
            elif code in items:
                _LOGGER.error(f"├─ {_COLOUR['RED']}Error{_COLOUR['RESET']}: "
                              f"Duplicate product code: {code}. Skipping.")
                continue
            items[code] = {
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

                "pris": product.get("price", {}).get("value", "-"),
            }

    return items


def _update_products(
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
    _LOGGER.info(f"┌─ Fetching {category.name}")

    products = _scrape_products(category)
    products = pd.DataFrame(products).T
    products.rename(
        columns={"pris": f"pris {pd.Timestamp.now().strftime('%Y-%m-%d')}"},
        inplace=True
    )

    if not os.path.exists(path):
        _LOGGER.info(f"├─ No file found, creating new ({path}).")
        products.to_parquet(path)
        _LOGGER.info(f"└─ {_COLOUR['GREEN']}Success{_COLOUR['RESET']}.")

        return products

    _LOGGER.info(f"├─ Mergind new data with old.")
    old = pd.read_parquet(path)
    updated = products.combine_first(old)
    updated.to_parquet(path)
    _LOGGER.info(f"└─ {_COLOUR['GREEN']}Success{_COLOUR['RESET']}.")

    return updated


def scrape_all(directory: str = "./storage/") -> pd.DataFrame:
    """
    Vinmonopolet updates their prices monthly.
    This function should therefore be called at the start of each month to fetch the new prices.

    Parameters
    ----------
    directory : str, optional
        The directory to store the products.

    Notes
    -----
    Loops through all categories and updates all products for each category.
    The products are stored in the `directory`, suffixed by the `CATEGORY` names.
    """
    categories = [category for category in CATEGORY]
    dfs = []
    for category in categories:
        try:
            dfs.append(_update_products(category, path=directory + category.name + ".parquet"))
        except ArrowTypeError as err:
            categories.append(category)
            _LOGGER.error(f"└─ {_COLOUR['RED']}Error{_COLOUR['RESET']}: "
                          f"Could not save. Retrying.")
            raise err
    dfs = pd.concat(dfs)
    return dfs
