# Risk Evaluation Tool MVP

## Overview
The risk evaluation tool analyses 3 aspects:
1. Climate Risk
2. Technology Risk
3. Policy Risk

## Directory Structure 
```
.
├── Data           
    ├── carbon_pricing_filtered.csv
    ├── temprisedata2.csv
    └── trade_tech_filtered.csv
├── pages
    ├── Carbon_Visualisation
    ├── Climate_Forecast
    └── Technology_Forecast
├── result  
    ├── climate.json
    ├── policy.json
    └── technology.json
├── Carbon Forecast.py   # main file to run the streamlit ui
├── README.md
└── risk_evaluator.py    # risk evaluation directly integrated into recommendation pipeline
```

## Usage
The tool is developed as a Streamlit App. Install `Dependencies Required` and run `Commands` to use the tool. 

### Dependencies Required

*   `pandas`
*   `numpy`
*   `streamlit`
*   `statsmodels`
*   `json`

### Commands
```
streamlit run Carbon_Forecast.py
```

## Features
1. Customisable inputs for countries (all risks) and emission scope (Policy risk)
2. Visualise the risk trends in graphical formats
3. Country and company specific analysis of each risk, displayed in risk levels (`High`, `Med` or `Low`) 
4. `Export` button in each `Forecast` page will convert the results into separate json files, found under `result` folder. 