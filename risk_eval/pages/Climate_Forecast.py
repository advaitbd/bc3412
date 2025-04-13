import streamlit as st
import pandas as pd
from statsmodels.tsa.api import Holt
import json


st.title("Risk Evaluation for Temperature Rise")

if "temprise_df" not in st.session_state:
    st.session_state.temprise_df = pd.read_csv("Data/temprisedata2.csv")
    st.session_state.temprise_df = st.session_state.temprise_df.loc[st.session_state.temprise_df["Element"] == "Temperature change"]

if "climate_results" not in st.session_state:
        st.session_state.climate_results = {}

# Extract unique country names
available_countries = sorted(st.session_state.temprise_df["Area"].unique())

# User selects countries for temperature rise analysis
selected_countries = st.multiselect("Select countries for analysis:", available_countries, placeholder="You may select more than 1 country.")

if selected_countries:
    # Filter dataset for selected countries and "Temperature Change"
    filtered_temprise_df = st.session_state.temprise_df[
        (st.session_state.temprise_df["Area"].isin(selected_countries)) &
        (st.session_state.temprise_df["Element"] == "Temperature change")
    ].copy()

    count_risk = {"High":0, "Med": 0, "Low": 0}

    st.session_state.climate_results["Countries"] = {}

    for country in selected_countries:
        temprise_country = filtered_temprise_df[filtered_temprise_df["Area"] == country]
        
        # Ensure Year column is properly formatted
        temprise_country["Year"] = pd.to_datetime(temprise_country["Year"], format="%Y").dt.year
        temprise_country.set_index("Year", inplace=True)

        # Handle missing values
        temprise_country_value = temprise_country["Value"].fillna(method='ffill').replace([float('inf'), -float('inf')], 0)

        if temprise_country_value.empty or temprise_country_value.isnull().all():
            st.warning(f"No valid temperature change data available for {country}.")
        else:
            st.subheader(f"Temperature Rise Analysis in {country}")
            # st.line_chart(temprise_country_value)

            # Slider for number of years to forecast
            # years_to_forecast = st.slider(f"Select number of years to forecast for {country}:", min_value=1, max_value=20, value=10)
            years_to_forecast = 3 # constant to reach 2027

            try:
                holt_model = Holt(temprise_country_value, initialization_method="estimated").fit()
                forecast = holt_model.forecast(steps=years_to_forecast)
                forecast_index = range(temprise_country_value.index[-1] + 1, temprise_country_value.index[-1] + 1 + years_to_forecast)

                # Combine actual & forecasted data
                forecast_df = pd.DataFrame({"Year": list(temprise_country_value.index) + list(forecast_index),
                                                "Temperature Change": list(temprise_country_value.values) + list(forecast.values)})
                forecast_df.Year = pd.to_datetime(forecast_df.Year, format= "%Y")

                # Display combined actual + forecasted values
                st.line_chart(forecast_df.set_index("Year"), x_label = "Year", y_label = "Temperature Rise (˚C)")

                final_forecast = forecast.values[-1]  # Last forecasted temperature

                if final_forecast <= 1.5:
                    st.markdown("**Overall: <span style='color:green;'>Low Risk</span>**", unsafe_allow_html=True)
                    count_risk["Low"] += 1
                    st.session_state.climate_results["Countries"][country] = "Low"
                elif 1.6 <= final_forecast <= 2.9:
                    st.markdown("**Overall: <span style='color:orange;'>Medium Risk</span>**", unsafe_allow_html=True)
                    count_risk["Med"] += 1
                    st.session_state.climate_results["Countries"][country] = "Med"
                else:
                    st.markdown("**Overall: <span style='color:red;'>High Risk</span>**", unsafe_allow_html=True)
                    count_risk["High"] += 1
                    st.session_state.climate_results["Countries"][country] = "High"

            except Exception as e:
                st.error(f"An error occurred while generating the forecast: {e}")

   
    st.session_state.climate_results["Overall"] = max(count_risk.items(), key = lambda x: x[1])[0]
    
    
    if st.button("Export"):
        st.session_state.climate_results["Year"] = "2027"
        with open('result/climate.json', 'w') as f:
            json.dump(st.session_state.climate_results, f)