"""Getters and setters used by the application."""

import logging

import pandas as pd

from database import uniques, load
from visualise import graph


_LOGGER = logging.getLogger(__name__)
_FEATURES = ['underkategori', 'volum', 'land', 'distrikt', 'underdistrikt']


def initialise(state):

    # Set the possible dropdown-values for each feature.
    for feature, values in uniques(_FEATURES).items():
        state['dropdown'][feature] = {
            str(k): k
            for k in sorted([v for v in values if v and v != '-'])
        }

    # Convert volume to neatly formatted string.
    state['dropdown']['volum'] = {
        str(vol): f'{vol:g} cL'
        for vol in state['dropdown']['volum'].to_dict().values()
    }

    # Get the data for the initial category.
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

    # Loading data for the current selection.
    try:
        state['data'] = load(
            **state['valgt'].to_dict(),

            sorting=state['prisendring']['fokus'],
            ascending=state['prisendring']['stigende'],
            amount=state['prisendring']['antall']
        )
    except ValueError:
        state['flag']['updating'] = False
        state['flag']['invalid'] = True
        state['flag']['valid'] = False
        return
    state['flag']['invalid'] = False
    state['flag']['valid'] = True

    # Remove duplicates if any.
    if state['data'].index.duplicated().any():
        _LOGGER.error('Found duplicates! Removing them.')
        state['data'] = state['data'][~state['data'].index.duplicated(keep='first')]

    # Refreshing the selected dropdown values.
    # _dropdown(state, state['data'])

    # Setting the discount data for the current selection.
    _discounts(state)

    state['flag']['updating'] = False


def _discounts(state):
    """
    Updates the discount data in the state to correspond with the current selection.

    Parameters
    ----------
    state : dict
        The current state of the application.
    """
    prices = sorted([col for col in state['data'].columns
                     if col.startswith('pris ')],
                    key=lambda x: pd.Timestamp(x.split(' ')[1]))
    state['data']['pris'] = state['data'][prices[-1]]

    state['data']['plot'] = graph(state['data'].copy(), prices)

    if len(prices) < 2:
        state['data']['pris_gammel'] = state['data']['pris'].copy()
    else:
        state['data']['pris_gammel'] = state['data'][prices[-2]]

    state['prisendring']['data'] = {
        str(k): v
        for k, v in state['data'].reset_index().T.to_dict().items()
    }


def reset_selection(state):
    """
    Resets the selection to 'Alle'.

    Parameters
    ----------
    state : dict
        The current state of the application.
    """
    for feature in state['valgt'].to_dict():
        state['valgt'][feature] = []

    get_data(state)


# def _dropdown(state, df: pd.DataFrame):
#     """
#     Refreshes the valid dropdown values of the state to correspond with the current selection.

#     Parameters
#     ----------
#     state : dict
#         The current state of the application.
#     df : pd.DataFrame
#         The currently selected data.
#     """
#     # Update the possible dropdown values for the current category.
#     state['dropdown']['mulig'] = {
#         col: {
#             str(k): k for k in sorted([v for v in list(df[col].unique())
#                                        if v and v != '-'])
#         }
#         for col in df
#         if col in _FEATURES
#     }

#     # Convert volume to neatly formatted string.
#     state['dropdown']['mulig']['volum'] = {
#         str(vol): f'{vol:g} cL'
#         for vol in state['dropdown']['mulig']['volum'].to_dict().values()
#     }

#     state['dropdown']['mulig'] = {
#         col: sorted(
#             [v for v in list(df[col].unique()) if v and v != '-']
#         )
#         for col in df
#         if col in _FEATURES
#     }
#     state['dropdown']['mulig']['volum'] = [f'{vol:g} cL' for vol in state['dropdown']['mulig']['volum']]

#     LEGG TIL LOGIKK ALA FINN.NO

#     state['dropdown']['underkategori'] = {
#         **{'Alle': 'Alle underkategorier'},
#         **{category: category
#            for category in state['dropdown']['possible']['subcategory']}
#     }

#     which = 'selected' if state['selection']['underkategori'] != 'Alle' else 'possible'
#     state['dropdown']['selected']['volume'] = {
#         **{'Alle': 'Alle volum'},
#         **{str(volume): f'{volume:g} cL'
#            for volume in state['dropdown'][which]['volume']}
#     }

#     which = 'selected' if state['selection']['volume'] != 'Alle' else which
#     state['dropdown']['selected']['country'] = {
#         **{'Alle': 'Alle land'},
#         **{country: country
#            for country in state['dropdown'][which]['country']}
#     }

#     which = 'selected' if state['selection']['country'] != 'Alle' else which
#     state['dropdown']['selected']['district'] = {
#         **{'Alle': 'Alle distrikter'},
#         **{district: district
#            for district in state['dropdown'][which]['district']}
#     }

#     which = 'selected' if state['selection']['district'] != 'Alle' else which
#     state['dropdown']['selected']['subdistrict'] = {
#         **{'Alle': 'Alle underdistrikter'},
#         **{district: district
#            for district in state['dropdown'][which]['subdistrict']}
#     }
