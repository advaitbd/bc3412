import React from "react";
import { Link } from "react-router-dom";
import type { DashboardData } from "../../types";
import {
  CheckCircleIcon,
  XCircleIcon,
  QuestionMarkCircleIcon,
} from "@heroicons/react/24/solid"; // Solid icons for clarity

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

// Helper to display boolean values nicely
const renderBooleanCell = (value: boolean | string | null | undefined) => {
  if (value === true || value === "Yes" || value === "TRUE") {
    return (
      <CheckCircleIcon className="h-5 w-5 text-green-500 mx-auto" title="Yes" />
    );
  } else if (value === false || value === "No" || value === "FALSE") {
    return <XCircleIcon className="h-5 w-5 text-red-500 mx-auto" title="No" />;
  } else {
    return (
      <QuestionMarkCircleIcon
        className="h-5 w-5 text-gray-400 mx-auto"
        title="N/A"
      />
    ); // Handle null, undefined, 'N/A'
  }
};

// Helper to format column headers
const formatHeader = (key: string): string => {
  // Simple formatter, can be expanded
  return key.replace(/([A-Z])/g, " $1").trim();
};

const ActionAdoptionTable: React.FC<ActionAdoptionTableProps> = ({ data }) => {
  if (!data || data.length === 0) {
    return (
      <p className="text-gray-500">No company data available for table.</p>
    );
  }

  // Filter action columns that actually exist in the first data row (as a sample)
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
                    {renderBooleanCell(company[col])}
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
    </div>
  );
};

export default ActionAdoptionTable;
