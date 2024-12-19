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

  // Define a color palette
  const colorPalette = [
      '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#C9CBCF'
  ];

  // Generate colors based on the labels
  const colors = labels.map((_, index) => colorPalette[index % colorPalette.length]);

  // Initialize Quantity Sold Pie Chart
  const quantityCtx = document.getElementById('quantityPieChart').getContext('2d');
  new Chart(quantityCtx, {
      type: 'pie',
      data: {
          labels: labels,
          datasets: [{
              label: 'Quantity Sold (%)',
              data: quantityData,
              backgroundColor: colors,
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
              backgroundColor: colors,
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
