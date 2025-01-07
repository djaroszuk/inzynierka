document.addEventListener("DOMContentLoaded", () => {
    const ltvDataElement = document.getElementById("ltvData");

    if (!ltvDataElement) {
        console.error("LTV data not found in the template.");
        return;
    }

    let ltvData;
    try {
        ltvData = JSON.parse(ltvDataElement.textContent);
    } catch (error) {
        console.error("Failed to parse Lifetime Value data:", error);
        return;
    }

    if (!ltvData || !ltvData.labels.length) {
        console.log("No LTV data available for the chart.");
        return;
    }

    renderLifetimeValueChart(ltvData.labels, ltvData.ltv_values);
});

function renderLifetimeValueChart(labels, ltvValues) {
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
                    text: "Lifetime Value (LTV)",
                },
            },
            scales: {
                y: {
                    beginAtZero: false,
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
