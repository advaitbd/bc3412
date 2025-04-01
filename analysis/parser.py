# analysis/parser.py
import re
import numpy as np
import logging
from config.settings import ACTION_CATEGORIES

def parse_gemini_output(response_text):
    """Parse the structured output from Gemini into a dictionary."""
    data = {
        "Executive Summary": np.nan,
        "Strategic Priorities (Energy Transition)": np.nan,
        "Financial Commitments (Energy Transition)": np.nan,
        "Identified Risks (Physical and Transition)": np.nan,
        "Sustainability Milestones": np.nan
    }

    # Use regex to find sections robustly, handling potential variations
    patterns = {
        "Executive Summary": r"^\s*1\.\s*Executive Summary:\s*(.*?)(?=^\s*2\.\s*Strategic Priorities|\Z)",
        "Strategic Priorities (Energy Transition)": r"^\s*2\.\s*Strategic Priorities \(Energy Transition\):\s*(.*?)(?=^\s*3\.\s*Financial Commitments|\Z)",
        "Financial Commitments (Energy Transition)": r"^\s*3\.\s*Financial Commitments \(Energy Transition\):\s*(.*?)(?=^\s*4\.\s*Identified Risks|\Z)",
        "Identified Risks (Physical and Transition)": r"^\s*4\.\s*Identified Risks \(Physical and Transition\):\s*(.*?)(?=^\s*5\.\s*Sustainability Milestones|\Z)",
        "Sustainability Milestones": r"^\s*5\.\s*Sustainability Milestones:\s*(.*?)(?=^\s*6\.\s*Action Classifications|\Z)"
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, response_text, re.DOTALL | re.IGNORECASE | re.MULTILINE)
        if match:
            extracted_value = match.group(1).strip()
            # Keep the text even if it says "Not Mentioned" or is empty
            data[key] = extracted_value if extracted_value else "No information found"  # Store text or placeholder
        else:
            # Section pattern not found at all
            data[key] = "Section not found in response"  # Indicate pattern failure
            logging.warning(f"Could not parse section '{key}' using pattern: {pattern}")

    # Parse action classifications
    action_section_match = re.search(r"^\s*6\.\s*Action Classifications:\s*(.*?)(?=\Z)",
                                    response_text, re.DOTALL | re.IGNORECASE | re.MULTILINE)

    if action_section_match:
        action_text = action_section_match.group(1).strip()

        # Process each action category
        for action in ACTION_CATEGORIES:
            # Pattern to find the action classification and justification
            action_pattern = rf"[a-g]\)\s*{action}:\s*\[(TRUE|FALSE)\]\s*(?:\[(.*?)\])?"
            action_match = re.search(action_pattern, action_text, re.IGNORECASE)

            if action_match:
                classification = action_match.group(1).upper() == "TRUE"
                justification = action_match.group(2).strip() if action_match.group(2) and len(action_match.groups()) > 1 else ""

                # Add to data dictionary
                data[action] = classification
                # Store justification with a consistent naming pattern
                data[f"{action}_Justification"] = justification if classification else "Action not identified"
            else:
                # Action not found in response
                data[action] = False
                data[f"{action}_Justification"] = "Classification not found in response"
    else:
        # Action Classifications section not found
        logging.warning("Action Classifications section not found in response")
        for action in ACTION_CATEGORIES:
            data[action] = False
            data[f"{action}_Justification"] = "Action Classifications section not found"

    return data
