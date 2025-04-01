# bc3412/services/visualization.py
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

        # Process data into vis.js format
        nodes = []
        edges = []
        node_id = 1

        # Add company as the root node
        company_node = {
            "id": node_id,
            "label": company_name,
            "type": "company",
            "details": "Company Energy Transition Roadmap"
        }
        nodes.append(company_node)
        company_node_id = node_id
        node_id += 1

        # Process each timeframe
        for timeframe in roadmap_data.get("timeframes", []):
            # Add timeframe node
            timeframe_node = {
                "id": node_id,
                "label": timeframe.get("name", "Unknown Timeframe"),
                "type": "timeframe",
                "details": ""
            }
            nodes.append(timeframe_node)

            # Add edge from company to timeframe
            edges.append({
                "from": company_node_id,
                "to": node_id,
                "label": ""
            })

            timeframe_node_id = node_id
            node_id += 1

            # Process actions for this timeframe
            for action in timeframe.get("actions", []):
                # Add action node
                action_node = {
                    "id": node_id,
                    "label": action.get("category", "Unknown Action"),
                    "type": "action",
                    "details": ""
                }
                nodes.append(action_node)

                # Add edge from timeframe to action
                edges.append({
                    "from": timeframe_node_id,
                    "to": node_id,
                    "label": ""
                })

                action_node_id = node_id
                node_id += 1

                # Process recommendations for this action
                for rec in action.get("recommendations", []):
                    # Add recommendation node
                    rec_node = {
                        "id": node_id,
                        "label": rec.get("title", "Unknown Recommendation"),
                        "type": "recommendation",
                        "details": rec.get("details", ""),
                        "reference": rec.get("reference", "No reference provided")
                    }
                    nodes.append(rec_node)

                    # Add edge from action to recommendation
                    edges.append({
                        "from": action_node_id,
                        "to": node_id,
                        "label": ""
                    })

                    node_id += 1

        # Create HTML file with vis.js visualization
        html_file = os.path.join(vis_dir, f"{company_name}_pathway.html")

        # Generate HTML with embedded vis.js
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Energy Transition Pathway for {company_name}</title>
            <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
            <style type="text/css">
                body, html {{
                    margin: 0;
                    padding: 0;
                    font-family: Arial, sans-serif;
                    height: 100%;
                    width: 100%;
                }}
                .container {{
                    width: 100%;
                    height: 100%;
                    display: flex;
                    flex-direction: column;
                }}
                #header {{
                    padding: 20px;
                    background-color: #3c4b64;
                    color: white;
                }}
                .content-area {{
                    display: flex;
                    flex: 1;
                    overflow: hidden;
                }}
                #pathway-visualization {{
                    flex: 2;
                    height: 100%;
                }}
                #details-panel {{
                    flex: 1;
                    padding: 20px;
                    background-color: #f5f5f5;
                    overflow: auto;
                    border-left: 1px solid #ddd;
                }}
                .node-title {{
                    background-color: #4b77be;
                    color: white;
                    border-radius: 5px;
                    padding: 10px;
                    font-weight: bold;
                    margin-bottom: 15px;
                }}
                .node-details {{
                    background-color: #fff;
                    border-radius: 5px;
                    padding: 15px;
                    margin-top: 10px;
                    border: 1px solid #ddd;
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
            </style>
        </head>
        <body>
            <div class="container">
                <div id="header">
                    <h1>Energy Transition Pathway for {company_name}</h1>
                    <p>Interactive visualization of the recommended transition roadmap</p>
                </div>

                <div class="content-area">
                    <div id="pathway-visualization"></div>
                    <div id="details-panel">
                        <h2>Pathway Details</h2>
                        <p>Click on any node in the visualization to see details.</p>
                        <div id="node-details"></div>
                    </div>
                </div>
            </div>

            <script type="text/javascript">
                // Visualization data
                const nodes = new vis.DataSet({json.dumps(nodes)});
                const edges = new vis.DataSet({json.dumps(edges)});

                // Create network
                const container = document.getElementById('pathway-visualization');
                const data = {{
                    nodes: nodes,
                    edges: edges
                }};

                // Configure visualization options
                const options = {{
                    nodes: {{
                        shape: 'box',
                        margin: 10,
                        widthConstraint: {{
                            maximum: 200
                        }},
                        font: {{
                            size: 14
                        }},
                        color: {{
                            border: '#2B7CE9',
                            background: '#D2E5FF'
                        }}
                    }},
                    edges: {{
                        arrows: {{
                            to: {{ enabled: true, scaleFactor: 1 }}
                        }},
                        smooth: true
                    }},
                    layout: {{
                        hierarchical: {{
                            direction: 'LR',
                            sortMethod: 'directed',
                            levelSeparation: 200,
                            nodeSpacing: 150
                        }}
                    }},
                    physics: false,
                    interaction: {{
                        hover: true,
                        tooltipDelay: 200
                    }}
                }};

                // Apply different colors based on node type
                nodes.forEach(node => {{
                    if (node.type === 'company') {{
                        node.color = {{background: '#E7F5FE', border: '#3498db'}};
                    }} else if (node.type === 'timeframe') {{
                        node.color = {{background: '#FDF2E9', border: '#e67e22'}};
                    }} else if (node.type === 'action') {{
                        node.color = {{background: '#E9F7EF', border: '#27ae60'}};
                    }} else if (node.type === 'recommendation') {{
                        node.color = {{background: '#F4ECF7', border: '#8e44ad'}};
                    }}
                }});

                const network = new vis.Network(container, data, options);

                // Handle node selection
                network.on("click", function(params) {{
                    if (params.nodes.length > 0) {{
                        const nodeId = params.nodes[0];
                        const node = nodes.get(nodeId);

                        const detailsPanel = document.getElementById('node-details');

                        let content = `<div class="node-title">${{node.label}}</div>`;

                        if (node.type === 'recommendation') {{
                            content += `
                                <div class="node-details">
                                    <p>${{node.details}}</p>
                                    <div class="reference">
                                        <strong>Reference:</strong><br>
                                        ${{node.reference}}
                                    </div>
                                </div>
                            `;
                        }} else if (node.type === 'company') {{
                            content += `
                                <div class="node-details">
                                    <p>This visualization shows the recommended energy transition roadmap for ${company_name}.</p>
                                    <p>Click on any timeframe, action category, or specific recommendation to see more details.</p>
                                </div>
                            `;
                        }} else if (node.type === 'timeframe') {{
                            content += `
                                <div class="node-details">
                                    <p>This timeframe represents actions to be taken during: <strong>${{node.label}}</strong></p>
                                    <p>Click on action categories within this timeframe to explore specific recommendations.</p>
                                </div>
                            `;
                        }} else if (node.type === 'action') {{
                            content += `
                                <div class="node-details">
                                    <p>Action category: <strong>${{node.label}}</strong></p>
                                    <p>Click on specific recommendations within this category to see implementation details and references.</p>
                                </div>
                            `;
                        }}

                        detailsPanel.innerHTML = content;
                    }}
                }});
            </script>
        </body>
        </html>
        """

        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

        logging.info(f"Pathway visualization saved to: {html_file}")

        return html_file

    except Exception as e:
        logging.error(f"Error generating pathway visualization: {e}")
        return None
