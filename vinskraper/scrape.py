"""Scrape products from Vinmonopolet's website."""

import os
import enum
import json
import logging

import requests
import pandas as pd
from bs4 import BeautifulSoup
from pyarrow.lib import ArrowTypeError

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
    """
    Iteratively finds the next available code by adding `0.1` if duplicated.

    Parameters
    ----------
    keys : list
        A list of existing keys.
    code : float
        The current code to check for duplicates.

    Returns
    -------
    float
        The next available code.
    """
    _LOGGER.debug(f"  [ID] Code {code} already exists, finding new code.")
    _code = int(code)
    while code in keys:
        code += 0.1 if code - _code < 0.9 else 0.01
    _LOGGER.debug(f"   [ID] New code found: {code}.")
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
    _LOGGER.info(f" [Scraping] {category.value}.")

    items = {}
    session = requests.Session()
    proxy = _get_proxy()

    # ----------------------------------------------------------------------------------------------
    # Loops through the pages of the category.
    # Assuming that there is less than 1000 pages.

    # TODO: Parallelise the fetching. Each session should use its own proxy.

    for page in range(1000):
        _LOGGER.debug(f"  [Page] {page}.")

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
                _LOGGER.debug("   [Proxy] Error, trying another proxy.")
                proxy = _get_proxy()
                i += 1
            except Exception as e:
                _LOGGER.error(f"[Error] Page {page} (with proxy {proxy} at retry {i}).\n{e}")
                break

        if response is None:
            _LOGGER.error(f"[Failed] Got no response for page {page}.")
            break
        elif response.status_code != 200:
            _LOGGER.error(f"[Failed] Got status code {response.status_code} for page {page}.")
            break

        # ------------------------------------------------------------------------------------------
        # Parses the response and extracts the products.

        soup = BeautifulSoup(response.text, "html.parser")
        products = json.loads(soup.string).get("productSearchResult", {}).get("products", [])
        if not products:
            _LOGGER.info(f"  [Done] No more products (final page: {page - 1}).")
            break

        # ------------------------------------------------------------------------------------------
        # Extracts the product information and stores it in the dictionary.

        for product in products:
            code = product.get("code", None)
            items[code if code not in items else _get_code(list(items.keys()), float(code))] = {
                "navn": product.get("name", None),
                "volum": product.get("volume", {}).get("value", None),

                "land": product.get("main_country", {}).get("name", None),
                "distrikt": product.get("district", {}).get("name", None),
                "underdistrikt": product.get("sub_District", {}).get("name", None),
                "underkategori": product.get("main_sub_category", {}).get("name", None),

                "meta": {
                    "url": f"https://www.vinmonopolet.no{product.get('url', None)}",

                    "bilde": {img['format']: img['url'] for img in product.get("images", [{
                        "format": "thumbnail",
                        "url": "https://bilder.vinmonopolet.no/bottle.png"
                    }, {
                        "format": "product",
                        "url": "https://bilder.vinmonopolet.no/bottle.png"
                    }])},

                    "kan kjøpes": product.get("buyable", False),
                    "utgått": product.get("expired", False),
                    "kan bestilles": product.get("storesAvailability", {}).get(
                        "infos", [{}]
                    )[0].get("readableValue", None),
                },

                "pris": product.get("price", {}).get("value", None),
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
    _LOGGER.info(f" {category.value}.")

    products = _scrape_products(category)
    products = pd.DataFrame(products).T
    products.rename(
        columns={"pris": f"pris {pd.Timestamp.now().strftime('%Y-%m-%d')}"},
        inplace=True
    )

    if not os.path.exists(path):
        _LOGGER.info(f" [File] No file found, creating new (here: {path}).")
        products.to_parquet(path)
        _LOGGER.info(f" {category.value} successful.")
        return products

    old = pd.read_parquet(path)

    products["meta"] = products["meta"].apply(json.dumps)
    old["meta"] = old["meta"].apply(json.dumps)
    updated = pd.merge(
        old, products,
        on=[col for col in old.columns if not col.startswith("pris")],
        how='outer'
    )
    updated["meta"] = updated["meta"].apply(json.loads)

    updated.to_parquet(path)

    _LOGGER.info(f"[Updating] Success ({category.value}).")
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
    _LOGGER.info("[Updating] All categories.")

    categories = [category for category in CATEGORY]
    dfs = []
    for category in categories:
        try:
            df = _update_products(category, path=directory + category.name + ".parquet")
            if category:
                df['kategori'] = category.value.capitalize() if '%' not in category.value else 'Cognac'
                df = df[['navn', 'volum', 'land',
                         'distrikt', 'underdistrikt',
                         'kategori', 'underkategori',
                         'meta',
                         *[col for col in df.columns if col.startswith('pris')]]]
            dfs.append(df)
        except ArrowTypeError as err:
            categories.append(category)
            _LOGGER.error(f"[Error] {err}.\nRetrying {category.name} after a while.")
    dfs = pd.concat(dfs)

    _LOGGER.info("[Updating] Success (all categories).")
    return dfs
