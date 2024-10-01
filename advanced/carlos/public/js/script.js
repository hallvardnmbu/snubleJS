document.addEventListener("DOMContentLoaded", function() {
  // Now, query for tab links and attach the click event listeners
  document.querySelectorAll('.tab-link').forEach(link => {
    link.addEventListener('click', function (e) {
      e.preventDefault();

      // Get the target item id
      const targetId = this.getAttribute('data-target');
      const parentContainer = this.closest('.item-information-container');

      // Remove 'active' class from all tabs and sections within the same container
      parentContainer.querySelectorAll('.tab-link').forEach(tab => tab.classList.remove('active'));
      parentContainer.querySelectorAll('.content-section').forEach(section => section.classList.remove('active'));

      // Add 'active' class to the clicked tab and corresponding section
      this.classList.add('active');
      parentContainer.querySelector(`#${targetId}`).classList.add('active');
    });
  });

  // Plotly chart
  document.querySelectorAll('.tester').forEach((tester, index) => {
    // Ensure we're using the correct index from the EJS data
    var priser = window.priserData[tester.id.split('-')[1]]; // Get the correct 'priser' based on the item's index

    if (priser && priser.length > 0) {
      // Generate x-axis labels representing months in reverse order
      var today = new Date(); // Get the current date
      var xLabels = priser.map((_, idx) => {
        let date = new Date(today); // Clone the current date
        date.setMonth(today.getMonth() - (priser.length - 1 - idx)); // Subtract months to get previous dates

        // Format the date as "Sep 24" (short month and last 2 digits of the year)
        let month = date.toLocaleString('en-US', { month: 'short' }); // Short month, e.g., "Sep"
        let year = date.getFullYear().toString().slice(-2); // Last two digits of the year, e.g., "24"
        return `${month} ${year}`; // Format as "Sep 24"
      });

      // Plot the chart with months on the x-axis
      Plotly.newPlot(tester, [{
        x: xLabels, // Use the formatted xLabels for x-axis values
        y: priser, // Use 'priser' array for y-axis values
        line: { color: '#136f63' } // Optional: change the line color
      }], {
        margin: { t: 0, b:17 },
        xaxis: {}//any modifications to the x-axis
      });
    }
  });
});


