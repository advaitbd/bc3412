import React from "react";

interface SummaryWidgetProps {
  title: string;
  value: string | number;
  icon?: React.ReactNode; // Optional icon element
}

const SummaryWidget: React.FC<SummaryWidgetProps> = ({
  title,
  value,
  icon,
}) => {
  return (
    <div className="bg-white p-5 rounded-lg shadow hover:shadow-md transition-shadow duration-200 flex items-center space-x-4">
      {icon && <div className="text-blue-500 text-3xl">{icon}</div>}
      <div>
        <dt className="text-sm font-medium text-gray-500 truncate">{title}</dt>
        <dd className="mt-1 text-2xl font-semibold text-gray-900">{value}</dd>
      </div>
    </div>
  );
};

// Example Usage within PathfinderDashboardPage:
// import { BuildingOffice2Icon, ChartPieIcon } from '@heroicons/react/24/outline'; // Example icons
// ...
// <SummaryWidget title="Companies Processed" value={dashboardData.length} icon={<BuildingOffice2Icon className="h-8 w-8"/>} />
// <SummaryWidget title="Avg. Reduction Target" value={`${avgReduction}%`} icon={<ChartPieIcon className="h-8 w-8"/>} /> // Calculate avgReduction

export default SummaryWidget;
