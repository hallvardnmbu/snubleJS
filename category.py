"""Enum class for the different categories of products available at vinmonopolet."""

import enum


class CATEGORY(enum.Enum):
    """
    Enum class for the different categories of products available at vinmonopolet.
    Extends the `scrape._URL` with the category value.
    """
    ALLE = 'alle_kategorier'

    RED_WINE = 'rødvin'
    WHITE_WINE = 'hvitvin'
    COGNAC = ('brennevin%3AmainSubCategory%3Abrennevin_druebrennevin'
              '%3AmainSubSubCategory%3Abrennevin_druebrennevin_cognac_tradisjonell')

    ROSE_WINE = 'rosévin'
    SPARKLING_WINE = 'musserende_vin'
    PEARLING_WINE = 'perlende_vin'
    FORTIFIED_WINE = 'sterkvin'
    AROMATIC_WINE = 'aromatisert_vin'
    FRUIT_WINE = 'fruktvin'
    SPIRIT = 'brennevin'
    BEER = 'øl'
    CIDER = 'sider'
    SAKE = 'sake'
    MEAD = 'mjød'
