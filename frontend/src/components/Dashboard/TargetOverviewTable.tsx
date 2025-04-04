import React from "react";
import { Link } from "react-router-dom";
import type { DashboardData } from "../../types";

interface TargetOverviewTableProps {
  data: DashboardData[];
}

const TargetOverviewTable: React.FC<TargetOverviewTableProps> = ({ data }) => {
  if (!data || data.length === 0) {
    // Don't render anything if no data, parent component shows message
    return null;
  }

  // Helper to truncate long text
  const truncateText = (
    text: string | null | undefined,
    maxLength = 100,
  ): string => {
    if (!text || typeof text !== "string") return "N/A";
    if (text.length <= maxLength) return text;
    return `${text.substring(0, maxLength)}...`;
  };

  return (
    <div className="bg-white p-4 rounded-lg shadow">
      <h2 className="text-lg font-semibold mb-4">Company Target Overview</h2>
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200 border border-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider sticky left-0 bg-gray-50 z-10">
                Company
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Emission Targets
              </th>
              <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                Target Year
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Scope Coverage
              </th>
              <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                View Pathway
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {data.map((company) => (
              <tr key={company.Name} className="hover:bg-gray-50">
                {/* Company Name */}
                <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900 sticky left-0 bg-white z-10">
                  {company.Name}
                </td>
                {/* Target Status */}
                <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600">
                  {company["Target Status"] || "N/A"}
                </td>
                {/* Emission Targets (Truncated) */}
                <td
                  className="px-4 py-3 text-sm text-gray-600"
                  title={
                    typeof company["Emission targets"] === "string"
                      ? company["Emission targets"]
                      : undefined
                  }
                >
                  {truncateText(company["Emission targets"], 100)}{" "}
                  {/* Show more chars */}
                </td>
                {/* Target Year */}
                <td className="px-4 py-3 whitespace-nowrap text-center text-sm text-gray-600">
                  {company["Target Year"] || "N/A"}
                </td>
                {/* Scope Coverage */}
                <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600">
                  {company["Scope coverage"] || "N/A"}
                </td>
                {/* Pathway Link */}
                <td className="px-4 py-3 whitespace-nowrap text-center text-sm font-medium">
                  <Link
                    to={`/pathway/${encodeURIComponent(company.Name)}`}
                    className="text-indigo-600 hover:text-indigo-900 hover:underline"
                    title={`View pathway for ${company.Name}`}
                  >
                    View
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default TargetOverviewTable;
