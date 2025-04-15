# analysis/recommendations.py
import os
import logging
import pandas as pd # Ensure pandas is imported
import json
import re
from config.settings import DETAILED_RECOMMENDATION_PROMPT, DEFAULT_OUTPUT_DIR, DEFAULT_OUTPUT_CSV
from services.gemini_service import get_gemini_response
from services.visualization import generate_pathway_visualization
from utils.file_utils import ensure_directory_exists, save_text_to_file
from risk_eval.risk_evaluator import run_comprehensive_risk_assessment
from analysis.integrator import generate_llm_peer_summary, get_industry_peers, generate_llm_executive_summary # Assuming these functions exist and work as expected
from data.savers import save_enhanced_data

def get_recommendations(company_name, enhanced_df, client, model):
    """Generate recommendations for a company using Gemini based on extracted data."""
    logging.info(f"Generating recommendations for: {company_name}")

    # --- Start: Add robust checks ---
    if enhanced_df is None or enhanced_df.empty:
        logging.error("Enhanced DataFrame is empty or None. Cannot proceed.")
        print("Error: Input data is empty.")
        return

    if 'Name' not in enhanced_df.columns:
        logging.error("Column 'Name' not found in the enhanced DataFrame.")
        print("Error: Input data is missing the 'Name' column.")
        return

    # Clean the company name for matching (important for reliable filtering)
    company_name_clean = str(company_name).strip() # Ensure input is string and stripped
    enhanced_df['Name'] = enhanced_df['Name'].astype(str).str.strip() # Ensure Name column is clean string

    # Filter for the specific company
    company_row = enhanced_df[enhanced_df['Name'] == company_name_clean]
    logging.debug(f"Filtered DataFrame shape for '{company_name_clean}': {company_row.shape}")

    # Check if the company was found
    if company_row.empty:
        logging.error(f"Company '{company_name_clean}' not found in the enhanced dataset.")
        print(f"Error: Company '{company_name_clean}' not found in the dataset.")
        # Optional: List available companies if not found
        available_companies = sorted(enhanced_df['Name'].unique())
        preview_count = 10
        print(f"Available companies (first {preview_count}):", ", ".join(available_companies[:preview_count]) + ('...' if len(available_companies) > preview_count else ''))
        return  # Exit if company not found

    # Check for duplicates
    if len(company_row) > 1:
        logging.warning(f"Multiple entries found for company '{company_name_clean}'. Using the first one found at index {company_row.index[0]}.")
        # Select only the first row, ensuring it's still a DataFrame slice
        company_row = company_row.iloc[[0]]

    # --- End: Add robust checks ---

    # Now we are confident company_row contains exactly one row.
    # Prepare the main data extraction logic within a try-except block.
    try:
        # Use .iloc[0] ONCE to get the data as a Pandas Series for easier access
        try:
            company_data = company_row.iloc[0]
        except IndexError:
             # This should be unreachable due to earlier checks, but acts as a failsafe
            logging.error(f"Internal error: Failed to select single row for '{company_name_clean}' after checks.")
            print(f"Error: Could not isolate data for '{company_name_clean}'.")
            return

        # --- Extract Countries and Handle User Input ---
        countries = []
        # Use .get() for safe access on the Series, check for pd.isna()
        countries_text = company_data.get('Countries of Operation')

        if pd.isna(countries_text) or str(countries_text).strip() == "Not Mentioned" or not str(countries_text).strip():
             logging.info(f"No countries mentioned for {company_name_clean}, column missing, or empty.")
             countries_text = None # Ensure it's None if not found, NaN, or 'Not Mentioned'
        else:
            # Split valid country text
            countries = [c.strip() for c in str(countries_text).split(',') if c.strip()] # Ensure no empty strings from splitting

        # If no countries found or identified, prompt the user
        if not countries:
            print(f"\nNo valid countries of operation found for {company_name_clean} in the annual report or data.")
            countries_input = input(f"Please enter a comma-separated list of countries where {company_name_clean} operates: ")
            countries_input_stripped = countries_input.strip()
            if countries_input_stripped:
                countries = [c.strip() for c in countries_input_stripped.split(',') if c.strip()]
                # Update the original enhanced_df DataFrame directly using the index
                original_index = company_row.index[0]
                enhanced_df.loc[original_index, 'Countries of Operation'] = countries_input_stripped # Save the user input
                logging.info(f"Updated 'Countries of Operation' for {company_name_clean} with user input: {countries_input_stripped}")
            else:
                logging.warning(f"User did not provide countries for {company_name_clean}. Proceeding without country-specific risk assessment.")
                countries = [] # Ensure countries list is empty if user provided nothing


        # --- Run Risk Assessment ---
        risk_assessment = ""
        risk_results = {} # Initialize as dict
        climate_risk = "Unknown"
        carbon_risk = "Unknown"
        tech_risk = "Unknown"

        if countries:
            print(f"Running risk assessment for {company_name_clean} in: {', '.join(countries)}")
            risk_results = run_comprehensive_risk_assessment(countries) # Assuming this returns a dict

            # Safely extract overall risk scores
            climate_risk = risk_results.get('climate_risk', {}).get('overall_risk', 'Unknown')
            carbon_risk = risk_results.get('carbon_price_risk', {}).get('overall_risk', 'Unknown')
            tech_risk = risk_results.get('technology_risk', {}).get('overall_risk', 'Unknown')

            print(f"Risk Assessment Results:")
            print(f"- Climate Risk: {climate_risk}")
            print(f"- Carbon Price Risk: {carbon_risk}")
            print(f"- Technology Risk: {tech_risk}")

            # Format risk assessment for prompt (handle potential missing keys gracefully)
            risk_assessment = f"""
RISK ASSESSMENT RESULTS:
- Climate Risk: {climate_risk}
- Carbon Price Risk: {carbon_risk}
- Technology Risk: {tech_risk}

Country-Specific Climate Risks:
"""
            country_risks_data = risk_results.get('climate_risk', {}).get('country_risks', {})
            if country_risks_data:
                for country, data in country_risks_data.items():
                    risk_level = data.get('risk_level', 'Unknown')
                    forecast_temp = data.get('forecast_temp_rise')
                    risk_assessment += f"- {country}: {risk_level}"
                    if forecast_temp is not None:
                        risk_assessment += f" (Forecasted temp rise: {forecast_temp}°C)"
                    risk_assessment += "\n"
            else:
                 risk_assessment += "No detailed country climate risk data available.\n"
        else:
            risk_assessment = "RISK ASSESSMENT: No country data available for risk assessment."
            logging.info("Skipping risk assessment as no countries were provided or found.")

        # --- Extract Actions and Justifications ---
        action_cols = ["Renewables", "Energy Efficiency", "Electrification", "Bioenergy",
                       "CCUS", "Hydrogen Fuel", "Behavioral Changes"]
        identified_actions = []
        actions_summary = "Identified Actions from Annual Report:\n"
        action_found = False

        for action in action_cols:
            # Access Series directly using .get(), check if value is explicitly True
            if company_data.get(action) is True: # Check for boolean True explicitly
                action_found = True
                justification = ""
                justification_col = f"{action}_Justification"
                # Use .get() for safe access to justification
                justification_text = company_data.get(justification_col)
                if not pd.isna(justification_text) and str(justification_text).strip():
                    justification = str(justification_text).strip()
                else:
                    justification = "Justification not provided." # Provide a default
                identified_actions.append({"action": action, "justification": justification})
                actions_summary += f"- {action}: {justification}\n"

        if not action_found:
            actions_summary = "No specific energy transition actions identified in the annual report."


        # --- Get Report Data Fields ---
        # Use .get() on the Series with default values
        fields = {
            'executive_summary': company_data.get('Executive Summary'),
            'strategic_priorities': company_data.get('Strategic Priorities (Energy Transition)'),
            'financial_commitments': company_data.get('Financial Commitments (Energy Transition)'),
            'sustainability_info': company_data.get('Sustainability Milestones'),
            'risks_info': company_data.get('Identified Risks (Physical and Transition)')
        }

        # Clean up fields, providing defaults if missing or 'Not Mentioned'
        for key, value in fields.items():
            if pd.isna(value) or str(value).strip() == "Not Mentioned" or not str(value).strip():
                fields[key] = f"No specific {key.replace('_', ' ')} mentioned in the report."
            else:
                fields[key] = str(value).strip() # Ensure it's a clean string


        # --- Get Structured Financial Data ---
        transition_capex = "Not specified"
        # Use .get() on the Series
        capex_perc = company_data.get('Transition_CapEx_Percentage')
        capex_amt = company_data.get('Transition_CapEx_Amount')
        capex_time = company_data.get('Transition_CapEx_Timeline')

        # Check specifically for non-NA numeric/string values before formatting
        if not pd.isna(capex_perc):
             try:
                 # Attempt to format as percentage if numeric, otherwise use as string
                 transition_capex = f"{float(capex_perc):.1f}% of total CapEx"
             except (ValueError, TypeError):
                 transition_capex = f"{str(capex_perc)} of total CapEx" # Use raw value if not float
        elif not pd.isna(capex_amt):
            transition_capex = f"{str(capex_amt)}" # Ensure string representation
            if not pd.isna(capex_time) and str(capex_time).strip():
                transition_capex += f" through {str(capex_time).strip()}"


        # --- Get Project Allocations ---
        project_allocations = company_data.get('Transition_Project_Allocations')
        if pd.isna(project_allocations) or str(project_allocations).strip() == "Not Mentioned" or not str(project_allocations).strip():
            project_allocations = "No specific project allocations mentioned."
        else:
            project_allocations = str(project_allocations).strip()


        # --- Generate LLM Summaries ---
        # Get peer data (uses original df and cleaned company name)
        peers_df_filtered = get_industry_peers(company_name_clean, enhanced_df) # Get only peers
        # Combine company row and peers for the LLM peer summary context
        combined_df_for_peers = pd.concat([company_row, peers_df_filtered])
        peer_summary = generate_llm_peer_summary(company_name_clean, combined_df_for_peers, client, model)

        # Pass the single row Series to executive summary function
        executive_summary_llm = generate_llm_executive_summary(company_data, client, model)


        # --- Create Prompt for Recommendations ---
        try:
            prompt_text = DETAILED_RECOMMENDATION_PROMPT.format(
                company_name=company_name_clean,
                # Use the cleaned fields derived above
                executive_summary=executive_summary_llm,
                peer_summary=peer_summary,
                strategic_priorities=fields['strategic_priorities'],
                financial_commitments=fields['financial_commitments'],
                sustainability_info=fields['sustainability_info'], # Check if this should be the specific target fields now?
                risks_info=fields['risks_info'],
                # Use financial data derived above
                transition_capex=transition_capex,
                project_allocations=project_allocations,
                # Use actions summary derived above
                actions_summary=actions_summary,
                # Use risk assessment text derived above
                risk_assessment=risk_assessment
                # Add any other placeholders defined in the recommendation prompt
            )
        except KeyError as e:
            logger.error(f"KeyError formatting recommendation prompt for {company_name_clean}: {e}")
            # Handle error gracefully, maybe return an error message
            print(f"Error: Could not format recommendation request for {company_name_clean}. Check data availability and prompt.")
            # Optionally save data gathered so far
            save_enhanced_data(enhanced_df, DEFAULT_OUTPUT_CSV)
            return # Exit the function

        logging.info(f"Sending recommendation request to Gemini for {company_name_clean}...")
        logging.debug(f"Recommendation Prompt Snippet:\n{prompt_text[:500]}...") # Log start of prompt
        response_text = get_gemini_response(prompt_text, client, model)

        if not response_text:
            logging.error(f"No response received from Gemini for {company_name_clean} recommendation.")
            print(f"Error: Could not generate recommendations for {company_name_clean}.")
            # Still save data up to this point if countries were added
            save_enhanced_data(enhanced_df, DEFAULT_OUTPUT_CSV)
            return

        logging.info(f"Received recommendation from Gemini for {company_name_clean}.")
        logging.debug(f"Raw Gemini Recommendation Response:\n{response_text[:500]}...")

        # --- Process and Save Recommendations ---
        print("\n" + "="*30 + f" Energy Transition Roadmap for {company_name_clean} " + "="*30)
        # Attempt to format/print JSON nicely if possible, otherwise print raw text
        try:
            parsed_recommendation = json.loads(response_text)
            print(json.dumps(parsed_recommendation, indent=2))
            roadmap_data_for_vis = parsed_recommendation # Use parsed JSON for visualization
        except json.JSONDecodeError:
            logging.warning("Recommendation response was not valid JSON. Printing raw text.")
            print(response_text)
            roadmap_data_for_vis = None # Cannot use for structured visualization

        print("="*80 + "\n")

        # Save the raw recommendation text to a file
        output_dir = os.path.join(DEFAULT_OUTPUT_DIR, "recommendations")
        ensure_directory_exists(output_dir)
        recommendation_file = os.path.join(output_dir, f"{company_name_clean}_roadmap.txt")
        # Sanitize company name for filename if necessary (e.g., replace spaces)
        # safe_company_name = re.sub(r'[^\w\-]+', '_', company_name_clean)
        # recommendation_file = os.path.join(output_dir, f"{safe_company_name}_roadmap.txt")

        content_to_save = f"Energy Transition Roadmap for {company_name_clean}\n{'='*80}\n\n{response_text}"
        save_text_to_file(content_to_save, recommendation_file)
        print(f"Raw recommendation text saved to: {recommendation_file}")


        # --- Generate Visualization if JSON was valid ---
        if roadmap_data_for_vis:
             # Add risk assessment data to JSON for visualization context
            if countries:
                 # Ensure 'risk_assessment' key exists
                 if "risk_assessment" not in roadmap_data_for_vis:
                     roadmap_data_for_vis["risk_assessment"] = {}

                 # Add overall risks and countries evaluated
                 roadmap_data_for_vis["risk_assessment"]["overall_climate_risk"] = climate_risk
                 roadmap_data_for_vis["risk_assessment"]["overall_carbon_price_risk"] = carbon_risk
                 roadmap_data_for_vis["risk_assessment"]["overall_technology_risk"] = tech_risk
                 roadmap_data_for_vis["risk_assessment"]["countries_evaluated"] = countries
                 # Optionally add detailed risk_results if needed by visualization
                 # roadmap_data_for_vis["risk_assessment"]["details"] = risk_results

            json_file_path = os.path.join(output_dir, f"{company_name_clean}_roadmap_structured.json")
            try:
                with open(json_file_path, 'w', encoding='utf-8') as f:
                    json.dump(roadmap_data_for_vis, f, indent=2, ensure_ascii=False)
                logging.info(f"Structured JSON recommendation saved to: {json_file_path}")
                print(f"Structured data saved for visualization to: {json_file_path}")

                # Generate the HTML visualization
                vis_file = generate_pathway_visualization(company_name_clean, roadmap_data_for_vis)
                if vis_file:
                    print(f"Interactive visualization created at: {vis_file}")
                else:
                    print("Warning: Could not create HTML visualization. Check logs for details.")

            except Exception as json_vis_error:
                 logging.error(f"Error saving structured JSON or generating visualization for {company_name_clean}: {json_vis_error}")
                 print("Warning: Error occurred during JSON saving or visualization generation.")
        else:
             logging.warning(f"Skipping structured JSON saving and visualization for {company_name_clean} as the recommendation response was not valid JSON.")
             print("Skipping visualization generation as the recommendation response was not valid JSON.")


    # --- Final Exception Handling for the main block ---
    except Exception as e:
        # Use the original company_name in the error message for user clarity
        logging.error(f"Error processing recommendations for {company_name}: {e}", exc_info=True) # Add traceback
        print(f"\nAn unexpected error occurred while generating recommendations for {company_name}. Check logs.")

    # --- Save Enhanced Data (potentially updated with countries) ---
    # This should happen outside the main try-except block if possible,
    # or within a finally block, to ensure data is saved even if recommendations fail.
    # However, given the current structure, saving here is acceptable.
    save_enhanced_data(enhanced_df, DEFAULT_OUTPUT_CSV)


