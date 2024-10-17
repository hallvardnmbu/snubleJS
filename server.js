import express from "express";
import vhost from "vhost";
import fs from "fs/promises";
import { MongoClient, ServerApiVersion } from "mongodb";
import path from "path";
import { fileURLToPath } from "url";
import dotenv from "dotenv";

dotenv.config();

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const port = 8080;
const app = express();

// SNUBLEJUICE APPLICATION
// ------------------------------------------------------------------------------------------------

const snublejuice = express();

snublejuice.set("view engine", "ejs");
snublejuice.set("views", path.join(__dirname, "views"));
snublejuice.use(express.static(path.join(__dirname, "public")));

import { load, categories } from "./public/js/fetch";

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

snublejuice.get("/test", (req, res) => {
  res.send("Snublejuice application is running!");
});

// Route to display products with pagination
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
      limit: 10,
      page: page,

      // Search for name;
      search: search,

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

// IND320 APPLICATION (Static files for ind320.no)
// ------------------------------------------------------------------------------------------------

const indStatic = express();
indStatic.use(express.static(path.join(__dirname, "other")));

// IND320 API APPLICATION (API endpoints for api.ind320.no)
// ------------------------------------------------------------------------------------------------

const indApi = express();
indApi.use(express.json());

const dataFile = path.join(__dirname, "other/data.json");

// Ensure the data file exists.
(async () => {
  try {
    await fs.access(dataFile);
  } catch {
    await fs.writeFile(dataFile, "[]");
  }
})();

// API endpoint to get data by dates.
indApi.get("/dates", async (req, res) => {
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
indApi.get("/id", async (req, res) => {
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
app.use(vhost("ind320.no", indStatic));
app.use(vhost("api.ind320.no", indApi));

app.listen(port, () => {
  console.log(`Server running at http://localhost:${port}`);
});
