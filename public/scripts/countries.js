const _STANDARD = "Alle land";

async function fetchCountries() {
  try {
    const response = await axios.get("/api/countries");
    const countries = response.data;
    sessionStorage.setItem("countriesData", JSON.stringify(countries));
    populateCountries(countries);
  } catch (error) {
    console.error("Error fetching countries:", error);
  }
}

function populateCountries(countries) {
  const countrySelect = document.getElementById("country");

  // Clear existing options
  countrySelect.innerHTML = "";

  // Add default option
  const defaultOption = document.createElement("option");
  defaultOption.value = _STANDARD;
  defaultOption.text = _STANDARD;
  countrySelect.appendChild(defaultOption);

  // Add new options
  for (const country of countries) {
    if (!country) continue;
    const option = document.createElement("option");
    option.value = country;
    option.text = country.charAt(0).toUpperCase() + country.slice(1);
    countrySelect.appendChild(option);
  }

  // Retrieve the selected country from local storage
  const selectedCountry = sessionStorage.getItem("selectedCountry");
  if (selectedCountry) {
    countrySelect.value = selectedCountry;
  } else {
    // Reset to default option if no selected country is found in sessionStorage
    countrySelect.value = _STANDARD;
  }

  // Add event listener to save the selected country to local storage
  countrySelect.addEventListener("change", () => {
    sessionStorage.setItem("selectedCountry", countrySelect.value);
  });
}

// Fetch countries on page load or use cached data
window.addEventListener("load", () => {
  const cachedCountries = sessionStorage.getItem("countriesData");
  if (cachedCountries) {
    populateCountries(JSON.parse(cachedCountries));
  } else {
    fetchCountries();
  }
});
