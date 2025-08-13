import pandas as pd
import re
import os
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import tempfile

def clean_phone_number(number):
    """Clean and format phone numbers"""
    if pd.isna(number):
        return None

    # Remove all non-digit characters
    number = re.sub(r'\D', '', str(number))

    # Remove all leading zeros
    number = number.lstrip('0')

    # Remove '91' prefix if present and length >= 12
    if number.startswith('91') and len(number) > 10:
        number = number[2:]

    # If still too long, keep only the last 10 digits
    if len(number) > 10:
        number = number[-10:]

    # Final validation
    if len(number) == 10:
        return '+91' + number
    else:
        return None

def read_excel_robust(file_path):
    """Try multiple methods to read Excel file"""
    methods = [
        lambda: pd.read_excel(file_path, engine='openpyxl'),
        lambda: pd.read_excel(file_path, engine='xlrd'),
        lambda: pd.read_csv(file_path) if file_path.endswith('.csv') else None
    ]
    
    for method in methods:
        try:
            df = method()
            if df is not None:
                return df
        except:
            continue
    
    # Try openpyxl directly
    try:
        import openpyxl
        wb = openpyxl.load_workbook(file_path, data_only=True, read_only=True)
        ws = wb.active
        data = []
        for row in ws.iter_rows(values_only=True):
            if any(cell is not None for cell in row):
                data.append(row)
        if data:
            return pd.DataFrame(data[1:], columns=data[0])
    except:
        pass
    
    return None

def index(request):
    """Main upload page"""
    return render(request, 'processor/index.html')

@csrf_exempt
def process_file(request):
    """Process uploaded Excel file"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method allowed'})
    
    if 'file' not in request.FILES:
        return JsonResponse({'error': 'No file uploaded'})
    
    uploaded_file = request.FILES['file']
    
    # Validate file type
    if not uploaded_file.name.endswith(('.xlsx', '.xls', '.csv')):
        return JsonResponse({'error': 'Please upload an Excel (.xlsx, .xls) or CSV file'})
    
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
            for chunk in uploaded_file.chunks():
                tmp_file.write(chunk)
            tmp_file_path = tmp_file.name
        
        # Read the file
        df = read_excel_robust(tmp_file_path)
        
        if df is None:
            os.unlink(tmp_file_path)
            return JsonResponse({'error': 'Could not read the file. Please ensure it\'s a valid Excel/CSV file.'})
        
        # Find phone column
        phone_columns = []
        for col in df.columns:
            if any(keyword in str(col).upper() for keyword in ['PHONE', 'MOBILE', 'NUMBER', 'CONTACT']):
                phone_columns.append(col)
        
        if not phone_columns:
            os.unlink(tmp_file_path)
            return JsonResponse({
                'error': 'No phone column found. Please ensure your file has a column with "phone", "mobile", "number", or "contact" in the name.',
                'columns': list(df.columns)
            })
        
        # Use the first phone column found
        phone_column = phone_columns[0]
        
        # Process phone numbers
        original_count = len(df)
        df['CleanedPhone'] = df[phone_column].apply(clean_phone_number)
        
        # Remove duplicates and invalid numbers
        df_valid = df[df['CleanedPhone'].notnull()].copy()
        df_unique = df_valid.drop_duplicates(subset=['CleanedPhone'])
        
        valid_count = len(df_valid)
        unique_count = len(df_unique)
        duplicates_removed = valid_count - unique_count
        
        # Create output file
        output_df = df_unique[['CleanedPhone']].copy()
        output_df.columns = ['Phone_Number']
        
        # Save to temporary file for download
        output_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
        output_df.to_excel(output_file.name, index=False)
        output_file.close()
        
        # Clean up input file
        os.unlink(tmp_file_path)
        
        # Store output file path in session for download
        request.session['output_file'] = output_file.name
        
        return JsonResponse({
            'success': True,
            'original_count': original_count,
            'valid_count': valid_count,
            'unique_count': unique_count,
            'duplicates_removed': duplicates_removed,
            'phone_column': phone_column
        })
        
    except Exception as e:
        if 'tmp_file_path' in locals():
            os.unlink(tmp_file_path)
        return JsonResponse({'error': f'Error processing file: {str(e)}'})

def download_file(request):
    """Download processed file"""
    if 'output_file' not in request.session:
        return HttpResponse('No file to download', status=404)
    
    file_path = request.session['output_file']
    
    if not os.path.exists(file_path):
        return HttpResponse('File not found', status=404)
    
    try:
        with open(file_path, 'rb') as f:
            response = HttpResponse(f.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = 'attachment; filename="cleaned_phone_numbers.xlsx"'
            
        # Clean up file after download
        os.unlink(file_path)
        del request.session['output_file']
        
        return response
        
    except Exception as e:
        return HttpResponse(f'Error downloading file: {str(e)}', status=500)