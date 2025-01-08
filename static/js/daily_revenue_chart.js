document.addEventListener("DOMContentLoaded", () => {
    // Retrieve data from the DOM
    const chartDataElement = document.getElementById("chart-data");
    const dailyRevenue = JSON.parse(chartDataElement.dataset.dailyRevenue);

    const labels = dailyRevenue.map((entry) => entry.date);
    const revenueData = dailyRevenue.map((entry) => entry.total_revenue);
    const ordersData = dailyRevenue.map((entry) => entry.total_orders);

    renderDailyRevenueChart(labels, revenueData, ordersData);
});

function renderDailyRevenueChart(labels, revenueData, ordersData) {
    const ctx = document.getElementById("dailyRevenueChart").getContext("2d");

    new Chart(ctx, {
        type: "bar",
        data: {
            labels: labels,
            datasets: [
                {
                    label: "Total Revenue",
                    data: revenueData,
                    backgroundColor: "rgba(75, 192, 192, 0.2)",
                    borderColor: "rgba(75, 192, 192, 1)",
                    borderWidth: 1,
                    yAxisID: 'y1'
                },
                {
                    label: "Number of Orders",
                    data: ordersData,
                    backgroundColor: "rgba(153, 102, 255, 0.2)",
                    borderColor: "rgba(153, 102, 255, 1)",
                    borderWidth: 1,
                    yAxisID: 'y2'
                }
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
                    text: "Daily Revenue and Orders",
                },
                tooltip: {
                    callbacks: {
                        // Format tooltip for the 'Total Revenue' dataset
                        label: function(tooltipItem) {
                            if (tooltipItem.datasetIndex === 0) {  // This is for revenue data
                                const revenue = tooltipItem.raw;
                                return `$${revenue.toLocaleString()}`; // Format as dollars
                            } else {  // For order count, return just the number
                                return tooltipItem.raw;  // Just show the number
                            }
                        }
                    }
                }
            },
            scales: {
                y1: {
                    beginAtZero: true,
                    position: 'left',
                    ticks: {
                        callback: function(value) { return "$" + value.toLocaleString(); }  // Format as currency
                    }
                },
                y2: {
                    beginAtZero: true,
                    position: 'right',
                    grid: {
                        drawOnChartArea: false,  // Don't draw grid lines for this axis
                    },
                    ticks: {
                        stepSize: 1,  // Ensure that ticks are whole numbers
                        callback: function(value) { return value; }  // Display only whole numbers
                    }
                }
            },
        },
    });
}
