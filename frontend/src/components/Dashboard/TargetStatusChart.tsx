import React from "react";
import { Pie } from "react-chartjs-2";
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend,
  Title, // Import Title
  ChartOptions, // Import ChartOptions type
} from "chart.js";
import type { DashboardData } from "../../types";

// Register Chart.js components
ChartJS.register(ArcElement, Tooltip, Legend, Title);

interface TargetStatusChartProps {
  data: DashboardData[];
}

const TargetStatusChart: React.FC<TargetStatusChartProps> = ({ data }) => {
  if (!data || data.length === 0) {
    return <p className="text-gray-500">No data available for chart.</p>;
  }

  // Process data to count target statuses
  const statusCounts: { [key: string]: number } = {};
  data.forEach((company) => {
    const status = company["Target Status"] || "Unknown"; // Handle null/undefined/empty string
    statusCounts[status] = (statusCounts[status] || 0) + 1;
  });

  const labels = Object.keys(statusCounts);
  const counts = Object.values(statusCounts);

  // Define colors (add more if you have many statuses)
  const backgroundColors = [
    "rgba(75, 192, 192, 0.6)", // Teal (e.g., On Track)
    "rgba(255, 206, 86, 0.6)", // Yellow (e.g., Needs Improvement)
    "rgba(255, 99, 132, 0.6)", // Red (e.g., Off Track)
    "rgba(153, 102, 255, 0.6)", // Purple (e.g., Achieved)
    "rgba(201, 203, 207, 0.6)", // Grey (e.g., Unknown/N/A)
    "rgba(54, 162, 235, 0.6)", // Blue
  ];
  const borderColors = backgroundColors.map((color) =>
    color.replace("0.6", "1"),
  ); // Make borders solid

  const chartData = {
    labels: labels,
    datasets: [
      {
        label: "# of Companies",
        data: counts,
        backgroundColor: backgroundColors.slice(0, labels.length),
        borderColor: borderColors.slice(0, labels.length),
        borderWidth: 1,
      },
    ],
  };

  const options: ChartOptions<"pie"> = {
    // Type the options for better safety
    responsive: true,
    maintainAspectRatio: false, // Allow chart to resize height
    plugins: {
      legend: {
        position: "top" as const, // Position legend at the top
      },
      title: {
        display: true,
        text: "Company Target Status Distribution", // Chart title
        font: {
          size: 16,
        },
      },
      tooltip: {
        callbacks: {
          label: function (context) {
            let label = context.dataset.label || "";
            if (label) {
              label += ": ";
            }
            if (context.parsed !== null) {
              // Calculate percentage
              const total = counts.reduce((acc, value) => acc + value, 0);
              const percentage = ((context.parsed / total) * 100).toFixed(1);
              label += `${context.parsed} (${percentage}%)`;
            }
            return label;
          },
        },
      },
    },
  };

  return (
    <div className="bg-white p-4 rounded-lg shadow h-96">
      {" "}
      {/* Set a fixed height or manage responsiveness */}
      <Pie data={chartData} options={options} />
    </div>
  );
};

export default TargetStatusChart;
