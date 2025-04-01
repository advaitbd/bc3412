# analysis/recommendations.py
import os
import logging
import pandas as pd
from config.settings import DETAILED_RECOMMENDATION_PROMPT, DEFAULT_OUTPUT_DIR
from services.gemini_service import get_gemini_response
from utils.file_utils import ensure_directory_exists, save_text_to_file

def get_recommendations(company_name, enhanced_df, gemini_model):
    """Generate recommendations for a company using Gemini based on extracted data."""
    logging.info(f"Generating recommendations for: {company_name}")

    try:
        company_row = enhanced_df[enhanced_df['Name'] == company_name]
        if company_row.empty:
            logging.error(f"Company '{company_name}' not found in the enhanced dataset.")
            print(f"Error: Company '{company_name}' not found.")
            return  # Exit if company not found

        # Extract identified actions and their justifications
        action_cols = ["Renewables", "Energy Efficiency", "Electrification", "Bioenergy",
                      "CCUS", "Hydrogen Fuel", "Behavioral Changes"]

        identified_actions = []
        for action in action_cols:
            if action in company_row.columns and company_row[action].iloc[0] == True:
                # Get justification if available
                justification = ""
                justification_col = f"{action}_Justification"
                if justification_col in company_row.columns and not pd.isna(company_row[justification_col].iloc[0]):
                    justification = company_row[justification_col].iloc[0]
                identified_actions.append({"action": action, "justification": justification})

        # Get report data fields
        fields = {
            'executive_summary': company_row['Executive Summary'].iloc[0] if 'Executive Summary' in company_row.columns else "Executive summary not available.",
            'strategic_priorities': company_row['Strategic Priorities (Energy Transition)'].iloc[0] if 'Strategic Priorities (Energy Transition)' in company_row.columns else "No specific strategic priorities mentioned.",
            'financial_commitments': company_row['Financial Commitments (Energy Transition)'].iloc[0] if 'Financial Commitments (Energy Transition)' in company_row.columns else "No specific financial commitments mentioned.",
            'sustainability_info': company_row['Sustainability Milestones'].iloc[0] if 'Sustainability Milestones' in company_row.columns else "No specific sustainability milestones mentioned.",
            'risks_info': company_row['Identified Risks (Physical and Transition)'].iloc[0] if 'Identified Risks (Physical and Transition)' in company_row.columns else "No specific risks mentioned."
        }

        # Clean up fields
        for key, value in fields.items():
            if pd.isna(value) or value == "Not Mentioned":
                fields[key] = f"No specific {key.replace('_', ' ')} mentioned."

        # Parse and format identified actions for prompt
        actions_summary = ""
        if identified_actions:
            actions_summary = "Identified Actions from Annual Report:\n"
            for item in identified_actions:
                actions_summary += f"- {item['action']}: {item['justification']}\n"
        else:
            actions_summary = "No specific energy transition actions identified in the annual report."

        # Create the prompt with the company's data
        prompt_text = DETAILED_RECOMMENDATION_PROMPT.format(
            company_name=company_name,
            executive_summary=fields['executive_summary'],
            strategic_priorities=fields['strategic_priorities'],
            financial_commitments=fields['financial_commitments'],
            sustainability_info=fields['sustainability_info'],
            risks_info=fields['risks_info'],
            actions_summary=actions_summary
        )

        # Get the recommendation from Gemini
        try:
            logging.info(f"Sending recommendation request to Gemini for {company_name}...")
            response_text = get_gemini_response(prompt_text, gemini_model)

            if not response_text:
                logging.error(f"No response received from Gemini for {company_name} recommendation.")
                print(f"Error: Could not generate recommendations for {company_name}.")
                return

            logging.info(f"Received recommendation from Gemini for {company_name}.")

            # Print the recommendation
            print("\n" + "="*30 + f" Energy Transition Roadmap for {company_name} " + "="*30)
            print(response_text)
            print("="*80 + "\n")

            # Save the recommendation to a text file
            output_dir = os.path.join(DEFAULT_OUTPUT_DIR, "recommendations")
            ensure_directory_exists(output_dir)

            recommendation_file = os.path.join(output_dir, f"{company_name}_roadmap.txt")
            content = f"Energy Transition Roadmap for {company_name}\n{'='*80}\n\n{response_text}"
            save_text_to_file(content, recommendation_file)
            print(f"Recommendation saved to: {recommendation_file}")

        except Exception as e:
            logging.error(f"Error getting recommendations for {company_name} from Gemini: {e}")
            print(f"Error: Could not generate recommendations for {company_name}.")

    except Exception as e:
        logging.error(f"Error preparing recommendation data for {company_name}: {e}")
        print(f"Error preparing data for {company_name}. Cannot generate recommendations.")
