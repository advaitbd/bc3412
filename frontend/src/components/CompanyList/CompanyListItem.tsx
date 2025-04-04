import React, { useState } from "react";
import type { CompanyStatus, GenericApiResponse, ApiError } from "../../types";
import { triggerProcessing } from "../../services/api"; // Keep processing logic here
import LoadingSpinner from "../LoadingSpinner";

interface CompanyListItemProps {
  company: CompanyStatus;
  onStatusUpdate: (
    companyName: string,
    newStatus: Partial<CompanyStatus>,
  ) => void;
  onError: (message: string) => void;
  onOpenUploadModal: (companyName: string) => void; // New prop to open modal
}

const CompanyListItem: React.FC<CompanyListItemProps> = ({
  company,
  onStatusUpdate,
  onError,
  onOpenUploadModal, // Receive the function
}) => {
  // Keep processing state local to the item
  const [isProcessing, setIsProcessing] = useState(false);
  const [processError, setProcessError] = useState<string | null>(null);

  const handleProcess = async () => {
    setIsProcessing(true);
    setProcessError(null);
    onError(""); // Clear page-level error

    const result = await triggerProcessing(company.name);

    if ("message" in result && result.company_status) {
      onStatusUpdate(company.name, {
        processed: result.company_status.processed,
        // Also update pdf_exists if processing confirms it (though upload should do this)
        pdf_exists: result.company_status.pdf_exists,
      });
      console.log(result.message); // Or use the page-level success handler if passed down
    } else {
      const errorMsg =
        (result as GenericApiResponse).error ||
        (result as ApiError).message ||
        "Processing failed";
      setProcessError(errorMsg); // Show error local to item
      onError(`Processing failed for ${company.name}: ${errorMsg}`); // Also show page level error
    }
    setIsProcessing(false);
  };

  const getStatusIndicator = () => {
    if (isProcessing)
      return <span className="text-blue-600 font-semibold">Processing...</span>;
    if (company.processed)
      return <span className="text-green-600 font-semibold">Processed</span>;
    if (company.pdf_exists)
      return (
        <span className="text-yellow-600 font-semibold">Ready to Process</span>
      );
    return <span className="text-red-600 font-semibold">PDF Needed</span>;
  };

  return (
    <li className="bg-white p-4 rounded shadow-sm flex flex-col sm:flex-row justify-between items-start sm:items-center space-y-3 sm:space-y-0 hover:bg-gray-50 transition-colors duration-150">
      <div className="flex-1 min-w-0 pr-4">
        {" "}
        {/* Add padding right */}
        <p className="text-lg font-medium text-gray-900 truncate">
          {company.name}
        </p>
        <p className="text-sm text-gray-500">{getStatusIndicator()}</p>
        {processError && (
          <p className="text-xs text-red-500 mt-1">
            Processing Error: {processError}
          </p>
        )}
      </div>

      <div className="flex space-x-2 items-center flex-shrink-0">
        {/* Upload Button - Triggers modal via prop function */}
        {!company.pdf_exists && !isProcessing && (
          <button
            onClick={() => onOpenUploadModal(company.name)} // Call the passed function
            className="px-3 py-1 text-sm bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
            disabled={isProcessing} // Disable if processing (though PDF wouldn't exist)
            title={`Upload PDF for ${company.name}`}
          >
            Upload PDF
          </button>
        )}

        {/* Processing Button and Spinner */}
        {isProcessing && <LoadingSpinner />}
        {company.pdf_exists && !company.processed && !isProcessing && (
          <button
            onClick={handleProcess}
            className="px-3 py-1 text-sm bg-green-500 text-white rounded hover:bg-green-600 disabled:opacity-50"
            disabled={isProcessing}
            title={`Process report for ${company.name}`}
          >
            Process Report
          </button>
        )}
      </div>
    </li>
  );
};

export default CompanyListItem;
