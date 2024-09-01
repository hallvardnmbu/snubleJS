require("dotenv").config();
const { MongoClient } = require("mongodb");

const mongoUri = `mongodb+srv://${process.env.mongodb_username}:${process.env.mongodb_password}@vinskraper.wykjrgz.mongodb.net/?retryWrites=true&w=majority&appName=vinskraper`;
const client = new MongoClient(mongoUri);

const _DATABASE = client.db("vinskraper").collection("vinmonopolet");
const _MAP = {
  årgang: "argang",
  "beskrivelse.kort": "beskrivelse",
  "passer til": "passer_til",
};

async function uniques(
  extract,
  kategori = [],
  underkategori = [],
  land = [],
  distrikt = [],
  underdistrikt = [],
  volum = [],
  argang = [],
  beskrivelse = [],
  kork = [],
  lagring = [],
  butikk = [],
  passer_til = [],
  kwargs = {},
) {
  let query = {
    utgått: false,
    "kan kjøpes": true,
  };

  if (!butikk) query["tilgjengelig for bestilling"] = true;
  if (butikk) query["butikk"] = { $all: butikk };
  if (passer_til) query["passer til"] = { $all: passer_til };

  [
    "kategori",
    "underkategori",
    "land",
    "distrikt",
    "underdistrikt",
    "beskrivelse.kort",
    "kork",
    "lagring",
  ].forEach((field) => {
    let value = eval(field);
    if (value) query[field] = { $in: value };
  });

  if (volum) query["volum"] = { $in: volum.map((v) => parseFloat(v)) };
  if (argang) query["årgang"] = { $in: argang.map((ar) => parseInt(ar.replace(".0", ""))) };

  let filtered = await _DATABASE.find(query).toArray();

  let mapping = {};
  for (let feature of extract) {
    let key = _MAP[feature] ? _MAP[feature] : feature;
    let values = [...new Set(filtered.map((item) => item[feature]))];
    values = values.filter((value) => value !== null && value !== "-");
    mapping[key] = values;
  }

  return mapping;
}

async function load(
  kategori = [],
  underkategori = [],
  land = [],
  distrikt = [],
  underdistrikt = [],
  volum = [],
  argang = [],
  beskrivelse = [],
  kork = [],
  lagring = [],
  butikk = [],
  passer_til = [],
  alkoholfritt = true,
  alkohol = null,
  fra = null,
  til = null,
  sorting = "prisendring",
  ascending = true,
  amount = 10,
  page = 1,
  search = "",
  filters = false,
  fresh = true,
) {
  let pipeline = [];

  if (search) {
    pipeline.push({
      $search: {
        index: "navn",
        text: {
          query: search,
          path: "navn",
        },
      },
    });
  }

  let match = {
    utgått: false,
    "kan kjøpes": true,
  };

  if (!butikk || !filters) match["tilgjengelig for bestilling"] = true;
  if (butikk && filters) match["butikk"] = { $all: butikk };
  if (passer_til && filters) match["passer til"] = { $all: passer_til };

  [
    "kategori",
    "underkategori",
    "land",
    "distrikt",
    "underdistrikt",
    "beskrivelse.kort",
    "kork",
    "lagring",
  ].forEach((field) => {
    let value = eval(field);
    if (value && filters) match[field] = { $in: value };
  });

  if (volum && filters) match["volum"] = { $in: volum.map((v) => parseFloat(v)) };
  if (argang && filters)
    match["årgang"] = { $in: argang.map((ar) => parseInt(ar.replace(".0", ""))) };

  if (alkohol) {
    if (!match["alkohol"]) match["alkohol"] = {};
    match["alkohol"]["$gte"] = alkohol;
  }
  if (!alkoholfritt) {
    if (!match["alkohol"]) match["alkohol"] = {};
    match["alkohol"]["$ne"] = null;
  }

  if (fra || til) {
    let between = {};
    if (fra) between["$gte"] = fra;
    if (til) between["$lte"] = til;
    if (sorting == "volum") {
      if (!match["volum"]) match["volum"] = {};
      Object.assign(match["volum"], between);
    } else {
      match[sorting] = between;
    }
  }
  if (!match[sorting]) match[sorting] = {};
  match[sorting]["$exists"] = true;
  match[sorting]["$ne"] = null;

  pipeline.push({ $match: match });

  let total = null;
  if (fresh) {
    total = await _DATABASE.aggregate([...pipeline, { $count: "amount" }]).toArray();
    if (total.length > 0) {
      total = total[0]["amount"];
    } else {
      throw new Error("No records found.");
    }
  }

  if (page >= 1665) {
    // TODO: Raise error. This leads to MongoDB error, due to huge skip (below).
  }

  pipeline.push(
    { $sort: { [sorting]: ascending ? 1 : -1 } },
    { $skip: (page - 1) * amount },
    { $limit: amount },
  );

  let collection = await _DATABASE.aggregate(pipeline).toArray();

  // TODO: Convert to DataFrame equivalent in JavaScript if needed.

  return [collection, total];
}
