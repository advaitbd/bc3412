# Energy Transition Data Pipeline MVP

## Overview

This project implements a data pipeline MVP (Minimum Viable Product) designed to analyze corporate sustainability reports (specifically PDFs) for energy companies. It extracts key information using Google's Gemini AI model, integrates it with existing company data, classifies transition actions, and generates tailored energy transition recommendations presented as an HTML roadmap.

## Features

*   **PDF Data Extraction:** Extracts relevant text sections (Executive Summary, Strategic Priorities, Financial Commitments, Risks, Milestones) from PDF reports.
*   **Gemini AI Integration:** Leverages the Gemini API for data extraction and generating structured recommendations.
*   **Data Integration:** Combines extracted PDF data with initial company data from an Excel sheet.
*   **Action Classification:** Categorizes company actions based on keywords found in the extracted text.
*   **Recommendation Generation:** Creates textual summaries and structured JSON roadmaps for energy transition strategies, tailored to each company.
*   **HTML Roadmap Visualization:** Generates user-friendly HTML files visualizing the recommended transition pathway for each company.
*   **Caching:** Saves the enhanced dataset to avoid reprocessing PDFs on subsequent runs unless forced.

## Project Structure

```
.
├── .env                # Stores API keys (created from .env.sample)
├── .env.sample         # Sample environment file template
├── .gitignore          # Specifies intentionally untracked files
├── data/
│   ├── Pathfinder Data.xlsx # Initial company data
│   └── pdfs/
│       └── [CompanyName].pdf # Input PDF reports (e.g., BP.pdf)
├── risk_eval/          # Risk Evaluation Models
    ├── Data            # contain the datasets used for risk evaluations
        ├── carbon_pricing_filtered.csv
        ├── temprisedata2.csv
        ├── trade_tech_filtered.csv

    ├── pages           # tabs for UI
        ├── Carbon_Visualisation
        ├── Climate_Forecast
        └── Technology_Forecast
    ├── results         # store results
    └── Carbon Forecast.py   # main file to run the streamlit ui
├── main.py             # Main script for the pipeline execution
├── outputs/
│   ├── enhanced_dataset.csv # Output CSV with integrated and classified data
│   └── [CompanyName].html   # Generated HTML recommendation roadmap
│   └── [CompanyName]_raw_fallback.html # Raw roadmap output if JSON parsing fails
├── requirements.txt    # Python dependencies
└── venv/               # Python virtual environment (created during setup)
```

## Setup

1.  **Clone the Repository:**
    ```bash
    git clone <repository_url>
    cd <repository_directory>
    ```

2.  **Create and Activate Virtual Environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows use `venv\\Scripts\\activate`
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment Variables:**
    *   Copy the sample environment file:
        ```bash
        cp .env.sample .env
        ```
    *   Edit the `.env` file and add your Google API Key:
        ```
        GOOGLE_API_KEY=YOUR_GOOGLE_API_KEY_HERE
        ```
    *   *Note:* Ensure the `.env` file is listed in your `.gitignore` to prevent accidentally committing your API key.

5.  **Prepare Input Data:**
    *   Place the initial company data Excel file at `data/Pathfinder Data.xlsx`.
    *   Place the corresponding company PDF reports inside the `data/pdfs/` directory. The PDF filenames should match the company names listed in the `Name` column of the Excel file (e.g., if the Excel has "BP", the PDF should be named `BP.pdf`).

## Usage

Run the main pipeline script from the project's root directory:

*   **Generate recommendations for ALL companies in the dataset:**
    ```bash
    python3 main.py
    ```
    This will process PDFs (if `outputs/enhanced_dataset.csv` doesn't exist), classify actions, save the enhanced dataset, and then generate recommendations and HTML roadmaps for every company found.

*   **Generate recommendations for a SPECIFIC company:**
    Use the `-c` or `--company` argument. Make sure the company name matches the entry in the `Name` column of the input Excel/CSV.
    ```bash
    python3 main.py -c "Exxon Mobil"
    ```

*   **Force Reprocessing of PDFs:**
    Use the `-f` or `--force-reprocess` flag to ignore any existing `enhanced_dataset.csv` and re-extract data from all PDFs.
    ```bash
    python3 main.py -f
    ```
    *(This will consume more API credits)*

*   **Enable Debug Logging:**
    Use the `--debug` flag for more verbose logging output.
    ```bash
    python3 main.py --debug
    ```

## Input Data

*   **`data/Pathfinder Data.xlsx`:** An Excel spreadsheet containing initial metadata about the companies. Must include a 'Name' column that matches the PDF filenames in `data/pdfs/`.
*   **`data/pdfs/[CompanyName].pdf`:** Annual or sustainability reports for each company, named according to the 'Name' column in the Excel file.

## Output

*   **`outputs/enhanced_dataset.csv`:** A CSV file containing the original data merged with extracted information from PDFs and action classifications. This file is used as a cache to avoid re-processing PDFs.
*   **`outputs/[CompanyName].html`:** An HTML file generated for each processed company, visualizing the structured energy transition roadmap recommended by the AI.
*   **`outputs/[CompanyName]_raw_fallback.html`:** If the AI's roadmap output cannot be parsed correctly as JSON, this raw output file is generated instead.

## Dependencies

Key Python libraries used:

*   `pandas`
*   `openpyxl`
*   `PyMuPDF` (fitz)
*   `google-generativeai`
*   `python-dotenv`
*   `numpy`
*   `argparse`
*   `streamlit`
*   `matplotlib`
*   `statsmodels`

See `requirements.txt` for the full list.
