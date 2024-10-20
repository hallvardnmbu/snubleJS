import express from "express";
import rateLimit from "express-rate-limit";
import vhost from "vhost";
import fs from "fs/promises";
import { MongoClient, ServerApiVersion } from "mongodb";
import path from "path";
import { fileURLToPath } from "url";
import dotenv from "dotenv";

dotenv.config();

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const _PERPAGE = 10;
const _PRELOAD = 5;

const port = 8080;
const app = express();
const limiter = rateLimit({
  windowMs: 10 * 60 * 1000, // 10 minutes
  max: 100, // Limit each IP to 100 requests per `window` (10 minutes)
  standardHeaders: true, // Return rate limit info in the `RateLimit-*` headers
  legacyHeaders: false, // Disable the `X-RateLimit-*` headers
});
app.use(limiter);

// SNUBLEJUICE APPLICATION
// ------------------------------------------------------------------------------------------------

const snublejuice = express();

snublejuice.set("view engine", "ejs");
snublejuice.set("views", path.join(__dirname, "views"));
snublejuice.use(express.static(path.join(__dirname, "public")));

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
  pageIndex = 1,

  // Search for name;
  search = null,

  // Calculate total pages;
  fresh = true,
} = {}) {
  let pipeline = [];

  if (search) {
    pipeline.push({
      $search: {
        index: "name",
        compound: {
          should: [
            {
              text: {
                query: search,
                path: "name",
                score: { boost: { value: 10 } },
              },
            },
            {
              text: {
                query: search,
                path: "name",
                fuzzy: {
                  maxEdits: 2, // Max single-character edits
                  prefixLength: 1, // Exact beginning of word matches
                  maxExpansions: 1, // Max variations
                },
              },
            },
          ],
        },
      },
    });
  }

  let matchStage = {
    // Only include updated products (i.e., non-expired ones).
    status: "aktiv",
    buyable: true,

    // Filter by products that either orderable or instores is true (or both).
    // Wrapped in `$and` in case `news = true` (see below).
    $and: [
      {
        $or: [{ orderable: true }, { instores: true }],
      },
    ],

    // Match the specified parameters if they are not null.
    ...(category && !search ? { category: category } : {}),
    ...(subcategory && !search ? { subcategory: subcategory } : {}),
    ...(country && !search ? { country: country } : {}),
    ...(district && !search ? { district: district } : {}),
    ...(subdistrict && !search ? { subdistrict: subdistrict } : {}),
    ...(year && !search ? { year: year } : {}),
    ...(cork && !search ? { cork: cork } : {}),
    ...(storage && !search ? { storage: storage } : {}),

    // Parameters that are arrays are matched using the $in operator.
    // ...(description.length && !search ? { "description.short": { $in: description } } : {}),
    ...(store && !search ? { stores: { $in: [store] } } : {}),
    // ...(pair.length && !search ? { pair: { $in: pair } } : {}),
  };

  if (!search) {
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
      matchStage.$and.push({
        $or: [{ oldprice: { $exists: false } }, { oldprice: null }],
      });
    }

    matchStage[sort] = { ...matchStage[sort], $exists: true, $ne: null };
  }

  pipeline.push({ $match: matchStage });

  let total;
  if (fresh) {
    const tot = await collection.aggregate([...pipeline, { $count: "amount" }]).toArray();
    if (tot.length === 0) {
      total = 1;
    } else {
      total = Math.floor(tot[0].amount / _PERPAGE) + 1;
    }
  } else {
    total = null;
  }

  if (!search) {
    pipeline.push({ $sort: { [sort]: ascending ? 1 : -1 } });
  }
  pipeline.push(
    { $skip: (pageIndex - 1) * (_PRELOAD * _PERPAGE) },
    { $limit: _PRELOAD * _PERPAGE },
  );

  try {
    const data = await collection.aggregate(pipeline).toArray();
    return { data, total };
  } catch (err) {
    return { data: null, total: 1 };
  }
}

let client;
try {
  client = await MongoClient.connect(
    `mongodb+srv://${process.env.MONGO_USR}:${process.env.MONGO_PWD}@snublejuice.faktu.mongodb.net/?retryWrites=true&w=majority&appName=snublejuice`,
    {
      serverApi: {
        version: ServerApiVersion.v1,
        strict: false,
        deprecationErrors: true,
      },
    },
  );
} catch (err) {
  console.error("Failed to connect to MongoDB", err);
  process.exit(1);
}
const db = client.db("snublejuice");
let collection = db.collection("products");

snublejuice.get("/api/stores", async (req, res) => {
  try {
    const stores = await collection.distinct("stores");
    res.json(stores);
  } catch (err) {
    res.status(500).send(err);
  }
});

