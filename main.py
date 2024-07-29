"""State management and initialisation of the application."""

from datetime import datetime
import writer

from getset import initialise, set_data, set_country, set_district, set_subdistrict, set_category, set_subcategory, set_volume, reset_selection, reset_search, set_next_page, set_previous_page


STATE = writer.init_state({

    # side
    # ----------------------------------------------------------------------------------------------
    # Current page of the data.

    'side': {
        'gjeldende': 1,
        'totalt': None,
    },

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
            'kategori': [],
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

    # finn
    # ----------------------------------------------------------------------------------------------
    # Text containing the name to search for.
    # Resets when the current selection is changed.

    'finn': {
        'navn': None,
        'filter': False,
    },

    # data
    # ----------------------------------------------------------------------------------------------
    # Dictionary containing the discount data for the current selection.
    # Dynamically updated when the selection is changed.
    # Ordered by the discount percentage.

    'data': {
        'antall': '10',
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

        'underkategori': False,
        'distrikt': False,
        'underdistrikt': False,
    }
})

initialise(STATE)
