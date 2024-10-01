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

const URL =
  "https://www.vinmonopolet.no/vmpws/v2/vmp/search?fields=FULL&searchType=product&q={}:relevance";

async function processId(index, _proxy) {
  for (let i = 0; i < 5; i++) {
    try {
      const response = await session.get(URL.replace("{}", index), {
        // proxy: _proxy,
        timeout: 10000,
      });

      if (response.status === 429) {
        console.log("Rate limited, waiting 10s.");
        await new Promise((resolve) => setTimeout(resolve, 10001));
        continue;
      } else if (response.status !== 200) {
        throw new Error(`Status code ${response.status}: ${response.data}`);
      }

      const responseData = response.data.productSearchResult || {};

      const store = responseData.facets
        ? responseData.facets
            .filter((element) => element.name.toLowerCase() === "butikker")
            .map((element) => element.values || [])
        : [];

      if (!responseData.products || responseData.products.length === 0) {
        return {
          index: index,
          status: "utgått",
          buyable: false,
          orderable: false,
          orderinfo: null,
          instores: false,
          storeinfo: null,
          stores: null,
        };
      }

      const product = responseData.products[0];

      return {
        index: index,

        stores: store.flat().map((element) => element.name),

        status: product.status || null,
        buyable: product.buyable || false,
        expired: product.expired || true,

        orderable: product.productAvailability?.deliveryAvailability?.availableForPurchase || false,
        orderinfo:
          product.productAvailability?.deliveryAvailability?.infos?.[0]?.readableValue || null,
        instores: product.productAvailability?.storesAvailability?.availableForPurchase || false,
        storeinfo:
          product.productAvailability?.storesAvailability?.infos?.[0]?.readableValue || null,
      };
    } catch (err) {
      throw new Error(`Failed to fetch product information for index ${index}: ${err}`);
    }
  }

  throw new Error("Failed to fetch product information.");
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

async function updateStores(_proxy, itemIds) {
  let items = [];
  for (const element of itemIds) {
    const id = element["index"];
    console.log(`Id ${id}.`);
    try {
      let product = await processId(id, _proxy);
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
  // Fetch products with discount.
  const itemIds = await itemCollection
    .find({ discount: { $lt: 0.0 } })
    .project({ index: 1, _id: 0 })
    .toArray();
  // TODO: Roter proxy hver X sider. Test ut proxyene.
  const _proxy = proxies[Math.floor(Math.random() * proxies.length)];
  await updateStores(_proxy, itemIds);
}

await main();

client.close();
process.exit(1);
