import React from "react";
import { Pie } from "react-chartjs-2";
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend,
  Title,
  ChartOptions,
} from "chart.js";
import type { DashboardData } from "../../types";

// Register Chart.js components
ChartJS.register(ArcElement, Tooltip, Legend, Title);

interface TargetStatusChartProps {
  data: DashboardData[];
}

// Helper to normalize status strings
const normalizeStatus = (status: string | null | undefined): string => {
  if (!status || typeof status !== "string") {
    return "Unknown";
  }
  const lowerStatus = status.trim().toLowerCase();
  if (
    lowerStatus === "n/a" ||
    lowerStatus === "not mentioned" ||
    lowerStatus === ""
  ) {
    return "Unknown";
  }
  // Simple normalization, can be expanded (e.g., map synonyms)
  if (lowerStatus.includes("on track")) return "On Track";
  if (lowerStatus.includes("needs improvement")) return "Needs Improvement";
  if (lowerStatus.includes("off track")) return "Off Track";
  if (lowerStatus.includes("achieved")) return "Achieved";
  // Add other common statuses you expect
  return "Other"; // Group less common statuses if needed, or return original capitalized
};

const TargetStatusChart: React.FC<TargetStatusChartProps> = ({ data }) => {
  if (!data || data.length === 0) {
    return (
      <div className="bg-white p-4 rounded-lg shadow h-96 flex items-center justify-center text-gray-400">
        No Status Data
      </div>
    );
  }

  // Process data to count normalized target statuses
  const statusCounts: { [key: string]: number } = {};
  data.forEach((company) => {
    // Use the helper function to normalize
    const normalized = normalizeStatus(company["Target Status"]);
    statusCounts[normalized] = (statusCounts[normalized] || 0) + 1;
  });

  // Ensure 'Unknown' is always present, even if count is 0, for consistent legend
  if (!("Unknown" in statusCounts)) {
    statusCounts["Unknown"] = 0;
  }

  // Sort labels for consistency (e.g., Unknown last)
  const sortedLabels = Object.keys(statusCounts).sort((a, b) => {
    if (a === "Unknown") return 1;
    if (b === "Unknown") return -1;
    if (a === "Other") return 1;
    if (b === "Other") return -1;
    return a.localeCompare(b); // Alphabetical for the rest
  });

  const counts = sortedLabels.map((label) => statusCounts[label]);

  // Define colors - map colors to specific statuses if possible
  const statusColors: { [key: string]: string } = {
    "On Track": "rgba(75, 192, 192, 0.7)", // Teal
    Achieved: "rgba(54, 162, 235, 0.7)", // Blue
    "Needs Improvement": "rgba(255, 206, 86, 0.7)", // Yellow
    "Off Track": "rgba(255, 99, 132, 0.7)", // Red
    Other: "rgba(153, 102, 255, 0.7)", // Purple
    Unknown: "rgba(201, 203, 207, 0.7)", // Grey
  };

  const backgroundColors = sortedLabels.map(
    (label) => statusColors[label] || statusColors["Unknown"],
  ); // Fallback to grey
  const borderColors = backgroundColors.map((color) =>
    color.replace("0.7", "1"),
  );

  const chartData = {
    labels: sortedLabels,
    datasets: [
      {
        label: "# of Companies",
        data: counts,
        backgroundColor: backgroundColors,
        borderColor: borderColors,
        borderWidth: 1,
      },
    ],
  };

  // Options remain largely the same as before
  const options: ChartOptions<"pie"> = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { position: "right" as const }, // Move legend if needed
      title: {
        display: true,
        text: "Company Target Status Distribution",
        font: { size: 16 },
        padding: { bottom: 15 }, // Add padding below title
      },
      tooltip: {
        /* Tooltip callback remains the same */
        callbacks: {
          /* ... */
        },
      },
    },
  };

  return (
    <div className="bg-white p-4 rounded-lg shadow h-96">
      <Pie data={chartData} options={options} />
    </div>
  );
};

export default TargetStatusChart;
