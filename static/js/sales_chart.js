document.addEventListener("DOMContentLoaded", () => {
    const ctx = document.getElementById("salesChart").getContext("2d");
    const params = new URLSearchParams(window.location.search);

    fetch(`/products/sales-data/?${params.toString()}`)
        .then((response) => response.json())
        .then((data) => {
            new Chart(ctx, {
                type: "bar",
                data: {
                    labels: data.labels,
                    datasets: [
                        {
                            label: "Total Sold",
                            data: data.total_sold,
                            backgroundColor: "rgba(75, 192, 192, 0.5)",
                            borderColor: "rgba(75, 192, 192, 1)",
                            borderWidth: 1,
                            yAxisID: "yLeft",
                        },
                        {
                            label: "Unique Customers",
                            data: data.unique_customers,
                            type: "line",
                            backgroundColor: "rgba(153, 102, 255, 0.5)",
                            borderColor: "rgba(153, 102, 255, 1)",
                            borderWidth: 2,
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
                            title: {
                                display: true,
                                text: "Total Sold", // Title for the left axis
                                font: {
                                    size: 14,
                                    weight: "bold",
                                },
                            },
                        },
                        yRight: {
                            beginAtZero: true,
                            position: "right",
                            grid: {
                                drawOnChartArea: false, // Prevent grid lines overlapping with the left axis
                            },
                            title: {
                                display: true,
                                text: "Unique Customers", // Title for the right axis
                                font: {
                                    size: 14,
                                    weight: "bold",
                                },
                            },
                        },
                        x: {
                            title: {
                                display: true,
                                font: {
                                    size: 14,
                                    weight: "bold",
                                },
                            },
                        },
                    },
                    plugins: {
                        legend: {
                            position: "top",
                        },
                    },
                },
            });
        })
        .catch((error) => console.error("Error fetching sales data:", error));
});
