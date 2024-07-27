"""Getters and setters used by the application."""

import logging

import pandas as pd

from database import uniques, load
from visualise import graph


_LOGGER = logging.getLogger(__name__)
_FEATURES = ['kategori', 'underkategori',
             'distrikt', 'underdistrikt',
             'volum', 'land']
_DIVIDER = ['UTILGJENGELIGE VALG', '-------------------']


def initialise(state):
    """
    Set the possible dropdown-values for each feature.
    Get the data for the initial selection.

    Parameters
    ----------
    state : dict
    """
    for feature, values in uniques(extract=_FEATURES).items():
        state['dropdown']['full'][feature] = {
            str(k): k
            for k in sorted([v for v in values if v and v != '-'])
        }
        state['dropdown'][feature] = state['dropdown']['full'][feature]

    # Convert volume to neatly formatted string.
    state['dropdown']['full']['volum'] = {
        str(vol): f'{vol:g} cL'
        for vol in state['dropdown']['full']['volum'].to_dict().values()
    }
    state['dropdown']['volum'] = state['dropdown']['full']['volum']

    get_data(state)


def get_data(state):
    """
    Updates the data in the state to correspond with the current category.
    This function should only be called when the category is changed.

    Parameters
    ----------
    state : dict
        The current state of the application.
    """
    state['flag']['updating'] = True

    # Removing the divider from the selection.
    state['valgt'] = {
        feature: [v for v in values if v not in _DIVIDER]
        for feature, values in state['valgt'].to_dict().items()
    }

    # Loading data for the current selection.
    try:
        data = load(
            **state['valgt'].to_dict(),

            sorting=state['data']['fokus'],
            ascending=state['data']['stigende'],
            amount=state['data']['antall']
        )
    except KeyError:
        state['flag']['updating'] = False
        state['flag']['invalid'] = True
        state['flag']['valid'] = False
        return
    state['flag']['invalid'] = False
    state['flag']['valid'] = True

    # Remove duplicates if any.
    if data.index.duplicated().any():
        _LOGGER.error('Found duplicates! Removing them.')
        data = data.drop_duplicates()

    # Refreshing the selected dropdown values.
    _dropdown(state)

    # Setting the discount data for the current selection.
    _discounts(state, data)

    state['flag']['updating'] = False


def _discounts(state, data: pd.DataFrame):
    """
    Updates the discount data in the state to correspond with the current selection.

    Parameters
    ----------
    state : dict
        The current state of the application.
    data : pd.DataFrame
        The currently selected data.
    """
    prices = sorted([col for col in data.columns
                     if col.startswith('pris ')],
                    key=lambda x: pd.Timestamp(x.split(' ')[1]))
    data['pris'] = data[prices[-1]]

    data['plot'] = graph(data, prices)

    if len(prices) < 2:
        data['pris_gammel'] = data['pris'].copy()
    else:
        data['pris_gammel'] = data[prices[-2]]

    state['data']['verdier'] = {
        str(k): v
        for k, v in data.reset_index().T.to_dict().items()
    }


def reset_selection(state):
    """
    Resets the current selection.

    Parameters
    ----------
    state : dict
        The current state of the application.
    """
    for feature in state['valgt'].to_dict():
        state['valgt'][feature] = []

    get_data(state)


def _dropdown(state):
    """
    Refreshes the valid dropdown values of the state to correspond with the current selection.

    Parameters
    ----------
    state : dict
        The current state of the application.
    """
    values = uniques(
        extract=_FEATURES,
        **state['valgt'].to_dict(),
    )
    del values['kategori']

    for feature, values in values.items():
        others = set(state['dropdown']['full'][feature].to_dict().keys()) - set(values)

        state['dropdown'][feature] = {
            str(k): k
            for k in list(
                sorted(values, key=lambda x: float(x) if feature == 'volum' else x)
                + (_DIVIDER if others else [])
                + sorted(others, key=lambda x: float(x) if feature == 'volum' else x)
            )
        }

    # Convert volume to neatly formatted string.
    state['dropdown']['volum'] = {
        str(vol): f'{float(vol):g} cL' if vol not in _DIVIDER else vol
        for vol in state['dropdown']['volum'].to_dict().values()
    }
