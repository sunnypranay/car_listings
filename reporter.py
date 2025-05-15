import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List
import pandas as pd


class EmailReporter:
    def __init__(self, smtp_server: str, smtp_port: int, smtp_user: str, smtp_password: str):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password

    def send_report(self, df: pd.DataFrame, duration: str, subject: str, to_emails: List[str]):
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = self.smtp_user
        msg['To'] = ', '.join(to_emails)

        # Deduplicate records based on VIN and brand
        df = df.drop_duplicates(subset=['vin', 'brand'])

        # Format DataFrame
        df = df.sort_values(by='price', ascending=True)
        df['price'] = df['price'].apply(lambda x: f"${x:,.0f}")
        df['price_change'] = df['price_change'].apply(lambda x: f"{x:+,.0f}")
        df['price_change_pct'] = df['price_change_pct'].apply(
            lambda x: f"{x:+.2f}%")
        df['odometer'] = df['odometer'].apply(lambda x: f"{x:,.0f}")

        # Create HTML table
        html_table = df[['brand', 'model', 'price', 'price_change', 'price_change_pct',
                        'odometer', 'drivetrain', 'url']].to_html(
            index=False, justify='center', border=1, classes='inventory-table')

        html_body = f"""
        <html>
        <head>
        <style>
          table.inventory-table {{ border-collapse: collapse; width: 100%; }}
          table.inventory-table td, table.inventory-table th {{ border: 1px solid #ddd; padding: 8px; }}
          table.inventory-table th {{ background-color: #f2f2f2; text-align: center; }}
        </style>
        </head>
        <body>
          <h2>Vehicle Inventory Report</h2>
          {html_table}
          <p><em>Runtime Duration: {duration}</em></p>
        </body>
        </html>
        """

        msg.attach(MIMEText(html_body, 'html'))

        with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as smtp:
            smtp.login(self.smtp_user, self.smtp_password)
            smtp.send_message(msg)

        print(f"Email sent to {msg['To']}")
