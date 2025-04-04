import React, { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import PathwayViewer from "../components/PathwayViewer";
import LoadingSpinner from "../components/LoadingSpinner";
import { generatePathway } from "../services/api";
import type { PathwayResponse, ApiError } from "../types";

const PathwayDisplayPage: React.FC = () => {
  const { companyName } = useParams<{ companyName: string }>();
  const [pathwayUrl, setPathwayUrl] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchPathway = async () => {
      if (!companyName) {
        setError("Company name not provided in URL.");
        setIsLoading(false);
        return;
      }
      setIsLoading(true);
      setError(null);
      setPathwayUrl(null); // Clear previous URL

      console.log(`Requesting pathway for: ${companyName}`); // Debugging
      const result = await generatePathway(companyName);

      if ("pathway_url" in result) {
        setPathwayUrl(result.pathway_url);
      } else {
        setError(`Failed to generate pathway: ${result.message}`);
      }
      setIsLoading(false);
    };

    fetchPathway();
  }, [companyName]); // Re-run if companyName changes

  if (!companyName) {
    return (
      <div className="text-red-600">
        Error: No company specified in the URL.
      </div>
    );
  }

  return (
    <div>
      <nav className="mb-4" aria-label="Breadcrumb">
        <ol className="flex items-center space-x-2 text-sm text-gray-500">
          <li>
            <Link to="/" className="hover:text-gray-700">
              Dashboard
            </Link>
          </li>
          <li>
            <span className="mx-2">/</span>
          </li>
          <li className="font-medium text-gray-700" aria-current="page">
            Pathway for {decodeURIComponent(companyName)}
          </li>
        </ol>
      </nav>

      {isLoading && <LoadingSpinner />}

      {error && (
        <div
          className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4"
          role="alert"
        >
          <strong className="font-bold">Error: </strong>
          <span className="block sm:inline">{error}</span>
          <p className="text-sm mt-2">
            Please ensure the company report has been processed successfully.
          </p>
          <Link
            to="/manage-companies"
            className="text-sm font-medium text-red-800 hover:underline"
          >
            Go to Company Management
          </Link>
        </div>
      )}

      {!isLoading && pathwayUrl && (
        <PathwayViewer
          url={pathwayUrl}
          companyName={decodeURIComponent(companyName)}
        />
      )}

      {!isLoading && !pathwayUrl && !error && (
        <p className="text-gray-500">Could not load pathway.</p> // Should ideally be handled by error state
      )}
    </div>
  );
};

export default PathwayDisplayPage;
