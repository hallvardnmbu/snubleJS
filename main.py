"""State management and initialisation of the application."""

import writer

from scrape import CATEGORY
from getset import get_data, set_discounts, reset_selection


STATE = writer.init_state({

    # dropdown
    # ----------------------------------------------------------------------------------------------
    # Dictionaries containing unique values for the selected category.
    # These are used to populate the selection dropdowns.
    # Dynamically updated when the category (etc.) is changed.

    'dropdown': {
        'category': {
            v.name: k.capitalize().replace('_', ' ') if '%' not in k else 'Cognac'
            for k, v in CATEGORY.__dict__['_value2member_map_'].items()
        },

        # The following are the unique values for each dropdown.
        # These are statically updated when the category is changed.
        'possible': {
            'subcategory': None,
            'volume': None,
            'country': None,
            'district': None,
            'subdistrict': None,
        },

        # The following depends on the selected category (`['selection']['category']`).
        # These are dynamically updated when the category is changed.
        # See `getset._dropdown` for more information.
        'selected': {
            'subcategory': None,
            'volume': None,
            'country': None,
            'district': None,
            'subdistrict': None,
        },
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
    # DataFrame
    #   Contains the data for the current category.

    'data': None,

    # discount
    # ----------------------------------------------------------------------------------------------
    # Dictionary containing the discount data for the current selection.
    # Dynamically updated when the selection is changed.
    # Ordered by the discount percentage.

    'discount': {
        'top': '10',
        'ascending': True,
        'feature': 'prisendring',
        'dropdown': {
            'prisendring': 'prisendring',
            'pris': 'pris',
            'navn': 'navn',
            'kategori': 'kategori',
            'underkategori': 'underkategori',
            'land': 'land',
            'distrikt': 'distrikt',
            'underdistrikt': 'underdistrikt',
            'volum': 'volum',
        },
        'data': None
    },

    # flag
    # ----------------------------------------------------------------------------------------------
    # Flag to indicate when data is being updated.

    'flag': {
        'updating': False
    }
})

get_data(STATE)
