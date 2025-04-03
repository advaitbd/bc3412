# risk_eval/risk_evaluator.py

import pandas as pd
import json
import os
import logging
from pathlib import Path
from statsmodels.tsa.api import Holt

def evaluate_climate_risk(countries):
    """
    Evaluates climate risk for specified countries.
    Returns risk level (High, Medium, Low) and detailed data.
    """
    try:
        # Get the directory that contains this file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Construct the path to the data file
        temprise_path = os.path.join(current_dir, "Data", "temprisedata2.csv")

        # Load the temperature rise data
        temprise_df = pd.read_csv(temprise_path)
        temprise_df = temprise_df.loc[temprise_df["Element"] == "Temperature change"]

        # Filter for relevant countries
        filtered_df = temprise_df[temprise_df["Area"].isin(countries)]

        results = {"overall_risk": "Low", "country_risks": {}}
        count_risk = {"High":0, "Med": 0, "Low": 0}

        # Process each country
        for country in countries:
            if country not in filtered_df["Area"].values:
                results["country_risks"][country] = {
                    "status": "No data available",
                    "risk_level": "Unknown"
                }
                continue

            country_data = filtered_df[filtered_df["Area"] == country]
            country_data["Year"] = pd.to_datetime(country_data["Year"], format="%Y").dt.year
            country_data.set_index("Year", inplace=True)

            # Fill missing values
            country_values = country_data["Value"].fillna(method='ffill').replace([float('inf'), -float('inf')], 0)

            if country_values.empty or country_values.isnull().all():
                results["country_risks"][country] = {
                    "status": "Insufficient data",
                    "risk_level": "Unknown"
                }
                continue

            try:
                # Apply Holt's forecasting
                years_to_forecast = 3  # To reach 2027
                holt_model = Holt(country_values, initialization_method="estimated").fit()
                forecast = holt_model.forecast(steps=years_to_forecast)

                final_forecast = forecast.values[-1]

                # Determine risk level
                if final_forecast <= 1.5:
                    risk_level = "Low"
                    count_risk["Low"] += 1
                elif 1.6 <= final_forecast <= 2.9:
                    risk_level = "Medium"
                    count_risk["Med"] += 1
                else:
                    risk_level = "High"
                    count_risk["High"] += 1

                results["country_risks"][country] = {
                    "status": "Forecasted",
                    "risk_level": risk_level,
                    "forecast_temp_rise": round(final_forecast, 2)
                }

            except Exception as e:
                results["country_risks"][country] = {
                    "status": f"Error in forecasting: {str(e)}",
                    "risk_level": "Unknown"
                }

        # Determine overall risk
        if count_risk["High"] > 0:
            results["overall_risk"] = "High"
        elif count_risk["Med"] > count_risk["Low"]:
            results["overall_risk"] = "Medium"
        else:
            results["overall_risk"] = "Low"

        return results
    except Exception as e:
        logging.error(f"Error in climate risk evaluation: {e}")
        return {"overall_risk": "Unknown", "error": str(e)}

def evaluate_carbon_price_risk(countries, sector="Industry"):
    """
    Evaluates carbon pricing risk for specified countries and sector.
    Returns risk level (High, Low) and detailed data.
    """
    try:
        # Get the directory that contains this file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Construct the path to the data file
        carbon_path = os.path.join(current_dir, "Data", "carbon_pricing_filtered.csv")

        # Load carbon pricing data
        carbon_df = pd.read_csv(carbon_path)

        # Filter for relevant countries
        filtered_df = carbon_df[carbon_df["AREA"].isin(countries)]

        if filtered_df.empty:
            return {
                "overall_risk": "Unknown",
                "details": "No carbon pricing data available for specified countries"
            }

        # Filter for sector if available in the data
        if "SECTOR" in filtered_df.columns:
            filtered_df = filtered_df[filtered_df["SECTOR"] == sector]

        results = {"overall_risk": "Low", "country_details": {}}
        high_risk_count = 0

        for country in countries:
            country_df = filtered_df[filtered_df["AREA"] == country]

            if country_df.empty:
                results["country_details"][country] = {
                    "status": "No data available",
                    "risk_level": "Unknown"
                }
                continue

            # Convert time column to datetime and set as index
            country_df["TIME"] = pd.to_datetime(country_df["TIME"])
            country_df.set_index("TIME", inplace=True)

            # Prepare forecast dataframe
            forecast_df = pd.DataFrame()

            # For each source and measure, forecast future values
            for source in country_df["SOURCE"].unique():
                source_df = country_df[country_df["SOURCE"] == source]

                source_forecast = {"source": source, "measures": {}}

                for measure in ["FUETAX", "CARBTAX", "MPERPRI", "SUBSID"]:
                    if measure in source_df.columns:
                        measure_data = source_df[measure]

                        try:
                            # Apply Holt's model
                            model = Holt(measure_data)
                            model_fit = model.fit()
                            pred = model_fit.forecast(4)  # Forecast to 2027

                            # Fill NaN values with last known value
                            if pred.isna().all():
                                pred = pred.fillna(measure_data.iloc[-1])

                            # Calculate change
                            initial_value = measure_data.iloc[-1] if not measure_data.empty else 0
                            final_value = pred.iloc[-1] if not pred.empty else 0
                            change = final_value - initial_value

                            source_forecast["measures"][measure] = {
                                "initial": float(initial_value),
                                "forecast": float(final_value),
                                "change": float(change)
                            }

                        except Exception as e:
                            source_forecast["measures"][measure] = {
                                "error": str(e),
                                "status": "Forecast failed"
                            }

                # Calculate Effective Carbon Rate changes
                ecr_change = 0
                for m in ["CARBTAX", "FUETAX", "MPERPRI"]:
                    if m in source_forecast["measures"]:
                        ecr_change += source_forecast["measures"][m].get("change", 0)

                source_forecast["ecr_change"] = ecr_change

                # Determine risk level for this source
                if ecr_change > 0:
                    source_forecast["risk_level"] = "High"
                    high_risk_count += 1
                else:
                    source_forecast["risk_level"] = "Low"

                results["country_details"][country] = source_forecast

        # Determine overall risk level
        if high_risk_count > len(countries) / 2:
            results["overall_risk"] = "High"
        else:
            results["overall_risk"] = "Low"

        return results

    except Exception as e:
        logging.error(f"Error in carbon price risk evaluation: {e}")
        return {"overall_risk": "Unknown", "error": str(e)}

