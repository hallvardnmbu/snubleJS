"""Getters and setters used by the application."""

import logging

import pandas as pd

from database import load, plots
from category import CATEGORY


_LOGGER = logging.getLogger(__name__)
_NOR = {
    'subcategory': 'underkategori',
    'volume': 'volum',
    'country': 'land',
    'district': 'distrikt',
    'subdistrict': 'underdistrikt'
}
_ENG = {v: k for k, v in _NOR.items()}


def get_data(state):
    """
    Updates the data in the state to correspond with the current category.
    This function should only be called when the category is changed.

    Parameters
    ----------
    state : dict
        The current state of the application.
    """
    # Loading data for the selected category from the database.
    state['data'] = load(CATEGORY[state['selection']['category']])

    # Remove duplicates if any.
    if state['data'].index.duplicated().any():
        _LOGGER.error('Found duplicates! Removing them.')
        state['data'] = state['data'][~state['data'].index.duplicated(keep='first')]

    # Rearranging the columns of the data.
    _rearrange(state)

    # Setting the possible dropdown values for the current category.
    state['dropdown']['possible'] = {
        _ENG[col]: sorted([c for c in list(state['data'][col].unique()) if c and c != '-'])
        for col in state['data']
        if col in _NOR.values()
    }

    # Refreshing the selected dropdown values.
    _dropdown(state, state['data'])

    # Setting the discount data for the current selection.
    set_discounts(state)


def set_discounts(state):
    """
    Updates the discount data in the state to correspond with the current selection.

    Parameters
    ----------
    state : dict
        The current state of the application.
    """
    state['flag']['updating'] = True

    products = _selection(state)
    _dropdown(state, products)

    prices = sorted([col for col in products.columns
                     if col.startswith('pris ')],
                    key=lambda x: pd.Timestamp(x.split(' ')[1]))
    products = products.rename(columns={prices[-1]: 'pris'}).replace({'-': None})

    products = products.sort_values(
        by=state['discount']['feature'],
        ascending=state['discount']['ascending']
    ).head(int(state['discount']['top']))

    plot = plots(list(products.index))

    df = pd.concat([products, plot], axis=1)

    if len(prices) < 2:
        df['pris_gammel'] = df['pris'].copy()
    else:
        df = df.rename(columns={prices[-2]: 'pris_gammel'})

    state['discount']['data'] = {str(k): v for k, v in df.reset_index().T.to_dict().items()}

    state['flag']['updating'] = False


def reset_selection(state):
    """
    Resets the selection to 'Alle'.

    Parameters
    ----------
    state : dict
        The current state of the application.
    """
    for feature in state['selection'].to_dict():
        state['selection'][feature] = 'Alle' if feature != 'category' else state['selection'][feature]

    set_discounts(state)


def _rearrange(state):
    """
    Rearrange the columns of the data in the state.
    Sort the price columns of the data in the state by date.

    Parameters
    ----------
    state : dict
        The current state of the application.
    """
    price = [col for col in state['data'].columns if col.startswith('pris ')]
    price = sorted(price, key=lambda x: pd.Timestamp(x.split(' ')[1]))

    cols = ['navn', 'volum', 'land',
            'distrikt', 'underdistrikt', 'kategori', 'underkategori',
            'meta', 'prisendring']

    state['data'] = state['data'][
        cols
        + list(set(state['data'].columns) - set(cols) - set(price))
        + price
    ]


def _dropdown(state, df: pd.DataFrame):
    """
    Refreshes the valid dropdown values of the state to correspond with the current selection.

    Parameters
    ----------
    state : dict
        The current state of the application.
    df : pd.DataFrame
        The currently selected data.
    """
    # Update the possible dropdown values for the current category.
    state['dropdown']['selected'] = {
        _ENG[col]: sorted([c for c in list(df[col].unique()) if c and c != '-'])
        for col in df
        if col in _NOR.values()
    }

    state['dropdown']['selected']['subcategory'] = {
        **{'Alle': 'Alle underkategorier'},
        **{category: category
           for category in state['dropdown']['possible']['subcategory']}
    }

    which = 'selected' if state['selection']['subcategory'] != 'Alle' else 'possible'
    state['dropdown']['selected']['volume'] = {
        **{'Alle': 'Alle volum'},
        **{str(volume): f'{volume:g} mL'
           for volume in state['dropdown'][which]['volume']}
    }

    which = 'selected' if state['selection']['volume'] != 'Alle' else which
    state['dropdown']['selected']['country'] = {
        **{'Alle': 'Alle land'},
        **{country: country
           for country in state['dropdown'][which]['country']}
    }

    which = 'selected' if state['selection']['country'] != 'Alle' else which
    state['dropdown']['selected']['district'] = {
        **{'Alle': 'Alle distrikter'},
        **{district: district
           for district in state['dropdown'][which]['district']}
    }

    which = 'selected' if state['selection']['district'] != 'Alle' else which
    state['dropdown']['selected']['subdistrict'] = {
        **{'Alle': 'Alle underdistrikter'},
        **{district: district
           for district in state['dropdown'][which]['subdistrict']}
    }


def _selection(state) -> pd.DataFrame:
    """
    Filter the category data based on current selection.

    Parameters
    ----------
    state : dict
        The current state of the application.

    Returns
    -------
    df : pd.DataFrame
        The filtered data based on the current selection.
    """
    df = state['data'].copy()

    for feature in state['selection'].to_dict():
        if feature == 'category' or state['selection'][feature] == 'Alle':
            continue

        if feature == 'volume' and any(df[_NOR[feature]] == float(state['selection'][feature])):
            df = df[df[_NOR[feature]] == float(state['selection'][feature])]
        elif any(df[_NOR[feature]] == str(state['selection'][feature])):
            df = df[df[_NOR[feature]] == state['selection'][feature]]
        else:
            state['selection'][feature] = 'Alle'

    return df
