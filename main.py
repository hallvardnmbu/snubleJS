"""State management and initialisation of the application."""

import writer

from scrape import CATEGORY
from getset import get_data, set_data, reset_selection


STATE = writer.init_state({

    # dropdown
    # ----------------------------------------------------------------------------------------------
    # Dictionaries containing unique values for the selected category.
    # These are used to populate the selection dropdowns.
    # Dynamically updated when the category is changed.

    'dropdown': {
        'categories': {
            v.name: k.capitalize().replace("_", " ") if "%" not in k else "Cognac"
            for k, v in CATEGORY.__dict__["_value2member_map_"].items()
        },

        # The following depends on the selected category (`['selection']['category']`).
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

    'selection': {
        'category': 'ALLE',
        'subcategory': 'Alle',
        'volume': 'Alle',
        'country': 'Alle',
        'district': 'Alle',
        'subdistrict': 'Alle',
    },

    # data
    # ----------------------------------------------------------------------------------------------
    # Dataframes containing all- and selected products for the chosen category and selection.
    # TODO: Remove data once the necessary data is plotted/found, to save memory.

    'data': {
        'full': None,
        'selected': None,

        'best': {str(i): {} for i in range(1, 6)}
    },

    # plot
    # ----------------------------------------------------------------------------------------------
    # Dictionary containing plot settings and figure data.
    # TODO: Add figures.

    'plot': {
        'colours': {
            'background': '#F3F7F4',
            'white': '#FFFFFF',
            'black': '#06070E',

            'red': '#8E3B46',
            'green': '#136F63',
        },

        'best': {}
    },

    # flag
    # ----------------------------------------------------------------------------------------------
    # Flags for fetching and updating data.
    # These are used to hide/show buttons and spinners.

    'flag': {
        # Spinners.
        'updating': False,

        # Message.
        'no_discounts': True,
    },
})

get_data(STATE)
