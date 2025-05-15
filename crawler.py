from abc import ABC, abstractmethod
import requests
import time
from typing import List, Dict, Any
from models import Vehicle, VehicleTransformer
from database import InventoryDatabase
from report import Report


class InventoryCrawler(ABC):
    def __init__(self, auth_token: str, transformer: VehicleTransformer, db_file: str):
        self.auth_token = auth_token
        self.transformer = transformer
        self.db = InventoryDatabase(db_file)
        self.all_vehicles: Dict[str, Vehicle] = {}

    @abstractmethod
    def fetch_inventory(self, zip_code: str, page_index: int) -> List[Dict[str, Any]]:
        """Fetch inventory for a specific zip code and page"""
        pass

    def crawl_zip_codes(self, zip_codes: List[str]):
        """Crawl inventory for multiple zip codes"""
        for index, zip_code in enumerate(zip_codes[0:3], start=1):
            print(f"Fetching inventory for ZIP: {zip_code}")
            page_index = 0
            while True:
                raw_vehicles = self.fetch_inventory(zip_code, page_index)
                if not raw_vehicles:
                    break

                # Transform raw data into Vehicle objects and deduplicate using VIN
                for raw_vehicle in raw_vehicles:
                    vehicle = self.transformer.transform(raw_vehicle)
                    self.all_vehicles[vehicle.vin] = vehicle

                print(
                    f"  Retrieved {len(raw_vehicles)} vehicles on page {page_index}")
                page_index += 1
                time.sleep(1)
            print(f"ZIP code {index} done")
            time.sleep(2)

    def generate_report(self, duration: str) -> Report:
        """Generate a report from the crawled inventory"""
        df_with_changes = self.db.update_inventory(
            list(self.all_vehicles.values()))
        report = Report.from_dataframe(df_with_changes, self.all_vehicles[list(
            self.all_vehicles.keys())[0]].brand, duration)
        report._df = df_with_changes  # Set the internal DataFrame
        return report
