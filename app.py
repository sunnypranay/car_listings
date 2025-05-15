import json
from datetime import datetime
from pathlib import Path
from bmw_crawler import BMWCrawler
from reporter import EmailReporter


def main():
    start_time = datetime.now()
    BASE_DIR = Path(__file__).resolve().parent

    # Load keys & tokens
    with open(BASE_DIR / 'keys.json', 'r') as f:
        keys = json.load(f)

    # Load BMW showroom ZIPs
    with open(BASE_DIR / 'showrooms.json', 'r') as f:
        bmw_showroom_zips = json.load(f)

    # Initialize crawler with common database
    crawler = BMWCrawler(
        auth_token=keys['auth_token'],
        series='3 Series',
        radius=50,
        db_file='vehicle_inventory.db'  # Common database for all brands
    )

    # Crawl inventory
    target_zips = [zip_code for zips in bmw_showroom_zips.values()
                   for zip_code in zips]
    crawler.crawl_zip_codes(target_zips)

    # Generate report
    duration = str(datetime.now() - start_time).split('.')[0]
    report = crawler.generate_report(duration)

    # Print report summary
    print(report.get_summary())

    # Send email report
    today = datetime.now().strftime('%Y-%m-%d %H:%M')
    reporter = EmailReporter(
        smtp_server="smtp.gmail.com",
        smtp_port=465,
        smtp_user=keys["smtp_user"],
        smtp_password=keys["smtp_password"]
    )

    reporter.send_report(
        df=report.get_dataframe(),
        duration=duration,
        subject=f"{report.brand} CPO Midwest Inventory - {today}",
        to_emails=keys["to_emails"]
    )

    print(f"Total runtime: {duration}")


if __name__ == "__main__":
    main()
