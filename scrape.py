"""Fetches products from Vinmonopolet's website."""

import enum
import json
import requests
from bs4 import BeautifulSoup

_URL = ("https://www.vinmonopolet.no/vmpws/v2/vmp/"
        "search?searchType=product"
        "&currentPage={}"
        "&q=%3Arelevance%3AmainCategory%3A{}")

_PROXIES = None
_PROXY_URL = ("https://api.proxyscrape.com/v3/free-proxy-list/get?request=displayproxies"
              "&proxy_format=protocolipport&format=text")


class CATEGORY(enum.Enum):
    """
    Enum class for (some of) the different categories of products available at Vinmonopolet.
    Extends the `_URL` with the category value.
    """
    RED_WINE = "rødvin"
    WHITE_WINE = "hvitvin"
    COGNAC = ("%3AmainSubCategory%3Abrennevin_druebrennevin"
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


def get_proxy():
    global _PROXIES

    if _PROXIES is None:
        _PROXIES = [proxy for proxy in
                    requests.get(_PROXY_URL).text.split('\r\n')
                    if proxy and proxy.startswith("http")]

    return {"http": _PROXIES.pop(0)}


def get_products(category: CATEGORY) -> dict:
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
    session = requests.Session()
    proxy = get_proxy()

    # ----------------------------------------------------------------------------------------------
    # Loops through the pages of the category.
    # Assuming that there is less than 1000 pages.

    for page in range(1000):

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
                proxy = get_proxy()
                i += 1

        if response is None or response.status_code != 200:
            print(f"Failed to fetch page {page}.")
            break

        # ------------------------------------------------------------------------------------------
        # Parses the response and extracts the products.

        soup = BeautifulSoup(response.text, "html.parser")
        products = json.loads(soup.string)["productSearchResult"]["products"]
        if not products:
            print(f"No more products (got to page {page - 1}).")
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

            items[code] = {
                "name": name,
                "price": price,
                "volume": volume,
                "country": country,
                "district": district,
                "sub_district": sub_district
            }

    return items
