import React, { useState, useRef } from "react";
import { uploadReport } from "../services/api";
import type { GenericApiResponse, ApiError } from "../types";
import LoadingSpinner from "./LoadingSpinner"; // Import the spinner

interface UploadModalProps {
  companyName: string;
  isOpen: boolean;
  onClose: () => void;
  onUploadSuccess: (
    companyName: string,
    status?: GenericApiResponse["company_status"],
  ) => void; // Pass back status
}

const UploadModal: React.FC<UploadModalProps> = ({
  isOpen,
  onClose,
  companyName,
  onUploadSuccess,
}) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Reset state when modal opens or closes
  React.useEffect(() => {
    if (!isOpen) {
      setSelectedFile(null);
      setIsUploading(false);
      setError(null);
      // Reset file input visually
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setError(null); // Clear previous error on new selection
    } else {
      setSelectedFile(null);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setError("Please select a PDF file first.");
      return;
    }

    setIsUploading(true);
    setError(null);

    const result = await uploadReport(companyName, selectedFile);

    if ("message" in result && !("error" in result)) {
      console.log("Upload successful:", result.message);
      onUploadSuccess(companyName, result.company_status); // Pass back status if available
      onClose(); // Close modal on success
    } else {
      const errorMsg =
        (result as ApiError | GenericApiResponse).error ||
        (result as ApiError).message ||
        "Upload failed";
      setError(errorMsg);
    }
    setIsUploading(false);
  };

  // Prevent modal close when clicking inside
  const handleModalContentClick = (e: React.MouseEvent) => {
    e.stopPropagation();
  };

  return (
    <div
      className="fixed inset-0 bg-gray-600 bg-opacity-75 overflow-y-auto h-full w-full flex items-center justify-center z-50 transition-opacity duration-300"
      onClick={onClose} // Close modal if backdrop is clicked
    >
      <div
        className="relative mx-auto p-6 border w-full max-w-md shadow-xl rounded-md bg-white transform transition-all duration-300 scale-95 opacity-0 animate-fade-in-scale"
        onClick={handleModalContentClick} // Stop propagation here
        style={{ animationFillMode: "forwards" }} // Keep final state of animation
      >
        <button
          onClick={onClose}
          className="absolute top-2 right-2 text-gray-400 hover:text-gray-600"
          aria-label="Close modal"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="h-6 w-6"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>

        <div className="mt-3 text-center sm:text-left">
          <h3 className="text-lg leading-6 font-medium text-gray-900 mb-2">
            Upload Report for <span className="font-bold">{companyName}</span>
          </h3>
          <div className="mt-4">
            <p className="text-sm text-gray-600 mb-4">
              Select the annual report PDF file for this company. The file
              should be named appropriately if processing relies on the
              filename.
            </p>

            {/* File Input */}
            <div>
              <label htmlFor="file-upload" className="sr-only">
                Choose file
              </label>
              <input
                id="file-upload"
                ref={fileInputRef}
                type="file"
                onChange={handleFileChange}
                accept=".pdf"
                className="block w-full text-sm text-slate-500 mb-2
                      file:mr-4 file:py-2 file:px-4
                      file:rounded-full file:border-0
                      file:text-sm file:font-semibold
                      file:bg-violet-50 file:text-violet-700
                      hover:file:bg-violet-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-violet-500"
                disabled={isUploading}
              />
              {selectedFile && (
                <p className="text-sm text-gray-500 truncate">
                  Selected: {selectedFile.name}
                </p>
              )}
            </div>

            {/* Error Message */}
            {error && (
              <p className="text-sm text-red-600 mt-2" role="alert">
                {error}
              </p>
            )}

            {/* Loading Spinner */}
            {isUploading && (
              <div className="mt-4">
                <LoadingSpinner />
              </div>
            )}
          </div>
        </div>

        {/* Action Buttons */}
        <div className="mt-5 sm:mt-6 sm:flex sm:flex-row-reverse">
          <button
            type="button"
            onClick={handleUpload}
            disabled={!selectedFile || isUploading}
            className={`inline-flex justify-center w-full rounded-md border border-transparent shadow-sm px-4 py-2 bg-blue-600 text-base font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:ml-3 sm:w-auto sm:text-sm ${!selectedFile || isUploading ? "opacity-50 cursor-not-allowed" : ""}`}
          >
            {isUploading ? "Uploading..." : "Upload File"}
          </button>
          <button
            type="button"
            onClick={onClose}
            disabled={isUploading}
            className={`mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:mt-0 sm:w-auto sm:text-sm ${isUploading ? "opacity-50 cursor-not-allowed" : ""}`}
          >
            Cancel
          </button>
        </div>
      </div>
      {/* Add CSS for animation if needed */}
      <style>{`
        @keyframes fade-in-scale {
          from { opacity: 0; transform: scale(0.95); }
          to { opacity: 1; transform: scale(1); }
        }
        .animate-fade-in-scale { animation: fade-in-scale 0.3s ease-out; }
      `}</style>
    </div>
  );
};

export default UploadModal;
