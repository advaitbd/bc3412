import React, { useState, useEffect, useCallback } from "react";
import CompanyList from "../components/CompanyList/CompanyList";
import LoadingSpinner from "../components/LoadingSpinner";
import UploadModal from "../components/UploadModal"; // Import the modal
import { getCompanies } from "../services/api";
import type { CompanyStatus, ApiError, GenericApiResponse } from "../types";

const CompanyManagementPage: React.FC = () => {
  const [companies, setCompanies] = useState<CompanyStatus[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [modalOpenFor, setModalOpenFor] = useState<string | null>(null); // State for modal
  const [actionMessage, setActionMessage] = useState<string | null>(null); // For success/info messages

  const fetchCompanyData = useCallback(async (showLoading = true) => {
    if (showLoading) setIsLoading(true);
    // Clear previous errors/messages when fetching
    setError(null);
    setActionMessage(null);
    const result = await getCompanies();
    if ("message" in result) {
      // Check if it's an ApiError
      setError(`Failed to load companies: ${result.message}`);
      setCompanies([]);
    } else {
      setCompanies(result);
    }
    if (showLoading) setIsLoading(false);
  }, []);

  useEffect(() => {
    fetchCompanyData();
  }, [fetchCompanyData]);

  // Function to update a single company's status in the local state
  const handleStatusUpdate = useCallback(
    (companyName: string, newStatus: Partial<CompanyStatus>) => {
      setCompanies((prevCompanies) =>
        prevCompanies.map((comp) =>
          comp.name === companyName ? { ...comp, ...newStatus } : comp,
        ),
      );
    },
    [],
  );

  // Function to display page-level errors/messages
  const handleItemError = (message: string) => {
    setError(message);
    setActionMessage(null); // Clear action message on new error
  };

  const handleItemSuccess = (message: string) => {
    setActionMessage(message);
    setError(null); // Clear error on new success message
    // Optionally hide message after a delay
    setTimeout(() => setActionMessage(null), 5000);
  };

  // --- Modal Handling ---
  const handleOpenUploadModal = (companyName: string) => {
    setError(null); // Clear errors when opening modal
    setActionMessage(null);
    setModalOpenFor(companyName);
  };

  const handleCloseModal = () => {
    setModalOpenFor(null);
  };

  const handleUploadSuccess = (
    companyName: string,
    status?: GenericApiResponse["company_status"],
  ) => {
    handleItemSuccess(`Successfully uploaded report for ${companyName}.`);
    if (status) {
      handleStatusUpdate(companyName, { pdf_exists: status.pdf_exists }); // Update based on response
    } else {
      handleStatusUpdate(companyName, { pdf_exists: true }); // Assume PDF exists after successful upload
    }
    // Optionally trigger processing automatically or refresh list
    // fetchCompanyData(false); // Refresh list without full loading spinner
  };

  // --- List Item Action Prop ---
  // We need to pass the modal opener down to the list item
  // Modify CompanyListItemProps to include onOpenUploadModal: (companyName: string) => void;
  // Modify CompanyListItem to call this prop onClick of the "Upload PDF" button instead of opening the file dialog directly.
  // **NOTE:** For simplicity here, we'll keep the existing CompanyListItem which handles its own file input Ref.
  // A cleaner approach would involve lifting file selection state up or passing the opener function.
  // The current implementation uses the modal *wrapper* logic here.

  return (
    <div>
      <h1 className="text-2xl font-semibold mb-6">Manage Company Reports</h1>

      {/* Action Message Display */}
      {actionMessage && (
        <div
          className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded relative mb-4"
          role="alert"
        >
          <span className="block sm:inline">{actionMessage}</span>
        </div>
      )}

      {/* Error Message Display */}
      {error && (
        <div
          className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4"
          role="alert"
        >
          <strong className="font-bold">Error: </strong>
          <span className="block sm:inline">{error}</span>
        </div>
      )}

      {isLoading && <LoadingSpinner />}

      {!isLoading && !error && (
        <>
          <CompanyList
            companies={companies}
            onStatusUpdate={handleStatusUpdate}
            onError={handleItemError}
            // Pass the function to open the modal for a specific company
            // NOTE: Requires modifying CompanyListItem to accept and use this prop
            onOpenUploadModal={handleOpenUploadModal}
          />
          {/* Render Upload Modal */}
          {modalOpenFor && (
            <UploadModal
              isOpen={!!modalOpenFor}
              onClose={handleCloseModal}
              companyName={modalOpenFor}
              onUploadSuccess={handleUploadSuccess}
            />
          )}
        </>
      )}

      {!isLoading &&
        companies.length >= 0 && ( // Show refresh even if list is empty but not loading/error
          <button
            onClick={() => fetchCompanyData(true)} // Re-fetch data with loading spinner
            className="mt-6 px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700 disabled:opacity-50"
            disabled={isLoading}
          >
            {isLoading ? "Refreshing..." : "Refresh List"}
          </button>
        )}
    </div>
  );
};

export default CompanyManagementPage;
