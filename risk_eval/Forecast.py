import streamlit as st
import pandas as pd
from statsmodels.tsa.api import Holt #(Trend + Level - Seasonality)

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
# TODO export into a csv (climate/policy/low-carbon products)
    