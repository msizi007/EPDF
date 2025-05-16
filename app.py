import os, shutil
from io import BytesIO
from flask import Flask, render_template, request, flash, redirect, url_for, send_from_directory, send_file
import fitz  # PyMuPDF
from datetime import datetime
from funcs import merge_pdfs, get_pdf_info
from PyPDF2 import PdfReader, PdfWriter
from werkzeug.utils import secure_filename

"""
1. MERGE FILES ANS STORE IT ON VIRTUAL STORAGE
"""

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # Required for flash messages
uploads_folder = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
app.config['UPLOAD_FOLDER'] = uploads_folder

# Constants
TEMP = BytesIO()

# Create uploads directory for viewing PDFs
UPLOAD_PATH = app.config['UPLOAD_FOLDER']

@app.route('/')
def index():
    global TEMP
    # RESTART TEMP
    if TEMP.closed:
        TEMP = BytesIO()  # Recreate it if it was closed
    else:
        TEMP.seek(0)
        TEMP.truncate(0)
    return render_template('index.html')

@app.route("/pdf")
def serve_pdf():
    TEMP.seek(0)
    return send_file(TEMP, mimetype='application/pdf', as_attachment=False, download_name='inline.pdf')



@app.route('/read', methods=['GET', 'POST'])
def read_pdf():
    global TEMP
    TEMP = BytesIO()

    if request.method == 'POST':
        print('post method...')

        if 'file' not in request.files:
            flash('No file uploaded', 'danger')
            return redirect(url_for('read_pdf'))

        pdf_file = request.files['file']
        if not pdf_file.filename.lower().endswith('.pdf'):
            flash('Please upload a PDF file', 'danger')
            return redirect(url_for('read_pdf'))

        # try:
        # Save PDF file for viewing
        # view_filepath = os.path.join(UPLOAD_PATH, pdf_file.filename)
        # pdf_file.save(view_filepath)
        # pdf_file.save(TEMP)
        TEMP.write(pdf_file.read())
        TEMP.seek(0)


        # Get PDF information
        # info = get_pdf_info(view_filepath)
        info = get_pdf_info(TEMP)
        
        return render_template('view_pdf.html', 
            filename=pdf_file.filename,
            url=url_for('serve_pdf'),
            num_words=info['numWords'],
            num_pages=info['numPages'],
            pdf_url=f'/static/uploads/{pdf_file.filename}'
        )

        """except Exception as e:
            # if os.path.exists(view_filepath):
            #     os.remove(view_filepath)
            print(e)
            flash(str(e), 'danger')
            return redirect(url_for('read_pdf'))"""
    
    else:
        return render_template('read.html')


@app.route('/merge', methods=['GET', 'POST'])
def merge_pdf():
    global TEMP
    TEMP = BytesIO()

    if request.method == "POST":
        if 'files[]' not in request.files:
            flash('No files uploaded', 'danger')
            return redirect(url_for('merge_pdf'))

        files = request.files.getlist('files[]')
        if not files or len(files) < 2:
            flash('Please upload at least 2 PDF files', 'danger')
            return redirect(url_for('merge_pdf'))

        # try:
            # Merge PDFs and get information
        result = merge_pdfs(files, TEMP)

        
        return render_template('view_pdf.html',
            filename=result['filename'],
            url=url_for('serve_pdf'),
            num_pages=result['numPages'],
            num_words=result['numWords'],
            merged_files=result['mergedFiles'],
            pdf_url=f'/static/uploads/{result["filename"]}'
        )

        """except Exception as e:
            flash(str(e), 'danger')
            return redirect(url_for('merge_pdf'))"""
    else:
        return render_template('merge.html')
    

@app.route('/split_pdf', methods=['GET', 'POST'])
def split_pdf():
    global TEMP
    TEMP = BytesIO()
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
        
        # try:
            # Save the uploaded file
        filename = secure_filename(file.filename)
        # filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        # file.save(filepath)
        file.save(TEMP)
        
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
        # pdf = PdfReader(filepath)
        pdf = PdfReader(TEMP)
        
        split_files = []
        
        for i, (start, end) in enumerate(ranges):
            writer = PdfWriter()
            for page_num in range(start - 1, min(end, len(pdf.pages))):
                writer.add_page(pdf.pages[page_num])
            
            output_filename = f'split_{i + 1}_{os.path.splitext(filename)[0]}.pdf'
            # output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
            output_temp = TEMP
            """
            with open(output_path, 'wb') as output_file:
                writer.write(output_file)"""
            
            # Get file metadata
            split_files.append({
                'filename': output_filename,
                'pages': end - start + 1
            })
        
        # Clean up the original file
        # os.remove(filepath)
        
        return render_template('split_result.html', split_files=split_files)
        """
        except ValueError as e:
            flash('Invalid page range format. Please use format like "1-3, 4-6, 7"', 'danger')
            return redirect(request.url)
        except Exception as e:
            flash(f'Error processing PDF: {str(e)}', 'danger')
            return redirect(request.url)"""
    
    return render_template('split.html')

@app.route('/view/<filename>')
def view_pdf(filename):
    file_path = os.path.join(UPLOAD_PATH, filename)
    if not os.path.exists(file_path):
        flash('File not found', 'danger')
        return redirect(url_for('index'))
    
    try:
        info = get_pdf_info(file_path)
        return render_template('split_result.html',
            original_filename=filename,
            split_files=[{
                'filename': TEMP,
                'num_pages': info['numPages'],
                'num_words': info['numWords']
            }],
            show_pdf=True,
            current_pdf=f'/static/uploads/{filename}'
        )
    except Exception as e:
        flash(str(e), 'danger')
        return redirect(url_for('index'))

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(UPLOAD_PATH, filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True, port=5080)
