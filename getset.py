"""Getters and setters used by the application."""

import logging

import pandas as pd

from database import uniques, load, plots
from category import CATEGORY
from visualise import graphs


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
    # Loading data for the selected category from the database.
    state['data'] = load(state['valgt']['kategori'])

    # Remove duplicates if any.
    if state['data'].index.duplicated().any():
        _LOGGER.error('Found duplicates! Removing them.')
        state['data'] = state['data'][~state['data'].index.duplicated(keep='first')]

    # Rearranging the columns of the data.
    _rearrange(state)

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
    products = products.rename(columns={prices[-1]: 'pris'})

    products = products.sort_values(
        by=state['prisendring']['kolonner'],
        ascending=state['prisendring']['stigende']
    ).head(int(state['prisendring']['antall']))

    # plot = plots(list(products.index))
    plot = graphs(products, prices)

    df = pd.concat([products, plot], axis=1)

    if len(prices) < 2:
        df['pris_gammel'] = df['pris'].copy()
    else:
        df = df.rename(columns={prices[-2]: 'pris_gammel'})

    state['prisendring']['data'] = {str(k): v for k, v in df.reset_index().T.to_dict().items()}

    state['flag']['updating'] = False


def reset_selection(state):
    """
    Resets the selection to 'Alle'.

    Parameters
    ----------
    state : dict
        The current state of the application.
    """
    for feature in state['valgt'].to_dict():
        state['valgt'][feature] = [] if feature != 'kategori' else state['valgt'][feature]

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
    cols = ['navn', 'volum', 'land',
            'distrikt', 'underdistrikt',
            'kategori', 'underkategori',
            'url',
            'status', 'kan kjøpes', 'utgått',
            'tilgjengelig for bestilling', 'bestillingsinformasjon',
            'tilgjengelig i butikk', 'butikkinformasjon',
            'produktutvalg',
            'bærekraftig',
            'bilde',
            'prisendring']

    price = list(set(state['data'].columns) - set(cols))
    price = sorted(price, key=lambda x: pd.Timestamp(x.split(' ')[1]))

    state['data'] = state['data'][cols + price]


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
    state['dropdown']['mulig'] = {
        col: {
            str(k): k for k in sorted([v for v in list(df[col].unique())
                                       if v and v != '-'])
        }
        for col in df
        if col in _FEATURES
    }

    # Convert volume to neatly formatted string.
    state['dropdown']['mulig']['volum'] = {
        str(vol): f'{vol:g} cL'
        for vol in state['dropdown']['mulig']['volum'].to_dict().values()
    }

    # state['dropdown']['mulig'] = {
    #     col: sorted(
    #         [v for v in list(df[col].unique()) if v and v != '-']
    #     )
    #     for col in df
    #     if col in _FEATURES
    # }
    # state['dropdown']['mulig']['volum'] = [f'{vol:g} cL' for vol in state['dropdown']['mulig']['volum']]

    # LEGG TIL LOGIKK ALA FINN.NO

    # state['dropdown']['underkategori'] = {
    #     **{'Alle': 'Alle underkategorier'},
    #     **{category: category
    #        for category in state['dropdown']['possible']['subcategory']}
    # }

    # which = 'selected' if state['selection']['underkategori'] != 'Alle' else 'possible'
    # state['dropdown']['selected']['volume'] = {
    #     **{'Alle': 'Alle volum'},
    #     **{str(volume): f'{volume:g} cL'
    #        for volume in state['dropdown'][which]['volume']}
    # }

    # which = 'selected' if state['selection']['volume'] != 'Alle' else which
    # state['dropdown']['selected']['country'] = {
    #     **{'Alle': 'Alle land'},
    #     **{country: country
    #        for country in state['dropdown'][which]['country']}
    # }

    # which = 'selected' if state['selection']['country'] != 'Alle' else which
    # state['dropdown']['selected']['district'] = {
    #     **{'Alle': 'Alle distrikter'},
    #     **{district: district
    #        for district in state['dropdown'][which]['district']}
    # }

    # which = 'selected' if state['selection']['district'] != 'Alle' else which
    # state['dropdown']['selected']['subdistrict'] = {
    #     **{'Alle': 'Alle underdistrikter'},
    #     **{district: district
    #        for district in state['dropdown'][which]['subdistrict']}
    # }


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

    for feature, values in state['valgt'].to_dict().items():
        if feature == 'kategori':
            continue

        if feature == 'volum':
            values = [float(val.split(' ')[0]) for val in values]
        else:
            values = [str(val) for val in values]

        if df[feature].isin(values).any():
            df = df[df[feature].isin(values)]
        else:
            state['valgt'][feature] = []

    return df
