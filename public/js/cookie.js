function acceptCookies() {
  localStorage.setItem("allowCookies", "accepted");
  document.getElementById("selectCookies").style.display = "none";
  loadAnalytics();
}

function declineCookies() {
  localStorage.setItem("allowCookies", "declined");
  document.getElementById("selectCookies").style.display = "none";
}

function loadAnalytics() {
  try {
    const script1 = document.createElement("script");
    script1.async = true;
    script1.src = "https://www.googletagmanager.com/gtag/js?id=G-PYBEXVQ5Q6";
    document.head.appendChild(script1);

    window.dataLayer = window.dataLayer || [];
    function gtag() {
      dataLayer.push(arguments);
    }
    gtag("js", new Date());
    gtag("config", "G-PYBEXVQ5Q6");
  } catch (error) {
    console.error("Error loading analytics:", error);
  }
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
    } else if (localStorage.getItem("allowCookies") === "accepted") {
      loadAnalytics();
    }
  } catch (error) {
    console.error("Error in cookie consent:", error);
  }
});
