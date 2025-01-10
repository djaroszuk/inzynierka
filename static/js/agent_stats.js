document.addEventListener('DOMContentLoaded', () => {
    // Retrieve data embedded in the DOM
    const chartDataElement = document.getElementById('chart-data');

    if (!chartDataElement) {
        console.error("Chart data element not found.");
        return;
    }

    // Parse preprocessed data for charts
    const dailyOrdersData = JSON.parse(chartDataElement.dataset.dailyOrders || '[]');
    const monthlyRevenueData = JSON.parse(chartDataElement.dataset.monthlyRevenue || '[]');

    // Determine whether we're working with single agent or all agents data
    const isSingleAgent = chartDataElement.dataset.isSingleAgent === "true";

    // Prepare daily orders data
    const dailyOrdersLabels = dailyOrdersData.map(item => item.date);
    const dailyOrdersValues = dailyOrdersData.map(item => isSingleAgent ? item.count : item.average_count); // Use count for single agent, average_count for all agents
    const dailyOrdersLabel = isSingleAgent ? 'Daily Orders (Single Agent)' : 'Average Daily Orders (All Agents)';
    renderDailyOrdersChart(dailyOrdersLabels, dailyOrdersValues, dailyOrdersLabel);

    // Prepare monthly revenue data
    const monthlyRevenueLabels = monthlyRevenueData.map(item => item.month);
    const monthlyRevenueValues = monthlyRevenueData.map(item => isSingleAgent ? item.revenue : item.average_revenue); // Use revenue for single agent, average_revenue for all agents
    const monthlyRevenueLabel = isSingleAgent ? 'Monthly Revenue (Single Agent)' : 'Average Monthly Revenue (All Agents)';
    renderMonthlyRevenueChart(monthlyRevenueLabels, monthlyRevenueValues, monthlyRevenueLabel);
});

// Daily Orders Chart
function renderDailyOrdersChart(labels, data, label) {
    const ctxDaily = document.getElementById('dailyOrdersChart').getContext('2d');
    new Chart(ctxDaily, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: label,
                data: data,
                borderColor: 'rgba(54,162,235,1)',
                backgroundColor: 'rgba(54,162,235,0.2)',
                borderWidth: 2,
                fill: true,
                pointRadius: 5,
                pointHoverRadius: 7,
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { position: 'top' },
                title: { display: true, text: label }
            },
            scales: {
                y: { beginAtZero: true }
            }
        }
    });
}

// Monthly Revenue Chart
function renderMonthlyRevenueChart(labels, data, label) {
    const ctxMonthly = document.getElementById('monthlyRevenueChart').getContext('2d');
    new Chart(ctxMonthly, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: label,
                data: data,
                borderColor: 'rgba(75,192,192,1)',
                backgroundColor: 'rgba(75,192,192,0.2)',
                borderWidth: 2,
                fill: true,
                pointRadius: 5,
                pointHoverRadius: 7,
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { position: 'top' },
                title: { display: true, text: label },
                tooltip: {
                    callbacks: {
                        label: function(tooltipItem) {
                            // Add the `$` symbol to the value in the tooltip
                            return `$${tooltipItem.raw.toLocaleString()}`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return '$' + value.toLocaleString();
                        }
                    }
                }
            }
        }
    });
}
