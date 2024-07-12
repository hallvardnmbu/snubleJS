"""Getters and setters used by the application."""

import os
import pandas as pd

from scrape.store import CATEGORY, update_prices, store_products


def set_data(state):
    """
    Updates the data in the state to correspond with the current category.

    Parameters
    ----------
    state : dict
        The current state of the application.
    """
    if not os.path.exists(state['parameter']['products']):
        get_products(state)
    elif not os.path.exists(state['parameter']['prices']):
        get_prices(state)

    state['flag']['updating'] = True

    state['data'] = {
        'products': pd.read_parquet(state['parameter']['products']),
        'prices': pd.read_parquet(state['parameter']['prices']),
    }

    if state['data']['prices'].columns[-1] < pd.Timestamp.now() - pd.Timedelta(days=1):
        state['flag']['fetch_allowed'] = True

    state['flag']['updating'] = False


def set_category(state):
    """
    Updates the current category with the selected value.
    Thereafter, the data is updated by calling `set_data`.

    Parameters
    ----------
    state : dict
        The current state of the application.
    """
    category = state['parameter']['category']['value']
    state['parameter'] = {
        'category': {
            'name': state['categories'][category],
            'value': category,
        },
        'products': f"./storage/products_{category}.parquet",
        'prices': f"./storage/prices_{category}.parquet",
    }

    set_data(state)


def get_prices(state):
    """
    Fetch the current prices from `vinmonopolet.no` and update the state with the newest data.

    Parameters
    ----------
    state : dict
        The current state of the application.
    """
    state['flag']['fetching'] = True

    update_prices(
        CATEGORY[state['parameter']['category']['value']],
        state['parameter']['prices']
    )

    state['flag']['fetching'] = False

    set_data(state)


def get_products(state):
    """
    Fetch the current products from `vinmonopolet.no` and update the state with the newest data.

    Parameters
    ----------
    state : dict
        The current state of the application.
    """
    state['flag']['fetching'] = True

    store_products(
        CATEGORY[state['parameter']['category']['value']],
        state['parameter']['products'],
        state['parameter']['prices']
    )

    state['flag']['fetching'] = False

    set_data(state)
