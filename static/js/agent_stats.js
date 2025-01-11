// Wait for the DOM to load completely before executing the script
document.addEventListener('DOMContentLoaded', () => {
    // Retrieve the DOM element containing the preprocessed chart data
    const chartDataElement = document.getElementById('chart-data');

    // Ensure the necessary data element exists; otherwise, log an error and stop execution
    if (!chartDataElement) {
        console.error("Chart data element not found.");
        return;
    }

    // Parse chart data for daily orders and monthly revenue, with fallbacks to empty arrays
    const dailyOrdersData = JSON.parse(chartDataElement.dataset.dailyOrders || '[]');
    const monthlyRevenueData = JSON.parse(chartDataElement.dataset.monthlyRevenue || '[]');

    // Check whether the data pertains to a single agent or aggregated across all agents
    const isSingleAgent = chartDataElement.dataset.isSingleAgent === "true";

    // Prepare data for the daily orders chart
    const dailyOrdersLabels = dailyOrdersData.map(item => item.date);
    const dailyOrdersValues = dailyOrdersData.map(item => isSingleAgent ? item.count : item.average_count); // Adjust data based on context
    const dailyOrdersLabel = isSingleAgent ? 'Daily Orders (Single Agent)' : 'Average Daily Orders (All Agents)';
    renderDailyOrdersChart(dailyOrdersLabels, dailyOrdersValues, dailyOrdersLabel);

    // Prepare data for the monthly revenue chart
    const monthlyRevenueLabels = monthlyRevenueData.map(item => item.month);
    const monthlyRevenueValues = monthlyRevenueData.map(item => isSingleAgent ? item.revenue : item.average_revenue); // Adjust data based on context
    const monthlyRevenueLabel = isSingleAgent ? 'Monthly Revenue (Single Agent)' : 'Average Monthly Revenue (All Agents)';
    renderMonthlyRevenueChart(monthlyRevenueLabels, monthlyRevenueValues, monthlyRevenueLabel);
});

// Render the daily orders chart using Chart.js
function renderDailyOrdersChart(labels, data, label) {
    const ctxDaily = document.getElementById('dailyOrdersChart').getContext('2d');
    new Chart(ctxDaily, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: label,
                data: data,
                borderColor: 'rgba(54,162,235,1)', // Line color
                backgroundColor: 'rgba(54,162,235,0.2)', // Background fill color
                borderWidth: 2,
                fill: true,
                pointRadius: 5,
                pointHoverRadius: 7,
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { position: 'top' }, // Position the legend
                title: { display: true, text: label } // Chart title
            },
            scales: {
                y: { beginAtZero: true } // Ensure Y-axis starts at zero
            }
        }
    });
}

// Render the monthly revenue chart using Chart.js
function renderMonthlyRevenueChart(labels, data, label) {
    const ctxMonthly = document.getElementById('monthlyRevenueChart').getContext('2d');
    new Chart(ctxMonthly, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: label,
                data: data,
                borderColor: 'rgba(75,192,192,1)', // Line color
                backgroundColor: 'rgba(75,192,192,0.2)', // Background fill color
                borderWidth: 2,
                fill: true,
                pointRadius: 5,
                pointHoverRadius: 7,
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { position: 'top' }, // Position the legend
                title: { display: true, text: label }, // Chart title
                tooltip: {
                    callbacks: {
                        // Format tooltip values as currency
                        label: function(tooltipItem) {
                            return `$${tooltipItem.raw.toLocaleString()}`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true, // Ensure Y-axis starts at zero
                    ticks: {
                        // Format Y-axis tick values as currency
                        callback: function(value) {
                            return '$' + value.toLocaleString();
                        }
                    }
                }
            }
        }
    });
}
