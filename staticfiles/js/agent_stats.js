// agent_stats.js

document.addEventListener('DOMContentLoaded', () => {
    // Retrieve data embedded in the DOM
    const chartDataElement = document.getElementById('chart-data');

    const leadStats = JSON.parse(chartDataElement.dataset.leadStats);
    const orderStats = JSON.parse(chartDataElement.dataset.orderStats);

    // Render charts
    renderLeadConversionChart(leadStats.sale, leadStats.no_sale);
    renderOrderStatsChart(orderStats.order_count, orderStats.total_value, orderStats.average_value);
});

// Lead Conversion Chart
function renderLeadConversionChart(leadSale, leadNoSale) {
    const ctxLeadConversion = document.getElementById('leadConversionChart').getContext('2d');
    new Chart(ctxLeadConversion, {
        type: 'pie',
        data: {
            labels: ['Sale', 'No Sale'],
            datasets: [{
                label: 'Lead Conversion',
                data: [leadSale, leadNoSale],
                backgroundColor: ['#4caf50', '#f44336'],
                borderColor: ['#2e7d32', '#c62828'],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'top',
                },
                title: {
                    display: true,
                    text: 'Lead Conversion (Sale vs. No Sale)'
                }
            }
        }
    });
}

// Order Statistics Chart
function renderOrderStatsChart(orderCount, totalValue, averageValue) {
    const ctxOrderStats = document.getElementById('orderStatsChart').getContext('2d');
    new Chart(ctxOrderStats, {
        type: 'bar',
        data: {
            labels: ['Total Orders', 'Total Order Value', 'Average Order Value'],
            datasets: [{
                label: 'Order Stats',
                data: [orderCount, totalValue, averageValue],
                backgroundColor: ['#2196f3', '#ff9800', '#8e24aa'],
                borderColor: ['#1565c0', '#ef6c00', '#6a1b9a'],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    display: false
                },
                title: {
                    display: true,
                    text: 'Order Statistics'
                }
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}
