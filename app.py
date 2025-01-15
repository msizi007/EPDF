import os, shutil
from flask import Flask, render_template, request, flash, redirect, url_for, send_from_directory
import fitz  # PyMuPDF
from datetime import datetime
from funcs import merge_pdfs, split_files, get_pdf_info
from PyPDF2 import PdfReader, PdfWriter
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # Required for flash messages
uploads_folder = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
app.config['UPLOAD_FOLDER'] = uploads_folder

# Constants
FILE_PATH = os.path.join(os.path.dirname(__file__), 'static', 'tmp')
os.makedirs(FILE_PATH, exist_ok=True)

# Create uploads directory for viewing PDFs
UPLOAD_PATH = app.config['UPLOAD_FOLDER']

def clean_data():
    os.removedirs(uploads_folder)
    os.mkdir(uploads_folder)


@app.route('/')
def index():
    clean_data()
    return render_template('index.html')

@app.route('/read')
def read_pdf():
    return render_template('read.html')

@app.route('/read', methods=['POST'])
def read_pdf_post():

    if 'file' not in request.files:
        flash('No file uploaded', 'error')
        return redirect(url_for('read_pdf'))

    pdf_file = request.files['file']
    if not pdf_file.filename.lower().endswith('.pdf'):
        flash('Please upload a PDF file', 'error')
        return redirect(url_for('read_pdf'))

    try:
        # Save PDF file for viewing
        view_filepath = os.path.join(UPLOAD_PATH, pdf_file.filename)
        pdf_file.save(view_filepath)

        # Get PDF information
        info = get_pdf_info(view_filepath)
        
        return render_template('view_pdf.html', 
            filename=pdf_file.filename,
            num_words=info['numWords'],
            num_pages=info['numPages'],
            pdf_url=f'/static/uploads/{pdf_file.filename}'
        )

    except Exception as e:
        if os.path.exists(view_filepath):
            os.remove(view_filepath)
        flash(str(e), 'error')
        return redirect(url_for('read_pdf'))

@app.route('/merge')
def merge_pdf():
    return render_template('merge.html')

@app.route('/merge', methods=['POST'])
def merge_pdf_post():
    if 'files[]' not in request.files:
        flash('No files uploaded', 'error')
        return redirect(url_for('merge_pdf'))

    files = request.files.getlist('files[]')
    if not files or len(files) < 2:
        flash('Please upload at least 2 PDF files', 'error')
        return redirect(url_for('merge_pdf'))

    try:
        # Merge PDFs and get information
        result = merge_pdfs(files, UPLOAD_PATH)

        
        return render_template('view_pdf.html',
            filename=result['filename'],
            num_pages=result['numPages'],
            num_words=result['numWords'],
            merged_files=result['mergedFiles'],
            pdf_url=f'/static/uploads/{result["filename"]}'
        )

    except Exception as e:
        flash(str(e), 'error')
        return redirect(url_for('merge_pdf'))

@app.route('/split_pdf', methods=['GET', 'POST'])
def split_pdf():
    if request.method == 'POST':
        if 'pdf_file' not in request.files:
            flash('No file selected', 'danger')
            return redirect(request.url)
        
        file = request.files['pdf_file']
        if file.filename == '':
            flash('No file selected', 'danger')
            return redirect(request.url)
        
        if not file.filename.endswith('.pdf'):
            flash('Please upload a PDF file', 'danger')
            return redirect(request.url)
        
        page_ranges = request.form.get('page_ranges', '').strip()
        if not page_ranges:
            flash('Please enter page ranges', 'danger')
            return redirect(request.url)
        
        try:
            # Save the uploaded file
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Process the page ranges
            ranges = []
            for part in page_ranges.split(','):
                part = part.strip()
                if '-' in part:
                    start, end = map(int, part.split('-'))
                    ranges.append((start, end))
                else:
                    page = int(part)
                    ranges.append((page, page))
            
            # Split the PDF
            pdf = PdfReader(filepath)
            split_files = []
            
            for i, (start, end) in enumerate(ranges):
                writer = PdfWriter()
                for page_num in range(start - 1, min(end, len(pdf.pages))):
                    writer.add_page(pdf.pages[page_num])
                
                output_filename = f'split_{i + 1}_{os.path.splitext(filename)[0]}.pdf'
                output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
                
                with open(output_path, 'wb') as output_file:
                    writer.write(output_file)
                
                # Get file metadata
                split_files.append({
                    'filename': output_filename,
                    'pages': end - start + 1
                })
            
            # Clean up the original file
            os.remove(filepath)
            
            return render_template('split_result.html', split_files=split_files)
            
        except ValueError as e:
            flash('Invalid page range format. Please use format like "1-3, 4-6, 7"', 'danger')
            return redirect(request.url)
        except Exception as e:
            flash(f'Error processing PDF: {str(e)}', 'danger')
            return redirect(request.url)
    
    return render_template('split.html')

@app.route('/view/<filename>')
def view_pdf(filename):
    file_path = os.path.join(UPLOAD_PATH, filename)
    if not os.path.exists(file_path):
        flash('File not found', 'error')
        return redirect(url_for('index'))
    
    try:
        info = get_pdf_info(file_path)
        return render_template('split_result.html',
            original_filename=filename,
            split_files=[{
                'filename': filename,
                'num_pages': info['numPages'],
                'num_words': info['numWords']
            }],
            show_pdf=True,
            current_pdf=f'/static/uploads/{filename}'
        )
    except Exception as e:
        flash(str(e), 'error')
        return redirect(url_for('index'))

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(UPLOAD_PATH, filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
