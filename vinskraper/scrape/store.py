"""Stores the fetched products and their prices in `parquet` files."""

import os
import pandas as pd

from .scrape import LOGGER, CATEGORY, scrape_products, scrape_prices


def store_products(
        category: CATEGORY = CATEGORY.RED_WINE,
        products: str = "../products.parquet",
        prices: str = "../prices.parquet"
):
    """
    Fetches all products from the given category and stores them in file `products` (overwrites).
    Updates the prices in file `prices` with the newly fetched values (appends).
    This function should not be called as regularly as `update_prices`.
    Only call this function when you want to update the product list.

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

    _products = scrape_products(category)
    _products = pd.DataFrame(_products).T
    _products.to_parquet(products)

    _update_prices(_products, prices)


def _update_prices(
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
        products.to_parquet(file)
        return

    old = pd.read_parquet(file)

    updated = pd.concat([old, products], axis=1)
    updated.to_parquet(file)


def update_prices(
        category: CATEGORY = CATEGORY.RED_WINE,
        file: str = "../prices.parquet"
):
    """
    Fetches all products from the given category and updates (appends) their prices in `file`.
    This is the function to call when you want to update the prices of the products.

    Parameters
    ----------
    category : CATEGORY, optional
        The category of products to fetch.
    file : str, optional
        The name of the `parquet` file to store the updated prices.
    """
    LOGGER.info(f"Storing prices from category {category.value}.")

    prices = scrape_prices(category)
    prices = pd.DataFrame(prices).T
    _update_prices(prices, file)