// Route to display products with pagination
const cache = {};
snublejuice.get("/", async (req, res) => {
  try {
    const page = parseInt(req.query.page) || 1;
    const sort = req.query.sort || "discount";
    const ascending = !(req.query.ascending === "false");
    const category = req.query.category || "null";
    const volume = parseFloat(req.query.volume) || null;
    const alcohol = parseFloat(req.query.alcohol) || null;
    const search = req.query.search || null;
    const news = req.query.news === "true";
    const store = req.query.store || "null";

    const cacheKey = `${sort}-${ascending}-${category}-${volume}-${alcohol}-${search}-${news}-${store}`;
    if (!cache[cacheKey]) {
      cache[cacheKey] = {};
    }

    const startPage = Math.floor((page - 1) / _PRELOAD) + 1;
    if (!cache[cacheKey][startPage]) {
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
        alcohol: alcohol,

        // Sorting;
        sort: sort,
        ascending: ascending,

        // Pagination;
        pageIndex: startPage,

        // Search for name;
        search: search,

        // Calculate total pages;
        fresh: true,
      });

      cache[cacheKey][startPage] = data;
      cache.total = total;
    }

    const cachedData = cache[cacheKey][startPage];
    const dataToDisplay = cachedData.slice(
      ((page - 1) % _PRELOAD) * _PERPAGE,
      page % _PRELOAD === 0 ? _PRELOAD * _PERPAGE : (page % _PRELOAD) * _PERPAGE,
    );

    res.render("products", {
      data: dataToDisplay,
      page: page,
      totalPages: cache.total,
      sort: sort,
      ascending: ascending,
      category: category,
      volume: volume,
      alcohol: alcohol,
      search: search,
      news: news,
      store: store,
    });
  } catch (err) {
    console.error(err);
    res.status(500).send("Error fetching data from MongoDB.");
  }
});

// IND320 API APPLICATION (api.ind320.no)
// ------------------------------------------------------------------------------------------------

const ind = express();
ind.use(express.json());
ind.use(express.static(path.join(__dirname, "other")));

const dataFile = path.join(__dirname, "other/data.json");

// Ensure the data file exists.
(async () => {
  try {
    await fs.access(dataFile);
  } catch {
    await fs.writeFile(dataFile, "[]");
  }
})();

ind.get("/", (req, res) => {
  res.sendFile(path.join(__dirname, "other", "index.html"));
});

// API endpoint to get data by dates.
ind.get("/dates", async (req, res) => {
  try {
    const data = await fs.readFile(dataFile, "utf8");
    let jsonData = JSON.parse(data);

    const { startDate, endDate } = req.query;

    if (!startDate || !endDate) {
      return res.status(400).json({ error: "Both startDate and endDate are required" });
    }

    // Assert that the dates are in the correct format
    const datePattern = /^\d{4}-\d{2}-\d{2}$/;
    if (!datePattern.test(startDate) || !datePattern.test(endDate)) {
      return res.status(400).json({ error: "Invalid date format. Use YYYY-MM-DD" });
    }

    // Assert that the dates are of valid values
    const valuePattern = /^\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])$/;
    if (!valuePattern.test(startDate) || !valuePattern.test(endDate)) {
      return res.status(400).json({ error: "Invalid date. Check their values" });
    }

    // Convert the dates to Date objects and assert that they are valid
    const start = new Date(startDate);
    const end = new Date(endDate);
    if (isNaN(start) || isNaN(end)) {
      return res.status(400).json({ error: "Invalid date format. Use YYYY-MM-DD" });
    }

    // Assert that the start date is not greater than the end date
    if (start > end) {
      return res.status(400).json({ error: "startDate cannot be greater than endDate" });
    }

    jsonData = jsonData.filter((item) => {
      const itemDate = new Date(item.date);
      return itemDate >= start && itemDate <= end;
    });

    res.json(jsonData);
  } catch (error) {
    res.status(500).json({ error: "Failed to read data, are the dates correct?" });
  }
});

// API endpoint to get data by id.
ind.get("/id", async (req, res) => {
  try {
    const data = await fs.readFile(dataFile, "utf8");
    let jsonData = JSON.parse(data);

    const { value } = req.query;

    if (!value) {
      return res.status(400).json({ error: "Value is required" });
    }

    // Assert that the value is an integer.
    const parsedValue = parseInt(value, 10);
    if (isNaN(parsedValue)) {
      return res.status(400).json({ error: "Invalid id. Use an integer" });
    }

    jsonData = jsonData.filter((item) => item.id === parsedValue);

    res.json(jsonData);
  } catch (error) {
    res.status(500).json({ error: "Failed to read data" });
  }
});

// FINAL APP WITH BOTH VHOSTS
// ------------------------------------------------------------------------------------------------

app.use(vhost("snublejuice.no", snublejuice));
app.use(vhost("api.ind320.no", ind));

snublejuice.listen(port, () => {
  console.log(`Server running at http://localhost:${port}`);
});
