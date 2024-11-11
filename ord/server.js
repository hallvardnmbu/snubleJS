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

app.set("view engine", "ejs");
app.set("views", path.join(__dirname, "views"));
app.use(express.static(path.join(__dirname, "public")));

let client;
try {
  client = await MongoClient.connect(
    `mongodb+srv://${process.env.MONGO_USR}:${process.env.MONGO_PWD}@ord.c8trc.mongodb.net/?retryWrites=true&w=majority&appName=ord`,
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
const db = client.db("ord");
let collection = db.collection("ord");

function formatDefinition(definition) {
  if (Array.isArray(definition.text)) {
    return definition.text
      .map((subDef) => formatDefinition(subDef))
      .filter(Boolean)
      .join(" | ");
  }
  return definition.text;
}

app.get("/", async (req, res) => {
  try {
    const words = await collection.aggregate([{ $sample: { size: 1 } }]).toArray();
    res.render("page", {
      words,
      error: null,
      formatDefinition: formatDefinition,
    });
  } catch (error) {
    res.status(500).render("page", {
      words: [],
      error: error.message,
      formatDefinition: formatDefinition,
    });
  }
});

app.listen(port, () => {
  console.log(`Server running at http://localhost:${port}`);
});