def evaluate_technology_risk(countries):
    """
    Evaluates technology transition risk for specified countries.
    Returns risk level (High, Low) and detailed data.
    """
    try:
        # Get the directory that contains this file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Construct the path to the data file
        tech_path = os.path.join(current_dir, "Data", "trade_tech_filtered.csv")

        # Load technology data
        tech_df = pd.read_csv(tech_path)

        # Ensure "Year" is properly formatted
        if "Year" in tech_df.columns:
            tech_df["Year"] = pd.to_datetime(tech_df["Year"], format="%Y").dt.year
            tech_df.set_index("Year", inplace=True)

        results = {"overall_risk": "Low", "country_details": {}}
        high_risk_count = 0

        for country in countries:
            if country not in tech_df.columns:
                results["country_details"][country] = {
                    "status": "No data available",
                    "risk_level": "Unknown"
                }
                continue

            # Extract country data
            country_data = tech_df[country].dropna()

            if country_data.empty:
                results["country_details"][country] = {
                    "status": "Insufficient data",
                    "risk_level": "Unknown"
                }
                continue

            try:
                # Get last 5 years of data
                last_5_years = country_data.tail(5)

                # Apply Holt's forecasting
                forecast_years = 4  # to 2027
                holt_model = Holt(country_data, initialization_method="estimated").fit()
                forecast = holt_model.forecast(steps=forecast_years)

                # Check if trend is decreasing (higher risk)
                if forecast.values[-1] <= forecast.values[-3]:
                    risk_level = "High"
                    high_risk_count += 1
                else:
                    risk_level = "Low"

                # Create detailed results
                country_result = {
                    "status": "Forecasted",
                    "risk_level": risk_level,
                    "forecast_trend": "Decreasing" if risk_level == "High" else "Increasing",
                    "current_value": float(country_data.iloc[-1]),
                    "forecast_value": float(forecast.values[-1])
                }

                results["country_details"][country] = country_result

            except Exception as e:
                results["country_details"][country] = {
                    "status": f"Error in forecasting: {str(e)}",
                    "risk_level": "Unknown"
                }

        # Determine overall risk
        if high_risk_count > len(countries) / 2:
            results["overall_risk"] = "High"
        else:
            results["overall_risk"] = "Low"

        return results
    except Exception as e:
        logging.error(f"Error in technology risk evaluation: {e}")
        return {"overall_risk": "Unknown", "error": str(e)}

def run_comprehensive_risk_assessment(countries):
    """
    Runs all risk assessments and returns compiled results.
    """
    if not countries:
        return {
            "error": "No countries specified for risk assessment",
            "climate_risk": {"overall_risk": "Unknown"},
            "carbon_price_risk": {"overall_risk": "Unknown"},
            "technology_risk": {"overall_risk": "Unknown"}
        }

    try:
        results = {
            "climate_risk": evaluate_climate_risk(countries),
            "carbon_price_risk": evaluate_carbon_price_risk(countries),
            "technology_risk": evaluate_technology_risk(countries),
            "timestamp": pd.Timestamp.now().strftime("%Y-%m-%d"),
            "evaluated_countries": countries
        }

        # Save results to JSON
        Path("risk_eval/result").mkdir(parents=True, exist_ok=True)
        with open("risk_eval/result/latest_assessment.json", "w") as f:
            json.dump(results, f, indent=2)

        return results
    except Exception as e:
        logging.error(f"Error in comprehensive risk assessment: {e}")
        return {
            "error": str(e),
            "climate_risk": {"overall_risk": "Unknown"},
            "carbon_price_risk": {"overall_risk": "Unknown"},
            "technology_risk": {"overall_risk": "Unknown"}
        }
