import axios from "axios";
import { MongoClient, ServerApiVersion } from "mongodb";
import dotenv from "dotenv";

dotenv.config();

const client = new MongoClient(
  `mongodb+srv://${process.env.MONGO_USR}:${process.env.MONGO_PWD}@snublejuice.faktu.mongodb.net/?retryWrites=true&w=majority&appName=snublejuice`,
  {
    serverApi: {
      version: ServerApiVersion.v1,
      strict: true,
      deprecationErrors: true,
    },
  },
);
await client.connect();

const database = client.db("snublejuice");
const itemCollection = database.collection("products");

const proxies = process.env.PROXY_IPS.split(",").flatMap((ip) => [
  {
    protocol: "http",
    host: ip,
    port: parseInt(process.env.PROXY_PRT),
    auth: {
      username: process.env.PROXY_USR,
      password: process.env.PROXY_PWD,
    },
  },
]);

const URL = "https://www.vinmonopolet.no/vmpws/v3/vmp/products/{}?fields=FULL";

function processInformation(product) {
  const processed = {
    index: parseInt(product.code, 10) || null,

    updated: true,

    volume: product.volume?.value || 0.0,
    price: product.price?.value || 0.0,

    colour: product.color || null,

    characteristics:
      product.content?.characteristics?.map((characteristic) => characteristic.readableValue) || [],
    ingredients: product.content?.ingredients?.map((ingredient) => ingredient.readableValue) || [],
    ...product.content?.traits?.reduce(
      (acc, trait) => ({ ...acc, [trait.name.toLowerCase()]: trait.readableValue }),
      {},
    ),
    smell: product.smell || null,
    taste: product.taste || null,
    allergens: product.allergens || null,

    pair: product.content?.isGoodFor?.map((element) => element.name) || [],
    storage: product.content?.storagePotential?.formattedValue || null,
    cork: product.cork || null,

    alcohol: product.traits?.find((trait) => trait.name === "Alkohol")?.readableValue || null,
    sugar: product.traits?.find((trait) => trait.name === "Sukker")?.readableValue || null,
    acid: product.traits?.find((trait) => trait.name === "Syre")?.readableValue || null,

    description: {
      lang: product.content?.style?.description || null,
      short: product.content?.style?.name || null,
    },
    method: product.method || null,
    year: product.year || null,
  };

  if (processed.volume > 0 && processed.price > 0) {
    processed.literprice = (processed.price / processed.volume) * 100;
  } else {
    processed.literprice = null;
  }

  // Check if "alkohol" or "alcohol" is present in the processed object.
  if (processed.alkohol || processed.alcohol) {
    // Split the string at the first space character, and convert to float.
    if (processed.alkohol) {
      processed.alcohol = parseFloat(processed.alkohol.split(" ")[0].replace(",", "."));

      // Remove the "alkohol" key from the object.
      delete processed.alkohol;
    } else {
      processed.alcohol = parseFloat(processed.alcohol.split(" ")[0].replace(",", "."));
    }

    // Calculate the alcohol price.
    processed.alcoholprice = processed.literprice / processed.alcohol;
  } else {
    processed.alcohol = 0.0;
    processed.alcoholprice = null;
  }

  return processed;
}

async function getInformation(id, _proxy) {
  for (let i = 0; i < 5; i++) {
    const response = await session.get(URL.replace("{}", id), {
      // proxy: _proxy,
      timeout: 10000,
    });

    if (response.status === 200) {
      return processInformation(response.data);
    } else {
      console.log(`Status code ${response.status} for id ${id} (trying another proxy); ${err}`);

      throw new Error(`Failed to fetch id ${id}. Aborting.`);

      // Rotate proxy.
      _proxy = proxies[(proxies.indexOf(_proxy) + 1) % proxies.length];

      // Delay before retrying.
      await new Promise((resolve) => setTimeout(resolve, 2000));
    }
  }
  throw new Error(`Failed to fetch id ${id} after 5 attempts.`);
}

async function updateDatabase(data) {
  const operations = data.map((record) => ({
    updateOne: {
      filter: { index: record.index },
      update: { $set: record },
      upsert: true,
    },
  }));

  return await itemCollection.bulkWrite(operations);
}

async function updateInformation(_proxy, itemIds) {
  let items = [];
  for (const element of itemIds) {
    const id = element["index"];
    console.log(`Id ${id}.`);
    try {
      let product = await getInformation(id, _proxy);
      if (!product) {
        console.log(`Unable to find product of Id ${id}. Aborting.`);
        break;
      } else {
        items.push(product);
        // Timeout 1.1sec
        await new Promise((resolve) => setTimeout(resolve, 1100));
      }
    } catch (err) {
      console.log(`Error: Id ${id}. Skipping this. ${err}`);
      break;
    }

    // Upsert to the database every 10 items.
    if (items.length >= 10) {
      console.log(`Adding ${items.length} products.`);

      const result = await updateDatabase(items);
      console.log(` Modified ${result.modifiedCount} records`);
      console.log(` Upserted ${result.upsertedCount} records`);

      items = [];
    }
  }

  // Insert the remaining products, if any.
  if (items.length === 0) {
    return;
  }
  const result = await updateDatabase(items);
  console.log(` Modified ${result.modifiedCount} records`);
  console.log(` Upserted ${result.upsertedCount} records`);
}

const session = axios.create();

async function main() {
  const itemIds = await itemCollection
    .find({ description: null })
    .project({ index: 1, _id: 0 })
    .toArray();

  // TODO: Roter proxy hver X sider. Test ut proxyene.
  const _proxy = proxies[Math.floor(Math.random() * proxies.length)];

  await updateInformation(_proxy, itemIds);
}

await main();

client.close();
process.exit(1);
