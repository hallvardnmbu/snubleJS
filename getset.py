"""Getters and setters used by the application."""

import logging
from typing import List

import pandas as pd

from database import uniques, amount, load, search
from visualise import graph


_LOGGER = logging.getLogger(__name__)
_FEATURES = ['kategori', 'underkategori',
             'distrikt', 'underdistrikt',
             'volum', 'land']
_DIVIDER = [' ', 'UTILGJENGELIGE VALG', '-------------------']


def initialise(state):
    """
    Set the possible dropdown-values for each feature.
    Get the data for the initial selection.

    Parameters
    ----------
    state : dict
    """
    for feature, values in uniques(extract=_FEATURES).items():
        items = {
            str(k): k
            for k in sorted([v for v in values if v and v != '-'])
        }
        state['dropdown'][feature] = items
        state['dropdown']['full'][feature] = list(items.keys())

    # Convert volume to neatly formatted string.
    state['dropdown']['volum'] = {
        str(vol): f'{vol:g} cL'
        for vol in state['dropdown']['volum'].to_dict().values()
    }

    set_data(state)


def set_data(state, fresh: bool = True):
    """
    Updates the data in the state to correspond with the current selection.

    Parameters
    ----------
    state : dict
        The current state of the application.
    fresh : bool
        Whether to reset the page number.
        Only set to False when the page number changes.
        See functions `set_{next/previous}_page`.
    """
    state['flag']['updating'] = True
    searching = state['finn']['navn'] is not None

    # Removing the divider from the selection.
    state['valgt'] = {
        feature: [v for v in values if v not in _DIVIDER]
        for feature, values in state['valgt'].to_dict().items()
    }

    # Loading data for the current selection.
    try:
        if searching:
            data = search(
                name=state['finn']['navn'],
                amount=int(state['data']['antall']) * 2,
                sorting=state['data']['fokus'],
                ascending=state['data']['stigende'],

                **state['valgt'].to_dict() if state['finn']['filter'] else {},
            )
        else:
            data = load(
                **state['valgt'].to_dict(),

                sorting=state['data']['fokus'],
                ascending=state['data']['stigende'],
                amount=int(state['data']['antall']),
                page=state['side']['gjeldende'],
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

    # Setting the discount data for the current selection.
    _discounts(state, data)

    # Setting the total number of pages.
    if fresh and not searching:
        state['side']['totalt'] = amount(
            **state['valgt'].to_dict(),
        ) // int(state['data']['antall'])
        state['side']['gjeldende'] = 1
    elif fresh and searching:
        state['side']['totalt'] = 1
        state['side']['gjeldende'] = 1

    state['flag']['updating'] = False


def set_next_page(state):

    if state['side']['gjeldende'] >= state['side']['totalt']:
        return

    state['side']['gjeldende'] += 1

    set_data(state, fresh=False)


def set_previous_page(state):

    if state['side']['gjeldende'] < 2:
        return

    state['side']['gjeldende'] -= 1

    set_data(state, fresh=False)


def _dropdown(
    state,
    feature: str,
    omit: List[str] = [],
    include_all: bool = False
):

    # Get the possible values for the current selection.
    # Omitting the current feature and the ones in the omit list.
    possible = uniques(
        extract=[feature],
        **{k: v for k, v in state['valgt'].to_dict().items() if k not in (omit + [feature])},
    )[feature]

    # Get the values that are not possible.
    others = (set(state['dropdown']['full'][feature]) - set(possible)) if include_all else []

    # Toggle flag if possible values, and a flag exists.
    if feature in state['flag'] and possible:
        state['flag'][feature] = True
    elif feature in state['flag']:
        state['flag'][feature] = False
        return

    # Update the dropdown for the current feature.
    # Including impossible values if `include_all` is `True`.
    state['dropdown'][feature] = {
        str(cat): cat if feature != 'volum' else (f'{float(cat):g} cL' if cat not in _DIVIDER else cat)
        for cat in sorted(possible)
        + (_DIVIDER if others else [])
        + sorted(others, key=lambda x: x if feature != 'volum' else float(x))
    }

    # Remove already selected values if they are not in the possible's list.
    for choice in [float(c) if feature == 'volum' else c for c in state['valgt'][feature]]:
        if choice not in possible:
            state['valgt'][feature].remove(choice)


def set_category(state, main: bool = True):

    # Toggle possibility of selecting subcategory if category is selected.
    # Update the possible dropdown for the subcategory otherwise.
    if not state['valgt']['kategori']:
        state['flag']['underkategori'] = False
        state['valgt']['underkategori'] = []
    else:
        _dropdown(state, 'underkategori')

    # Cascade downwards.
    set_subcategory(state, main=main)


def set_subcategory(state, main: bool = True):

    if not main:
        return

    _dropdown(state, 'land', omit=['distrikt', 'underdistrikt'], include_all=True)
    _dropdown(state, 'volum', include_all=True)

    set_country(state, main=False)
    set_volume(state, main=False)

    set_data(state)


def set_country(state, main: bool = True):

    # _dropdown(state, 'land', omit=['distrikt', 'underdistrikt'], include_all=True)

    # Toggle possibility of selecting district if a country is selected.
    # Update the possible dropdown for the district otherwise.
    if not state['valgt']['land']:
        state['flag']['distrikt'] = False
        state['flag']['underdistrikt'] = False
        state['valgt']['distrikt'] = []
        state['valgt']['underdistrikt'] = []
    else:
        _dropdown(state, 'distrikt', omit=['underdistrikt'])

    # Cascade downwards.
    set_district(state, main=main)


def set_district(state, main: bool = True):

    # Toggle possibility of selecting subdistrict if a district is selected.
    # Update the possible dropdown for the subdistrict otherwise.
    if not state['valgt']['distrikt']:
        state['flag']['underdistrikt'] = False
        state['valgt']['underdistrikt'] = []
    else:
        _dropdown(state, 'underdistrikt')

    # Cascade downwards.
    set_subdistrict(state, main=main)


def set_subdistrict(state, main: bool = True):

    if not main:
        return

    _dropdown(state, 'kategori', omit=['underkategori'], include_all=True)
    _dropdown(state, 'volum', include_all=True)

    set_category(state, main=False)
    set_volume(state, main=False)

    set_data(state)


def set_volume(state, main: bool = True):

    if not main:
        return

    _dropdown(state, 'kategori', omit=['underkategori'], include_all=True)
    _dropdown(state, 'land', omit=['distrikt', 'underdistrikt'], include_all=True)

    set_category(state, main=False)
    set_country(state, main=False)

    set_data(state)


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

    # Reset the dropdown.
    # Arbitrarily chosen, as all `set_{selection}` functions cascade downwards.
    set_category(state)


def reset_search(state):
    state['finn'] = {
        'navn': None,
        'filter': False,
    }
    set_data(state)


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