# --- Helper function to structure response if needed ---
# (Keep the structure_response_as_json function as defined previously,
#  it acts as a fallback if the primary JSON parsing fails)
def structure_response_as_json(text, company_name):
    """Convert text response to structured JSON format if it's not already in JSON format."""
    logging.info("Attempting to structure non-JSON text response into JSON format")
    structured_data = {
        "company": company_name,
        "description": "Fallback structure generated from text response.",
        "timeframes": []
    }
    # Define potential section headers (adjust regex as needed based on observed text patterns)
    timeframe_patterns = {
        "Immediate actions (Now - 2030)": r'(Immediate actions \(Now - 2030\)|Immediate Actions:|Now - 2030:)',
        "Medium-term actions (2030 - 2040)": r'(Medium-term actions \(2030 - 2040\)|Medium-Term Actions:|2030 - 2040:)',
        "Long-term goals (2040 - 2050)": r'(Long-term goals \(2040 - 2050\)|Long-Term Goals:|2040 - 2050:)'
    }
    category_keywords = [
        "Renewables", "Energy Efficiency", "Electrification", "Bioenergy",
        "CCUS", "Carbon Capture", "Hydrogen Fuel", "Behavioral Changes",
        "Policy", "Finance", "Reporting", "Innovation", "Supply Chain" # Add other potential categories
    ]

    # Split text roughly by timeframes first
    text_sections = {}
    sorted_timeframes = sorted(timeframe_patterns.keys(), key=lambda x: text.find(x) if text.find(x) != -1 else float('inf'))

    start_index = 0
    for i, tf_name in enumerate(sorted_timeframes):
        # Find the start of the current timeframe using its patterns
        match = None
        for pattern in timeframe_patterns[tf_name].split('|'): # Try each pattern part
             current_match = re.search(pattern, text[start_index:], re.IGNORECASE | re.DOTALL)
             if current_match:
                 match = current_match
                 break # Use the first pattern that matches

        if match:
            tf_start = start_index + match.start()

            # Find the start of the *next* timeframe to delimit the current one
            next_tf_start = len(text) # Default to end of text
            if i + 1 < len(sorted_timeframes):
                next_tf_name = sorted_timeframes[i+1]
                next_match = None
                for pattern in timeframe_patterns[next_tf_name].split('|'):
                    current_next_match = re.search(pattern, text[tf_start + 1:], re.IGNORECASE | re.DOTALL) # Search after current timeframe starts
                    if current_next_match:
                        next_match = current_next_match
                        break
                if next_match:
                    next_tf_start = tf_start + 1 + next_match.start()


            # Extract the section for the current timeframe
            section_text = text[tf_start:next_tf_start].strip()
            text_sections[tf_name] = section_text
            start_index = next_tf_start # Update for next iteration


    # If sections were identified, process each
    if text_sections:
        for timeframe_name, timeframe_text in text_sections.items():
            timeframe_data = {
                "name": timeframe_name,
                "actions": []
            }

            # Try to find categories within the timeframe text
            # This part is heuristic and might need refinement based on LLM output format
            current_category = None
            current_recommendations = []

            lines = timeframe_text.split('\n')
            for line in lines:
                line = line.strip()
                if not line: continue

                # Check if line looks like a category header
                matched_category = None
                for cat_keyword in category_keywords:
                    # Simple check: starts with keyword followed by colon or is just the keyword
                    if line.lower().startswith(cat_keyword.lower() + ":") or line.lower() == cat_keyword.lower():
                        matched_category = cat_keyword
                        break
                    # Check for bullet point category like "- Renewables:"
                    if re.match(r'^\s*[\-\*]\s*' + re.escape(cat_keyword) + r':?', line, re.IGNORECASE):
                         matched_category = cat_keyword
                         break


                if matched_category:
                    # Save previous category's recommendations if any
                    if current_category and current_recommendations:
                        timeframe_data["actions"].append({
                            "category": current_category,
                            "recommendations": current_recommendations
                        })
                    # Start new category
                    current_category = matched_category
                    current_recommendations = []
                    # Try to capture text following the category header on the same line
                    header_end = line.find(':')
                    if header_end != -1:
                         first_detail = line[header_end+1:].strip()
                         if first_detail:
                              current_recommendations.append({
                                   "title": "Recommendation",
                                   "details": first_detail,
                                   "reference": "[Extracted from text]",
                                   "justification": {}
                              })

                elif current_category:
                    # Assume this line is a recommendation/detail for the current category
                    # Simple parsing: look for bullet points or numbered lists
                    rec_match = re.match(r'^\s*([\d\.\-\*]+)\s*(.*)', line)
                    title = "Recommendation"
                    details = line
                    if rec_match:
                        # title = rec_match.group(1) # Could be the number/bullet
                        details = rec_match.group(2).strip()

                    if details: # Only add if there's actual text
                        current_recommendations.append({
                            "title": title,
                            "details": details,
                            "reference": "[Extracted from text]",
                            "justification": {} # Placeholder
                        })

            # Add the last category found
            if current_category and current_recommendations:
                timeframe_data["actions"].append({
                    "category": current_category,
                    "recommendations": current_recommendations
                })

            # Add the timeframe data if it has actions
            if timeframe_data["actions"]:
                structured_data["timeframes"].append(timeframe_data)

    # If no timeframes could be structured, add raw text
    if not structured_data["timeframes"]:
        logging.warning("Could not extract structured timeframes, saving raw text in JSON")
        structured_data["raw_text"] = text # Add raw text under a specific key

    return structured_data
