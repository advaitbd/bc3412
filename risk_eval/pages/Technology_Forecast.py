import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
from statsmodels.tsa.api import Holt
import json

st.title("Risk Evaluation for Technology Products")

if "tech_df" not in st.session_state:
    st.session_state.tech_df = pd.read_csv("Data/trade_tech_filtered.csv")

if "tech_results" not in st.session_state:
        st.session_state.tech_results = {}

count_risk = {"High": 0, "Low":0}

# Ensure the dataset is properly referenced
tech = st.session_state.tech_df.copy()

# Ensure "Year" is a proper datetime format, extract only the year, and set as index
if "Year" in tech.columns:
    tech["Year"] = pd.to_datetime(tech["Year"], format="%Y").dt.year
    tech.set_index("Year", inplace=True)
else:
    st.error("No 'Year' column found in the dataset. Please check the data format.")

# Exclude first column (assuming it's "Year")
available_countries = list(tech.columns)

# Multi-select for country selection
selected_countries = st.multiselect("Select countries for analysis:", available_countries, placeholder="You may select more than 1 country.")

# Select number of years for forecasting
forecast_years = 4 # until 2027

# initialise results
st.session_state.tech_results["Countries"] = {}

if selected_countries:
    # Show data and forecast for each selected country
    for country in selected_countries:
        st.subheader(f"Trade in Low Carbon Products Analysis for {country}")

        # Extract country-specific data
        country_data = tech[country].dropna()

        if country_data.empty:
            st.warning(f"No data available for {country}. Skipping forecast.")
            continue

        # Get last 5 years of actual data
        last_5_years = country_data.tail(5)

        # Apply Holt’s model
        holt_model = Holt(country_data, initialization_method="estimated").fit()
        forecast = holt_model.forecast(steps=forecast_years)

        # Create forecast index
        forecast_index = range(country_data.index[-1] + 1, country_data.index[-1] + 1 + forecast_years)
        
        # Combine actual last 5 years and forecasted data into one DataFrame
        forecast_df = pd.DataFrame({"Year": list(last_5_years.index) + list(forecast_index),
                                    "Trade Value": list(last_5_years.values) + list(forecast.values)})

        forecast_df.Year = pd.to_datetime(forecast_df.Year, format= "%Y")
        
        st.line_chart(forecast_df.set_index("Year"), x_label = "Year", y_label = "Trade in Low Carbon Technology Products (% of GDP)",)

        if forecast.values[-1] > forecast.values[-3]:
            st.markdown("**Overall: <span style='color:green;'>Low Risk</span>**", unsafe_allow_html=True)
            count_risk["Low"] += 1
            st.session_state.tech_results["Countries"][country] = "Low"
        else:
            st.markdown("**Overall: <span style='color:red;'>High Risk</span>**", unsafe_allow_html=True)
            count_risk["High"] += 1
            st.session_state.tech_results["Countries"][country] = "High"
        

        st.session_state.tech_results["Countries"]["Overall"] = max(count_risk.items(), key = lambda x: x[1])[0]

    if st.button("Export"):
        st.session_state.tech_results["Year"] = "2027"
        with open('result/technology.json', 'w') as f:
            json.dump(st.session_state.tech_results, f)
    


