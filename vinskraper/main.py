"""State management and initialisation of the application."""

import streamsync

from getset import CATEGORY, set_data, set_category, get_prices, get_products


STATE = streamsync.init_state({
    'categories': {
        v.name: k.capitalize().replace("_", " ") if "%" not in k else "Cognac"
        for k, v in CATEGORY.__dict__["_value2member_map_"].items()
    },

    'parameter': {
        'category': {
            'name': 'Rødvin',
            'value': 'RED_WINE',
        },
        'products': './storage/products_RED_WINE.parquet',
        'prices': './storage/prices_RED_WINE.parquet',
    },

    'data': {
        'products': None,
        'prices': None,
    },

    'plot': {
        'colours': {
            'pink': '#c37892',
            'brown': '#8a795d',
            'purple': '#746cc0',
            'red': 'red',
            'background': '#AAD3DF',
            'green': '#BCDAB1',
            'black': '#143439',
            'white': '#F3EFE8',
        },
    },

    'flag': {
        'fetching': False,
        'fetch_allowed': False,
        'updating': False,
    },
})

STATE.import_stylesheet("theme", "/stylesheet.css")

set_data(STATE)
