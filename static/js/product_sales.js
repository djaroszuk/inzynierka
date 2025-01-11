document.addEventListener('DOMContentLoaded', () => {
    // Retrieve chart data elements from the DOM
    const labelsElement = document.getElementById('chart-labels');
    const quantityElement = document.getElementById('chart-quantity');
    const revenueElement = document.getElementById('chart-revenue');

    let labels, quantityData, revenueData;

    try {
        // Parse JSON data for labels, quantity, and revenue
        labels = JSON.parse(labelsElement.textContent);
        quantityData = JSON.parse(quantityElement.textContent);
        revenueData = JSON.parse(revenueElement.textContent);
    } catch (e) {
        console.error('Error parsing chart data:', e);
        labels = [];
        quantityData = [];
        revenueData = [];
    }

    // Exit if any of the datasets are empty
    if (labels.length === 0 || quantityData.length === 0 || revenueData.length === 0) {
        console.warn('No data available for the charts.');
        return;
    }

    // Define a palette for the pie chart
    const subtleColors = [
        '#A8D5BA', // Green
        '#F7B7B7', // Red
        '#A0C4FF', // Blue
        '#FFE5A0', // Yellow
        '#FFC3A0'  // Orange
    ];
    const greyColor = '#E0E0E0'; // Neutral grey for excess data
    const colors = labels.map((_, index) => index < subtleColors.length ? subtleColors[index] : greyColor);

    // Render Quantity Sold Pie Chart
    const quantityCtx = document.getElementById('quantityPieChart').getContext('2d');
    new Chart(quantityCtx, {
        type: 'pie',
        data: {
            labels: labels,
            datasets: [{
                label: 'Quantity Sold (%)',
                data: quantityData,
                backgroundColor: colors,
                borderColor: '#ffffff', // White border for better visibility
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { position: 'top' } // Position legend at the top
            }
        }
    });

    // Render Revenue Contribution Pie Chart
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
                legend: { position: 'top' } // Position legend at the top
            }
        }
    });
});
