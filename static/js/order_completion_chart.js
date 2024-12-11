document.addEventListener("DOMContentLoaded", () => {
    // Retrieve the data passed from Django
    const acceptedOrders = parseInt(document.getElementById("orderCompletionChart").dataset.acceptedOrders);  // Access accepted orders
    const remainingOrders = parseInt(document.getElementById("orderCompletionChart").dataset.remainingOrders);  // Access remaining orders
    const totalOrders = parseInt(document.getElementById("orderCompletionChart").dataset.totalOrders);  // Access total orders

    // Log to verify the correct data is being passed
    console.log("Accepted Orders:", acceptedOrders);
    console.log("Remaining Orders:", remainingOrders);
    console.log("Total Orders:", totalOrders);

    // Render the chart
    renderOrderCompletionChart(acceptedOrders, remainingOrders, totalOrders);
});

function renderOrderCompletionChart(acceptedOrders, remainingOrders, totalOrders) {
    const ctx = document.getElementById("orderCompletionChart").getContext("2d");

    new Chart(ctx, {
        type: "pie",  // Pie chart
        data: {
            labels: ["Completed Orders", "Remaining Orders"],
            datasets: [{
                data: [acceptedOrders, remainingOrders],
                backgroundColor: ["#4caf50", "#f44336"],  // Green for Completed, Red for Remaining
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: "top",
                },
                title: {
                    display: true,
                    text: "Order Completion Rate"
                },
                tooltip: {
                    callbacks: {
                        label: function(tooltipItem) {
                            const label = tooltipItem.label;
                            const value = tooltipItem.raw;
                            const percentage = ((value / totalOrders) * 100).toFixed(2) + '%';  // Format percentage
                            return `${label}: ${value} orders (${percentage})`;  // Show number and percentage
                        }
                    }
                },
                datalabels: {
                    display: true,
                    color: 'white',
                    formatter: (value, ctx) => {
                        const percentage = ((value / totalOrders) * 100).toFixed(2) + '%';  // Display percentage
                        const number = value.toFixed(0);  // Display number of orders
                        return `${number} (${percentage})`;  // Show both number and percentage
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
