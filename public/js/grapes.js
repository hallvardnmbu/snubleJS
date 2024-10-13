function grapePercentage(input) {
  if (typeof input !== "string") {
    return {};
  }

  // Define regex patterns
  const patterns = [
    /(\d+)\s*%\s*([a-zA-ZæøåÆØÅ, ]+)/i, // Matches "90% eple" or "10% (rips, solbær)"
    /([a-zA-ZæøåÆØÅ, ]+)\s*(\d+)\s*prosent/i, // Matches "Pinot Bianco 80 prosent".
    /([a-zA-ZæøåÆØÅ, ]+)/i, // Matches single word types like "Riesling"
  ];

  console.log(input);

  for (const pattern of patterns) {
    const match = input.match(pattern);
    console.log(match);
    if (match) {
      if (pattern === patterns[0]) {
        // For pattern 0, the grape type is in the second group and percentage in the first group
        return { grape: match[2].trim(), percentage: parseFloat(match[1].trim()) };
      } else if (pattern === patterns[1]) {
        // For pattern 1, the grape type is in the first group and percentage in the second group
        return { grape: match[1].trim(), percentage: parseFloat(match[2].trim()) };
      } else if (pattern === patterns[2]) {
        // For pattern 2, the grape type is in the first group and percentage is assumed to be 100
        return { grape: match[1].trim(), percentage: 100.0 };
      }
    }
  }
  return {};
}

window.grapePercentage = grapePercentage;
