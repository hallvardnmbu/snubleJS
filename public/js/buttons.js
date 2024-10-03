// Submit the form.
function applyFilters() {
  document.getElementById("filter").submit();
}

function changePage(newPage) {
  document.querySelector('input[name="page"]').value = newPage;
  applyFilters();
}

// Toggle sort order.
document.getElementById("sortButton").onclick = function (event) {
  event.preventDefault();

  const ascendingInput = document.querySelector('input[name="ascending"]');
  ascending = ascendingInput.value === "true" ? "false" : "true";

  ascendingInput.value = ascending;

  applyFilters();
};

// Toggle advanced visibility.
document.getElementById("toggleAdvanced").onclick = function (event) {
  event.preventDefault();

  const section = document.getElementById("advancedSelection");
  section.style.display = section.style.display === "flex" ? "none" : "flex";

  // Set the button text based on visibility.
  document.getElementById("toggleAdvanced").innerHTML =
    section.style.display === "flex" ? "&divide;" : "+";

  // Save the visibility state to local storage.
  localStorage.setItem("advancedSelection", section.style.display === "flex");
};

// Update the button text based on visibility (from storage).
document.addEventListener("DOMContentLoaded", function () {
  const element = document.getElementById("advancedSelection");
  const isVisible = localStorage.getItem("advancedSelection") === "true";
  element.style.display = isVisible ? "flex" : "none";
  document.getElementById("toggleAdvanced").innerHTML = isVisible ? "&divide;" : "+";
});

// Volume change.
document.getElementById("volume").addEventListener("change", function () {
  applyFilters();
});

// New products toggle.
document.getElementById("newsButton").onclick = function (event) {
  event.preventDefault();
  const newsInput = document.querySelector('input[name="news"]');
  newsInput.value = newsInput.value === "true" ? "false" : "true";
  applyFilters();
};

// Information popup modal.
document.getElementById("info").onclick = function (event) {
  event.preventDefault();
  document.getElementById("infobox").style.display = "block";
};
document.querySelector(".close").onclick = function (event) {
  event.preventDefault();
  document.getElementById("infobox").style.display = "none";
};
window.onclick = function (event) {
  if (event.target === document.getElementById("infobox")) {
    document.getElementById("infobox").style.display = "none";
  }
};
