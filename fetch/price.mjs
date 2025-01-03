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
const visitCollection = database.collection("visits");

const URL =
  "https://www.vinmonopolet.no/vmpws/v2/vmp/search?fields=FULL&searchType=product&currentPage={}&q=%3Arelevance";
const LINK = "https://www.vinmonopolet.no{}";

const IMAGE = {
  thumbnail: "https://bilder.vinmonopolet.no/bottle.png",
  product: "https://bilder.vinmonopolet.no/bottle.png",
};

function processImages(images) {
  return images ? images.reduce((acc, img) => ({ ...acc, [img.format]: img.url }), {}) : IMAGE;
}

function processProducts(products, alreadyUpdated) {
  const processed = [];

  for (const product of products) {
    const index = parseInt(product.code, 10) || null;

    // Extra check to avoid duplicates.
    // The alreadyUpdated is set in the main function below.
    // Only used if the scraping crashes and needs to be restarted.
    // In this way, it skips the already processed products (before crash).
    if (alreadyUpdated.includes(index)) {
      continue;
    }

    processed.push({
      index: index,

      updated: true,

      name: product.name || null,
      price: product.price?.value || 0.0,

      volume: product.volume?.value || 0.0,
      literprice:
        product.price?.value && product.volume?.value
          ? product.price.value / (product.volume.value / 100.0)
          : 0.0,

      url: product.url ? LINK.replace("{}", product.url) : null,
      images: product.images ? processImages(product.images) : IMAGE,

      category: product.main_category?.name || null,
      subcategory: product.main_sub_category?.name || null,

      country: product.main_country?.name || null,
      district: product.district?.name || null,
      subdistrict: product.sub_District?.name || null,

      selection: product.product_selection || null,
      sustainable: product.sustainable || false,

      buyable: product.buyable || false,
      expired: product.expired || true,
      status: product.status || null,

      orderable: product.productAvailability?.deliveryAvailability?.availableForPurchase || false,
      orderinfo:
        product.productAvailability?.deliveryAvailability?.infos?.[0]?.readableValue || null,

      instores: product.productAvailability?.storesAvailability?.availableForPurchase || false,
      storeinfo: product.productAvailability?.storesAvailability?.infos?.[0]?.readableValue || null,
    });
  }

  return processed;
}

async function getPage(page, alreadyUpdated) {
  try {
    const response = await session.get(URL.replace("{}", page), {
      timeout: 10000,
    });

    if (response.status === 200) {
      return processProducts(response.data["productSearchResult"]["products"], alreadyUpdated);
    }

    console.log(`Status code ${response.status} at page ${page}; ${err}`);
  } catch (err) {
    console.log(`Request failed for page ${page}: ${err.message}`);
  }

  throw new Error(`Failed to fetch page ${page} after 5 attempts.`);
}

async function updateDatabase(data) {
  const operations = data.map((record) => ({
    updateOne: {
      filter: { index: record.index },
      update: [
        { $set: { oldprice: "$price" } },
        { $set: record },
        { $set: { prices: { $ifNull: ["$prices", []] } } },
        { $set: { prices: { $concatArrays: ["$prices", ["$price"]] } } },
        {
          $set: {
            discount: {
              $cond: {
                if: {
                  $and: [
                    { $gt: ["$oldprice", 0] },
                    { $gt: ["$price", 0] },
                    { $ne: ["$oldprice", null] },
                    { $ne: ["$price", null] },
                  ],
                },
                then: {
                  $multiply: [
                    {
                      $divide: [{ $subtract: ["$price", "$oldprice"] }, "$oldprice"],
                    },
                    100,
                  ],
                },
                else: 0,
              },
            },
            literprice: {
              $cond: {
                if: {
                  $and: [
                    { $gt: ["$price", 0] },
                    { $gt: ["$volume", 0] },
                    { $ne: ["$price", null] },
                    { $ne: ["$volume", null] },
                  ],
                },
                then: {
                  $multiply: [
                    {
                      $divide: ["$price", "$volume"],
                    },
                    100,
                  ],
                },
                else: null,
              },
            },
          },
        },
        {
          $set: {
            alcoholprice: {
              $cond: {
                if: {
                  $and: [
                    { $gt: ["$literprice", 0] },
                    { $gt: ["$alcohol", 0] },
                    { $ne: ["$literprice", null] },
                    { $ne: ["$alcohol", null] },
                  ],
                },
                then: {
                  $divide: ["$literprice", "$alcohol"],
                },
                else: null,
              },
            },
          },
        },
      ],
      upsert: true,
    },
  }));

  return await itemCollection.bulkWrite(operations);
}

async function getProducts(startPage = 0, alreadyUpdated = []) {
  let items = [];

  for (let page = startPage; page < 10000; page++) {
    // Fetch products of page.
    console.log(`Page ${page}.`);
    try {
      let products = await getPage(page, alreadyUpdated);
      if (products.length === 0) {
        console.log(`No more products (final page: ${page - 1}).`);
        break;
      }

      items = items.concat(products);

      await new Promise((resolve) => setTimeout(resolve, 900));
    } catch (err) {
      console.log(`Error page ${page}! ${err}`);
      break;
    }

    // Upsert to the database every 10 pages.
    if (page % 10 === 0) {
      if (items.length === 0) {
        throw new Error(`No items for the last 10 pages. Aborting.`);
      }

      console.log(`Updating ${items.length} products.`);
      const result = await updateDatabase(items);
      console.log(` Modified ${result.modifiedCount} records`);
      console.log(` Upserted ${result.upsertedCount} records`);

      items = [];
    }
  }

  // Upsert the remaining products, if any.
  if (items.length === 0) {
    return;
  }
  console.log(`Updating ${items.length} final products.`);
  const result = await updateDatabase(items);
  console.log(` Modified ${result.modifiedCount} records`);
  console.log(` Upserted ${result.upsertedCount} records`);
}

async function syncUnupdatedProducts(threshold = null) {
  const unupdatedCount = await itemCollection.countDocuments({ updated: false });
  console.log(`Unupdated products: ${unupdatedCount}`);
  if (threshold && unupdatedCount >= threshold) {
    console.log(`Above threshold, aborting.`);
    return;
  }

  try {
    const result = await itemCollection.updateMany({ updated: false }, [
      { $set: { oldprice: "$price" } },
      { $set: { price: "$oldprice", discount: 0, literprice: 0, alcoholprice: null } },
      { $set: { prices: { $ifNull: ["$prices", []] } } },
      { $set: { prices: { $concatArrays: ["$prices", ["$price"]] } } },
    ]);

    console.log(`Added ${result.modifiedCount} empty prices to unupdated products.`);
  } catch (err) {
    console.error("Error adding unupdated prices:", err);
  }
}

const session = axios.create();

async function main() {
  await visitCollection.updateOne({ class: "prices" }, { $set: { updated: false } });

  await itemCollection.updateMany({}, { $set: { updated: false } });
  const alreadyUpdated = await itemCollection
    .find({ updated: true })
    .map((item) => item.index)
    .toArray();

  const startPage = 0;
  await getProducts(startPage, alreadyUpdated);

  // [!] ONLY RUN THIS AFTER ALL PRICES HAVE BEEN UPDATED [!]
  await syncUnupdatedProducts(100);

  await visitCollection.updateOne({ class: "prices" }, { $set: { updated: true } });
}

await main();

client.close();
