"""State management and initialisation of the application."""

import streamsync

from getset import CATEGORY, set_data, set_category, get_products


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
        'path': './storage/RED_WINE.parquet',
    },

    'data': None,

    'plot': {
        'colours': {
            'background': '#F3F7F4',
            'black': '#06070E',

            'red': '#8E3B46',
            'green': '#136F63',
        },
    },

    'flag': {
        'fetching': False,
        'updating': False,

        'fetch_allowed': False,
    },
})

set_data(STATE)
