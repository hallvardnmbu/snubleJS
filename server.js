import express from "express";
import { MongoClient, ServerApiVersion } from "mongodb";
import path from "path";
import { fileURLToPath } from "url";
import dotenv from "dotenv";

dotenv.config();

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const categories = {
  null: null,
  alkoholfritt: "Alkoholfritt",
  aromatisert: "Aromatisert vin",
  brennevin: "Brennevin",
  fruktvin: "Fruktvin",
  hvitvin: "Hvitvin",
  mjød: "Mjød",
  musserende: "Musserende vin",
  perlende: "Perlende vin",
  rosévin: "Rosévin",
  rødvin: "Rødvin",
  sake: "Sake",
  sider: "Sider",
  sterkvin: "Sterkvin",
  øl: "Øl",
};

const app = express();
const port = 8080;

let collection;

async function load({
  collection,

  // Single parameters;
  category = null,
  subcategory = null,
  country = null,
  district = null,
  subdistrict = null,
  year = null,
  cork = null,
  storage = null,

  // Include non-alcoholic products;
  nonalcoholic = false,

  // Only show new products;
  news = false,

  // Array parameters;
  description = null,
  store = null,
  pair = null,

  // If specified, only include values >=;
  volume = null,
  alcohol = null,

  // Sorting;
  sort = "discount",
  ascending = true,

  // Pagination;
  limit = 10,
  page = 1,

  // Search, and whether to include filters (typically `false` for `search != null`);
  search = null,
  filters = true,

  // Calculate total pages;
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
    // updated: true,
    status: "aktiv",

    // Match the specified parameters if they are not null.
    ...(category && filters ? { category: category } : {}),
    ...(subcategory && filters ? { subcategory: subcategory } : {}),
    ...(country && filters ? { country: country } : {}),
    ...(district && filters ? { district: district } : {}),
    ...(subdistrict && filters ? { subdistrict: subdistrict } : {}),
    ...(year && filters ? { year: year } : {}),
    ...(cork && filters ? { cork: cork } : {}),
    ...(storage && filters ? { storage: storage } : {}),

    // Parameters that are arrays are matched using the $in operator.
    // ...(description.length && filters ? { "description.short": { $in: description } } : {}),
    ...(store && filters ? { stores: { $in: [store] } } : {}),
    // ...(pair.length && filters ? { pair: { $in: pair } } : {}),
  };

  if (volume) {
    matchStage["volume"] = { ...matchStage["volume"], $gte: volume };
  }

  if (alcohol) {
    matchStage["alcohol"] = { ...matchStage["alcohol"], $gte: alcohol };
  }
  if (!nonalcoholic) {
    matchStage["alcohol"] = { ...matchStage["alcohol"], $ne: null, $exists: true, $gt: 0 };
  }

  if (news) {
    matchStage["$or"] = [{ oldprice: { $exists: false } }, { oldprice: null }];
  }

  matchStage[sort] = { ...matchStage[sort], $exists: true, $ne: null };

  pipeline.push({ $match: matchStage });

  let total;
  if (fresh) {
    const tot = await collection.aggregate([...pipeline, { $count: "amount" }]).toArray();
    if (tot.length === 0) {
      total = 1;
    } else {
      total = Math.floor(tot[0].amount / limit) + 1;
    }
  } else {
    total = null;
  }

  pipeline.push(
    { $sort: { [sort]: ascending ? 1 : -1 } },
    { $skip: (page - 1) * limit },
    { $limit: limit },
  );

  try {
    const data = await collection.aggregate(pipeline).toArray();
    return { data, total };
  } catch (err) {
    return { data: null, total: 1 };
  }
}

app.set("view engine", "ejs");
app.set("views", path.join(__dirname, "views"));
app.use(express.static(path.join(__dirname, "public")));

MongoClient.connect(
  `mongodb+srv://${process.env.MONGO_USR}:${process.env.MONGO_PWD}@snublejuice.faktu.mongodb.net/?retryWrites=true&w=majority&appName=snublejuice`,
  {
    serverApi: {
      version: ServerApiVersion.v1,
      strict: false,
      deprecationErrors: true,
    },
  },
)
  .then((client) => {
    const db = client.db("snublejuice");
    collection = db.collection("products");

    app.get("/api/stores", async (req, res) => {
      try {
        const stores = await collection.distinct("stores");
        res.json(stores);
      } catch (err) {
        res.status(500).send(err);
      }
    });

    // Route to display products with pagination
    app.get("/", async (req, res) => {
      try {
        const page = parseInt(req.query.page) || 1;
        const sort = req.query.sort || "discount";
        const ascending = !(req.query.ascending === "false");
        const category = req.query.category || "null";
        const volume = parseInt(req.query.volume) || null;
        const news = req.query.news === "true";
        const store = req.query.store || "null";

        let { data, total } = await load({
          collection,

          // Single parameters;
          category: categories[category],
          subcategory: null,
          country: null,
          district: null,
          subdistrict: null,
          year: null,
          cork: null,
          storage: null,

          // Include non-alcoholic products;
          nonalcoholic: false,

          // Only show new products;
          news: news,

          // Array parameters;
          description: null,
          store: store === "null" ? null : store,
          pair: null,

          // If specified, only include values >=;
          volume: volume,
          alcohol: null,

          // Sorting;
          sort: sort,
          ascending: ascending,

          // Pagination;
          limit: 10,
          page: page,

          // Search, and whether to include filters (typically `false` for `search != null`);
          search: null,
          filters: true,

          // Calculate total pages;
          fresh: true,
        });

        res.render("products", {
          data: data,
          page: page,
          totalPages: total,
          sort: sort,
          ascending: ascending,
          category: category,
          volume: volume,
          news: news,
          store: store,
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