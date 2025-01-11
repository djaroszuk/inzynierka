document.addEventListener("DOMContentLoaded", () => {
    // Retrieve Lifetime Value (LTV) data from the DOM
    const ltvDataElement = document.getElementById("ltvData");

    // Ensure the LTV data element exists; log an error if not
    if (!ltvDataElement) {
        console.error("LTV data not found in the template.");
        return;
    }

    let ltvData;
    try {
        // Parse the LTV data; handle errors for malformed data
        ltvData = JSON.parse(ltvDataElement.textContent);
    } catch (error) {
        console.error("Failed to parse Lifetime Value data:", error);
        return;
    }

    // Ensure data is available for the chart
    if (!ltvData || !ltvData.labels.length) {
        console.log("No LTV data available for the chart.");
        return;
    }

    // Render the LTV chart
    renderLifetimeValueChart(ltvData.labels, ltvData.ltv_values);
});

function renderLifetimeValueChart(labels, ltvValues) {
    const ctx = document.getElementById("lifetimeValueChart").getContext("2d");

    new Chart(ctx, {
        type: "line", // Line chart for Lifetime Value trends
        data: {
            labels: labels,
            datasets: [
                {
                    label: "Lifetime Value (LTV)", // Dataset label
                    data: ltvValues,
                    borderColor: "rgba(75, 192, 192, 1)", // Line color
                    backgroundColor: "rgba(75, 192, 192, 0.2)", // Fill color
                    borderWidth: 2,
                    tension: 0.1, // Smooth curves
                    pointRadius: 5,
                    pointHoverRadius: 7,
                },
            ],
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: "Lifetime Value (LTV)", // Chart title
                },
                legend: {
                    position: "top", // Position the legend at the top
                },
            },
            scales: {
                y: {
                    beginAtZero: false, // Allow values to start above zero
                    ticks: {
                        callback: value => `$${value}`, // Format Y-axis values as dollars
                    },
                    title: {
                        display: true,
                        text: "Lifetime Value ($)", // Y-axis label
                    },
                },
                x: {
                    title: {
                        display: true,
                        text: "Month", // X-axis label
                    },
                },
            },
        },
    });
}
