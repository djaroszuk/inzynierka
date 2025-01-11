document.addEventListener("DOMContentLoaded", () => {
    // Retrieve order data from the DOM dataset
    const acceptedOrders = parseInt(document.getElementById("orderCompletionChart").dataset.acceptedOrders);
    const remainingOrders = parseInt(document.getElementById("orderCompletionChart").dataset.remainingOrders);
    const totalOrders = parseInt(document.getElementById("orderCompletionChart").dataset.totalOrders);

    // Debugging: Log the retrieved data
    console.log("Accepted Orders:", acceptedOrders);
    console.log("Remaining Orders:", remainingOrders);
    console.log("Total Orders:", totalOrders);

    // Render the pie chart with the retrieved data
    renderOrderCompletionChart(acceptedOrders, remainingOrders, totalOrders);
});

function renderOrderCompletionChart(acceptedOrders, remainingOrders, totalOrders) {
    const ctx = document.getElementById("orderCompletionChart").getContext("2d");

    new Chart(ctx, {
        type: "pie", // Pie chart to represent completion rate
        data: {
            labels: ["Completed Orders", "Remaining Orders"], // Chart labels
            datasets: [{
                data: [acceptedOrders, remainingOrders], // Chart data
                backgroundColor: ["#4caf50", "#f44336"], // Colors for each slice
            }]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: "Order Completion Rate", // Chart title
                },
                tooltip: {
                    callbacks: {
                        // Customize tooltips to show value and percentage
                        label: function (tooltipItem) {
                            const label = tooltipItem.label;
                            const value = tooltipItem.raw;
                            const percentage = ((value / totalOrders) * 100).toFixed(2) + '%';
                            return `${label}: ${value} orders (${percentage})`;
                        }
                    }
                },
                datalabels: {
                    display: true,
                    color: 'white', // Text color for chart labels
                    formatter: (value) => {
                        const percentage = ((value / totalOrders) * 100).toFixed(2) + '%';
                        const number = value.toFixed(0);
                        return `${number} (${percentage})`; // Show both value and percentage
                    },
                    font: {
                        weight: 'bold',
                        size: 14,
                    },
                    align: 'center',
                    anchor: 'center'
                }
            }
        }
    });
}
