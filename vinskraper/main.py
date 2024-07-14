"""State management and initialisation of the application."""

import streamsync

from scrape import scrape_all
from getset import CATEGORY, set_data, set_selection, get_products, reset_selection


STATE = streamsync.init_state({

    # dir
    # ----------------------------------------------------------------------------------------------
    # Directory for storing data.

    'dir': './storage/',

    # dropdown
    # ----------------------------------------------------------------------------------------------
    # Dictionaries containing unique values for the selected category.
    # These are used to populate the selection dropdowns.
    # Dynamically updated when the category is changed.

    'dropdown': {
        'categories': {
            **{"Alle": "Alle kategorier"},
            **{v.name: k.capitalize().replace("_", " ") if "%" not in k else "Cognac"
               for k, v in CATEGORY.__dict__["_value2member_map_"].items()}
        },

        # The following depends on the selected category (`['selection']['kategori']`).
        # These are updated when the category is changed.
        'subcategories': None,
        'volumes': None,
        'countries': None,
        'districts': None,
        'subdistricts': None,
    },

    # selection
    # ----------------------------------------------------------------------------------------------
    # Current selection for each dropdown.
    # TODO: Handle selection change.
    # TODO: Selection change should cascade.

    'selection': {
        'kategori': 'RED_WINE',  # Alle
        'underkategori': 'Alle',
        'volum': 'Alle',
        'land': 'Alle',
        'distrikt': 'Alle',
        'underdistrikt': 'Alle',
    },

    # data
    # ----------------------------------------------------------------------------------------------
    # Dataframes containing all- and selected products for the chosen category and selection.

    'data': {
        'full': None,
        'selected': None,

        # Mapping from product ID (index) to product name.
        'id_to_name': None,
    },

    # plot
    # ----------------------------------------------------------------------------------------------
    # Dictionary containing plot settings and figure data.
    # TODO: Add figures.

    'plot': {
        'colours': {
            'background': '#F3F7F4',
            'black': '#06070E',

            'red': '#8E3B46',
            'green': '#136F63',
        },
    },

    # flag
    # ----------------------------------------------------------------------------------------------
    # Flags for fetching and updating data.
    # These are used to hide/show buttons and spinners.

    'flag': {
        # Spinners.
        'fetching': False,
        'updating': False,

        # Buttons.
        'fetch_allowed': False,
    },
})

set_data(STATE)
