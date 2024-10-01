document.getElementById("minVolume").addEventListener("change", function () {
  document.getElementById("volumeForm").submit();
});

// Function to toggle visibility and store status in local storage
function toggleVisibility(ids) {
  ids.forEach((id) => {
    const element = document.getElementById(id);
    if (element) {
      const isVisible = element.style.display !== "none";
      element.style.display = isVisible ? "none" : "block";
      localStorage.setItem(id, !isVisible);
    }
  });
}

// Function to set visibility based on local storage
function setVisibilityFromLocalStorage(ids) {
  ids.forEach((id) => {
    const element = document.getElementById(id);
    if (element) {
      const isVisible = localStorage.getItem(id) === "true";
      element.style.display = isVisible ? "block" : "none";
    }
  });
}

// Set visibility on page load
document.addEventListener("DOMContentLoaded", function () {
  setVisibilityFromLocalStorage(["volumeForm", "newsForm", "disclaimer-1", "disclaimer-2"]);
});
