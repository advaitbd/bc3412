import streamlit as st
import pandas as pd
from statsmodels.tsa.api import Holt #(Trend + Level - Seasonality)
import matplotlib.pyplot as plt

if "df" not in st.session_state:
    st.session_state.df = pd.read_csv("Data/carbon_pricing_filtered.csv")

st.title("Carbon Pricing")
countries = st.multiselect(label="Countries", options=sorted(st.session_state.df.AREA.unique()), placeholder="You may select more than 1 country.")
print(countries)

if countries:
    sector = st.radio(label="Industry", options=sorted(st.session_state.df["SECTOR"].loc[st.session_state.df["AREA"].isin(countries)].unique()))
    print(sector)

    if sector:
        sources = st.multiselect(label="Scope", options=sorted(st.session_state.df["SOURCE"].loc[(st.session_state.df["AREA"].isin(countries)) &
                                                                                                  (st.session_state.df["SECTOR"]==sector)].unique()))
        print(sources)
        
        if sources:
            if st.button("Forecast"):
                fil_df = st.session_state.df.loc[(st.session_state.df["AREA"].isin(countries)) & 
                                                (st.session_state.df["SECTOR"] == sector) & 
                                                (st.session_state.df["SOURCE"].isin(sources))]
                
                st.header("Analysis")
                
                if (fil_df.loc[(fil_df.TOTTAX > 0) | (fil_df.MPERPRI >0)].empty):
                    st.warning("NO tax or credit used")
                    
                else:

                    if not (fil_df.loc[(fil_df.TOTTAX > 0) & (fil_df.MPERPRI > 0)].empty):
                        st.warning("Both credit and tax used")
                    elif not (fil_df.loc[(fil_df.MPERPRI > 0)].empty):
                        st.warning("Carbon credit used only")
                    elif not (fil_df.loc[(fil_df.FUETAX > 0) & (fil_df.CARBTAX > 0)].empty):
                        st.warning("Fuel and Carbon tax used")
                    elif not (fil_df.loc[(fil_df.FUETAX > 0)].empty):
                        st.warning("Fuel tax used only")
                    else:
                        st.warning("Carbon tax used only")


                    st.session_state.forecast_df = pd.DataFrame()
                    ecr_change_df = {}
                    necr_change_df = {}

                    for country in countries:
                        ecr_change_df[country] = {}
                        necr_change_df[country] = {}

                        for source in sources:
                            spec_df = fil_df.loc[(fil_df["AREA"] == country) & 
                                            (fil_df["SECTOR"] == sector) & 
                                            (fil_df["SOURCE"] == source)]
                            
                            spec_df["TIME"] = pd.to_datetime(spec_df["TIME"])
                            spec_df.set_index("TIME", inplace=True)
                        
                            new_df = pd.DataFrame()
                            for measure in ["FUETAX", "CARBTAX", "MPERPRI", "SUBSID"]:
                                model = Holt(spec_df[measure])
                                model_double_fit = model.fit()

                                pred = model_double_fit.forecast(4)
                                if pred.isna().all() == True:
                                    pred = pred.fillna(spec_df[measure].iloc[-1])
                                
                                new_df[measure] = pd.concat([spec_df[measure], pd.DataFrame(pred,columns=[measure])]) # until 2027
                                                
                                if measure == "SUBSID":
                                    new_df[measure] = new_df[measure].replace(to_replace=new_df[measure].loc[new_df[measure]>0].unique(), value=0)
                                else:
                                    new_df[measure] = new_df[measure].replace(to_replace=new_df[measure].loc[new_df[measure]<0].unique(), value=0)


                            new_df["ECRATE"] = new_df["CARBTAX"] + new_df["FUETAX"] + new_df["MPERPRI"]
                            new_df["NETECR"] = new_df["ECRATE"] + new_df["SUBSID"]

                            new_df["AREA"] = country
                            new_df["SOURCE"] = source

                            st.session_state.forecast_df = pd.concat([st.session_state.forecast_df, new_df])

                            # show individual changes
                            
                            ecr_change_df[country][source] = (new_df["ECRATE"].iloc[-1] - new_df["ECRATE"].iloc[4])
                            necr_change_df[country][source] = (new_df["NETECR"].iloc[-1] - new_df["NETECR"].iloc[4])

                    st.subheader("Effective Carbon Rate")
                    change = pd.DataFrame(ecr_change_df).values.sum()
                    if change > 0:
                        st.markdown("Overall: :red[High Risk]")
                    else:
                        st.markdown("Overall: :green[Low Risk]")
                    # st.write("Overall", change)
                    st.dataframe(ecr_change_df)


                    st.subheader("Net Effective Carbon Rate")
                    change = pd.DataFrame(necr_change_df).values.sum()
                    
                    if change > 0:
                        st.markdown("Overall: :red[High Risk]")
                    else:
                        st.markdown("Overall: :green[Low Risk]")
                    # st.write("Overall", change)
                    st.dataframe(necr_change_df)

                    
