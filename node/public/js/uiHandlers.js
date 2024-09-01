import {
  initialise,
  set_data,
  set_focus,
  set_store,
  set_country,
  set_district,
  set_subdistrict,
  set_category,
  set_subcategory,
  set_volume,
  reset_selection,
  set_next_page,
  set_previous_page,
  set_page_one,
  set_page,
} from "./getset.js";

export async function populateDropdowns(state) {
  // This function should populate the dropdowns in the UI based on the state.
  // Assuming dropdowns are select elements with ids matching the keys in state.dropdown
  for (let [key, values] of Object.entries(state.dropdown)) {
    let select = document.getElementById(`${key}-select`);
    if (select) {
      // Clear existing options
      select.innerHTML = "";
      // Add new options
      for (let [value, text] of Object.entries(values)) {
        let option = document.createElement("option");
        option.value = value;
        option.text = text;
        select.add(option);
      }
    }
  }
}

export async function updateResults(state) {
  // Print the state dictionary to the console
  console.log(state);

  // This function should update the results in the UI based on the state.
  // Assuming results are displayed in a table with id 'results-table'
  let resultsTable = document.getElementById("results-table");
  if (resultsTable) {
    // Clear existing results
    resultsTable.innerHTML = "";
    // Add new results
    for (let [key, value] of Object.entries(state.data.verdier)) {
      let row = resultsTable.insertRow();
      row.insertCell().textContent = value.navn;
      row.insertCell().textContent = value.kategori;
      row.insertCell().textContent = value.pris;
      row.insertCell().textContent = value.prisendring;
      row.insertCell().textContent = value.volum;
      row.insertCell().textContent = value.alkohol;
    }
  }
}

export async function handleFilterChange(state, select) {
  // This function should handle the change event for the filter dropdowns.
  // It should update the state and the UI based on the selected filter.
  state.valgt[select.id.replace("-select", "")] = Array.from(
    select.selectedOptions,
    (option) => option.value,
  );
  await set_data(state);
  await populateDropdowns(state);
  await updateResults(state);
}

export async function handleSort(state, value) {
  // This function should handle the change event for the sort dropdown.
  // It should update the state and the UI based on the selected sort option.
  state.data.fokus = value;
  await set_focus(state);
  await updateResults(state);
}

export async function handlePageChange(state, direction) {
  // This function should handle the click event for the page navigation buttons.
  // It should update the state and the UI based on the clicked button (next or previous).
  if (direction === "prev") {
    await set_previous_page(state);
  } else if (direction === "next") {
    await set_next_page(state);
  }
  await updateResults(state);
}
