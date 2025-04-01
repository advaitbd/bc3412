# bc3412/web/routes.py
import os
import pandas as pd
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, send_from_directory
from werkzeug.utils import secure_filename
from web.forms import UploadForm

# Import your existing functions
from data.loaders import load_excel_data, extract_text_from_pdf
from data.savers import save_enhanced_data
from services.gemini_service import configure_gemini
from services.extraction import get_gemini_extraction
from analysis.integrator import integrate_data
from analysis.recommendations import get_recommendations

# Create the Blueprint at the top level
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/upload', methods=['GET', 'POST'])
def upload():
    form = UploadForm()
    if form.validate_on_submit():
        company_name = form.company_name.data
        # Secure the filename
        filename = secure_filename(f"{company_name}.pdf")
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)

        # Save the uploaded file
        form.report_file.data.save(file_path)
        flash(f'Annual report for {company_name} uploaded successfully!', 'success')

        # Redirect to companies list
        return redirect(url_for('main.companies'))

    return render_template('upload.html', form=form)

@main_bp.route('/companies')
def companies():
    # Check for enhanced dataset file
    output_csv = os.path.join(current_app.config['OUTPUT_FOLDER'], 'enhanced_dataset.csv')

    if os.path.exists(output_csv):
        # Load existing enhanced data
        df = pd.read_csv(output_csv)
        companies_list = df[['Name', 'Industry']].to_dict('records')
    else:
        # If enhanced dataset doesn't exist, get companies from PDF directory
        pdf_dir = current_app.config['UPLOAD_FOLDER']
        companies_list = []
        for filename in os.listdir(pdf_dir):
            if filename.endswith('.pdf'):
                company_name = os.path.splitext(filename)[0]
                companies_list.append({'Name': company_name, 'Industry': 'Unknown'})

    return render_template('companies.html', companies=companies_list)

@main_bp.route('/company/<company_name>')
def company_details(company_name):
    # Check for enhanced dataset file
    output_csv = os.path.join(current_app.config['OUTPUT_FOLDER'], 'enhanced_dataset.csv')

    if os.path.exists(output_csv):
        # Load existing enhanced data
        df = pd.read_csv(output_csv)
        company_data = df[df['Name'] == company_name].to_dict('records')[0] if not df[df['Name'] == company_name].empty else None
    else:
        company_data = {'Name': company_name, 'Status': 'Not analyzed yet'}

    # Check for recommendations
    recommendation_file = os.path.join(current_app.config['OUTPUT_FOLDER'], 'recommendations', f"{company_name}_roadmap.txt")
    has_recommendation = os.path.exists(recommendation_file)

    # Check for visualization
    visualization_file = os.path.join(current_app.config['OUTPUT_FOLDER'], 'visualizations', f"{company_name}_pathway.html")
    has_visualization = os.path.exists(visualization_file)

    return render_template(
        'company_details.html',
        company=company_data,
        has_recommendation=has_recommendation,
        has_visualization=has_visualization
    )

@main_bp.route('/analyze/<company_name>')
def analyze_company(company_name):
    from config.settings import DEFAULT_EXCEL_PATH, DEFAULT_PDF_DIR, DEFAULT_OUTPUT_CSV

    # Initialize Gemini model
    gemini_model = configure_gemini()

    # Load original data
    original_df = load_excel_data(DEFAULT_EXCEL_PATH)

    # Extract text from PDF
    pdf_path = os.path.join(current_app.config['UPLOAD_FOLDER'], f"{company_name}.pdf")
    report_text = extract_text_from_pdf(pdf_path)

    if report_text:
        # Extract data using Gemini
        extracted_data = get_gemini_extraction(report_text, company_name, gemini_model)

        # Add company name for merging
        extracted_data['Name'] = company_name

        # Check if we have an existing enhanced dataset
        output_csv = DEFAULT_OUTPUT_CSV
        if os.path.exists(output_csv):
            enhanced_df = pd.read_csv(output_csv)

            # Remove existing entry for this company if present
            enhanced_df = enhanced_df[enhanced_df['Name'] != company_name]

            # Add new data as a new row
            new_df = pd.DataFrame([extracted_data])
            enhanced_df = pd.concat([enhanced_df, new_df], ignore_index=True)
        else:
            # Create new dataset with just this company
            extracted_list = [extracted_data]
            enhanced_df = integrate_data(original_df, extracted_list)

        # Save the enhanced data
        save_enhanced_data(enhanced_df, output_csv)

        flash(f'Analysis completed for {company_name}!', 'success')
    else:
        flash(f'Could not extract text from PDF for {company_name}.', 'error')

    return redirect(url_for('main.company_details', company_name=company_name))

@main_bp.route('/generate_roadmap/<company_name>')
def generate_roadmap(company_name):
    from config.settings import DEFAULT_OUTPUT_CSV

    # Initialize Gemini model
    gemini_model = configure_gemini()

    # Load enhanced data
    output_csv = DEFAULT_OUTPUT_CSV
    if os.path.exists(output_csv):
        enhanced_df = pd.read_csv(output_csv)

        # Generate recommendations
        get_recommendations(company_name, enhanced_df, gemini_model)

        flash(f'Energy transition roadmap generated for {company_name}!', 'success')
    else:
        flash('Enhanced dataset not found. Please analyze the company first.', 'error')

    return redirect(url_for('main.company_details', company_name=company_name))

@main_bp.route('/view_roadmap/<company_name>')
def view_roadmap(company_name):
    recommendation_file = os.path.join(current_app.config['OUTPUT_FOLDER'], 'recommendations', f"{company_name}_roadmap.txt")

    if os.path.exists(recommendation_file):
        with open(recommendation_file, 'r') as f:
            content = f.read()
        return render_template('roadmap.html', company_name=company_name, content=content)
    else:
        flash('Roadmap not found. Please generate it first.', 'error')
        return redirect(url_for('main.company_details', company_name=company_name))

@main_bp.route('/visualization/<company_name>')
def visualization(company_name):
    """Serve visualization files from the outputs directory"""
    visualization_dir = os.path.join(current_app.config['OUTPUT_FOLDER'], 'visualizations')
    return send_from_directory(visualization_dir, f"{company_name}_pathway.html")

@main_bp.route('/view_visualization/<company_name>')
def view_visualization(company_name):
    # Check if visualization file exists
    visualization_file = os.path.join(current_app.config['OUTPUT_FOLDER'], 'visualizations', f"{company_name}_pathway.html")

    if os.path.exists(visualization_file):
        return redirect(url_for('main.visualization', company_name=company_name))
    else:
        flash('Visualization not found. Please generate the roadmap first.', 'error')
        return redirect(url_for('main.company_details', company_name=company_name))
