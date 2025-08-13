# Phone Number Cleaner

A Django web application that processes Excel files to clean and format phone numbers with +91 prefix, removes duplicates, and provides downloadable results.

## Features

- Upload Excel (.xlsx, .xls) or CSV files
- Automatically detects phone number columns
- Cleans and formats numbers with +91 prefix
- Removes duplicates and invalid numbers
- Download processed results as Excel file
- Modern drag-and-drop interface

## Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run migrations:
```bash
python manage.py migrate
```

3. Start development server:
```bash
python manage.py runserver
```

4. Open http://127.0.0.1:8000

## Deployment on Render

1. Connect your GitHub repository to Render
2. Create a new Web Service
3. Use these settings:
   - Build Command: `./build.sh`
   - Start Command: `gunicorn phone_cleaner.wsgi:application`
   - Environment Variables:
     - `DEBUG=False`
     - `SECRET_KEY=your-secret-key`

## Usage

1. Upload your Excel/CSV file with phone numbers
2. Click "Process File"
3. Download the cleaned results

The app automatically detects columns containing "phone", "mobile", "number", or "contact" keywords.