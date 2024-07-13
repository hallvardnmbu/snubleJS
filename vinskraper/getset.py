"""Getters and setters used by the application."""

import os
import pandas as pd

from scrape import CATEGORY, update_products


def set_data(state):
    """
    Updates the data in the state to correspond with the current category.

    Parameters
    ----------
    state : dict
        The current state of the application.
    """
    if not os.path.exists(state['parameter']['path']):
        get_products(state)
        return

    state['flag']['updating'] = True
    state['data'] = pd.read_parquet(state['parameter']['path'])
    state['flag']['updating'] = False

    _check_fetch_allowed(state)


def _check_fetch_allowed(state):
    """
    Toggle flag if last update was within the last 24 hours.

    Parameters
    ----------
    state : dict
        The current state of the application.
    """
    now = pd.Timestamp.now()
    if any([(now - pd.Timestamp(col.split(" ")[1])).days <= 1
            for col in state['data'].columns
            if col.startswith('price')]):
        state['flag']['fetch_allowed'] = False
    else:
        state['flag']['fetch_allowed'] = True


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
        'path': f"./storage/{category}.parquet",
    }

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

    state['data'] = update_products(
        CATEGORY[state['parameter']['category']['value']],
        state['parameter']['path'],
    )

    state['flag']['fetching'] = False

    _check_fetch_allowed(state)
