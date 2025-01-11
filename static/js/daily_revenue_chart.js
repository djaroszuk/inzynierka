document.addEventListener("DOMContentLoaded", () => {
    // Retrieve and parse daily revenue data from the DOM
    const chartDataElement = document.getElementById("chart-data");
    const dailyRevenue = JSON.parse(chartDataElement.dataset.dailyRevenue);

    // Extract data for labels, revenue, and orders
    const labels = dailyRevenue.map(entry => entry.date);
    const revenueData = dailyRevenue.map(entry => entry.total_revenue);
    const ordersData = dailyRevenue.map(entry => entry.total_orders);

    // Render the chart using extracted data
    renderDailyRevenueChart(labels, revenueData, ordersData);
});

function renderDailyRevenueChart(labels, revenueData, ordersData) {
    const ctx = document.getElementById("dailyRevenueChart").getContext("2d");

    new Chart(ctx, {
        type: "bar", // Bar chart for visualizing revenue and orders
        data: {
            labels: labels,
            datasets: [
                {
                    label: "Total Revenue",
                    data: revenueData,
                    backgroundColor: "rgba(75, 192, 192, 0.6)", // Bar color
                    borderColor: "rgba(75, 192, 192, 1)", // Bar border color
                    yAxisID: 'y1',
                },
                {
                    label: "Number of Orders",
                    data: ordersData,
                    backgroundColor: "rgba(153, 102, 255, 0.6)", // Bar color
                    borderColor: "rgba(153, 102, 255, 1)", // Bar border color
                    yAxisID: 'y2',
                }
            ]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: "Daily Revenue and Orders", // Chart title
                },
                tooltip: {
                    callbacks: {
                        // Customize tooltips for datasets
                        label: tooltipItem => tooltipItem.datasetIndex === 0
                            ? `$${tooltipItem.raw.toLocaleString()}`
                            : `${tooltipItem.raw} orders`,
                    }
                }
            },
            scales: {
                y1: {
                    beginAtZero: true,
                    ticks: {
                        callback: value => `$${value.toLocaleString()}`, // Format as currency
                    },
                },
                y2: {
                    beginAtZero: true,
                    grid: { drawOnChartArea: false }, // Prevent overlapping gridlines
                    ticks: {
                        stepSize: 1, // Use whole numbers for orders
                    },
                }
            },
        },
    });
}
