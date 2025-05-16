import os
import fitz
from PyPDF2 import PdfReader, PdfWriter
from datetime import datetime
from io import BytesIO

def merge_pdfs(files, temp):
    """
    Merge multiple PDF files and return metadata
    """
    # try:
    merger = PdfWriter()
    total_pages = 0
    total_words = 0
    filenames = []
    temp_output = BytesIO()

    # Process each file
    for pdf_file in files:
        temp_file = BytesIO()
        if not pdf_file.filename.lower().endswith('.pdf'):
            raise ValueError(f'{pdf_file.filename} is not a PDF file')

        # temp_path = os.path.join(output_dir, pdf_file.filename)
        # pdf_file.save(temp_path)
        pdf_file.save(temp_file)
        filenames.append(pdf_file.filename)

        # Get page count and word count
        with fitz.open(stream=temp_file, filetype='pdf') as pdf:
            total_pages += pdf.page_count
            for page in pdf:
                total_words += len(page.get_text("text").split())

        # Add to merger
        """
        with open(temp_file, 'rb') as pdf:
            reader = PdfReader(pdf)
            for page in reader.pages:
                merger.add_page(page)"""
        reader = PdfReader(temp_file)
        for page in reader.pages:
            merger.add_page(page)



    # Save merged file
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    merged_filename = f'merged_{timestamp}.pdf'
    merged_filepath = os.path.join(output_dir, merged_filename)
    
    
    with open(merged_filepath, 'wb') as output:
        merger.write(output)
    


    # Clean up temporary files
    for filename in filenames:
        temp_path = os.path.join(output_dir, filename)
        if os.path.exists(temp_path):
            os.remove(temp_path)
    """
    merger.write(temp)
    temp.seek(0)
    return {
        'success': True,
        'filename': 'output.pdf',
        'numPages': total_pages,
        'numWords': total_words,
        'mergedFiles': filenames
    }

    """except Exception as e:
        # Clean up any temporary files on error
        for filename in filenames:
            temp_path = os.path.join(output_dir, filename)
            if os.path.exists(temp_path):
                os.remove(temp_path)
        raise e"""

def get_pdf_info(filepath):
    """
    Get PDF file information
    """
    try:
        with fitz.open(stream=filepath, filetype='pdf') as pdf:
            text = ""
            num_pages = pdf.page_count
            num_words = 0
            for page in pdf:
                text += page.get_text("text")
                num_words += len(text.split())
        return {
            'success': True,
            'numPages': num_pages,
            'numWords': num_words
        }
    except Exception as e:
        raise e
