"""State management and initialisation of the application."""

import writer

from category import CATEGORY
from getset import initialise, get_data, set_discounts, reset_selection


STATE = writer.init_state({

    # dropdown
    # ----------------------------------------------------------------------------------------------
    # Dictionaries containing unique values for the selected category.
    # These are used to populate the selection dropdowns.
    # Dynamically updated when the category (etc.) is changed.

    'dropdown': {

        # The following are the unique values for each dropdown.
        # These are based on the full dataset (i.e., across categories).
        'kategori': {
            v.name: k.capitalize().replace('_', ' ') if '%' not in k else 'Cognac'
            for k, v in CATEGORY.__dict__['_value2member_map_'].items()
        },
        'underkategori': [],
        'volum': [],
        'land': [],
        'distrikt': [],
        'underdistrikt': [],

        # The following depends on the current selection.
        # These are dynamically updated any of the dropdowns are changed.
        # They reflect the actual unique values for the selected data.
        # See `getset._dropdown` for more information.
        'mulig': {
            'underkategori': [],
            'volum': [],
            'land': [],
            'distrikt': [],
            'underdistrikt': [],
        },
    },

    # valgt
    # ----------------------------------------------------------------------------------------------
    # Current selection for each dropdown.

    'valgt': {
        'kategori': [],
        'underkategori': [],
        'volum': [],
        'land': [],
        'distrikt': [],
        'underdistrikt': [],
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

    'prisendring': {
        'antall': '10',
        'stigende': True,
        'kolonner': ['prisendring'],
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

initialise(STATE)
