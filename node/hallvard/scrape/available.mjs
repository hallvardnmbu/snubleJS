import axios from "axios";
import { MongoClient } from "mongodb";
import dotenv from "dotenv";
import cron from "node-cron";

dotenv.config();

const client = new MongoClient(
  `mongodb+srv://${process.env.MONGO_USR}:${process.env.MONGO_PWD}@vinskraper.wykjrgz.mongodb.net/?retryWrites=true&w=majority&appName=vinskraper`,
);

const database = client.db("vinskraper");
const varerCollection = database.collection("varer");
const expiredCollection = database.collection("utgått");
let currentPage = 0;

const proxyIps = process.env.PROXY_IPS.split(",");
const proxies = proxyIps.flatMap((ip) => [
  {
    protocol: "http",
    host: ip,
    port: parseInt(process.env.PROXY_PRT),
    auth: {
      username: process.env.PROXY_USR,
      password: process.env.PROXY_PWD,
    },
  },
  {
    protocol: "socks5",
    host: ip,
    port: parseInt(process.env.SOCKS_PRT),
    auth: {
      username: process.env.PROXY_USR,
      password: process.env.PROXY_PWD,
    },
  },
]);

// console.log(proxies);
// console.exit(0);

const storesUrl = "https://www.vinmonopolet.no/vmpws/v2/vmp/stores?fields=FULL&pageSize=1000";
const productUrl =
  "https://www.vinmonopolet.no/vmpws/v2/vmp/search?fields=FULL&searchType=product&q={}:relevance";

async function fetchStores() {
  let proxyIndex = 0;
  let response;

  for (let i = 0; i < 10; i++) {
    try {
      response = await axios.get(storesUrl, {
        params: { q: "*" },
        proxy: proxies[proxyIndex],
        timeout: 3000,
      });
      break;
    } catch (err) {
      console.log(`Error: Trying another proxy. ${err}`);
      proxyIndex = (proxyIndex + 1) % proxies.length;
    }
  }

  if (!response || response.status !== 200) {
    throw new Error("Failed to fetch store information.");
  }

  const stores = response.data.stores || [];
  if (stores.length === 0) {
    throw new Error("No stores found.");
  }

  const formattedStores = stores.map((store) => {
    return {
      index: parseInt(store.name),
      navn: store.displayName,
      adresse: store.address.formattedAddress,
      koordinater: store.geoPoint,
      sortiment: store.assortment || null,
      "klikk og hent": store.clickAndCollect,
      mobilbetaling: store.mobileCheckoutEnabled,
    };
  });

  await database.collection("butikk").deleteMany({});
  await database.collection("butikk").insertMany(formattedStores);
}

async function fetchProduct(index, proxy) {
  let response;

  for (let i = 0; i < 10; i++) {
    try {
      response = await axios.get(productUrl.replace("{}", index), {
        proxy: proxy,
        timeout: 10000,
      });

      if (response.status === 429) {
        await new Promise((resolve) => setTimeout(resolve, 500));
        continue;
      } else if (response.status === 503 || response.status === 502) {
        await new Promise((resolve) => setTimeout(resolve, 1000));
        continue;
      } else if (response.status !== 200) {
        throw new Error(`Status code ${response.status}: ${response.data}`);
      }

      const productSearchResult = response.data.productSearchResult || {};
      const store = productSearchResult.facets
        .filter((facet) => facet.name.toLowerCase() === "butikker")
        .flatMap((facet) => facet.values || []);

      if (!productSearchResult.products || productSearchResult.products.length === 0) {
        return {
          index: index,
          status: "utgått",
          "kan kjøpes": false,
          "tilgjengelig for bestilling": false,
          bestillingsinformasjon: null,
          "tilgjengelig i butikk": false,
          butikkinformasjon: null,
          utgått: true,
          butikk: null,
        };
      }

      const product = productSearchResult.products[0];

      return {
        index: index,
        oppdater: false,
        butikk: store.map((element) => element.name),
        status: product.status || null,
        "kan kjøpes": product.buyable || false,
        utgått: product.expired || true,
        "tilgjengelig for bestilling":
          product.productAvailability.deliveryAvailability.availableForPurchase || false,
        bestillingsinformasjon:
          product.productAvailability.deliveryAvailability.infos[0]?.readableValue || null,
        "tilgjengelig i butikk":
          product.productAvailability.storesAvailability.availableForPurchase || false,
        butikkinformasjon:
          product.productAvailability.storesAvailability.infos[0]?.readableValue || null,
      };
    } catch (err) {
      console.log(`${index}: Trying another proxy. ${err}`);
      proxy = proxies[(proxies.indexOf(proxy) + 1) % proxies.length];
    }
  }

  throw new Error("Failed to fetch product information.");
}

async function updateAvailableProducts(products = null) {
  if (!products) {
    console.log("Fetching all products.");
    products = await varerCollection.distinct("index");
  }

  // Shuffle the products.
  products = products.sort(() => Math.random() - 0.5);

  const step = 1; // Process one product at a time

  for (let i = currentPage; i < products.length / 24; i += step) {
    console.log(`Processing product ${i + 1} of ${products.length}.`);

    const expired = [];
    const operations = [];

    for (let j = i; j < i + step && j < products.length; j++) {
      const productIndex = products[j];
      const proxy = proxies[j % proxies.length];
      let product;
      try {
        product = await fetchProduct(productIndex, proxy);
      } catch (err) {
        console.error(`Failed to fetch product ${productIndex}: ${err}`);
        continue; // Skip to the next product
      }

      if (!product) continue;

      if (!product.butikk) {
        product.butikk = null;
      }

      const operation = {
        updateOne: {
          filter: { index: product.index },
          update: { $set: product },
          upsert: true,
        },
      };

      if (product.utgått || ["utgått", "utgatt"].includes(product.status)) {
        expired.push(operation);
        operations.push({ deleteOne: { filter: { index: product.index } } });
      } else {
        operations.push(operation);
      }
    }

    await varerCollection.bulkWrite(operations);
    if (expired.length > 0) {
      await expiredCollection.bulkWrite(expired);
    }

    currentPage = i + step; // Update the current page
    break; // Exit the loop to wait for the next scheduled run
  }
}

await client.connect();

async function main() {
  await updateAvailableProducts();
  await new Promise((resolve) => setTimeout(resolve, 5000));
  await updateAvailableProducts();
  await new Promise((resolve) => setTimeout(resolve, 5000));
  await updateAvailableProducts();
  await new Promise((resolve) => setTimeout(resolve, 5000));
  await updateAvailableProducts();
  await new Promise((resolve) => setTimeout(resolve, 5000));
  await updateAvailableProducts();
  await new Promise((resolve) => setTimeout(resolve, 5000));
  await updateAvailableProducts();
  await new Promise((resolve) => setTimeout(resolve, 5000));
  await updateAvailableProducts();
  await new Promise((resolve) => setTimeout(resolve, 5000));
  await updateAvailableProducts();
  await new Promise((resolve) => setTimeout(resolve, 5000));
  await updateAvailableProducts();
}

process.on("exit", () => {
  client.close();
});

// Schedule the task to run every 1 minute.
cron.schedule("*/1 * * * *", async () => {
  console.log("Running scheduled task...");
  try {
    await main();
  } catch (err) {
    console.error(`Scheduled task failed: ${err}`);
  }
});

// Run the script immediately on startup
main();

// node available.js
