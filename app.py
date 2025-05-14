import requests
import pandas as pd
import time
from datetime import datetime
import smtplib
import sqlite3
from email.message import EmailMessage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import json
from pathlib import Path


class BMWCPOCrawler:
    def __init__(self, auth_token, series='3 Series', radius=50, db_file='bmw_inventory.db'):
        self.url = 'https://inventoryservices.bmwdealerprograms.com/vehicle'
        self.headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {auth_token}',
            'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N)'
        }
        self.series = series
        self.radius = radius
        self.db_file = db_file
        self.all_vehicles = []

    def fetch_inventory(self, zip_code, page_index):
        body = {
            "pageIndex": page_index,
            "PageSize": 100,
            "postalCode": zip_code,
            "radius": self.radius,
            "sortBy": "price",
            "sortDirection": "asc",
            "formatResponse": False,
            "includeFacets": True,
            "includeDealers": True,
            "includeVehicles": True,
            "filters": [
                {"name": "Series", "values": [self.series]},
                {"name": "Type", "values": ["CPO"]},
                {"name": "Odometer", "values": ["30,000 or less"]},
                {"name": "Price", "values": [
                    "$20,000 - $29,999", "$30,000 - $39,999"]},
                {"name": "Drivetrain", "values": ["AWD"]}
            ]
        }
        response = requests.post(self.url, headers=self.headers, json=body)
        if response.status_code == 200:
            return response.json().get('vehicles', [])
        else:
            print(f"Error {response.status_code} for ZIP {zip_code}")
            return []

    def crawl_zip_codes(self, zip_codes):
        for index, zip_code in enumerate(zip_codes, start=1):
            print(f"Fetching inventory for ZIP: {zip_code}")
            page_index = 0
            while True:
                vehicles = self.fetch_inventory(zip_code, page_index)
                if not vehicles:
                    break
                self.all_vehicles.extend(vehicles)
                print(
                    f"  Retrieved {len(vehicles)} vehicles on page {page_index}")
                page_index += 1
                time.sleep(1)
            print(f"ZIP code {index} done")
            time.sleep(2)

    def update_database_and_calculate_changes(self):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        cursor.execute('''CREATE TABLE IF NOT EXISTS inventory (
            vin TEXT PRIMARY KEY,
            model TEXT,
            internetPrice REAL,
            odometer REAL,
            drivetrain TEXT,
            vdpUrl TEXT,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')

        df_current = pd.DataFrame(
            self.all_vehicles).drop_duplicates(subset='vin')

        df_previous = pd.read_sql_query("SELECT * FROM inventory", conn)

        df_merged = df_current.merge(
            df_previous[['vin', 'internetPrice']], on='vin', how='left', suffixes=('', '_previous'))

        df_merged['price_change'] = df_merged['internetPrice'] - \
            df_merged['internetPrice_previous']
        df_merged['price_change_pct'] = (
            df_merged['price_change'] / df_merged['internetPrice_previous']) * 100

        df_merged['price_change'] = df_merged['price_change'].fillna(0)
        df_merged['price_change_pct'] = df_merged['price_change_pct'].fillna(0)

        # Update database with latest prices
        for _, row in df_current.iterrows():
            cursor.execute('''INSERT OR REPLACE INTO inventory (vin, model, internetPrice, odometer, drivetrain, vdpUrl) VALUES (?, ?, ?, ?, ?, ?)''',
                           (row['vin'], row['model'], row['internetPrice'], row['odometer'], row['drivetrain'], row['vdpUrl']))

        conn.commit()
        conn.close()

        return df_merged

    def send_email_with_table(self, df, duration, subject, to_emails, smtp_server, smtp_port, smtp_user, smtp_password):
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = smtp_user
        msg['To'] = ', '.join(to_emails) if isinstance(
            to_emails, list) else to_emails
        df = df.sort_values(by='internetPrice', ascending=True)
        df['internetPrice'] = df['internetPrice'].apply(lambda x: f"${x:,.0f}")
        df['price_change'] = df['price_change'].apply(lambda x: f"{x:+,.0f}")
        df['price_change_pct'] = df['price_change_pct'].apply(
            lambda x: f"{x:+.2f}%")
        df['odometer'] = df['odometer'].apply(lambda x: f"{x:,.0f}")
        html_table = df[['model', 'internetPrice', 'price_change', 'price_change_pct', 'odometer',
                         'drivetrain', 'vdpUrl']].to_html(index=False, justify='center', border=1, classes='bmw-table')

        html_body = f"""
        <html>
        <head>
        <style>
          table.bmw-table {{ border-collapse: collapse; width: 100%; }}
          table.bmw-table td, table.bmw-table th {{ border: 1px solid #ddd; padding: 8px; }}
          table.bmw-table th {{ background-color: #f2f2f2; text-align: center; }}
        </style>
        </head>
        <body>
          <h2>BMW CPO Midwest Inventory Report</h2>
          {html_table}
          <p><em>Runtime Duration: {str(duration).split('.')[0]}</em></p>
        </body>
        </html>
        """

        msg.attach(MIMEText(html_body, 'html'))

        with smtplib.SMTP_SSL(smtp_server, smtp_port) as smtp:
            smtp.login(smtp_user, smtp_password)
            smtp.send_message(msg)

        print(f"Email sent to {msg['To']}")


if __name__ == "__main__":
    start_time = datetime.now()
    BASE_DIR = Path(__file__).resolve().parent

    # Load keys & tokens
    with open(BASE_DIR / 'keys.json', 'r') as f:
        keys = json.load(f)

    # Load BMW showroom ZIPs
    with open(BASE_DIR / 'showrooms.json', 'r') as f:
        bmw_showroom_zips = json.load(f)

    auth_token = keys['auth_token']

    target_zips = [zip_code for zips in bmw_showroom_zips.values()
                   for zip_code in zips]
    today = datetime.now().strftime('%Y-%m-%d %H:%M')
    crawler = BMWCPOCrawler(auth_token)
    crawler.crawl_zip_codes(target_zips)
    df_with_changes = crawler.update_database_and_calculate_changes()
    end_time = datetime.now()
    duration = end_time - start_time
    crawler.send_email_with_table(
        df=df_with_changes,
        duration=duration,
        subject=f"BMW CPO Midwest Inventory - {today}",
        to_emails=keys["to_emails"],
        smtp_server="smtp.gmail.com",
        smtp_port=465,
        smtp_user=keys["smtp_user"],
        smtp_password=keys["smtp_password"]  # Use an App Password
    )
    print(f"Total runtime: {str(duration).split('.')[0]}")
