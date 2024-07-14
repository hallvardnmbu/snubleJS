"""Getters and setters used by the application."""

import os
import pandas as pd

from scrape import CATEGORY, scrape_all


def set_data(state):
    """
    Updates the data in the state to correspond with the current category.

    Parameters
    ----------
    state : dict
        The current state of the application.
    """
    state['flag']['updating'] = True

    if state['selection']['kategori'] == 'Alle':
        files = os.listdir(state['dir'])
        if not files:
            state['data']['full'] = scrape_all(state['dir'], category=True)
        else:
            dfs = []
            for file in files:
                if file.endswith('.parquet'):
                    df = pd.read_parquet(os.path.join(state['dir'], file))
                    name = getattr(CATEGORY, file.split('.')[0]).value
                    df['kategori'] = name.capitalize() if '%' not in name else 'Cognac'
                    df = df[['navn', 'volum', 'land',
                             'distrikt', 'underdistrikt',
                             'kategori', 'underkategori',
                             'meta',
                             *[col for col in df.columns if col.startswith('pris')]]]
                    dfs.append(df)
            state['data']['full'] = pd.concat(dfs)
    else:
        path = str(os.path.join(state['dir'], state['selection']['kategori'] + '.parquet'))
        if not os.path.exists(path):
            dfs = scrape_all(state['dir'])
            state['data']['full'] = dfs[dfs['kategori'] == state['selection']['kategori']]
        else:
            state['data']['full'] = pd.read_parquet(path)

    state['data']['selected'] = state['data']['full'].copy()

    _refresh_dropdown(state)

    state['flag']['updating'] = False

    set_selection(state)
    _check_fetch_allowed(state)


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
    state['dropdown']['volumes'] = {
        **{'Alle': 'Alle volum'},
        **{str(volume): f'{volume:g} mL'
           for volume in sorted([v for v in state['data']['selected']['volum'].unique() if v])}
    }
    state['dropdown']['countries'] = {
        **{'Alle': 'Alle land'},
        **{country: country
           for country in sorted([c for c in state['data']['selected']['land'].unique().tolist() if c])}
    }
    state['dropdown']['districts'] = {
        **{'Alle': 'Alle distrikter'},
        **{district: district
           for district in
           sorted([d for d in state['data']['selected']['distrikt'].unique().tolist() if d])}
    }
    state['dropdown']['subdistricts'] = {
        **{'Alle': 'Alle underdistrikter'},
        **{district: district
           for district in
           sorted([d for d in state['data']['selected']['underdistrikt'].unique().tolist() if d])}
    }
    state['dropdown']['subcategories'] = {
        **{'Alle': 'Alle underkategorier'},
        **{category: category
           for category in
           sorted([c for c in state['data']['selected']['underkategori'].unique().tolist() if c])}
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
    for feature in [feat for feat in state['selection'].to_dict() if feat != 'kategori']:
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

    if feature == 'volum' and any(df[feature] == float(state['selection'][feature])):
        df = df[df[feature] == float(state['selection'][feature])]
    elif any(df[feature] == str(state['selection'][feature])):
        df = df[df[feature] == state['selection'][feature]]
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
        state['selection'][feature] = 'Alle' if feature != 'kategori' else state['selection'][feature]

    state['flag']['updating'] = False
    set_selection(state)
    _check_fetch_allowed(state)