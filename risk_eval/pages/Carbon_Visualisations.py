import streamlit as st
import pandas as pd

if "forecast_carbon_df" in st.session_state:
        
    st.title("Carbon Pricing Visualisation")
        
    st.session_state.choice = st.radio("Evaluation Mode", options=["Effective Carbon Rate", "Net Effective Carbon Rate"])

    st.header("Individual Diagrams")
    if st.session_state.choice == "Effective Carbon Rate":
        max_per_year = st.session_state.forecast_carbon_df.loc[st.session_state.forecast_carbon_df.groupby([st.session_state.forecast_carbon_df.index])["ECRATE"].idxmax()]
        for country in st.session_state.forecast_carbon_df.AREA.unique():
            for source in st.session_state.forecast_carbon_df.SOURCE.unique():
                st.write("Effective Carbon Rate", "(", country, "-", source, ")")
                data = st.session_state.forecast_carbon_df[["FUETAX", "CARBTAX", "MPERPRI"]].loc[(st.session_state.forecast_carbon_df["AREA"] == country) & (st.session_state.forecast_carbon_df["SOURCE"] == source)]
                st.area_chart(data.mask(data == 0).dropna(axis=1), x_label="Year", y_label="Euros per tonnes CO2 equivalent", stack=True)

    else:
        max_per_year = st.session_state.forecast_carbon_df.loc[st.session_state.forecast_carbon_df.groupby([st.session_state.forecast_carbon_df.index])["NETECR"].idxmax()]
        for country in st.session_state.forecast_carbon_df.AREA.unique():
                for source in st.session_state.forecast_carbon_df.SOURCE.unique():
                    st.write("Net Effective Carbon Rate", "(", country, "-", source, ")")
                    st.area_chart(data=st.session_state.forecast_carbon_df["NETECR"].loc[(st.session_state.forecast_carbon_df["AREA"] == country) &
                                                                                (st.session_state.forecast_carbon_df["SOURCE"] == source)], 
                                                                                x_label="Year", y_label="Euros per tonnes CO2 equivalent")






