document.addEventListener('DOMContentLoaded', () => {
    // Retrieve data embedded in the DOM
    const chartDataElement = document.getElementById('chart-data');

    const leadStats = JSON.parse(chartDataElement.dataset.leadStats);
    const orderStats = JSON.parse(chartDataElement.dataset.orderStats);

    // New data sets
    const dailyOrdersData = JSON.parse(chartDataElement.dataset.dailyOrders);
    const monthlyRevenueData = JSON.parse(chartDataElement.dataset.monthlyRevenue);

    // Render existing charts
    renderLeadConversionChart(leadStats.sale, leadStats.no_sale);
    renderOrderStatsChart(orderStats.order_count, orderStats.total_value, orderStats.average_value);

    // Prepare daily orders data
    const dailyOrdersLabels = dailyOrdersData.map(item => item.date);
    const dailyOrdersCounts = dailyOrdersData.map(item => item.count);
    renderDailyOrdersChart(dailyOrdersLabels, dailyOrdersCounts);

    // Prepare monthly revenue data
    const monthlyRevenueLabels = monthlyRevenueData.map(item => item.month);
    const monthlyRevenueValues = monthlyRevenueData.map(item => item.revenue);
    renderMonthlyRevenueChart(monthlyRevenueLabels, monthlyRevenueValues);
});

// Lead Conversion Chart (Existing)
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
                legend: { position: 'top' },
                title: { display: true, text: 'Lead Conversion (Sale vs. No Sale)' }
            }
        }
    });
}

// Order Statistics Chart (Existing)
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
                legend: { display: false },
                title: { display: true, text: 'Order Statistics' }
            },
            scales: {
                y: { beginAtZero: true }
            }
        }
    });
}

// Daily Orders Chart (New)
function renderDailyOrdersChart(labels, data) {
    const ctxDaily = document.getElementById('dailyOrdersChart').getContext('2d');
    new Chart(ctxDaily, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Daily Orders',
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
                title: { display: true, text: 'Daily Order Count (Last 7 Days)' }
            },
            scales: {
                y: { beginAtZero: true }
            }
        }
    });
}

// Monthly Revenue Chart (New)
function renderMonthlyRevenueChart(labels, data) {
    const ctxMonthly = document.getElementById('monthlyRevenueChart').getContext('2d');
    new Chart(ctxMonthly, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Monthly Revenue',
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
                title: { display: true, text: 'Monthly Revenue Trend' }
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
