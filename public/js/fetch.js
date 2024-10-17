export const categories = {
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

export async function load({
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
        text: {
          query: search,
          path: "name",
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
      total = Math.floor(tot[0].amount / limit) + 1;
    }
  } else {
    total = null;
  }

  if (!search) {
    pipeline.push({ $sort: { [sort]: ascending ? 1 : -1 } });
  }
  pipeline.push({ $skip: (page - 1) * limit }, { $limit: limit });

  try {
    const data = await collection.aggregate(pipeline).toArray();
    return { data, total };
  } catch (err) {
    return { data: null, total: 1 };
  }
}
