export interface CompanyStatus {
  name: string;
  pdf_exists: boolean;
  processed: boolean;
  error?: string; // Optional error message per company
}

export interface DashboardData {
  Name: string;
  Industry: string | null; // Allow null from backend
  "Annual Revenue"?: string | number | null;
  "Employee Size"?: string | number | null;
  "Geographical Region"?: string | null;
  "Target Status"?: string | null;
  // --- Add New Target Fields ---
  "Emission targets"?: string | null;
  "Strategic Priorities (Energy Transition)"?: string | null; // Added field
  "Target Year"?: number | string | null;
  "Scope coverage"?: string | null;
  "Base Year"?: number | string | null;
  "Interim Targets"?: string | null;
  // --- End New Target Fields ---
  "Emissions Reduction (% achieved)"?: number | string | null;
  Renewables?: boolean | null; // Allow boolean or null
  Renewables_Justification?: string | null; // Added justification
  "Energy Efficiency"?: boolean | null;
  "Energy Efficiency_Justification"?: string | null; // Added justification
  Electrification?: boolean | null;
  Electrification_Justification?: string | null; // Added justification
  Bioenergy?: boolean | null;
  Bioenergy_Justification?: string | null; // Added justification
  CCUS?: boolean | null;
  CCUS_Justification?: string | null; // Added justification
  "Hydrogen Fuel"?: boolean | null;
  "Hydrogen Fuel_Justification"?: string | null; // Added justification
  "Behavioral Changes"?: boolean | null;
  [key: string]: any; // Keep for flexibility
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
