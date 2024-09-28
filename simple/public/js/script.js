document.querySelectorAll(".informasjonsnavigasjon a").forEach(function (navLink) {
  navLink.addEventListener("click", function (event) {
    event.preventDefault();

    // Get the tab to show
    const tabToShow = this.getAttribute("tab");

    // Get the parent .produkt element
    const produktElement = this.closest(".produkt");

    // Hide all .fokus elements
    produktElement.querySelectorAll(".fokus").forEach(function (fokusElement) {
      fokusElement.classList.remove("active");
    });

    // Show the selected tab
    produktElement.querySelector("#" + tabToShow).classList.add("active");

    // Remove active class from all nav links
    produktElement.querySelectorAll(".informasjonsnavigasjon a").forEach(function (navLink) {
      navLink.classList.remove("active");
    });

    // Add active class to the clicked nav link
    this.classList.add("active");
  });
});
