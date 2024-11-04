function acceptCookies() {
  localStorage.setItem("allowCookies", "accepted");
  document.getElementById("selectCookies").style.display = "none";
  loadAnalytics();
}

function declineCookies() {
  localStorage.setItem("allowCookies", "declined");
  document.getElementById("selectCookies").style.display = "none";
}

const GTAG = "G-PYBEXVQ5Q6";

function loadAnalytics() {
  try {
    const script = document.createElement("script");
    script.async = true;
    script.defer = true;
    script.src = `https://www.googletagmanager.com/gtag/js?id=${GTAG}`;
    document.head.appendChild(script);

    window.dataLayer = window.dataLayer || [];
    function gtag() {
      dataLayer.push(arguments);
    }
    gtag("js", new Date());
    gtag("config", GTAG);
  } catch (error) {
    console.error("Error loading analytics:", error);
  }
}

if (localStorage.getItem("allowCookies") === "accepted") {
  loadAnalytics();
}

document.addEventListener("DOMContentLoaded", function () {
  try {
    const selectCookies = document.getElementById("selectCookies");
    if (!selectCookies) {
      console.error("selectCookies element not found");
      return;
    }
    if (!localStorage.getItem("allowCookies")) {
      selectCookies.style.display = "flex";
    }
  } catch (error) {
    console.error("Error in cookie consent:", error);
  }
});
