"""State management and initialisation of the application."""

from datetime import datetime
import writer

from getset import initialise, get_data, reset_selection


STATE = writer.init_state({

    # dropdown
    # ----------------------------------------------------------------------------------------------
    # Dictionaries containing unique values for the selected category.
    # These are used to populate the selection dropdowns.
    # Dynamically updated when the category (etc.) is changed.

    'dropdown': {

        'kategori': {},
        'underkategori': {},
        'volum': {},
        'land': {},
        'distrikt': {},
        'underdistrikt': {},

        'full': {
            'kategori': {},
            'underkategori': {},
            'volum': {},
            'land': {},
            'distrikt': {},
            'underdistrikt': {},
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
    # Dictionary containing the discount data for the current selection.
    # Dynamically updated when the selection is changed.
    # Ordered by the discount percentage.

    'data': {
        'antall': '5',
        'stigende': True,
        'fokus': 'prisendring',
        'dropdown': {
            'prisendring': 'prisendring',
            f'pris {datetime.now().strftime("%Y-%m-01")}': 'pris',
            'navn': 'navn',
            'kategori': 'kategori',
            'underkategori': 'underkategori',
            'land': 'land',
            'distrikt': 'distrikt',
            'underdistrikt': 'underdistrikt',
            'volum': 'volum',
        },
        'verdier': None
    },

    # flag
    # ----------------------------------------------------------------------------------------------
    # Flag to indicate when data is being updated, and if the current selection is invalid.

    'flag': {
        'updating': False,
        'invalid': False,
        'valid': True,
    }
})

initialise(STATE)
