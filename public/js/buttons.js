// Submit the form.
function applyFilters(resetPage = false) {
  if (resetPage) {
    document.querySelector('input[name="page"]').value = 1;
  }
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

// Reset the page.
document.getElementById("clearFilters").onclick = function (event) {
  event.preventDefault();
  sessionStorage.clear();
  window.location.href = "/";
};

// Toggle advanced visibility.
document.getElementById("toggleAdvanced").onclick = function (event) {
  event.preventDefault();

  const section = document.getElementById("advancedSelection");
  section.style.display = section.style.display === "flex" ? "none" : "flex";

  // Set the button text based on visibility.
  document.getElementById("toggleAdvanced").innerHTML =
    section.style.display === "flex" ? "&divide;" : "+";

  // Save the visibility state to session storage.
  sessionStorage.setItem("advancedSelection", section.style.display === "flex");
};

// Update the button text based on visibility (from storage).
document.addEventListener("DOMContentLoaded", function () {
  const element = document.getElementById("advancedSelection");
  const isVisible = sessionStorage.getItem("advancedSelection") === "true";
  element.style.display = isVisible ? "flex" : "none";
  document.getElementById("toggleAdvanced").innerHTML = isVisible ? "&divide;" : "+";
});

// Volume, alcohol and search change.
document.getElementById("fvolume").addEventListener("change", function () {
  applyFilters(true);
});
document.getElementById("falcohol").addEventListener("change", function () {
  applyFilters(true);
});
document.getElementById("fsearch").addEventListener("change", function () {
  applyFilters(true);
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
  document.getElementById("infobox").style.display = "flex";
};
document.querySelector(".exit").onclick = function (event) {
  event.preventDefault();
  document.getElementById("infobox").style.display = "none";
};
window.onclick = function (event) {
  if (event.target === document.getElementById("infobox")) {
    document.getElementById("infobox").style.display = "none";
  }
};

document.addEventListener("DOMContentLoaded", function () {
  // Open modal when section is clicked
  const productSections = document.querySelectorAll(".product");
  productSections.forEach((section) => {
    section.addEventListener("click", function () {
      const itemIndex = this.getAttribute("index");
      const modal = document.getElementById(`detailed-${itemIndex}`);
      modal.style.display = "block";

      // Trigger resize event
      window.dispatchEvent(new Event("resize"));
    });
  });

  // Close modal when the 'x' is clicked
  const closeModalButtons = document.querySelectorAll(".close");
  closeModalButtons.forEach((button) => {
    button.addEventListener("click", function (event) {
      event.stopPropagation(); // Prevent bubbling to avoid modal reopening
      const itemIndex = this.getAttribute("index");
      const modal = document.getElementById(`detailed-${itemIndex}`);
      modal.style.display = "none";
    });
  });

  // Close modal when clicking outside of the modal content
  window.onclick = function (event) {
    const modals = document.querySelectorAll(".modal");
    modals.forEach((modal) => {
      if (event.target === modal) {
        modal.style.display = "none";
      }
    });
  };
});
