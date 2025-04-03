# services/visualization.py
import os
import json
import logging
from pathlib import Path
from config.settings import DEFAULT_OUTPUT_DIR

def generate_pathway_visualization(company_name, json_data):
    """
    Generate an interactive HTML visualization of the energy transition pathway
    using structured JSON data directly from the LLM.
    """
    try:
        # Parse JSON if it's a string
        if isinstance(json_data, str):
            roadmap_data = json.loads(json_data)
        else:
            roadmap_data = json_data

        # Create visualization directory
        vis_dir = os.path.join(DEFAULT_OUTPUT_DIR, "visualizations")
        Path(vis_dir).mkdir(parents=True, exist_ok=True)

        # Get risk data if available
        risk_data = roadmap_data.get("risk_assessment", {})
        climate_risk = risk_data.get("climate_risk", "Unknown")
        carbon_risk = risk_data.get("carbon_price_risk", "Unknown")
        tech_risk = risk_data.get("technology_risk", "Unknown")
        countries = risk_data.get("countries", [])

        # Get External Factors data
        external_factors = roadmap_data.get("external_factors", {})

        # Get Internal Factors data
        internal_factors = roadmap_data.get("internal_factors", {})

        # Get Factor Rankings
        factor_rankings = roadmap_data.get("factor_rankings", [])

        # Generate External Factors HTML
        external_factors_html = ""
        if external_factors:
            external_factors_html = """
            <div class="factors-section">
                <h2>External Factors</h2>
            """

            # Climate Risk
            climate_data = external_factors.get("climate_risk", {})
            if climate_data:
                climate_score = climate_data.get("score", "Unknown")
                external_factors_html += f"""
                <div class="factor-card">
                    <h3>Climate Risk</h3>
                    <div class="risk-indicator risk-{climate_score.lower()}">{climate_score}</div>
                    <div class="factor-details">
                        <p><strong>Interpretation:</strong> {climate_data.get("interpretation", "Not provided")}</p>
                        <p><strong>Impact:</strong> {climate_data.get("impact", "Not provided")}</p>
                    </div>
                </div>
                """

            # Carbon Price Risk
            carbon_data = external_factors.get("carbon_price_risk", {})
            if carbon_data:
                carbon_score = carbon_data.get("score", "Unknown")
                external_factors_html += f"""
                <div class="factor-card">
                    <h3>Carbon Price Risk</h3>
                    <div class="risk-indicator risk-{carbon_score.lower()}">{carbon_score}</div>
                    <div class="factor-details">
                        <p><strong>Interpretation:</strong> {carbon_data.get("interpretation", "Not provided")}</p>
                        <p><strong>Impact:</strong> {carbon_data.get("impact", "Not provided")}</p>
                    </div>
                </div>
                """

            # Technology Risk
            tech_data = external_factors.get("technology_risk", {})
            if tech_data:
                tech_score = tech_data.get("score", "Unknown")
                external_factors_html += f"""
                <div class="factor-card">
                    <h3>Technology Risk</h3>
                    <div class="risk-indicator risk-{tech_score.lower()}">{tech_score}</div>
                    <div class="factor-details">
                        <p><strong>Interpretation:</strong> {tech_data.get("interpretation", "Not provided")}</p>
                        <p><strong>Impact:</strong> {tech_data.get("impact", "Not provided")}</p>
                    </div>
                </div>
                """

            # Policy Environment
            policy_env = external_factors.get("policy_environment", "No policy analysis provided")
            external_factors_html += f"""
            <div class="factor-card">
                <h3>Policy Environment</h3>
                <div class="factor-details">
                    <p>{policy_env}</p>
                </div>
            </div>
            """

            external_factors_html += "</div>"

        # Generate Internal Factors HTML
        internal_factors_html = ""
        if internal_factors:
            internal_factors_html = """
            <div class="factors-section">
                <h2>Internal Factors</h2>
            """

            # Operational Feasibility
            op_data = internal_factors.get("operational_feasibility", {})
            if op_data:
                op_assessment = op_data.get("assessment", "Unknown")
                internal_factors_html += f"""
                <div class="factor-card">
                    <h3>Operational Feasibility</h3>
                    <div class="assessment-indicator assessment-{op_assessment.lower()}">{op_assessment}</div>
                    <div class="factor-details">
                        <p>{op_data.get("details", "No details provided")}</p>
                    </div>
                </div>
                """

            # Financial Viability
            fin_data = internal_factors.get("financial_viability", {})
            if fin_data:
                fin_assessment = fin_data.get("assessment", "Unknown")
                internal_factors_html += f"""
                <div class="factor-card">
                    <h3>Financial Viability</h3>
                    <div class="assessment-indicator assessment-{fin_assessment.lower()}">{fin_assessment}</div>
                    <div class="factor-details">
                        <p>{fin_data.get("details", "No details provided")}</p>
                    </div>
                </div>
                """

            # Existing Capabilities
            cap_data = internal_factors.get("existing_capabilities", {})
            if cap_data:
                cap_assessment = cap_data.get("assessment", "Unknown")
                internal_factors_html += f"""
                <div class="factor-card">
                    <h3>Existing Capabilities</h3>
                    <div class="assessment-indicator assessment-{cap_assessment.lower()}">{cap_assessment}</div>
                    <div class="factor-details">
                        <p>{cap_data.get("details", "No details provided")}</p>
                    </div>
                </div>
                """

            # Organizational Readiness
            org_data = internal_factors.get("organizational_readiness", {})
            if org_data:
                org_assessment = org_data.get("assessment", "Unknown")
                internal_factors_html += f"""
                <div class="factor-card">
                    <h3>Organizational Readiness</h3>
                    <div class="assessment-indicator assessment-{org_assessment.lower()}">{org_assessment}</div>
                    <div class="factor-details">
                        <p>{org_data.get("details", "No details provided")}</p>
                    </div>
                </div>
                """

            internal_factors_html += "</div>"

        # Generate Factor Rankings HTML
        factor_rankings_html = ""
        if factor_rankings:
            factor_rankings_html = """
            <div class="factors-section">
                <h2>Factor Rankings</h2>
                <table class="rankings-table">
                    <thead>
                        <tr>
                            <th>Rank</th>
                            <th>Factor</th>
                            <th>Importance</th>
                            <th>Justification</th>
                        </tr>
                    </thead>
                    <tbody>
            """

            for factor in factor_rankings:
                rank = factor.get("rank", "")
                factor_name = factor.get("factor", "Unknown")
                importance = factor.get("importance", "Unknown")
                justification = factor.get("justification", "No justification provided")

                factor_rankings_html += f"""
                <tr>
                    <td>{rank}</td>
                    <td>{factor_name}</td>
                    <td class="importance-{importance.lower()}">{importance}</td>
                    <td>{justification}</td>
                </tr>
                """

            factor_rankings_html += """
                    </tbody>
                </table>
            </div>
            """

        # Create HTML file with visualization
        html_file = os.path.join(vis_dir, f"{company_name}_pathway.html")

        # Generate timeframes and their actions for the HTML structure
        timeframes_html = ""
        for timeframe in roadmap_data.get("timeframes", []):
            timeframe_name = timeframe.get("name", "Unknown Timeframe")
            timeframe_id = timeframe_name.lower().replace(" ", "-").replace("(", "").replace(")", "")

            actions_html = ""
            for action in timeframe.get("actions", []):
                action_category = action.get("category", "Unknown Action")
                action_id = f"{timeframe_id}-{action_category.lower().replace(' ', '-')}"

                recommendations_html = ""
                for rec in action.get("recommendations", []):
                    rec_title = rec.get("title", "Unknown Recommendation")
                    rec_details = rec.get("details", "")
                    rec_reference = rec.get("reference", "No reference provided")

                    # Process justifications if available
                    justification_html = ""
                    if rec.get("justification"):
                        just = rec.get("justification", {})
                        justification_items = []

                        if just.get("peer_alignment"):
                            justification_items.append(f"<div class='justification-item'><strong>Peer Alignment:</strong> {just.get('peer_alignment')}</div>")
                        if just.get("financial_viability"):
                            justification_items.append(f"<div class='justification-item'><strong>Financial Viability:</strong> {just.get('financial_viability')}</div>")
                        if just.get("operational_feasibility"):
                            justification_items.append(f"<div class='justification-item'><strong>Operational Feasibility:</strong> {just.get('operational_feasibility')}</div>")
                        if just.get("target_alignment"):
                            justification_items.append(f"<div class='justification-item'><strong>Target Alignment:</strong> {just.get('target_alignment')}</div>")
                        if just.get("risk_mitigation"):
                            justification_items.append(f"<div class='justification-item'><strong>Risk Mitigation:</strong> {just.get('risk_mitigation')}</div>")

                        if justification_items:
                            justification_html = f"""
                            <div class="justification">
                                <h4>Recommendation Justification</h4>
                                {"".join(justification_items)}
                            </div>
                            """

                    recommendations_html += f"""
                    <div class="recommendation">
                        <h4>{rec_title}</h4>
                        <div class="recommendation-content">
                            <p>{rec_details}</p>
                            <div class="reference">
                                <strong>Reference:</strong> {rec_reference}
                            </div>
                            {justification_html}
                        </div>
                    </div>
                    """

                actions_html += f"""
                <div class="action">
                    <h3 class="action-header" onclick="toggleActionContent('{action_id}')">{action_category}</h3>
                    <div class="action-content" id="{action_id}">
                        {recommendations_html}
                    </div>
                </div>
                """

            timeframes_html += f"""
            <div class="timeframe">
                <h2 class="timeframe-header" onclick="toggleTimeframeContent('{timeframe_id}')">{timeframe_name}</h2>
                <div class="timeframe-content" id="{timeframe_id}">
                    {actions_html}
                </div>
            </div>
            """

        # Navigation items for sidebar
        nav_items = []
        for tf in roadmap_data.get("timeframes", []):
            tf_name = tf.get("name", "Unknown")
            tf_id = tf_name.lower().replace(" ", "-").replace("(", "").replace(")", "")
            nav_items.append(f'<li><a href="#" onclick="toggleTimeframeContent(\'{tf_id}\'); return false;">{tf_name}</a></li>')
        nav_html = "".join(nav_items)

        # Generate HTML content
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Energy Transition Pathway for {company_name}</title>
            <style>
                body, html {{
                    margin: 0;
                    padding: 0;
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    background-color: #f8f9fa;
                }}
                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                header {{
                    background-color: #3c4b64;
                    color: white;
                    padding: 30px;
                    border-radius: 5px;
                    margin-bottom: 30px;
                }}
                h1 {{
                    margin: 0;
                    font-size: 28px;
                }}
                .factors-section {{
                    background-color: white;
                    border-radius: 5px;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                    padding: 20px;
                    margin-bottom: 20px;
                }}
                .factor-card {{
                    border: 1px solid #e0e0e0;
                    border-radius: 5px;
                    padding: 15px;
                    margin-bottom: 15px;
                    background-color: #ffffff;
                }}
                .factor-card h3 {{
                    margin-top: 0;
                    border-bottom: 1px solid #eee;
                    padding-bottom: 10px;
                }}
                .risk-indicator, .assessment-indicator {{
                    display: inline-block;
                    padding: 6px 12px;
                    border-radius: 4px;
                    font-weight: bold;
                    margin-bottom: 10px;
                }}
                .risk-high, .assessment-low {{
                    background-color: #f8d7da;
                    color: #721c24;
                    border: 1px solid #f5c6cb;
                }}
                .risk-medium, .assessment-medium {{
                    background-color: #fff3cd;
                    color: #856404;
                    border: 1px solid #ffeeba;
                }}
                .risk-low, .assessment-high, .assessment-strong {{
                    background-color: #d4edda;
                    color: #155724;
                    border: 1px solid #c3e6cb;
                }}
                .assessment-moderate {{
                    background-color: #fff3cd;
                    color: #856404;
                    border: 1px solid #ffeeba;
                }}
                .assessment-weak {{
                    background-color: #f8d7da;
                    color: #721c24;
                    border: 1px solid #f5c6cb;
                }}
                .risk-unknown, .assessment-unknown {{
                    background-color: #e2e3e5;
                    color: #383d41;
                    border: 1px solid #d6d8db;
                }}
                .rankings-table {{
                    width: 100%;
                    border-collapse: collapse;
                }}
                .rankings-table th, .rankings-table td {{
                    padding: 10px;
                    border: 1px solid #ddd;
                    text-align: left;
                }}
                .rankings-table th {{
                    background-color: #f2f2f2;
                }}
                .importance-critical {{
                    color: #721c24;
                    font-weight: bold;
                }}
                .importance-high {{
                    color: #e74c3c;
                    font-weight: bold;
                }}
                .importance-medium {{
                    color: #f39c12;
                }}
                .importance-low {{
                    color: #27ae60;
                }}
                .pathway-container {{
                    display: flex;
                    gap: 20px;
                    align-items: flex-start;
                }}
                .pathway {{
                    flex: 1;
                    background-color: white;
                    border-radius: 5px;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                    padding: 20px;
                }}
                .timeframe {{
                    margin-bottom: 20px;
                    border: 1px solid #e0e0e0;
                    border-radius: 5px;
                    overflow: hidden;
                }}
                .timeframe-header {{
                    background-color: #FDF2E9;
                    color: #e67e22;
                    padding: 15px;
                    margin: 0;
                    cursor: pointer;
                    border-bottom: 1px solid #e0e0e0;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }}
                .timeframe-header::after {{
                    content: "▼";
                    font-size: 12px;
                }}
                .timeframe-header.collapsed::after {{
                    content: "▶";
                }}
                .timeframe-content {{
                    padding: 0 15px;
                }}
                .action {{
                    margin: 15px 0;
                    border: 1px solid #e0e0e0;
                    border-radius: 5px;
                    overflow: hidden;
                }}
                .action-header {{
                    background-color: #E9F7EF;
                    color: #27ae60;
                    padding: 10px 15px;
                    margin: 0;
                    cursor: pointer;
                    border-bottom: 1px solid #e0e0e0;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }}
                .action-header::after {{
                    content: "▼";
                    font-size: 12px;
                }}
                .action-header.collapsed::after {{
                    content: "▶";
                }}
                .action-content {{
                    padding: 0 15px;
                }}
                .recommendation {{
                    margin: 15px 0;
                    border: 1px solid #e0e0e0;
                    border-radius: 5px;
                    overflow: hidden;
                }}
                .recommendation h4 {{
                    background-color: #F4ECF7;
                    color: #8e44ad;
                    padding: 10px 15px;
                    margin: 0;
                    cursor: pointer;
                    border-bottom: 1px solid #e0e0e0;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }}
                .recommendation h4::after {{
                    content: "▼";
                    font-size: 12px;
                }}
                .recommendation h4.collapsed::after {{
                    content: "▶";
                }}
                .recommendation-content {{
                    padding: 15px;
                }}
                .reference {{
                    font-size: 0.9em;
                    font-style: italic;
                    color: #777;
                    margin-top: 10px;
                    background-color: #f9f9f9;
                    padding: 8px;
                    border-left: 3px solid #4b77be;
                }}
                .justification {{
                    margin-top: 15px;
                    background-color: #f0f7ff;
                    padding: 10px;
                    border-radius: 5px;
                }}
                .justification h4 {{
                    margin-top: 0;
                    color: #3c4b64;
                    background-color: transparent;
                    border: none;
                    padding: 0;
                    display: block;
                }}
                .justification h4::after {{
                    content: none;
                }}
                .justification-item {{
                    margin: 5px 0;
                    padding: 5px;
                    border-left: 2px solid #6c88a5;
                    background-color: #ffffff;
                }}
                .risk-assessment {{
                    margin-top: 20px;
                    padding: 15px;
                    background-color: #f8f9fa;
                    border-radius: 5px;
                    border: 1px solid #dee2e6;
                }}
                .risk-item {{
                    display: inline-block;
                    margin: 5px;
                    padding: 8px 12px;
                    border-radius: 4px;
                    font-weight: bold;
                }}
                .country-list {{
                    margin-top: 10px;
                    font-style: italic;
                    color: #495057;
                    background-color: #e9ecef;
                    padding: 8px;
                    border-radius: 4px;
                    border: 1px solid #ced4da;
                }}
                .controls {{
                    margin: 15px 0;
                }}
                .controls button {{
                    background-color: #4b77be;
                    color: white;
                    border: none;
                    padding: 8px 15px;
                    margin-right: 10px;
                    border-radius: 4px;
                    cursor: pointer;
                }}
                .controls button:hover {{
                    background-color: #3c639e;
                }}
                .sidebar {{
                    width: 300px;
                    background-color: white;
                    border-radius: 5px;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                    padding: 20px;
                    position: sticky;
                    top: 20px;
                }}
                @media (max-width: 768px) {{
                    .pathway-container {{
                        flex-direction: column;
                    }}
                    .sidebar {{
                        width: auto;
                        position: static;
                        margin-bottom: 20px;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <header>
                    <h1>Energy Transition Pathway for {company_name}</h1>
                    <p>Interactive visualization of the recommended transition roadmap</p>

                    <div class="risk-assessment">
                        <h3>Risk Assessment</h3>
                        <div class="risk-item risk-{climate_risk.lower()}">Climate Risk: {climate_risk}</div>
                        <div class="risk-item risk-{carbon_risk.lower()}">Carbon Price Risk: {carbon_risk}</div>
                        <div class="risk-item risk-{tech_risk.lower()}">Technology Risk: {tech_risk}</div>
                        <div class="country-list">
                            <strong>Countries assessed:</strong> {', '.join(countries) if countries else 'None specified'}
                        </div>
                    </div>

                    <div class="controls">
                        <button onclick="expandAll()">Expand All</button>
                        <button onclick="collapseAll()">Collapse All</button>
                    </div>
                </header>

                {external_factors_html}
                {internal_factors_html}
                {factor_rankings_html}

                <div class="pathway-container">
                    <div class="pathway">
                        <h2>Energy Transition Roadmap</h2>
                        {timeframes_html}
                    </div>

                    <div class="sidebar">
                        <h2>Navigation</h2>
                        <p>Click on any section header to expand or collapse it:</p>
                        <ul>
                            {nav_html}
                        </ul>

                        <div class="risk-summary">
                            <h3>Risk Summary</h3>
                            <p><strong>Climate:</strong> <span class="risk-{climate_risk.lower()}">{climate_risk}</span></p>
                            <p><strong>Carbon Price:</strong> <span class="risk-{carbon_risk.lower()}">{carbon_risk}</span></p>
                            <p><strong>Technology:</strong> <span class="risk-{tech_risk.lower()}">{tech_risk}</span></p>
                        </div>
                    </div>
                </div>
            </div>

            <script>
                // Make all content visible initially
                document.addEventListener('DOMContentLoaded', function() {{
                    const allTimeframes = document.querySelectorAll('.timeframe-content');
                    const allActions = document.querySelectorAll('.action-content');

                    // Start with everything collapsed
                    collapseAll();

                    // But open the first timeframe
                    if (allTimeframes.length > 0) {{
                        const firstTimeframe = allTimeframes[0];
                        firstTimeframe.style.display = 'block';
                        firstTimeframe.previousElementSibling.classList.remove('collapsed');
                    }}
                }});

                function toggleTimeframeContent(timeframeId) {{
                    const content = document.getElementById(timeframeId);
                    const header = content.previousElementSibling;

                    if (content.style.display === 'none' || content.style.display === '') {{
                        content.style.display = 'block';
                        header.classList.remove('collapsed');
                    }} else {{
                        content.style.display = 'none';
                        header.classList.add('collapsed');
                    }}
                }}

                function toggleActionContent(actionId) {{
                    const content = document.getElementById(actionId);
                    const header = content.previousElementSibling;

                    if (content.style.display === 'none' || content.style.display === '') {{
                        content.style.display = 'block';
                        header.classList.remove('collapsed');
                    }} else {{
                        content.style.display = 'none';
                        header.classList.add('collapsed');
                    }}
                }}

                function toggleRecommendationContent(element) {{
                    const content = element.nextElementSibling;

                    if (content.style.display === 'none' || content.style.display === '') {{
                        content.style.display = 'block';
                        element.classList.remove('collapsed');
                    }} else {{
                        content.style.display = 'none';
                        element.classList.add('collapsed');
                    }}
                }}

                function expandAll() {{
                    const allTimeframes = document.querySelectorAll('.timeframe-content');
                    const allActions = document.querySelectorAll('.action-content');
                    const allHeaders = document.querySelectorAll('.timeframe-header, .action-header');

                    allTimeframes.forEach(function(tf) {{ tf.style.display = 'block'; }});
                    allActions.forEach(function(action) {{ action.style.display = 'block'; }});
                    allHeaders.forEach(function(header) {{ header.classList.remove('collapsed'); }});
                }}

                function collapseAll() {{
                    const allTimeframes = document.querySelectorAll('.timeframe-content');
                    const allActions = document.querySelectorAll('.action-content');
                    const allHeaders = document.querySelectorAll('.timeframe-header, .action-header');

                    allTimeframes.forEach(function(tf) {{ tf.style.display = 'none'; }});
                    allActions.forEach(function(action) {{ action.style.display = 'none'; }});
                    allHeaders.forEach(function(header) {{ header.classList.add('collapsed'); }});
                }}

                // Add click listeners to recommendation headers
                document.addEventListener('DOMContentLoaded', function() {{
                    const recommendationHeaders = document.querySelectorAll('.recommendation h4');
                    recommendationHeaders.forEach(function(header) {{
                        header.addEventListener('click', function() {{
                            toggleRecommendationContent(this);
                        }});
                        // Start collapsed
                        header.classList.add('collapsed');
                        header.nextElementSibling.style.display = 'none';
                    }});
                }});
            </script>
        </body>
        </html>
        """

        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

        logging.info(f"Enhanced HTML pathway visualization saved to: {html_file}")

        return html_file

    except Exception as e:
        logging.error(f"Error generating pathway visualization: {e}")
        return None
