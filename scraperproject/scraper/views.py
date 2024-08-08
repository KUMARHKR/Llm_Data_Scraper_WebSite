from django.shortcuts import render, redirect
from .forms import ScrapeForm
from .scrape import scrape_yellow_pages
import pandas as pd
import io
from django.http import FileResponse, HttpResponse
from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SERVICE_ACCOUNT_FILE = 'path/to/your/service-account-file.json'

def home(request):
    if request.method == 'POST':
        form = ScrapeForm(request.POST)
        if form.is_valid():
            search_query = form.cleaned_data['search_query']
            location = form.cleaned_data['location']
            num_pages = form.cleaned_data['num_pages']

            df = scrape_yellow_pages(search_query, location, num_pages)

            # Save to Google Sheets
            credentials = service_account.Credentials.from_service_account_file(
                SERVICE_ACCOUNT_FILE, scopes=SCOPES)
            service = build('sheets', 'v4', credentials=credentials)
            sheet = service.spreadsheets()

            spreadsheet = {
                'properties': {
                    'title': f'{search_query}_{location}'
                }
            }

            spreadsheet = sheet.create(body=spreadsheet, fields='spreadsheetId').execute()
            spreadsheet_id = spreadsheet.get('spreadsheetId')

            values = [df.columns.tolist()] + df.values.tolist()
            body = {
                'values': values
            }

            sheet.values().update(
                spreadsheetId=spreadsheet_id,
                range='Sheet1!A1',
                valueInputOption='RAW',
                body=body
            ).execute()

            request.session['data'] = df.to_json()

            return redirect('results')
    else:
        form = ScrapeForm()

    return render(request, 'scraper/home.html', {'form': form})

def results(request):
    df = pd.read_json(request.session['data'])
    return render(request, 'scraper/results.html', {'data': df.to_html(classes='table table-striped')})

def download(request):
    df = pd.read_json(request.session['data'])
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Sheet1')
        writer.save()
    buffer.seek(0)

    return FileResponse(buffer, as_attachment=True, filename='data.xlsx')
