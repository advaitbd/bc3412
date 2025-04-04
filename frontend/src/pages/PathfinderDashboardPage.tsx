import React, { useState, useEffect, useMemo } from "react";
import LoadingSpinner from "../components/LoadingSpinner";
import SummaryWidget from "../components/Dashboard/SummaryWidget";
import TargetStatusChart from "../components/Dashboard/TargetStatusChart";
import ActionAdoptionTable from "../components/Dashboard/ActionAdoptionTable";
import { getDashboardData } from "../services/api";
import type { DashboardData, ApiError } from "../types";
import TargetOverviewTable from "../components/Dashboard/TargetOverviewTable";
import { Link } from "react-router-dom";
// Example Icons (install @heroicons/react)
import {
  BuildingOffice2Icon,
  ChartPieIcon,
  CheckBadgeIcon,
  ExclamationTriangleIcon,
} from "@heroicons/react/24/outline";

const PathfinderDashboardPage: React.FC = () => {
  const [dashboardData, setDashboardData] = useState<DashboardData[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true);
      setError(null);
      const result = await getDashboardData();
      if ("message" in result) {
        setError(`Failed to load dashboard data: ${result.message}`);
        setDashboardData([]);
      } else {
        setDashboardData(result);
      }
      setIsLoading(false);
    };
    fetchData();
  }, []);

  // Calculate summary statistics using useMemo for efficiency
  const summaryStats = useMemo(() => {
    if (!dashboardData || dashboardData.length === 0) {
      return {
        totalCompanies: 0,
        companiesOnTrack: 0,
        avgReduction: "N/A", // Default value
        mostCommonIndustry: "N/A",
      };
    }

    let totalReduction = 0;
    let reductionCount = 0;
    const industryCounts: { [key: string]: number } = {};
    let companiesOnTrack = 0;

    dashboardData.forEach((company) => {
      // Average Reduction Calculation
      const reductionVal = company["Emissions Reduction (% achieved)"];
      if (typeof reductionVal === "number") {
        totalReduction += reductionVal;
        reductionCount++;
      }

      // Industry Count
      const industry = company.Industry || "Unknown";
      industryCounts[industry] = (industryCounts[industry] || 0) + 1;

      // On Track Count (adjust condition based on your actual status values)
      if (company["Target Status"]?.toLowerCase().includes("on track")) {
        companiesOnTrack++;
      }
    });

    const avgReduction =
      reductionCount > 0
        ? (totalReduction / reductionCount).toFixed(1) + "%"
        : "N/A";
    const mostCommonIndustry =
      Object.keys(industryCounts).length > 0
        ? Object.entries(industryCounts).sort(([, a], [, b]) => b - a)[0][0]
        : "N/A";

    return {
      totalCompanies: dashboardData.length,
      companiesOnTrack: companiesOnTrack,
      avgReduction: avgReduction,
      mostCommonIndustry: mostCommonIndustry,
    };
  }, [dashboardData]);

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-gray-800">
          Pathfinder Dashboard
        </h1>
        {/* Optional: Add a refresh button or auto-refresh */}
      </div>
      <p className="mb-8 text-lg text-gray-600">
        Overview of energy transition progress across analyzed companies.
      </p>

      {isLoading && <LoadingSpinner />}

      {error && (
        <div
          className="bg-red-100 border-l-4 border-red-500 text-red-700 p-4 mb-6"
          role="alert"
        >
          <p className="font-bold">Error Loading Dashboard</p>
          <p>{error}</p>
          {error.includes("Enhanced dataset not found") && (
            <p className="mt-2">
              Please go to{" "}
              <Link
                to="/manage-companies"
                className="font-medium hover:underline"
              >
                Manage Companies
              </Link>{" "}
              to process reports.
            </p>
          )}
        </div>
      )}

      {!isLoading && !error && dashboardData.length === 0 && (
        <div
          className="bg-yellow-100 border-l-4 border-yellow-500 text-yellow-700 p-4"
          role="alert"
        >
          <p className="font-bold">No Data Available</p>
          <p>The dashboard is empty. Please process company reports first.</p>
          <Link
            to="/manage-companies"
            className="mt-2 inline-block font-medium text-yellow-800 hover:underline"
          >
            Go to Company Management →
          </Link>
        </div>
      )}

      {!isLoading && !error && dashboardData.length > 0 && (
        <div className="space-y-8">
          {/* Summary Widgets Row */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            <SummaryWidget
              title="Companies Analyzed"
              value={summaryStats.totalCompanies}
              icon={<BuildingOffice2Icon className="h-8 w-8 text-blue-500" />}
            />
            <SummaryWidget
              title="Companies On Track"
              value={summaryStats.companiesOnTrack}
              icon={<CheckBadgeIcon className="h-8 w-8 text-green-500" />}
            />
            {/* <SummaryWidget
              title="Avg. Emission Reduction"
              value={summaryStats.avgReduction}
              icon={<ChartPieIcon className="h-8 w-8 text-purple-500" />}
            /> */}
            <SummaryWidget
              title="Most Common Industry"
              value={summaryStats.mostCommonIndustry}
              icon={
                <ExclamationTriangleIcon className="h-8 w-8 text-yellow-500" />
              }
            />
          </div>

          {/* Charts and Tables Row */}
          {/* <div className="grid grid-cols-1 lg:grid-cols-2 gap-8"> */}
          {/* <TargetStatusChart data={dashboardData} /> */}
          {/* Add another chart here if needed, e.g., Industry Distribution */}
          {/* <div className="bg-white p-4 rounded-lg shadow h-96 flex items-center justify-center text-gray-400">
              Placeholder for another chart (e.g., Industry Breakdown)
            </div> */}
          {/* </div> */}
          {/* Targets Table */}
          <div>
            <TargetOverviewTable data={dashboardData} />
          </div>
          {/* Full Width Table */}
          <div>
            <ActionAdoptionTable data={dashboardData} />
          </div>
        </div>
      )}
    </div>
  );
};

export default PathfinderDashboardPage;
