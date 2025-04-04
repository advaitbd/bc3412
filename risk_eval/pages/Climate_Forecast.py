import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
from statsmodels.tsa.api import Holt


st.title("Risk Evaluation for Temperature Rise")

if "temprise_df" not in st.session_state:
    st.session_state.temprise_df = pd.read_csv("Data/temprisedata2.csv")
    st.session_state.temprise_df = st.session_state.temprise_df.loc[st.session_state.temprise_df["Element"] == "Temperature change"]

if "results" not in st.session_state:
        st.session_state.results = {}

# Extract unique country names
available_countries = sorted(st.session_state.temprise_df["Area"].unique())

# User selects countries for temperature rise analysis
selected_countries = st.multiselect("Select countries for analysis:", available_countries)

if selected_countries:
    # Filter dataset for selected countries and "Temperature Change"
    filtered_temprise_df = st.session_state.temprise_df[
        (st.session_state.temprise_df["Area"].isin(selected_countries)) &
        (st.session_state.temprise_df["Element"] == "Temperature change")
    ].copy()

    count_risk = {"High":0, "Med": 0, "Low": 0}

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
            # st.subheader(f"📈 Temperature Rise Over Time in {country}")
            # st.line_chart(temprise_country_value)

            # Slider for number of years to forecast
            # years_to_forecast = st.slider(f"Select number of years to forecast for {country}:", min_value=1, max_value=20, value=10)
            years_to_forecast = 3 # constant to reach 2027

            # Forecasting Button
            try:
                holt_model = Holt(temprise_country_value, initialization_method="estimated").fit()
                forecast = holt_model.forecast(steps=years_to_forecast)
                forecast_index = range(temprise_country_value.index[-1] + 1, temprise_country_value.index[-1] + 1 + years_to_forecast)

                # Combine actual & forecasted data
                forecast_df = pd.DataFrame({"Year": list(temprise_country_value.index) + list(forecast_index),
                                                "Temperature Change": list(temprise_country_value.values) + list(forecast.values)})
                
                # Display combined actual + forecasted values
                st.subheader(f"Temperature Rise Data & Forecast for {country} (Last 5 Years + Next {years_to_forecast} Years)")
                # st.dataframe(forecast_df.set_index("Year"))

                # Plot actual vs forecast
                fig, ax = plt.subplots(figsize=(10, 5))
                ax.plot(temprise_country_value, label="Actual", color="blue")
                ax.plot(forecast_index, forecast, label="Holt’s Forecast", linestyle="dashed", color="red")
                ax.set_title(f"Holt’s Forecast: Temperature Rise in {country}")
                ax.legend()
                ax.set_xlabel("Year")
                ax.set_ylabel("Temperature Rise (˚C)")
                st.pyplot(fig)

                final_forecast = forecast.values[-1]  # Last forecasted temperature

                if final_forecast <= 1.5:
                    st.markdown("**Overall: <span style='color:green;'>Low Risk</span>**", unsafe_allow_html=True)
                    count_risk["Low"] += 1
                elif 1.6 <= final_forecast <= 2.9:
                    st.markdown("**Overall: <span style='color:yellow;'>Medium Risk</span>**", unsafe_allow_html=True)
                    count_risk["Med"] += 1
                else:
                    st.markdown("**Overall: <span style='color:red;'>High Risk</span>**", unsafe_allow_html=True)
                    count_risk["High"] += 1

            except Exception as e:
                st.error(f"An error occurred while generating the forecast: {e}")

    
    st.session_state.results["Climate"] = max(count_risk.items(), key = lambda x: x[1])[0]