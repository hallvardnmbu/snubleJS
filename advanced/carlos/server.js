//testing git cause i am a noob

import express from "express";
import { MongoClient } from "mongodb";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const port = 3000;

let collection;

const uri = `mongodb+srv://web:ByiT9WakPCj8izEO@vinskraper.wykjrgz.mongodb.net/`;

async function load({  
  collection,
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
  search = null,
  filters = false,
  fresh = true,
} = {}) {
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

  let matchStage = {
    utgått: false,
    "kan kjøpes": true,
    ...(butikk.length && filters ? { butikk: { $all: butikk } } : {}),
    ...(passer_til.length && filters ? { "passer til": { $all: passer_til } } : {}),
    ...(kategori.length && filters ? { kategori: { $in: kategori } } : {}),
    ...(underkategori.length && filters ? { underkategori: { $in: underkategori } } : {}),
    ...(volum.length && filters ? { volum: { $in: volum.map((v) => parseFloat(v)) } } : {}),
    ...(land.length && filters ? { land: { $in: land } } : {}),
    ...(distrikt.length && filters ? { distrikt: { $in: distrikt } } : {}),
    ...(underdistrikt.length && filters ? { underdistrikt: { $in: underdistrikt } } : {}),
    ...(argang.length && filters
      ? { årgang: { $in: argang.map((ar) => parseInt(ar.replace(".0", ""))) } }
      : {}),
    ...(beskrivelse.length && filters ? { "beskrivelse.kort": { $in: beskrivelse } } : {}),
    ...(kork.length && filters ? { kork: { $in: kork } } : {}),
    ...(lagring.length && filters ? { lagring: { $in: lagring } } : {}),
  };

  if (alkohol !== null) {
    matchStage["alkohol"] = { ...matchStage["alkohol"], $gte: alkohol };
  }
  if (!alkoholfritt) {
    matchStage["alkohol"] = { ...matchStage["alkohol"], $ne: null };
  }

  if (fra !== null || til !== null) {
    let between = {};
    if (fra !== null) between["$gte"] = fra;
    if (til !== null) between["$lte"] = til;

    if (sorting === "volum") {
      matchStage["volum"] = { ...matchStage["volum"], ...between };
    } else {
      matchStage[sorting] = between;
    }
  }

  matchStage[sorting] = { ...matchStage[sorting], $exists: true, $ne: null };

  pipeline.push({ $match: matchStage });

  let total;
  if (fresh) {
    const tot = await collection.aggregate([...pipeline, { $count: "amount" }]).toArray();
    if (tot.length === 0) {
      throw new Error("No records found.");
    }
    total = Math.floor(tot[0].amount / amount);
  } else {
    total = null;
  }

  pipeline.push(
    { $sort: { [sorting]: ascending ? 1 : -1 } },
    { $skip: (page - 1) * amount },
    { $limit: amount },
  );

  const data = await collection.aggregate(pipeline).toArray();

  return { data, total };
}

app.set("view engine", "ejs");
app.set("views", path.join(__dirname, "views"));
app.use(express.static(path.join(__dirname, "public")));

MongoClient.connect(uri)
  .then((client) => {
    const db = client.db("vinskraper"); // Replace with your database name
    collection = db.collection("varer"); // Replace with your collection name

    // Route to display products with pagination
    app.get("/", async (req, res) => {
      try {
        const page = parseInt(req.query.page) || 1; // Get the current page number from query string, default to 1
        const limit = 10; // Number of products to display per page

        let { data, total } = await load({
          collection: collection,
          kategori: [],
          underkategori: [],
          land: [],
          distrikt: [],
          underdistrikt: [],
          volum: [],
          argang: [],
          beskrivelse: [],
          kork: [],
          lagring: [],
          butikk: [],
          passer_til: [],
          alkoholfritt: true,
          alkohol: null,
          fra: null,
          til: null,
          sorting: "prisendring",
          ascending: true,
          amount: limit,
          page: page,
          search: "",
          filters: false,
          fresh: true,
        });

        res.render("index", {
          data: data,
          currentPage: page,
          totalPages: total,
        });
      } catch (err) {
        console.error(err);
        res.status(500).send("Error fetching data from MongoDB");
      }
    });

    app.listen(port, () => {
      console.log(`Server running at http://localhost:${port}`);
    });
  })
  .catch((error) => console.error(error));
