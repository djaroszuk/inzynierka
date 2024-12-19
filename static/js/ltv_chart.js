document.addEventListener("DOMContentLoaded", () => {
    const ltvDataElement = document.getElementById("ltvData");
    const baselineValueElement = document.getElementById("baselineValue");

    if (!ltvDataElement || !baselineValueElement) {
        console.error("LTV data or baseline value not found in the template.");
        return;
    }

    let ltvData, baselineValue;
    try {
        ltvData = JSON.parse(ltvDataElement.textContent);
        baselineValue = 300; // Set baseline value to 300
    } catch (error) {
        console.error("Failed to parse Lifetime Value data or baseline value:", error);
        return;
    }

    if (!ltvData || !ltvData.labels.length) {
        console.log("No LTV data available for the chart.");
        return;
    }

    renderLifetimeValueChart(ltvData.labels, ltvData.ltv_values, baselineValue);
});

function renderLifetimeValueChart(labels, ltvValues, baselineValue) {
    const ctx = document.getElementById("lifetimeValueChart").getContext("2d");

    new Chart(ctx, {
        type: "line",
        data: {
            labels: labels,
            datasets: [
                {
                    label: "Lifetime Value (LTV)",
                    data: ltvValues,
                    borderColor: "rgba(75, 192, 192, 1)",
                    backgroundColor: "rgba(75, 192, 192, 0.2)",
                    borderWidth: 2,
                    tension: 0.1,
                    pointRadius: 5,
                    pointHoverRadius: 7,
                },
            ],
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: "top",
                },
                title: {
                    display: true,
                    text: "Lifetime Value (LTV) with Baseline",
                },
                annotation: {
                    annotations: {
                        baseline: {
                            type: "line",
                            yMin: baselineValue,
                            yMax: baselineValue,
                            borderColor: "rgba(255, 99, 132, 1)", // Red baseline
                            borderWidth: 2,
                            label: {
                                content: `Baseline ($${baselineValue})`,
                                enabled: true,
                                position: "end",
                                backgroundColor: "rgba(255, 99, 132, 0.8)",
                                color: "#ffffff",
                                font: {
                                    size: 12,
                                },
                            },
                        },
                    },
                },
            },
            scales: {
                y: {
                    beginAtZero: false,
                    min: Math.min(...ltvValues, baselineValue) - 50, // Ensure baseline is visible
                    max: Math.max(...ltvValues, baselineValue) + 50,
                    ticks: {
                        callback: function (value) {
                            return `$${value}`;
                        },
                    },
                    title: {
                        display: true,
                        text: "Lifetime Value ($)",
                    },
                },
                x: {
                    title: {
                        display: true,
                        text: "Time Period",
                    },
                },
            },
        },
    });
}
