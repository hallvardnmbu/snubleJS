"""State management and initialisation of the application."""

import datetime
import writer

from database import load
from getset import initialise, set_data, set_focus, set_store, set_country, set_district, set_subdistrict, set_category, set_subcategory, set_volume, reset_selection, set_next_page, set_previous_page, set_page_one, set_page


# To prevent errors before the newest data is loaded, the newest column is set manually.
_prices = sorted([col for col in load(amount=1)[0].columns if col.startswith('pris ')],
                  key=lambda x: datetime.date(*[int(y) for y in x.split(' ')[-1].split('-')]))


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
        'butikk': {},
        'passer_til': {},
        'argang': {},
        'beskrivelse': {},
        'kork': {},
        'lagring': {},

        'full': {
            'kategori': [],
            'underkategori': [],
            'volum': [],
            'land': [],
            'distrikt': [],
            'underdistrikt': [],
            'butikk': [],
            'passer_til': [],
            'argang': [],
            'beskrivelse': [],
            'kork': [],
            'lagring': []
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
        'butikk': [],
        'passer_til': [],
        'argang': [],
        'beskrivelse': [],
        'kork': [],
        'lagring': [],

        'fra': None,
        'til': None,
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
        'antall': 10,
        'stigende': ['True'],
        'fokus': 'prisendring',
        'prisendring': {
            'valg': None,
            'mulig': {
                dato: dato.split(' ')[-1] for dato in _prices
            }
        },
        'dropdown': {
            'prisendring': 'Prisendring',
            'literpris': 'Literpris',
            'alkoholpris': 'Alkoholpris',
            _prices[-1]: 'Pris',
            'navn': 'Navn',
            'volum': 'Volum',
            'alkohol': 'Alkoholprosent',
            'ny': 'Nye produkter',
        },
        'verdier': None,
    },

    # flag
    # ----------------------------------------------------------------------------------------------
    # Flag to indicate when data is being updated, and if the current selection is invalid.

    'flag': {
        'updating': False,
        'invalid': False,
        'valid': True,
        'butikk': False,

        'mellom': True,

        'underkategori': False,
        'distrikt': False,
        'underdistrikt': False,
    }
})

initialise(STATE)
