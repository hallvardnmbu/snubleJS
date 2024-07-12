"""Fetches products from Vinmonopolet's website."""

import enum
import json
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from fp.fp import FreeProxy

_URL = ("https://www.vinmonopolet.no/vmpws/v2/vmp/"
        "search?searchType=product"
        "&currentPage={}"
        "&q=%3Arelevance%3AmainCategory%3A{}")


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


def get_free_proxies():
    proxy_list_url = "https://www.proxy-list.download/api/v1/get?type=https"
    response = requests.get(proxy_list_url)
    proxies = response.text.split('\r\n')
    return [proxy for proxy in proxies if proxy][::-1]


def get_products(category: CATEGORY, use_proxy: bool = True) -> dict:
    """
    Fetches all products from the given category.

    Parameters
    ----------
    category : CATEGORY
        The category of products to fetch.
    use_proxy : bool, optional
        Whether to use a VPN to fetch the products.

    Returns
    -------
    dict
        A dictionary containing the products fetched from the given category.
        The product ID is used as the key, and the product information is stored as a dictionary.
    """
    items = {}
    session = requests.Session()

    # Works: 195.159.124.56:85
    #        195.159.124.57:85
    proxy = {
        "http": f"http://195.159.124.57:85",
        "https": f"http://195.159.124.57:85"
    }

    for page in range(1000):
        response = session.get(_URL.format(page, category.value), proxies=proxy)

        if response.status_code != 200:
            print(f"Failed to fetch page {page}.")
            break

        soup = BeautifulSoup(response.text, "html.parser")

        products = json.loads(soup.string)["productSearchResult"]["products"]
        if not products:
            print(f"No more products (got to page {page - 1}).")
            break

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

    return items
