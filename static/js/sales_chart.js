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
                        },
                        {
                            label: "Unique Customers",
                            data: data.unique_customers,
                            type: "line",
                            backgroundColor: "rgba(153, 102, 255, 0.5)",
                            borderColor: "rgba(153, 102, 255, 1)",
                            borderWidth: 1,
                        },
                    ],
                },
                options: {
                    responsive: true,
                    scales: {
                        y: {
                            beginAtZero: true,
                        },
                    },
                },
            });
        })
        .catch((error) => console.error("Error fetching sales data:", error));
});
