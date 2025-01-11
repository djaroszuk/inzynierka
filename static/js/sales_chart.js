document.addEventListener("DOMContentLoaded", () => {
    const ctx = document.getElementById("salesChart").getContext("2d");
    const params = new URLSearchParams(window.location.search);

    // Fetch sales data dynamically based on query parameters
    fetch(`/products/sales-data/?${params.toString()}`)
        .then((response) => response.json())
        .then((data) => {
            new Chart(ctx, {
                type: "bar",
                data: {
                    labels: data.labels, // X-axis labels (e.g., products or time periods)
                    datasets: [
                        {
                            label: "Total Sold", // Bar chart for total sales
                            data: data.total_sold,
                            backgroundColor: "rgba(75, 192, 192, 0.5)",
                            borderColor: "rgba(75, 192, 192, 1)",
                            yAxisID: "yLeft",
                        },
                        {
                            label: "Unique Customers", // Line chart for unique customers
                            data: data.unique_customers,
                            type: "line",
                            backgroundColor: "rgba(153, 102, 255, 0.5)",
                            borderColor: "rgba(153, 102, 255, 1)",
                            yAxisID: "yRight",
                        },
                    ],
                },
                options: {
                    responsive: true,
                    scales: {
                        yLeft: {
                            beginAtZero: true,
                            position: "left",
                            title: { display: true, text: "Total Sold" },
                        },
                        yRight: {
                            beginAtZero: true,
                            position: "right",
                            grid: { drawOnChartArea: false }, // Avoid overlapping gridlines
                            title: { display: true, text: "Unique Customers" },
                        },
                        x: {
                            title: { display: true, text: "Time Period or Products" },
                        },
                    },
                    plugins: {
                        legend: { position: "top" }, // Position the legend at the top
                    },
                },
            });
        })
        .catch((error) => console.error("Error fetching sales data:", error)); // Log fetch errors
});
