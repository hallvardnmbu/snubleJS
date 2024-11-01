// Format the date to custom string.
function formatDateAsLocalString(date) {
  const year = date.getFullYear();
  const month = (date.getMonth() + 1).toString().padStart(2, "0");
  return `${year}-${month}`;
}

// Function to generate dates on the 1st of each month in local time
function generateDates(numPrices) {
  var dates = [];
  var currentDate = new Date();
  for (var i = 0; i < numPrices; i++) {
    var newDate = new Date(currentDate.getFullYear(), currentDate.getMonth() - i, 1);
    dates.unshift(formatDateAsLocalString(newDate));
  }
  return dates;
}

function graphPrices() {
  for (let index = 0; index < 10; index++) {
    // Extract prices and dates from session storage
    const data = JSON.parse(sessionStorage.getItem(`${index}`));
    if (!data) {
      continue;
    }
    const prices = data.price;
    const dates = data.date;

    // Color assigning based on the the discount sign.
    let color;
    if (prices.length > 2) {
      const oldPrice = prices[prices.length - 3];
      const newPrice = prices[prices.length - 2];

      if (oldPrice > newPrice) {
        color = {
          marker: "#00640099",
          line: "#00640033",
        };
      } else if (oldPrice < newPrice) {
        color = {
          marker: "#64000099",
          line: "#64000033",
        };
      } else {
        color = {
          marker: "black",
          line: "#666666",
        };
      }
    } else {
      color = {
        marker: "black",
        line: "#666666",
      };
    }

    var canvas = document.getElementById(`graph-${index}`);
    var ctx = canvas.getContext("2d");

    // Resize canvas to fit container
    canvas.width = canvas.parentElement.clientWidth;
    canvas.height = canvas.parentElement.clientHeight;

    // Calculate margins and plot area
    var margin = { top: 20, right: 10, bottom: 40, left: 50 };
    var plotWidth = canvas.width - margin.left - margin.right;
    var plotHeight = canvas.height - margin.top - margin.bottom;

    // Calculate scales
    var xScale = plotWidth / (dates.length - 1);
    var yMax = Math.max(...prices) * 1.05;
    var yMin = Math.min(...prices) * 0.95;
    var yScale = plotHeight / (yMax - yMin);

    // Draw line
    ctx.beginPath();
    ctx.moveTo(margin.left, canvas.height - margin.bottom - (prices[0] - yMin) * yScale);
    for (var i = 1; i < prices.length; i++) {
      // Move horizontally to the new X position
      ctx.lineTo(
        margin.left + i * xScale,
        canvas.height - margin.bottom - (prices[i - 1] - yMin) * yScale,
      );
      // Move vertically to the new Y position
      ctx.lineTo(
        margin.left + i * xScale,
        canvas.height - margin.bottom - (prices[i] - yMin) * yScale,
      );
    }
    ctx.strokeStyle = color.line;
    ctx.lineWidth = 10;
    ctx.stroke();

    // Draw markers
    for (var i = 0; i < prices.length; i++) {
      ctx.beginPath();
      ctx.rect(
        margin.left + i * xScale - 5,
        canvas.height - margin.bottom - (prices[i] - yMin) * yScale - 5,
        10,
        10,
      );
      ctx.fillStyle = color.marker;
      ctx.fill();
    }

    // Draw labels
    ctx.fillStyle = "black";
    ctx.textAlign = "center";
    ctx.font = "14px alpha-beta";
    for (var i = 0; i < dates.length; i++) {
      ctx.fillText(dates[i], margin.left + i * xScale, canvas.height - margin.bottom + 20);
    }
    ctx.fillStyle = "black";
    ctx.textAlign = "right";
    ctx.textBaseline = "middle";
    for (var i = 0; i <= 5; i++) {
      var yValue = yMin + ((yMax - yMin) * i) / 5;
      ctx.fillText(
        yValue.toFixed(0),
        margin.left - 10,
        canvas.height - margin.bottom - yScale * (yValue - yMin),
      );
    }
  }
}

window.addEventListener("resize", function () {
  graphPrices();
});
