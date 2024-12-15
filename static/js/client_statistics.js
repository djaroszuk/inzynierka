// static/js/client_statistics.js

document.addEventListener("DOMContentLoaded", () => {
    // Retrieve the embedded JSON data using the <script> tag
    const monthlyOrderStatsElement = document.getElementById("monthlyOrderStatsData");

    if (!monthlyOrderStatsElement) {
        console.error("Monthly order stats data not found in the template.");
        return;
    }

    let monthlyOrderStats;
    try {
        monthlyOrderStats = JSON.parse(monthlyOrderStatsElement.textContent);
    } catch (error) {
        console.error("Failed to parse monthly order stats data:", error);
        return;
    }

    if (!monthlyOrderStats || !monthlyOrderStats.labels.length) {
        console.log("No data available for the order frequency chart.");
        return;
    }

    renderOrderFrequencyChart(monthlyOrderStats.labels, monthlyOrderStats.order_counts, monthlyOrderStats.total_spent);
});

function renderOrderFrequencyChart(labels, orderCounts, totalSpent) {
    const ctx = document.getElementById("orderFrequencyChart").getContext("2d");

    new Chart(ctx, {
        type: "bar", // Bar chart to display both datasets
        data: {
            labels: labels,
            datasets: [
                {
                    label: "Number of Orders",
                    data: orderCounts,
                    backgroundColor: "rgba(75, 192, 192, 0.6)",
                    borderColor: "rgba(75, 192, 192, 1)",
                    borderWidth: 1,
                    yAxisID: 'y-orders',
                },
                {
                    label: "Total Spent ($)",
                    data: totalSpent,
                    backgroundColor: "rgba(153, 102, 255, 0.6)",
                    borderColor: "rgba(153, 102, 255, 1)",
                    borderWidth: 1,
                    yAxisID: 'y-spent',
                },
            ]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: "top",
                },
                title: {
                    display: true,
                    text: "Monthly Order Frequency &amp; Spending",
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    callbacks: {
                        label: function (tooltipItem) {
                            if (tooltipItem.dataset.label === "Total Spent ($)") {
                                return `${tooltipItem.raw} $`;
                            }
                            return `${tooltipItem.raw} orders`;
                        }
                    }
                }
            },
            scales: {
                'y-orders': {
                    beginAtZero: true,
                    position: 'left',
                    ticks: {
                        stepSize: 1, // Ensure whole numbers
                        callback: function (value) {
                            return value;
                        }
                    },
                    title: {
                        display: true,
                        text: 'Number of Orders',
                    },
                },
                'y-spent': {
                    beginAtZero: true,
                    position: 'right',
                    grid: {
                        drawOnChartArea: false, // only want the grid lines for one axis
                    },
                    ticks: {
                        callback: function (value) {
                            return `$${value}`;
                        }
                    },
                    title: {
                        display: true,
                        text: 'Total Spent ($)',
                    },
                },
            },
            interaction: {
                mode: 'index',
                intersect: false,
            },
        },
    });
}
