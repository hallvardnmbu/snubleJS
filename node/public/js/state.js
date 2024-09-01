// State management and initialization of the application

import { formatDate, subtractMonths } from "./date";
import { load } from "./database";
import { initialise } from "./getset";

const _discounts = load((amount = 1))
  .columns.filter((col) => col.startsWith("prisendring "))
  .sort((a, b) => {
    const dateA = new Date(...a.split(" ")[1].split("-").map(Number));
    const dateB = new Date(...b.split(" ")[1].split("-").map(Number));
    return dateA - dateB;
  });

const _month = formatDate(subtractMonths(new Date(), 1));

const STATE = {
  // side
  side: {
    gjeldende: 1,
    totalt: null,
  },

  // dropdown
  dropdown: {
    kategori: {},
    underkategori: {},
    volum: {},
    land: {},
    distrikt: {},
    underdistrikt: {},
    butikk: {},

    passer_til: {},
    argang: {},
    beskrivelse: {},
    kork: {},
    lagring: {},

    full: {
      kategori: [],
      underkategori: [],
      volum: [],
      land: [],
      distrikt: [],
      underdistrikt: [],
      butikk: [],

      passer_til: [],
      argang: [],
      beskrivelse: [],
      kork: [],
      lagring: [],
    },
  },

  // valgt
  valgt: {
    kategori: [],
    underkategori: [],
    volum: [],
    land: [],
    distrikt: [],
    underdistrikt: [],
    butikk: [],

    passer_til: [],
    argang: [],
    beskrivelse: [],
    kork: [],
    lagring: [],

    alkohol: null,
    fra: null,
    til: null,

    alkoholfritt: [],
  },

  // finn
  finn: {
    navn: null,
    filter: false,
  },

  // data
  data: {
    antall: 10,
    stigende: ["True"],
    fokus: _discounts[_discounts.length - 2],
    prisendring: {
      valg: _discounts[_discounts.length - 2],
      mulig: Object.fromEntries(
        _discounts.map((discounted) => [discounted, discounted.split(" ")[1]]),
      ),
    },
    dropdown: {
      [_discounts[_discounts.length - 2]]: "Prisendring",
      literpris: "Literpris",
      alkoholpris: "Alkoholpris",
      [_discounts[_discounts.length - 1].replace("endring", "")]: "Pris",
      navn: "Navn",
      volum: "Volum",
      alkohol: "Alkoholprosent",
      ny: "Nye produkter",
    },
    verdier: null,
  },

  // flag
  flag: {
    updating: false,
    invalid: false,
    valid: true,
    butikk: false,

    mellom: true,

    underkategori: false,
    distrikt: false,
    underdistrict: false,
  },
};

// Functions to manipulate state (these would be defined elsewhere)
initialise(STATE);
// setData(STATE, newData);
// setFocus(STATE, newFocus);
// setStore(STATE, newStore);
// setCountry(STATE, newCountry);
// setDistrict(STATE, newDistrict);
// setSubdistrict(STATE, newSubdistrict);
// setCategory(STATE, newCategory);
// setSubcategory(STATE, newSubcategory);
// setVolume(STATE, newVolume);
// resetSelection(STATE);
// setNextPage(STATE);
// setPreviousPage(STATE);
// setPageOne(STATE);
// setPage(STATE, newPage);

export default STATE;
