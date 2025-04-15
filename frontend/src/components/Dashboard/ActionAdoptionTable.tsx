import React from "react";
import { Link } from "react-router-dom";
import { Tooltip } from "react-tooltip"; // Import Tooltip
import "react-tooltip/dist/react-tooltip.css"; // Import default styles
import type { DashboardData } from "../../types";
import {
  CheckCircleIcon,
  XCircleIcon,
  QuestionMarkCircleIcon,
} from "@heroicons/react/24/solid";

interface ActionAdoptionTableProps {
  data: DashboardData[];
}

// Define which action columns to display
const actionColumns: (keyof DashboardData)[] = [
  "Renewables",
  "Energy Efficiency",
  "Electrification",
  "Bioenergy",
  "CCUS",
  "Hydrogen Fuel",
  // 'Behavioral Changes' // Add if needed
];

// Helper to display boolean values nicely with Tooltip attributes
const renderBooleanCell = (
  companyName: string, // Add companyName for unique ID
  actionKey: string, // Add actionKey for unique ID
  value: boolean | string | null | undefined,
  justification: string | null | undefined,
) => {
  const tooltipId = `tooltip-${companyName}-${actionKey}`; // Create unique ID
  const tooltipContent = justification || "N/A"; // Content for the tooltip

  if (value === true || value === "Yes" || value === "TRUE") {
    return (
      <CheckCircleIcon
        className="h-5 w-5 text-green-500 mx-auto cursor-pointer" // Add cursor pointer
        data-tooltip-id={tooltipId}
        data-tooltip-content={tooltipContent}
      />
    );
  } else if (value === false || value === "No" || value === "FALSE") {
    return (
      <XCircleIcon
        className="h-5 w-5 text-red-500 mx-auto cursor-pointer" // Add cursor pointer
        data-tooltip-id={tooltipId}
        data-tooltip-content={tooltipContent}
      />
    );
  } else {
    return (
      <QuestionMarkCircleIcon
        className="h-5 w-5 text-gray-400 mx-auto cursor-pointer" // Add cursor pointer
        data-tooltip-id={tooltipId}
        data-tooltip-content={tooltipContent}
      />
    );
  }
};

// Helper to format column headers
const formatHeader = (key: string): string => {
  return key.replace(/([A-Z])/g, " $1").trim();
};

const ActionAdoptionTable: React.FC<ActionAdoptionTableProps> = ({ data }) => {
  if (!data || data.length === 0) {
    return (
      <p className="text-gray-500">No company data available for table.</p>
    );
  }

  const availableActionColumns = actionColumns.filter((col) => col in data[0]);

  return (
    <div className="bg-white p-4 rounded-lg shadow">
      <h2 className="text-lg font-semibold mb-4">Transition Action Adoption</h2>
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200 border border-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider sticky left-0 bg-gray-50 z-10">
                Company
              </th>
              {availableActionColumns.map((col) => (
                <th
                  key={col as string}
                  className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider"
                >
                  {formatHeader(col as string)}
                </th>
              ))}
              <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                View Pathway
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {data.map((company) => (
              <tr key={company.Name} className="hover:bg-gray-50">
                <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900 sticky left-0 bg-white z-10">
                  {company.Name}
                </td>
                {availableActionColumns.map((col) => (
                  <td
                    key={col as string}
                    className="px-4 py-3 whitespace-nowrap text-center text-sm"
                  >
                    {renderBooleanCell(
                      company.Name, // Pass company name
                      col as string, // Pass action key
                      company[col],
                      company[`${col}_Justification`],
                    )}
                  </td>
                ))}
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
      {/* Render the Tooltip components for each unique ID prefix */}
      {/* We can use a single Tooltip component and let it handle multiple targets */}
      {data.map((company) =>
        availableActionColumns.map((col) => (
          <Tooltip
            key={`tooltip-${company.Name}-${col}`}
            id={`tooltip-${company.Name}-${col}`}
            place="top"
            effect="solid"
            className="high-z-tooltip" // Apply the high z-index class
            // You can add custom styling via className prop if needed
            // className="custom-tooltip-style"
          />
        )),
      )}
    </div>
  );
};

export default ActionAdoptionTable;
