"""Stores the fetched products and their prices in `parquet` files."""

import os
import pandas as pd

from scrape import LOGGER, CATEGORY, get_products


def store_products(
        category: CATEGORY = CATEGORY.RED_WINE,
        products: str = "products",
        prices: str = "prices"
):
    """
    Fetches all products from the given category and stores them in file `products` (overwrites).
    Updates the prices in file `prices` with the newly fetched values (appends).

    Parameters
    ----------
    category : CATEGORY, optional
        The category of products to fetch.
    products : str, optional
        The name of the `parquet` file to store the products.
        Overwrites the file if it exists.
    prices : str, optional
        The name of the `parquet` file to store the updated prices.
    """
    LOGGER.info(f"Storing products from category {category.value}.")

    _products = get_products(category)
    _products = pd.DataFrame(_products).T
    _products.to_parquet(products + ".parquet")

    _store_prices(_products, prices)


def _store_prices(
        products: pd.DataFrame,
        file: str
):
    """
    Updates (appends) the prices in the given file with the new values.

    Parameters
    ----------
    products : pd.DataFrame
        The products with their current metadata.
    file : str
        The name of the `parquet` file to store the updated prices.
    """
    LOGGER.info(f" Storing prices in {file}.")

    products = products[["price"]].copy()
    products.rename(columns={"price": pd.Timestamp.now()}, inplace=True)

    if not os.path.exists(file):
        LOGGER.debug(f"Creating new file {file}.")
        products.to_parquet(file + ".parquet")
        return

    old = pd.read_parquet(file + ".parquet")

    updated = pd.concat([old, products], axis=1)
    updated.to_parquet(file + ".parquet")


def store_prices(
        category: CATEGORY = CATEGORY.RED_WINE,
        file: str = "prices"
):
    """
    Fetches all products from the given category and updates (appends) their prices in `file`.

    Parameters
    ----------
    category : CATEGORY, optional
        The category of products to fetch.
    file : str, optional
        The name of the `parquet` file to store the updated prices.
    """
    LOGGER.info(f"Storing prices from category {category.value}.")

    products = get_products(category)
    products = pd.DataFrame(products).T
    _store_prices(products, file)
