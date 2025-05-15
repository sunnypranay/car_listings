from typing import List, Dict, Any
from crawler import InventoryCrawler
from models import BMWVehicleTransformer
import requests


class BMWCrawler(InventoryCrawler):
    def __init__(self, auth_token: str, series: str = '3 Series', radius: int = 50, db_file: str = 'vehicle_inventory.db'):
        super().__init__(auth_token, BMWVehicleTransformer(), db_file)
        self.url = 'https://inventoryservices.bmwdealerprograms.com/vehicle'
        self.headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {auth_token}',
            'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N)'
        }
        self.series = series
        self.radius = radius

    def fetch_inventory(self, zip_code: str, page_index: int) -> List[Dict[str, Any]]:
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
