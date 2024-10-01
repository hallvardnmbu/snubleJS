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

// Plotly chart
document.querySelectorAll(".graf").forEach((produkt, index) => {
  var priser = window.priserData[produkt.id.split("-")[1]];
  if (priser && priser.length > 0) {
    var today = new Date();
    var current = new Date(today);

    var xLabels = priser.map((_, idx) => {
      let date = new Date(today);
      date.setMonth(today.getMonth() - (priser.length - 1 - idx));
      let month = date.toLocaleString("no-NB", { month: "long" });
      let year = date.getFullYear().toString();
      return `${month} ${year}`;
    });
    let thisDate =
      current.toLocaleString("no-NB", { month: "long", day: "numeric" }) +
      " " +
      current.getFullYear().toString();
    xLabels.push(thisDate);

    var diff = priser.length < 2 ? 0 : priser[priser.length - 1] - priser[priser.length - 2];

    var color = diff < 0 ? "#006400" : diff > 0 ? "#640000" : "#000000";
    var fillcolor = diff < 0 ? "#0064001a" : diff > 0 ? "#6400001a" : "#eeeeee";

    var priserExtended = priser.concat(priser[priser.length - 1]);

    Plotly.newPlot(
      produkt,
      [
        {
          x: xLabels,
          y: priserExtended,
          mode: "lines+markers",
          line: { color: color, shape: "hv", width: 3 },
          marker: { size: 8, color: color },
          fill: "tozeroy",
          fillcolor: fillcolor,
        },
      ],
      {
        height: produkt.clientHeight,
        width: produkt.clientWidth,
        dragmode: "pan",
        yaxis: {
          ticksuffix: " kr",
        },
      },
    );
  }
});
