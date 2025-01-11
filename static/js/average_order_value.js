document.addEventListener("DOMContentLoaded", () => {
    // Retrieve the embedded JSON data from the DOM element
    const aovDataElement = document.getElementById("averageOrderValueData");

    // Check if the required data element exists; log an error and exit if not
    if (!aovDataElement) {
        console.error("Average Order Value data not found in the template.");
        return;
    }

    let aovData;
    try {
        // Parse the JSON data; handle any potential parsing errors
        aovData = JSON.parse(aovDataElement.textContent);
    } catch (error) {
        console.error("Failed to parse Average Order Value data:", error);
        return;
    }

    // Ensure there is valid data to render the chart
    if (!aovData || !aovData.labels.length) {
        console.log("No Average Order Value data available for the chart.");
        return;
    }

    // Render the chart with the provided labels and values
    renderAverageOrderValueChart(aovData.labels, aovData.average_order_value);
});

function renderAverageOrderValueChart(labels, averageOrderValues) {
    const ctx = document.getElementById("averageOrderValueChart").getContext("2d");

    new Chart(ctx, {
        type: "line", // Use a line chart to visualize Average Order Value
        data: {
            labels: labels, // X-axis labels (e.g., months)
            datasets: [
                {
                    label: "Average Order Value ($)", // Chart dataset label
                    data: averageOrderValues, // Y-axis data points
                    borderColor: "rgba(255, 99, 132, 1)", // Line color
                    backgroundColor: "rgba(255, 99, 132, 0.2)", // Area fill color
                    borderWidth: 2, // Line thickness
                    fill: true, // Enable background fill under the line
                    tension: 0.1, // Smooth the line curves
                    pointRadius: 5, // Size of data points
                    pointHoverRadius: 7, // Size of data points when hovered
                }
            ]
        },
        options: {
            responsive: true, // Adjust chart dimensions based on container size
            plugins: {
                legend: {
                    position: "top", // Position the legend at the top
                },
                title: {
                    display: true,
                    text: "Monthly Average Order Value (AOV)", // Chart title
                },
                tooltip: {
                    callbacks: {
                        // Format tooltip values as currency
                        label: function (tooltipItem) {
                            return `$${tooltipItem.raw}`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true, // Start Y-axis at zero
                    ticks: {
                        // Add a dollar sign to Y-axis tick values
                        callback: function(value) {
                            return `$${value}`;
                        }
                    },
                    title: {
                        display: true,
                        text: 'AOV ($)', // Y-axis label
                    },
                },
                x: {
                    title: {
                        display: true,
                        text: 'Month', // X-axis label
                    },
                }
            },
        },
    });
}
