import axios, { AxiosError } from "axios";
import type {
  CompanyStatus,
  DashboardData,
  PathwayResponse,
  ApiError,
  GenericApiResponse,
} from "../types";

// Use environment variable for API base URL, fallback for development
// VITE_API_URL should be like http://localhost:5001 (NO trailing slash or /api)
const API_DOMAIN = import.meta.env.VITE_API_URL || "http://localhost:5001";
const API_BASE_URL = `${API_DOMAIN}/api`; // Append /api for specific calls

console.log("API Domain:", API_DOMAIN); // For debugging

// --- Helper for Error Handling ---
const handleError = (error: unknown, context: string): ApiError => {
  let errorMessage = `An unknown error occurred in ${context}`;
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<{
      error?: string;
      message?: string;
    }>;
    console.error(
      `Axios error in ${context}:`,
      axiosError.response?.data || axiosError.message,
    );
    // Prefer specific error message from backend if available
    errorMessage =
      axiosError.response?.data?.error ||
      axiosError.response?.data?.message ||
      axiosError.message ||
      `HTTP error ${axiosError.response?.status}`;
  } else if (error instanceof Error) {
    console.error(`Error in ${context}:`, error.message);
    errorMessage = error.message;
  } else {
    console.error(`Unknown error type in ${context}:`, error);
  }
  return { message: errorMessage };
};

// --- API Functions ---

export const getCompanies = async (): Promise<CompanyStatus[] | ApiError> => {
  try {
    const response = await axios.get<CompanyStatus[]>(
      `${API_BASE_URL}/companies`,
    );
    // Check if backend returned an error structure within the data
    if (
      response.data &&
      Array.isArray(response.data) &&
      response.data.length > 0 &&
      response.data[0].error
    ) {
      return handleError(
        new Error(response.data[0].error),
        "getCompanies - Backend Error",
      );
    }
    return response.data;
  } catch (error) {
    return handleError(error, "getCompanies");
  }
};

export const uploadReport = async (
  companyName: string,
  file: File,
): Promise<GenericApiResponse | ApiError> => {
  const formData = new FormData();
  formData.append("file", file);
  try {
    const response = await axios.post<GenericApiResponse>(
      `${API_BASE_URL}/companies/${encodeURIComponent(companyName)}/upload`,
      formData,
      { headers: { "Content-Type": "multipart/form-data" } },
    );
    return response.data;
  } catch (error) {
    return handleError(error, "uploadReport");
  }
};

export const triggerProcessing = async (
  companyName: string,
): Promise<GenericApiResponse | ApiError> => {
  try {
    const response = await axios.post<GenericApiResponse>(
      `${API_BASE_URL}/companies/${encodeURIComponent(companyName)}/process`,
    );
    return response.data;
  } catch (error) {
    return handleError(error, "triggerProcessing");
  }
};

export const getDashboardData = async (): Promise<
  DashboardData[] | ApiError
> => {
  try {
    const response = await axios.get<DashboardData[]>(
      `${API_BASE_URL}/dashboard/data`,
    );
    return response.data;
  } catch (error) {
    return handleError(error, "getDashboardData");
  }
};

export const generatePathway = async (
  companyName: string,
): Promise<PathwayResponse | ApiError> => {
  try {
    // Call the API endpoint which returns a RELATIVE path starting with /static/...
    const response = await axios.post<{ pathway_url: string }>(
      `${API_BASE_URL}/companies/${encodeURIComponent(companyName)}/generate-pathway`,
    );

    // Prepend the API_DOMAIN to the relative path to get the full URL
    const fullUrl = `${API_DOMAIN}${response.data.pathway_url}`;
    console.log("Generated Full Pathway URL:", fullUrl); // Debugging

    return { pathway_url: fullUrl };
  } catch (error) {
    return handleError(error, "generatePathway");
  }
};
