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

    // Define a palette with subtle tones of normal colors
    const subtleColors = [
        '#A8D5BA', // Subtle Green
        '#F7B7B7', // Subtle Red
        '#A0C4FF', // Subtle Blue
        '#FFE5A0', // Subtle Yellow
        '#FFC3A0', // Subtle Orange
    ];

    // All other colors will appear as a neutral grey
    const greyColor = '#E0E0E0';

    // Generate colors array: use subtle colors for the first 5, grey for the rest
    const colors = labels.map((_, index) => {
        return index < subtleColors.length ? subtleColors[index] : greyColor;
    });

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
