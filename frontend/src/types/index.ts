export interface CompanyStatus {
  name: string;
  pdf_exists: boolean;
  processed: boolean;
  error?: string; // Optional error message per company
}

// Define based on your actual enhanced_dataset.csv columns and dashboard needs
export interface DashboardData {
  Name: string;
  Industry: string;
  "Annual Revenue"?: string | number | "N/A"; // Optional and allow N/A
  "Employee Size"?: string | number | "N/A";
  "Geographical Region"?: string | "N/A";
  "Target Status"?: string | "N/A";
  "Emission targets"?: string | "N/A";
  "Target Year"?: number | string | "N/A";
  "Scope coverage"?: string | "N/A";
  "Emissions Reduction (% achieved)"?: number | string | "N/A";
  Renewables?: boolean | string; // Allow boolean or string like 'Yes'/'No'/'N/A'
  "Energy Efficiency"?: boolean | string;
  Electrification?: boolean | string;
  Bioenergy?: boolean | string;
  CCUS?: boolean | string;
  "Hydrogen Fuel"?: boolean | string;
  "Behavioral Changes"?: boolean | string;
  [key: string]: any; // Allow other potential columns
}

export interface PathwayResponse {
  pathway_url: string; // This will be the full URL after processing in api.ts
}

export interface ApiError {
  message: string;
}

// For upload/process responses if needed
export interface GenericApiResponse {
  message: string;
  company_status?: CompanyStatus; // Optional updated status after processing
  error?: string;
}
