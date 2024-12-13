// your_app/static/js/product_sales.js

document.addEventListener('DOMContentLoaded', () => {
    // Retrieve the embedded JSON data using their IDs
    const labelsElement = document.getElementById('chart-labels');
    const quantityElement = document.getElementById('chart-quantity');
    const revenueElement = document.getElementById('chart-revenue');

    let labels, quantityData, revenueData;

    try {
      labels = JSON.parse(labelsElement.textContent);
      quantityData = JSON.parse(quantityElement.textContent);
      revenueData = JSON.parse(revenueElement.textContent);
    } catch (e) {
      console.error('Error parsing chart data:', e);
      labels = [];
      quantityData = [];
      revenueData = [];
    }

    if (labels.length === 0 || quantityData.length === 0 || revenueData.length === 0) {
      console.warn('No data available for the charts.');
      return;
    }

    // Function to generate consistent colors for products across both charts
    function generateConsistentColors(labels) {
      const colors = {};
      const hueStep = 360 / labels.length;
      labels.forEach((label, index) => {
        const hue = (index * hueStep) % 360;
        colors[label] = `hsl(${hue}, 70%, 50%)`;
      });
      return colors;
    }

    const consistentColors = generateConsistentColors(labels);

    // Prepare colors for both charts using the consistent color mapping
    const quantityColors = labels.map(label => consistentColors[label]);
    const revenueColors = labels.map(label => consistentColors[label]);

    // Initialize Quantity Sold Pie Chart
    const quantityCtx = document.getElementById('quantityPieChart').getContext('2d');
    new Chart(quantityCtx, {
      type: 'pie',
      data: {
        labels: labels,
        datasets: [{
          label: 'Quantity Sold (%)',
          data: quantityData,
          backgroundColor: quantityColors,
          borderColor: '#ffffff',
          borderWidth: 1
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: {
            position: 'top'
          },
          title: {
            display: false,
            text: 'Quantity Sold Distribution (%)'
          }
        }
      }
    });

    // Initialize Revenue Contribution Pie Chart
    const revenueCtx = document.getElementById('revenuePieChart').getContext('2d');
    new Chart(revenueCtx, {
      type: 'pie',
      data: {
        labels: labels,
        datasets: [{
          label: 'Revenue Contribution (%)',
          data: revenueData,
          backgroundColor: revenueColors,
          borderColor: '#ffffff',
          borderWidth: 1
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: {
            position: 'top'
          },
          title: {
            display: false,
            text: 'Revenue Contribution Distribution (%)'
          }
        }
      }
    });
  });
