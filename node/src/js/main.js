import STATE from "./appState.js";
import {
  populateDropdowns,
  updateResults,
  handleFilterChange,
  handleSort,
  handlePageChange,
} from "./uiHandlers.js";

document.addEventListener("DOMContentLoaded", () => {
  // Initialize dropdowns
  populateDropdowns(STATE);

  // Set up event listeners
  document.querySelectorAll("select").forEach((select) => {
    select.addEventListener("change", () => handleFilterChange(STATE, select));
  });

  document.getElementById("navn-search").addEventListener("input", (e) => {
    STATE.finn.navn = e.target.value;
    updateResults(STATE);
  });

  document.getElementById("filter-toggle").addEventListener("click", () => {
    const extraFilters = document.getElementById("extra-filters");
    extraFilters.style.display = extraFilters.style.display === "none" ? "block" : "none";
  });

  document
    .getElementById("sort-by")
    .addEventListener("change", (e) => handleSort(STATE, e.target.value));
  document.getElementById("sort-ascending").addEventListener("change", (e) => {
    STATE.data.stigende = [e.target.checked.toString()];
    updateResults(STATE);
  });

  document
    .getElementById("prev-page")
    .addEventListener("click", () => handlePageChange(STATE, "prev"));
  document
    .getElementById("next-page")
    .addEventListener("click", () => handlePageChange(STATE, "next"));

  // Initial results update
  updateResults(STATE);
});
