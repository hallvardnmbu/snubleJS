import os
import pandas as pd

from scrape import CATEGORY, get_products


def store_products(
        category: CATEGORY = CATEGORY.RED_WINE,
        products_filename: str = "products.csv",
        prices_filename: str = "prices.csv"
):
    """
    Fetches all products from the given category and stores them in a CSV file.

    Parameters
    ----------
    category : CATEGORY
        The category of products to fetch.
    products_filename : str
        The name of the CSV file to store the products.
    prices_filename : str
        The name of the CSV file to store the prices updated prices.
    """
    products = get_products(category)
    df = pd.DataFrame(products).T
    df.to_csv(products_filename)

    _store_prices(df, prices_filename)


def _store_prices(products: pd.DataFrame, filename: str):
    products.reset_index(inplace=True, names="id")
    products.set_index(['name', 'volume', 'country', 'district', 'sub_district'], inplace=True)
    products.rename(columns={"price": pd.Timestamp.now()}, inplace=True)

    if not os.path.exists(filename):
        products.to_csv(filename)
        return

    old = pd.read_csv(filename, index_col=['name', 'volume', 'country', 'district', 'sub_district'])

    updated = pd.concat([old, products], axis=1)
    updated.to_csv(filename)


def store_prices(
        category: CATEGORY = CATEGORY.RED_WINE,
        filename: str = "prices.csv"
):
    """
    Fetches all products from the given category and updates the prices in the given CSV file.

    Parameters
    ----------
    category : CATEGORY
        The category of products to fetch.
    filename : str
        The name of the CSV file to store the prices updated prices.
    """
    products = get_products(category)
    products = pd.DataFrame(products).T
    _store_prices(products, filename)
