import argparse
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from bmw_crawler import BMWCrawler
from mercedes_crawler import MercedesCrawler
from reporter import EmailReporter
import json
import pandas as pd


def load_config(file_path: str) -> dict:
    """Load configuration from a JSON file"""
    config_path = Path(__file__).parent / file_path

    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Config file not found at {config_path}")
        raise
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in config file {config_path}")
        raise


def get_crawler(brand: str, keys: dict, db_file: str):
    """Factory function to create the appropriate crawler"""
    if brand.lower() == 'bmw':
        return BMWCrawler(
            auth_token=keys['auth_token'],
            series='3 Series',
            radius=50,
            db_file=db_file
        )
    elif brand.lower() == 'mercedes':
        return MercedesCrawler(
            auth_token=keys['auth_token'],
            radius=50,
            db_file=db_file
        )
    else:
        raise ValueError(f"Unsupported brand: {brand}")


def get_all_zip_codes(showrooms_config: dict) -> list:
    """Extract all ZIP codes from the showrooms configuration"""
    all_zips = []
    for state_zips in showrooms_config.values():
        all_zips.extend(state_zips)
    return all_zips


def crawl_brand(brand: str, keys: dict, zip_codes: list, db_file: str):
    """Crawl inventory for a specific brand"""
    start_time = time.time()
    crawler = get_crawler(brand, keys, db_file)
    crawler.crawl_zip_codes(zip_codes)
    duration = time.strftime('%H:%M:%S', time.gmtime(time.time() - start_time))
    return crawler.generate_report(duration)


def main():
    parser = argparse.ArgumentParser(description='Crawl car inventory')
    parser.add_argument('--brands', nargs='+', default=['bmw', 'mercedes'],
                        help='Brands to crawl (default: all)')
    args = parser.parse_args()

    # Set up paths
    base_path = Path(__file__).parent
    db_file = str(base_path / 'vehicle_inventory.db')

    # Load configuration
    keys = load_config('config/keys.json')
    showrooms_config = load_config('config/showrooms.json')

    # Get all ZIP codes from the showrooms configuration
    all_zip_codes = get_all_zip_codes(showrooms_config)

    # Track overall start time
    overall_start_time = time.time()

    # Run crawlers in parallel
    with ThreadPoolExecutor() as executor:
        futures = []
        for brand in args.brands:
            if brand.lower() == 'bmw':
                futures.append(executor.submit(
                    crawl_brand,
                    'bmw',
                    keys,
                    all_zip_codes,
                    db_file
                ))
            elif brand.lower() == 'mercedes':
                futures.append(executor.submit(
                    crawl_brand,
                    'mercedes',
                    keys,
                    all_zip_codes,
                    db_file
                ))

        # Wait for all crawlers to complete and collect reports
        reports = []
        for future in futures:
            report = future.result()
            reports.append(report)
            print(f"\nReport for {report.brand}:")
            print(f"Duration: {report.duration}")
            print("Summary:", report.get_summary())

        # Send email with all reports
        if reports:
            email_reporter = EmailReporter(
                smtp_server="smtp.gmail.com",
                smtp_port=465,
                smtp_user=keys['smtp_user'],
                smtp_password=keys['smtp_password']
            )
            # Combine all reports into one DataFrame
            all_data = pd.concat([report.get_dataframe()
                                 for report in reports])
            # Get unique brands from the reports
            brands = sorted(set(report.brand for report in reports))
            subject = f"Vehicle Inventory Report - {', '.join(brands)}"
            email_reporter.send_report(
                df=all_data,
                duration=time.strftime('%H:%M:%S', time.gmtime(
                    time.time() - overall_start_time)),
                subject=subject,
                to_emails=keys['to_emails']
            )


if __name__ == '__main__':
    main()
