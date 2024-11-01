import axios from "axios";
import { MongoClient, ServerApiVersion } from "mongodb";
import dotenv from "dotenv";

dotenv.config();

const client = new MongoClient(
  `mongodb+srv://${process.env.MONGO_USR}:${process.env.MONGO_PWD}@snublejuice.faktu.mongodb.net/?retryWrites=true&w=majority&appName=snublejuice`,
  {
    serverApi: {
      version: ServerApiVersion.v1,
      strict: false,
      deprecationErrors: true,
    },
  },
);
await client.connect();

const database = client.db("snublejuice");
const itemCollection = database.collection("products");
const itemIds = await itemCollection.distinct("index");

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
  "https://www.vinmonopolet.no/vmpws/v2/vmp/search?fields=FULL&searchType=product&currentPage={}&q=%3Arelevance%3AnewProducts%3Atrue";

const LINK = "https://www.vinmonopolet.no{}";

const IMAGE = {
  thumbnail: "https://bilder.vinmonopolet.no/bottle.png",
  product: "https://bilder.vinmonopolet.no/bottle.png",
};

function processImages(images) {
  return images ? images.reduce((acc, img) => ({ ...acc, [img.format]: img.url }), {}) : IMAGE;
}

function processProducts(products) {
  const processedProducts = [];

  for (const product of products) {
    const index = parseInt(product.code, 10) || null;

    if (itemIds.includes(index)) {
      break;
    }

    processedProducts.push({
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

  return processedProducts;
}

async function getPage(page, _proxy) {
  for (let i = 0; i < 5; i++) {
    const response = await session.get(URL.replace("{}", page), {
      // proxy: _proxy,
      timeout: 10000,
    });

    if (response.status === 200) {
      return processProducts(response.data["productSearchResult"]["products"]);
    } else {
      console.log(`Status code ${response.status} at page ${page} (trying another proxy); ${err}`);

      throw new Error(`Failed to fetch page ${page}. Aborting.`);

      // Rotate proxy.
      _proxy = proxies[(proxies.indexOf(_proxy) + 1) % proxies.length];

      // Delay before retrying.
      await new Promise((resolve) => setTimeout(resolve, 2000));
    }
  }
  throw new Error(`Failed to fetch page ${page} after 5 attempts.`);
}

async function updateDatabase(data) {
  return await itemCollection.insertMany(data);
}

async function getProducts(_proxy) {
  let items = [];
  for (let page = 0; page < 10000; page++) {
    // Fetch products of page.
    console.log(`Page ${page}.`);
    try {
      let products = await getPage(page, _proxy);
      if (products.length === 0) {
        console.log(`No more new products (final page: ${page - 1}).`);
        break;
      } else {
        items = items.concat(products);
        // Timeout 1.1sec
        await new Promise((resolve) => setTimeout(resolve, 1100));
      }
    } catch (err) {
      console.log(`Error: Page ${page}. Skipping this. ${err}`);
      break;
    }

    // Upsert to the database every 10 pages.
    if (page % 10 === 0) {
      if (items.length === 0) {
        throw new Error(`No items for the last 10 pages. Aborting.`);
      }

      console.log(`Adding ${items.length} products.`);

      const result = await updateDatabase(items);
      console.log(` Inserted ${result.insertedCount} records`);

      items = [];
    }
  }

  // Insert the remaining products, if any.
  if (items.length === 0) {
    return;
  }
  const result = await updateDatabase(items);
  console.log(` Inserted ${result.insertedCount} records`);
}

const session = axios.create();

async function main() {
  // TODO: Roter proxy hver X sider. Test ut proxyene.
  const _proxy = proxies[Math.floor(Math.random() * proxies.length)];
  await getProducts(_proxy);
}

await main();

client.close();
