import express from "express";
import { MongoClient, ServerApiVersion } from "mongodb";
import path from "path";
import { fileURLToPath } from "url";
import dotenv from "dotenv";

dotenv.config();

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const port = 3000;

let collection;

async function load({
  collection,
  category = null,
  subcategory = null,
  country = null,
  district = null,
  subdistrict = null,
  volume = null,
  year = null,

  nonalcoholic = false,

  cork = null,
  storage = null,

  description = null,
  store = null,
  pair = null,

  alcohol = null,
  from = null,
  to = null,

  sort = "discount",
  ascending = true,
  limit = 10,
  page = 1,

  search = null,
  filters = true,
  fresh = true,
} = {}) {
  let pipeline = [];

  if (search) {
    pipeline.push({
      $search: {
        index: "name",
        text: {
          query: search,
          path: "name",
        },
      },
    });
  }

  let matchStage = {
    // Only include updated products (i.e., non-expired ones).
    updated: true,

    // Match the specified parameters if they are not null.
    ...(category && filters ? { category: category } : {}),
    ...(subcategory && filters ? { subcategory: subcategory } : {}),
    ...(country && filters ? { country: country } : {}),
    ...(district && filters ? { district: district } : {}),
    ...(subdistrict && filters ? { subdistrict: subdistrict } : {}),
    ...(volume && filters ? { volume: volume } : {}),
    ...(year && filters ? { year: year } : {}),
    ...(cork && filters ? { cork: cork } : {}),
    ...(storage && filters ? { storage: storage } : {}),

    // Parameters that are arrays are matched using the $in operator.
    // ...(description.length && filters ? { "description.short": { $in: description } } : {}),
    // ...(store.length && filters ? { store: { $in: store } } : {}),
    // ...(pair.length && filters ? { pair: { $in: pair } } : {}),
  };

  if (alcohol) {
    matchStage["alcohol"] = { ...matchStage["alcohol"], $gte: alcohol };
  }
  if (!nonalcoholic) {
    matchStage["alcohol"] = { ...matchStage["alcohol"], $ne: null, $exists: true, $ne: 0 };
  }

  if (from || to) {
    let between = {};
    if (from) between["$gte"] = from;
    if (to) between["$lte"] = to;

    if (sort === "volume") {
      matchStage["volume"] = { ...matchStage["volume"], ...between };
    } else {
      matchStage[sort] = between;
    }
  }

  matchStage[sort] = { ...matchStage[sort], $exists: true, $ne: null };

  pipeline.push({ $match: matchStage });

  let total;
  if (fresh) {
    const tot = await collection.aggregate([...pipeline, { $count: "amount" }]).toArray();
    if (tot.length === 0) {
      throw new Error("No records found.");
    }
    total = Math.floor(tot[0].amount / limit);
  } else {
    total = null;
  }

  pipeline.push(
    { $sort: { [sort]: ascending ? 1 : -1 } },
    { $skip: (page - 1) * limit },
    { $limit: limit },
  );

  const data = await collection.aggregate(pipeline).toArray();

  return { data, total };
}

app.set("view engine", "ejs");
app.set("views", path.join(__dirname, "views"));
app.use(express.static(path.join(__dirname, "public")));

MongoClient.connect(
  `mongodb+srv://${process.env.MONGO_USR}:${process.env.MONGO_PWD}@snublejuice.faktu.mongodb.net/?retryWrites=true&w=majority&appName=snublejuice`,
  {
    serverApi: {
      version: ServerApiVersion.v1,
      strict: true,
      deprecationErrors: true,
    },
  },
)
  .then((client) => {
    const db = client.db("snublejuice");
    collection = db.collection("products");

    // Route to display products with pagination
    app.get("/", async (req, res) => {
      try {
        const currentPage = parseInt(req.query.currentPage) || 1;
        const sortBy = req.query.sortBy || "discount";
        const sortAsc = !(req.query.sortAsc === "false");

        let { data, total } = await load({
          collection,
          category: null,
          subcategory: null,
          country: null,
          district: null,
          subdistrict: null,
          volume: null,
          year: null,

          nonalcoholic: false,

          cork: null,
          storage: null,

          description: null,
          store: null,
          pair: null,

          alcohol: null,
          from: null,
          to: null,

          sort: sortBy,
          ascending: sortAsc,
          limit: 10,
          page: currentPage,

          search: null,
          filters: true,
          fresh: true,
        });

        res.render("products", {
          data: data,
          currentPage: currentPage,
          totalPages: total,
          sortBy: sortBy,
          sortAsc: sortAsc,
        });
      } catch (err) {
        console.error(err);
        res.status(500).send("Error fetching data from MongoDB.");
      }
    });

    app.listen(port, () => {
      console.log(`Server running at http://localhost:${port}`);
    });
  })
  .catch((error) => console.error(error));
