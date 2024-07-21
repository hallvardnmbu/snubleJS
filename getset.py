"""Getters and setters used by the application."""

import json
import pandas as pd

from scrape import scrape
from database import load
from category import CATEGORY
from visualise import graph_best_prices


_EN_TO_NO = {
    'subcategory': 'underkategori',
    'volume': 'volum',
    'country': 'land',
    'district': 'distrikt',
    'subdistrict': 'underdistrikt'
}


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

    # Loading data for the selected category from the database.
    state['data']['full'] = load(CATEGORY[state['selection']['category']])

    # Parsing the JSON metadata.
    state['data']['full']['meta'] = state['data']['full']['meta'].apply(json.loads)

    # Replacing missing values (`'-'` and `0.0`) with `None`.
    state['data']['full'] = state['data']['full'].replace('-', None)
    for price in [col for col in state['data']['full'].columns if col.startswith('pris ')]:
        state['data']['full'][price] = state['data']['full'][price].replace(0.0, None)
    state['data']['full'].sort_values('prisendring', ascending=True, inplace=True)

    # Rearranging the columns of the `full` data.
    # Updating the selected data to correspond with the full data.
    # Refreshing the valid dropdown values.
    _rearrange(state)
    state['data']['selected'] = state['data']['full'].copy()
    _dropdown(state)

    state['flag']['updating'] = False

    set_data(state)


def _rearrange(state):
    """
    Rearrange the columns of the data in the state.
    Sort the price columns of the data in the state by date.

    Parameters
    ----------
    state : dict
        The current state of the application.
    """
    price = [col for col in state['data']['full'].columns if col.startswith('pris ')]
    price = sorted(price, key=lambda x: pd.Timestamp(x.split(" ")[1]))

    cols = ['navn', 'volum', 'land',
            'distrikt', 'underdistrikt', 'kategori', 'underkategori',
            'meta', 'prisendring']

    state['data']['full'] = state['data']['full'][
        cols
        + list(set(state['data']['full'].columns) - set(cols) - set(price))
        + price
    ]


# def _check_fetch_allowed(state):
#     """
#     Toggle flag if last update was within the current month.
#
#     Parameters
#     ----------
#     state : dict
#         The current state of the application.
#     """
#     now = pd.Timestamp.now().month
#     if any([now == pd.Timestamp(col.split(" ")[1]).month
#             for col in state['data']['selected'].columns
#             if col.startswith('pris ')]):
#         state['flag']['fetch_allowed'] = False
#     else:
#         state['flag']['fetch_allowed'] = True
#
#
# def scrape_products(state):
#     """
#     Fetch the current products from `vinmonopolet.no` and update the state with the newest data.

#     Parameters
#     ----------
#     state : dict
#         The current state of the application.
#     """
#     state['flag']['fetching'] = True
#     scrape()
#     state['flag']['fetching'] = False
#     set_data(state)


def _dropdown(state):
    """
    Refreshes the valid dropdown values of the state to correspond with the current selection.

    Parameters
    ----------
    state : dict
        The current state of the application.
    """
    state['dropdown']['subcategories'] = {
        **{'Alle': 'Alle underkategorier'},
        **{category: category
           for category in
           sorted([c for c in state['data']['full']['underkategori'].unique().tolist() if c])}
    }

    data = 'selected' if state['selection']['subcategory'] != 'Alle' else 'full'
    state['dropdown']['volumes'] = {
        **{'Alle': 'Alle volum'},
        **{str(volume): f'{volume:g} mL'
           for volume in sorted([v for v in state['data'][data]['volum'].unique() if v])}
    }

    data = 'selected' if state['selection']['volume'] != 'Alle' else data
    state['dropdown']['countries'] = {
        **{'Alle': 'Alle land'},
        **{country: country
           for country in sorted([c for c in state['data'][data]['land'].unique().tolist() if c])}
    }

    data = 'selected' if state['selection']['country'] != 'Alle' else data
    state['dropdown']['districts'] = {
        **{'Alle': 'Alle distrikter'},
        **{district: district
           for district in
           sorted([d for d in state['data'][data]['distrikt'].unique().tolist() if d])}
    }

    data = 'selected' if state['selection']['district'] != 'Alle' else data
    state['dropdown']['subdistricts'] = {
        **{'Alle': 'Alle underdistrikter'},
        **{district: district
           for district in
           sorted([d for d in state['data'][data]['underdistrikt'].unique().tolist() if d])}
    }


def set_data(state):
    """
    Updates the selected data in the state to correspond with the current selection.
    This function should be called when dropdown values (except `category`) are changed.

    Parameters
    ----------
    state : dict
        The current state of the application.
    """
    state['flag']['updating'] = True

    df = state['data']['full'].copy()
    for feature in [feat for feat in state['selection'].to_dict() if feat != 'category']:
        df = _selection(state, df, feature)
    state['data']['selected'] = df

    for i in range(1, 6):
        try:
            state['data']['best'][str(i)] = {
                k: v for k, v in df.iloc[i].to_dict().items()
            }
        except IndexError:
            state['data']['best'][str(i)] = {'prisendring': 0}
            break

        price = sorted([col for col in df.columns if col.startswith('pris ')],
                       key=lambda x: pd.Timestamp(x.split(" ")[1]))[-1]
        state['data']['best'][str(i)]['pris'] = state['data']['best'][str(i)][price]

    if state['data']['best']['1']['prisendring']:
        state['flag']['no_discounts'] = False
    else:
        graph_best_prices(state)

    _dropdown(state)

    state['flag']['updating'] = False


def _selection(state, df: pd.DataFrame, column: str) -> pd.DataFrame:
    """
    Updates the data with respect to the given column.
    The values are filtered according to the current selection.

    Parameters
    ----------
    state : dict
        The current state of the application.
    df : pd.DataFrame
        The current data.
    column : str
        The column to update.

    Returns
    -------
    pd.DataFrame
        The updated data.
    """
    if state['selection'][column] == 'Alle':
        return df

    if column == 'volume' and any(df[_EN_TO_NO[column]] == float(state['selection'][column])):
        df = df[df[_EN_TO_NO[column]] == float(state['selection'][column])]
    elif any(df[_EN_TO_NO[column]] == str(state['selection'][column])):
        df = df[df[_EN_TO_NO[column]] == state['selection'][column]]
    else:
        state['selection'][column] = 'Alle'

    return df


def reset_selection(state):
    """
    Resets the selection to 'Alle'.

    Parameters
    ----------
    state : dict
        The current state of the application.
    """
    state['flag']['updating'] = True

    for feature in state['selection'].to_dict():
        state['selection'][feature] = 'Alle' if feature != 'category' else state['selection'][feature]

    state['flag']['updating'] = False
    set_data(state)
