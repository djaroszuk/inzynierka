// static/js/average_order_value.js

document.addEventListener("DOMContentLoaded", () => {
    // Retrieve the embedded JSON data using the <script> tag
    const aovDataElement = document.getElementById("averageOrderValueData");

    if (!aovDataElement) {
        console.error("Average Order Value data not found in the template.");
        return;
    }

    let aovData;
    try {
        aovData = JSON.parse(aovDataElement.textContent);
    } catch (error) {
        console.error("Failed to parse Average Order Value data:", error);
        return;
    }

    if (!aovData || !aovData.labels.length) {
        console.log("No Average Order Value data available for the chart.");
        return;
    }

    renderAverageOrderValueChart(aovData.labels, aovData.average_order_value);
});

function renderAverageOrderValueChart(labels, averageOrderValues) {
    const ctx = document.getElementById("averageOrderValueChart").getContext("2d");

    new Chart(ctx, {
        type: "line", // Line chart for AOV
        data: {
            labels: labels,
            datasets: [
                {
                    label: "Average Order Value ($)",
                    data: averageOrderValues,
                    borderColor: "rgba(255, 99, 132, 1)", // Red
                    backgroundColor: "rgba(255, 99, 132, 0.2)", // Light Red
                    borderWidth: 2,
                    fill: true,
                    tension: 0.1, // Smooth curves
                    pointRadius: 5,
                    pointHoverRadius: 7,
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
                    text: "Monthly Average Order Value (AOV)",
                },
                tooltip: {
                    callbacks: {
                        label: function (tooltipItem) {
                            return `$${tooltipItem.raw}`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        // Include a dollar sign in the ticks
                        callback: function(value) {
                            return `$${value}`;
                        }
                    },
                    title: {
                        display: true,
                        text: 'AOV ($)',
                    },
                },
                x: {
                    title: {
                        display: true,
                        text: 'Month',
                    },
                }
            },
        },
    });
}
