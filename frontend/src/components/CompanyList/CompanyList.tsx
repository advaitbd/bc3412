import React from "react";
import type { CompanyStatus } from "../../types";
import CompanyListItem from "./CompanyListItem";

interface CompanyListProps {
  companies: CompanyStatus[];
  onStatusUpdate: (
    companyName: string,
    newStatus: Partial<CompanyStatus>,
  ) => void;
  onError: (message: string) => void;
  onOpenUploadModal: (companyName: string) => void; // Add prop here
}

const CompanyList: React.FC<CompanyListProps> = ({
  companies,
  onStatusUpdate,
  onError,
  onOpenUploadModal, // Receive prop
}) => {
  if (!companies || companies.length === 0) {
    return (
      <p className="text-center text-gray-500 mt-4">
        No companies found in the source data.
      </p>
    );
  }

  return (
    <ul className="space-y-3">
      {" "}
      {/* Slightly reduced spacing */}
      {companies.map((company) => (
        <CompanyListItem
          key={company.name}
          company={company}
          onStatusUpdate={onStatusUpdate}
          onError={onError}
          onOpenUploadModal={onOpenUploadModal} // Pass prop down
        />
      ))}
    </ul>
  );
};

export default CompanyList;
