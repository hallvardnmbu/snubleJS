"""Getters and setters used by the application."""

import os
import json
import pandas as pd

from scrape import scrape_all


_EN_TO_NO = {
    'subcategory': 'underkategori',
    'volume': 'volum',
    'country': 'land',
    'district': 'distrikt',
    'subdistrict': 'underdistrikt'
}


def set_data(state):
    """
    Updates the data in the state to correspond with the current category.

    Parameters
    ----------
    state : dict
        The current state of the application.
    """
    state['flag']['updating'] = True

    if state['selection']['category'] == 'Alle':
        files = os.listdir(state['dir'])
        if not files:
            state['data']['full'] = scrape_all(state['dir'])
        else:
            dfs = []
            for file in files:
                if file.endswith('.parquet'):
                    dfs.append(pd.read_parquet(os.path.join(state['dir'], file)))
            state['data']['full'] = pd.concat(dfs)
    else:
        path = str(os.path.join(state['dir'], state['selection']['category'] + '.parquet'))
        if not os.path.exists(path):
            dfs = scrape_all(state['dir'])
            state['data']['full'] = dfs[dfs['kategori'] == state['selection']['category']]
        else:
            state['data']['full'] = pd.read_parquet(path)
    state['data']['full']['meta'] = state['data']['full']['meta'].apply(json.loads)

    _sort_prices(state)

    state['data']['selected'] = state['data']['full'].copy()

    _refresh_dropdown(state)

    state['flag']['updating'] = False

    set_selection(state)
    _check_fetch_allowed(state)


def _sort_prices(state):
    """
    Sort the price columns of the data in the state by date.

    Parameters
    ----------
    state : dict
        The current state of the application.
    """
    cols = [col for col in state['data']['full'].columns if col.startswith('pris')]
    cols = sorted(cols, key=lambda x: pd.Timestamp(x.split(" ")[1]))
    state['data']['full'] = state['data']['full'][
        ['navn', 'volum', 'land', 'distrikt', 'underdistrikt', 'kategori', 'underkategori', 'meta']
        + cols
    ]


def _check_fetch_allowed(state):
    """
    Toggle flag if last update was within the current month.

    Parameters
    ----------
    state : dict
        The current state of the application.
    """
    now = pd.Timestamp.now().month
    if any([now == pd.Timestamp(col.split(" ")[1]).month
            for col in state['data']['selected'].columns
            if col.startswith('pris')]):
        state['flag']['fetch_allowed'] = False
    else:
        state['flag']['fetch_allowed'] = True


def get_products(state):
    """
    Fetch the current products from `vinmonopolet.no` and update the state with the newest data.

    Parameters
    ----------
    state : dict
        The current state of the application.
    """
    state['flag']['fetching'] = True
    _ = scrape_all(state['dir'])
    state['flag']['fetching'] = False

    set_data(state)


def _refresh_dropdown(state):
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

    state['data']['id_to_name'] = state['data']['selected']['navn'].to_dict()


def set_selection(state):
    """
    Updates the selected data in the state to correspond with the current selection.

    Parameters
    ----------
    state : dict
        The current state of the application.
    """
    state['flag']['updating'] = True

    df = state['data']['full'].copy()
    for feature in [feat for feat in state['selection'].to_dict() if feat != 'category']:
        df = _update_selection(state, df, feature)

    state['data']['selected'] = df
    _refresh_dropdown(state)

    state['flag']['updating'] = False


def _update_selection(state, df: pd.DataFrame, feature: str) -> pd.DataFrame:
    """
    Updates the selection for the given feature.

    Parameters
    ----------
    state : dict
        The current state of the application.
    df : pd.DataFrame
        The current data.
    feature : str
        The feature to update.

    Returns
    -------
    pd.DataFrame
        The updated data.
    """
    if state['selection'][feature] == 'Alle':
        return df

    if feature == 'volume' and any(df[_EN_TO_NO[feature]] == float(state['selection'][feature])):
        df = df[df[_EN_TO_NO[feature]] == float(state['selection'][feature])]
    elif any(df[_EN_TO_NO[feature]] == str(state['selection'][feature])):
        df = df[df[_EN_TO_NO[feature]] == state['selection'][feature]]
    else:
        state['selection'][feature] = 'Alle'

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
    set_selection(state)
    _check_fetch_allowed(state)