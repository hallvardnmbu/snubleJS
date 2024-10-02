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


// Get modal element
var modal = document.getElementById("infoModal");

// Get button that opens the modal
var btn = document.getElementById("info");

// Get the <span> element that closes the modal
var span = document.getElementsByClassName("close")[0];

// When the user clicks the button, open the modal
btn.onclick = function() {
  modal.style.display = "block";
}

// When the user clicks on <span> (x), close the modal
span.onclick = function() {
  modal.style.display = "none";
}

// When the user clicks anywhere outside of the modal, close it
window.onclick = function(event) {
  if (event.target == modal) {
    modal.style.display = "none";
  }
}