# TODO integrate the tech and climate 
if "temprise_df" not in st.session_state:
    st.session_state.temprise_df = pd.read_csv("Data/temprisedata2.csv")

st.title("Temperature Rise Analysis")

# Extract unique country names
available_countries = sorted(st.session_state.temprise_df["Area"].unique())

# User selects countries for temperature rise analysis
selected_countries = st.multiselect("Select countries for analysis:", available_countries, default=available_countries[:1])

if selected_countries:
    # Filter dataset for selected countries and "Temperature Change"
    filtered_temprise_df = st.session_state.temprise_df[
        (st.session_state.temprise_df["Area"].isin(selected_countries)) &
        (st.session_state.temprise_df["Element"] == "Temperature change")
    ].copy()

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
            st.subheader(f"📈 Temperature Rise Over Time in {country}")
            st.line_chart(temprise_country_value)

            # Slider for number of years to forecast
            years_to_forecast = st.slider(f"Select number of years to forecast for {country}:", min_value=1, max_value=20, value=10)

            # Forecasting Button
            if st.button(f"Run Forecast for {country} (Next {years_to_forecast} Years)"):
                try:
                    holt_model = Holt(temprise_country_value, initialization_method="estimated").fit()
                    forecast = holt_model.forecast(steps=years_to_forecast)
                    forecast_index = range(temprise_country_value.index[-1] + 1, temprise_country_value.index[-1] + 1 + years_to_forecast)

                    # Combine actual & forecasted data
                    forecast_df = pd.DataFrame({"Year": list(temprise_country_value.index) + list(forecast_index),
                                                 "Temperature Change": list(temprise_country_value.values) + list(forecast.values)})
                    
                    # Display combined actual + forecasted values
                    st.subheader(f"Temperature Rise Data & Forecast for {country} (Last 5 Years + Next {years_to_forecast} Years)")
                    st.dataframe(forecast_df.set_index("Year"))

                    # Plot actual vs forecast
                    fig, ax = plt.subplots(figsize=(10, 5))
                    ax.plot(temprise_country_value, label="Actual", color="blue")
                    ax.plot(forecast_index, forecast, label="Holt’s Forecast", linestyle="dashed", color="red")
                    ax.set_title(f"Holt’s Forecast: Temperature Rise in {country}")
                    ax.legend()
                    st.pyplot(fig)

                    final_forecast = forecast.values[-1]  # Last forecasted temperature

                    if final_forecast <= 1.5:
                        st.markdown("**Overall: <span style='color:green;'>Low Risk</span>**", unsafe_allow_html=True)
                    elif 1.6 <= final_forecast <= 2.9:
                        st.markdown("**Overall: <span style='color:yellow;'>Medium Risk</span>**", unsafe_allow_html=True)
                    else:
                        st.markdown("**Overall: <span style='color:red;'>High Risk</span>**", unsafe_allow_html=True)


                except Exception as e:
                    st.error(f"An error occurred while generating the forecast: {e}")


#Tech Forecast
# Load dataset into session state
if "tech" not in st.session_state:
    st.session_state.tech = pd.read_csv("Data/trade_tech_filtered.csv")

st.title("Technology Risk")

# Ensure the dataset is properly referenced
tech = st.session_state.tech.copy()

# Ensure "Year" is a proper datetime format, extract only the year, and set as index
if "Year" in tech.columns:
    tech["Year"] = pd.to_datetime(tech["Year"], format="%Y").dt.year
    tech.set_index("Year", inplace=True)
else:
    st.error("No 'Year' column found in the dataset. Please check the data format.")

# Exclude first column (assuming it's "Year")
available_countries = list(tech.columns)

# Multi-select for country selection
selected_countries = st.multiselect("Select countries for analysis:", available_countries, default=available_countries[:1])

# Select number of years for forecasting
forecast_years = st.slider(f"Select number of years to forecast for {country}:", min_value=1, max_value=20, value=10, key=f"slider_{country}")

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

    # Display combined actual + forecasted values
    st.write(f"Trade in Low Carbon Products Data & Forecast for {country} (Last 5 Years + Next {forecast_years} Years)")
    st.dataframe(forecast_df.set_index("Year"))

    # Plot Actual vs Forecast
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(country_data, label="Actual", color="blue")
    ax.plot(forecast_index, forecast, label="Forecasted Trade in Low Carbon Products", linestyle="dashed", color="red")
    ax.set_title(f"Forecasted Trade in Low Carbon Products for {country}")
    ax.legend()
    st.pyplot(fig)


# TODO export into a csv (climate/policy/low-carbon products)
    