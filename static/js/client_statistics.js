document.addEventListener("DOMContentLoaded", () => {
    // Retrieve the JSON data embedded in the DOM
    const monthlyOrderStatsElement = document.getElementById("monthlyOrderStatsData");

    // Ensure the required data element exists; log an error and stop execution if not found
    if (!monthlyOrderStatsElement) {
        console.error("Monthly order stats data not found in the template.");
        return;
    }

    let monthlyOrderStats;
    try {
        // Parse the JSON data; handle errors if the data is malformed
        monthlyOrderStats = JSON.parse(monthlyOrderStatsElement.textContent);
    } catch (error) {
        console.error("Failed to parse monthly order stats data:", error);
        return;
    }

    // Check for valid data before attempting to render the chart
    if (!monthlyOrderStats || !monthlyOrderStats.labels.length) {
        console.log("No data available for the order frequency chart.");
        return;
    }

    // Pass the parsed data to the chart rendering function
    renderOrderFrequencyChart(
        monthlyOrderStats.labels,
        monthlyOrderStats.order_counts,
        monthlyOrderStats.total_spent
    );
});

function renderOrderFrequencyChart(labels, orderCounts, totalSpent) {
    const ctx = document.getElementById("orderFrequencyChart").getContext("2d");

    new Chart(ctx, {
        type: "bar", // Use a bar chart to compare datasets
        data: {
            labels: labels, // X-axis labels (e.g., months)
            datasets: [
                {
                    label: "Number of Orders", // Dataset for order frequency
                    data: orderCounts,
                    backgroundColor: "rgba(75, 192, 192, 0.6)", // Bar color
                    borderColor: "rgba(75, 192, 192, 1)", // Bar border color
                    borderWidth: 1,
                    yAxisID: 'y-orders', // Link this dataset to the "y-orders" axis
                },
                {
                    label: "Total Spent ($)", // Dataset for total spending
                    data: totalSpent,
                    backgroundColor: "rgba(153, 102, 255, 0.6)", // Bar color
                    borderColor: "rgba(153, 102, 255, 1)", // Bar border color
                    borderWidth: 1,
                    yAxisID: 'y-spent', // Link this dataset to the "y-spent" axis
                },
            ]
        },
        options: {
            responsive: true, // Adjust chart size dynamically
            plugins: {
                legend: {
                    position: "top", // Position the legend at the top
                },
                title: {
                    display: true,
                    text: "Monthly Order Frequency & Spending", // Chart title
                },
                tooltip: {
                    mode: 'index', // Show tooltips for both datasets simultaneously
                    intersect: false,
                    callbacks: {
                        // Customize tooltip labels based on dataset
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
                    beginAtZero: true, // Start the Y-axis at zero
                    position: 'left', // Position the axis on the left
                    ticks: {
                        stepSize: 1, // Use whole numbers for orders
                    },
                    title: {
                        display: true,
                        text: 'Number of Orders', // Axis label
                    },
                },
                'y-spent': {
                    beginAtZero: true, // Start the Y-axis at zero
                    position: 'right', // Position the axis on the right
                    grid: {
                        drawOnChartArea: false, // Avoid overlapping grid lines
                    },
                    ticks: {
                        // Add a dollar sign to the Y-axis tick labels
                        callback: function (value) {
                            return `$${value}`;
                        }
                    },
                    title: {
                        display: true,
                        text: 'Total Spent ($)', // Axis label
                    },
                },
            },
            interaction: {
                mode: 'index', // Allow cross-dataset interactions
                intersect: false,
            },
        },
    });
}
