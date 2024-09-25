import axios from "axios";
import { MongoClient } from "mongodb";
import dotenv from "dotenv";

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

const URL =
  "https://www.vinmonopolet.no/vmpws/v2/vmp/search?searchType=product&currentPage={}&q=%3Arelevance%3AmainCategory%3A{}";

const session = axios.create();

const IMAGE = {
  thumbnail: "https://bilder.vinmonopolet.no/bottle.png",
  product: "https://bilder.vinmonopolet.no/bottle.png",
};

const CATEGORY = {
  RED_WINE: "rødvin",
  WHITE_WINE: "hvitvin",
  SPARKLING_WINE: "musserende_vin",
  PEARLING_WINE: "perlende_vin",
  FORTIFIED_WINE: "sterkvin",
  AROMATIC_WINE: "aromatisert_vin",
  FRUIT_WINE: "fruktvin",
  ROSE_WINE: "rosévin",
  SPIRIT: "brennevin",
  BEER: "øl",
  CIDER: "sider",
  SAKE: "sake",
  MEAD: "mjød",
  ALCOHOL_FREE: "alkoholfritt",
};

async function upsert(data) {
  const operations = data.map((record) => ({
    updateOne: {
      filter: { index: record.index },
      update: [
        { $rename: { pris: "førpris" } },
        { $set: record },
        { $set: { priser: { $ifNull: ["$priser", []] } } },
        { $set: { priser: { $concatArrays: ["$priser", ["$pris"]] } } },
        {
          $set: {
            prisendring: {
              $cond: [
                {
                  if: {
                    $and: [{ $gt: ["$førpris", 0] }, { $gt: ["$pris", 0] }],
                  },
                },
                {
                  $multiply: [
                    {
                      $divide: [{ $subtract: ["$pris", "$førpris"] }, "$førpris"],
                    },
                    100,
                  ],
                },
                0,
              ],
            },
          },
        },
        {
          $set: {
            literpris: {
              $cond: {
                if: {
                  $and: [
                    { $ne: ["$pris", null] },
                    { $ne: ["$pris", 0] },
                    { $ne: ["$volum", null] },
                    { $ne: ["$volum", 0] },
                  ],
                },
                then: {
                  $multiply: [{ $divide: ["$pris", "$volum"] }, 100],
                },
                else: null,
              },
            },
          },
        },
        {
          $set: {
            alkoholpris: {
              $cond: {
                if: {
                  $and: [
                    { $ne: ["$literpris", null] },
                    { $ne: ["$literpris", 0] },
                    { $ne: ["$alkohol", null] },
                    { $ne: ["$alkohol", 0] },
                  ],
                },
                then: { $divide: ["$literpris", "$alkohol"] },
                else: null,
              },
            },
          },
        },
      ],
      upsert: true,
    },
  }));

  const result = await varerCollection.bulkWrite(operations);
  return result;
}

async function scrapePage(category, page, proxy) {
  for (let i = 0; i < 10; i++) {
    try {
      const response = await session.get(URL.replace("{}", page).replace("{}", category), {
        proxy: proxy,
        timeout: 3000,
      });
      return response;
    } catch (err) {
      console.log(`Error: Page ${page} (trying another proxy); ${err}`);
      proxy = proxies[(proxies.indexOf(proxy) + 1) % proxies.length];
    }
  }
  console.log(`Error: Failed to fetch page ${page} after 10 attempts.`);
  return { status: 500 };
}

function processImages(images) {
  return images ? images.reduce((acc, img) => ({ ...acc, [img.format]: img.url }), {}) : IMAGE;
}

function processProducts(products) {
  return products.map((product) => ({
    index: parseInt(product.code, 10) || 0,
    status: product.status || null,
    "kan kjøpes": product.buyable || false,
    utgått: product.expired || true,
    "tilgjengelig for bestilling":
      product.productAvailability?.deliveryAvailability?.availableForPurchase || false,
    bestillingsinformasjon:
      product.productAvailability?.deliveryAvailability?.infos?.[0]?.readableValue || null,
    "tilgjengelig i butikk":
      product.productAvailability?.storesAvailability?.availableForPurchase || false,
    butikkinformasjon:
      product.productAvailability?.storesAvailability?.infos?.[0]?.readableValue || null,
    pris: product.price?.value || 0.0,
  }));
}

async function scrapeCategory(category, proxy) {
  let items = [];
  for (let page = currentPage; page < 10000; page++) {
    const response = await scrapePage(category, page, proxy);
    if (response.status !== 200) {
      console.log(
        `${category} Failed: Page ${page} (status code ${response.status}): ${response.data}.`,
      );
      continue;
    }

    const products = response.data.productSearchResult?.products || [];
    if (!products.length) {
      console.log(`${category} No more products (final page: ${page - 1}).`);
      currentPage = 0;
      break;
    }

    items = items.concat(processProducts(products));
  }

  console.log(`${category} Inserting into database.`);
  try {
    const result = await upsert(items);
    console.log(`${category} Modified ${result.modifiedCount} records`);
    console.log(`${category} Upserted ${result.upsertedCount} records`);
    console.log(`${category} Success.`);
    return true;
  } catch (err) {
    console.log(`${category} Error: Bulk write operation; ${err}.`);
    return false;
  }
}

async function scrape(categories = Object.values(CATEGORY)) {
  const failed = [];
  for (const category of categories) {
    const proxy = proxies[Math.floor(Math.random() * proxies.length)];
    const success = await scrapeCategory(category, proxy);
    if (!success) {
      failed.push(category);
    }
  }

  const expired = await varerCollection.find({ utgått: true }).toArray();
  if (expired.length) {
    await expiredCollection.insertMany(expired);
    const ids = expired.map((doc) => doc.index);
    const result = await varerCollection.deleteMany({ index: { $in: ids } });
    console.log(`Moved ${ids.length} documents to the expired collection.`);
    console.log(`Deleted ${result.deletedCount} documents from the stock collection.`);
  } else {
    console.log("No expired documents found.");
  }

  return failed;
}

await client.connect();

async function main() {
  await scrape();
  await new Promise((resolve) => setTimeout(resolve, 5000));
  await scrape();
  await new Promise((resolve) => setTimeout(resolve, 5000));
  await scrape();
  await new Promise((resolve) => setTimeout(resolve, 5000));
  await scrape();
  await new Promise((resolve) => setTimeout(resolve, 5000));
  await scrape();
  await new Promise((resolve) => setTimeout(resolve, 5000));
  await scrape();
  await new Promise((resolve) => setTimeout(resolve, 5000));
  await scrape();
  await new Promise((resolve) => setTimeout(resolve, 5000));
  await scrape();
  await new Promise((resolve) => setTimeout(resolve, 5000));
  await scrape();
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

// node price.js
