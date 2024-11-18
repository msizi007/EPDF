import os
import fitz
from PyPDF2 import PdfReader, PdfWriter
from datetime import datetime

def merge_pdfs(files, output_dir):
    """
    Merge multiple PDF files and return metadata
    """
    try:
        merger = PdfWriter()
        total_pages = 0
        total_words = 0
        filenames = []

        # Process each file
        for pdf_file in files:
            if not pdf_file.filename.lower().endswith('.pdf'):
                raise ValueError(f'{pdf_file.filename} is not a PDF file')

            temp_path = os.path.join(output_dir, pdf_file.filename)
            pdf_file.save(temp_path)
            filenames.append(pdf_file.filename)

            # Get page count and word count
            with fitz.open(temp_path) as pdf:
                total_pages += pdf.page_count
                for page in pdf:
                    total_words += len(page.get_text("text").split())

            # Add to merger
            with open(temp_path, 'rb') as pdf:
                reader = PdfReader(pdf)
                for page in reader.pages:
                    merger.add_page(page)

        # Save merged file
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

        return {
            'success': True,
            'filename': merged_filename,
            'numPages': total_pages,
            'numWords': total_words,
            'mergedFiles': filenames,
            'filepath': merged_filepath
        }

    except Exception as e:
        # Clean up any temporary files on error
        for filename in filenames:
            temp_path = os.path.join(output_dir, filename)
            if os.path.exists(temp_path):
                os.remove(temp_path)
        raise e

def split_files(filepath, pages, split_option):
    """
    Split a PDF file based on page numbers
    """
    results = []
    reader = PdfReader(filepath)
    total_pages = len(reader.pages)
    
    try:
        if split_option == 'single':
            # Split into two files at the specified page
            split_page = int(pages)
            if split_page < 1 or split_page >= total_pages:
                raise ValueError(f'Invalid split page number. Must be between 1 and {total_pages-1}')

            # First part
            writer1 = PdfWriter()
            for page in reader.pages[:split_page]:
                writer1.add_page(page)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename1 = f'split1_{timestamp}.pdf'
            filepath1 = os.path.join(os.path.dirname(filepath), filename1)
            with open(filepath1, 'wb') as output:
                writer1.write(output)
            results.append(filename1)

            # Second part
            writer2 = PdfWriter()
            for page in reader.pages[split_page:]:
                writer2.add_page(page)
            
            filename2 = f'split2_{timestamp}.pdf'
            filepath2 = os.path.join(os.path.dirname(filepath), filename2)
            with open(filepath2, 'wb') as output:
                writer2.write(output)
            results.append(filename2)

        else:  # multiple pages
            # Extract specific pages
            page_numbers = [int(p.strip()) for p in pages.split(',')]
            page_numbers = sorted(set(page_numbers))  # Remove duplicates and sort
            
            if not all(1 <= p <= total_pages for p in page_numbers):
                raise ValueError(f'Page numbers must be between 1 and {total_pages}')

            for i, page_num in enumerate(page_numbers, 1):
                writer = PdfWriter()
                writer.add_page(reader.pages[page_num - 1])  # Convert to 0-based index
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f'page{page_num}_{timestamp}.pdf'
                filepath = os.path.join(os.path.dirname(filepath), filename)
                with open(filepath, 'wb') as output:
                    writer.write(output)
                results.append(filename)

        return results

    except Exception as e:
        # Clean up any created files on error
        for filename in results:
            filepath = os.path.join(os.path.dirname(filepath), filename)
            if os.path.exists(filepath):
                os.remove(filepath)
        raise e

def get_pdf_info(filepath):
    """
    Get PDF file information
    """
    try:
        with fitz.open(filepath) as pdf:
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
