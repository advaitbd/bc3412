# analysis/recommendations.py
import os
import logging
import pandas as pd
import json
import re
from config.settings import DETAILED_RECOMMENDATION_PROMPT, DEFAULT_OUTPUT_DIR
from services.gemini_service import get_gemini_response
from services.visualization import generate_pathway_visualization  # Import visualization service
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

        # Get structured financial data
        transition_capex = "Not specified"
        if 'Transition_CapEx_Percentage' in company_row.columns and not pd.isna(company_row['Transition_CapEx_Percentage'].iloc[0]):
            transition_capex = f"{company_row['Transition_CapEx_Percentage'].iloc[0]}% of total CapEx"
        elif 'Transition_CapEx_Amount' in company_row.columns and not pd.isna(company_row['Transition_CapEx_Amount'].iloc[0]):
            transition_capex = f"{company_row['Transition_CapEx_Amount'].iloc[0]}"

            if 'Transition_CapEx_Timeline' in company_row.columns and not pd.isna(company_row['Transition_CapEx_Timeline'].iloc[0]):
                transition_capex += f" through {company_row['Transition_CapEx_Timeline'].iloc[0]}"

        # Get project allocations
        project_allocations = "No specific allocations mentioned"
        if 'Transition_Project_Allocations' in company_row.columns and not pd.isna(company_row['Transition_Project_Allocations'].iloc[0]):
            project_allocations = company_row['Transition_Project_Allocations'].iloc[0]

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
            transition_capex=transition_capex,
            project_allocations=project_allocations,
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

            # Parse and save JSON for visualization
            try:
                # First, try to parse the entire response as JSON
                try:
                    roadmap_data = json.loads(response_text)
                    logging.info("Successfully parsed response as pure JSON")
                except json.JSONDecodeError:
                    # If not pure JSON, try to extract JSON part using regex
                    logging.info("Attempting to extract JSON from mixed text response...")
                    json_match = re.search(r'({[\s\S]*})', response_text)

                    if json_match:
                        try:
                            json_str = json_match.group(1)
                            roadmap_data = json.loads(json_str)
                            logging.info("Successfully extracted JSON from text response")
                        except json.JSONDecodeError:
                            # If still can't parse, try to structure the text as JSON
                            logging.warning("Could not parse JSON from extracted text, attempting to structure response...")
                            roadmap_data = structure_response_as_json(response_text, company_name)
                    else:
                        # If no JSON pattern found, structure the text
                        logging.warning("Could not extract JSON pattern, attempting to structure response...")
                        roadmap_data = structure_response_as_json(response_text, company_name)

                # Save the structured JSON data for visualization
                json_file = os.path.join(output_dir, f"{company_name}_roadmap.json")
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(roadmap_data, f, indent=2)
                logging.info(f"Structured JSON saved to: {json_file}")
                print(f"Structured data saved for visualization to: {json_file}")

                # Generate visualization using the visualization service
                vis_file = generate_pathway_visualization(company_name, roadmap_data)
                if vis_file:
                    print(f"Interactive visualization created at: {vis_file}")
                else:
                    print("Warning: Could not create visualization. Check logs for details.")

            except Exception as e:
                logging.error(f"Error processing JSON for visualization: {e}")
                print(f"Warning: Could not structure data for visualization. See text output instead.")

        except Exception as e:
            logging.error(f"Error getting recommendations for {company_name} from Gemini: {e}")
            print(f"Error: Could not generate recommendations for {company_name}.")

    except Exception as e:
        logging.error(f"Error preparing recommendation data for {company_name}: {e}")
        print(f"Error preparing data for {company_name}. Cannot generate recommendations.")

def structure_response_as_json(text, company_name):
    """Convert text response to structured JSON if it's not already in JSON format."""
    logging.info("Converting text response to structured JSON format")

    # Initialize the structure
    structured_data = {
        "company": company_name,
        "timeframes": []
    }

    # Define the expected timeframes
    timeframes = [
        "Immediate actions (Now - 2030)",
        "Medium-term actions (2030 - 2040)",
        "Long-term goals (2040 - 2050)"
    ]

    # Regular expressions to extract sections
    timeframe_pattern = r'(Immediate actions|Medium-term actions|Long-term goals).*?(?=Immediate actions|Medium-term actions|Long-term goals|\Z)'
    category_pattern = r'([A-Za-z\s&()]+):\s*'

    # Find all timeframe sections
    for timeframe_name in timeframes:
        timeframe_data = {
            "name": timeframe_name,
            "actions": []
        }

        # Extract the timeframe section using regex
        timeframe_match = re.search(fr'{timeframe_name}(.*?)(?={"|".join(timeframes)}|\Z)', text, re.DOTALL)
        if not timeframe_match:
            continue

        timeframe_text = timeframe_match.group(1)

        # Action categories (aligned with our constants)
        categories = [
            "Renewables", "Energy Efficiency", "Electrification", "Bioenergy",
            "CCUS", "Carbon Capture Utilization and Storage", "Hydrogen Fuel", "Behavioral Changes"
        ]

        # Find all category sections within this timeframe
        for category in categories:
            # Adjust for alternative naming of CCUS
            search_category = category
            if category == "CCUS":
                search_category = r"(CCUS|Carbon Capture Utilization and Storage)"

            category_match = re.search(fr'{search_category}:(.*?)(?={"|".join(categories)}|\Z)', timeframe_text, re.DOTALL | re.IGNORECASE)
            if not category_match:
                continue

            category_text = category_match.group(1).strip()

            # Normalize category name
            display_category = category
            if "Carbon Capture" in category:
                display_category = "CCUS"

            category_data = {
                "category": display_category,
                "recommendations": []
            }

            # Extract individual recommendations
            recommendation_pattern = r'(?:(\d+\.\s*|\-\s*))?([^:\n]+):\s*(.*?)(?=\d+\.\s*|\-\s*|$)'
            recommendations = re.finditer(recommendation_pattern, category_text, re.DOTALL)

            for rec in recommendations:
                title = rec.group(2).strip() if rec.group(2) else "Recommendation"
                details = rec.group(3).strip() if rec.group(3) else ""

                # Extract reference if available
                reference = ""
                ref_match = re.search(r'\[([^\]]+)\]', details)
                if ref_match:
                    reference = ref_match.group(0)
                    # Remove reference from details if it's at the end
                    details = details.replace(reference, "").strip()

                recommendation_data = {
                    "title": title,
                    "details": details,
                    "reference": reference
                }

                category_data["recommendations"].append(recommendation_data)

            if category_data["recommendations"]:
                timeframe_data["actions"].append(category_data)

        if timeframe_data["actions"]:
            structured_data["timeframes"].append(timeframe_data)

    # If no structured data could be extracted, create a basic structure with the raw text
    if not structured_data["timeframes"]:
        structured_data["text"] = text
        logging.warning("Could not extract structured data, saving raw text in JSON")

    return structured_data
