async function fetchStores() {
  try {
    const response = await axios.get("/api/stores");
    const stores = response.data;
    const storeSelect = document.getElementById("store");

    // Clear existing options
    storeSelect.innerHTML = "";

    // Add default option
    const defaultOption = document.createElement("option");
    defaultOption.value = "null";
    defaultOption.text = "Alle butikker og nettlager";
    storeSelect.appendChild(defaultOption);

    // Add new options
    for (const store of stores) {
      if (!store) continue;
      const option = document.createElement("option");
      option.value = store;
      option.text = store.charAt(0).toUpperCase() + store.slice(1);
      storeSelect.appendChild(option);
    }

    // Retrieve the selected store from local storage
    const selectedStore = sessionStorage.getItem("selectedStore");
    if (selectedStore) {
      storeSelect.value = selectedStore;
    }

    // Add event listener to save the selected store to local storage
    storeSelect.addEventListener("change", () => {
      sessionStorage.setItem("selectedStore", storeSelect.value);
      displayMessage(storeSelect.value);
    });

    // Display message if a store other than "null" is selected on page load
    displayMessage(storeSelect.value);
  } catch (error) {
    console.error("Error fetching stores:", error);
  }
}

// Function to display a message if a store other than "null" is selected
function displayMessage(selectedValue) {
  const messageElement = document.getElementById("message");
  if (selectedValue !== "null") {
    // Set the style to block to display the message
    messageElement.style.display = "block";
  } else {
    messageElement.style.display = "none";
  }
}

// Fetch stores on page load
window.onload = fetchStores;
