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
    state['data']['data'] = pd.read_parquet(state['parameter']['path'])
    _refresh_data(state)
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
            for col in state['data']['data'].columns
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

    state['data']['data'] = update_products(
        CATEGORY[state['parameter']['category']['value']],
        state['parameter']['path'],
    )
    _refresh_data(state)

    state['flag']['fetching'] = False

    _check_fetch_allowed(state)


def _refresh_data(state):
    state['data']['volumes'] = {
        **{'Alle': 'Fokuser på alle volumer'},
        **{str(volume): f'{volume:g} mL'
           for volume in sorted([v for v in state['data']['data']['volume'].unique() if v])}
    }
    state['data']['countries'] = {
        **{'Alle': 'Fokuser på alle land'},
        **{country: country
           for country in sorted([c for c in state['data']['data']['country'].unique().tolist() if c])}
    }
    state['data']['districts'] = {
        **{'Alle': 'Fokuser på alle distrikter'},
        **{district: district
           for district in
           sorted([d for d in state['data']['data']['district'].unique().tolist() if d])}
    }
    state['data']['names'] = state['data']['data']['name'].to_dict()
