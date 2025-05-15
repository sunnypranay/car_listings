from typing import List, Dict, Any
from crawler import InventoryCrawler
from models import MercedesVehicleTransformer
import requests


class MercedesCrawler(InventoryCrawler):
    def __init__(self, auth_token: str = None, series: str = None, radius: int = 50, db_file: str = 'vehicle_inventory.db'):
        super().__init__(auth_token, MercedesVehicleTransformer(), db_file)
        self.url = 'https://nafta-service.mbusa.com/api/inv/en_us/used/vehicles/search'
        self.radius = radius
        self.series = series

    def fetch_inventory(self, zip_code: str, page_index: int) -> List[Dict[str, Any]]:
        """Fetch inventory for a specific zip code and page"""
        params = {
            'count': 100,
            'distance': self.radius,
            'invType': 'cpo',
            'model': 'A220W,A220W4,A35W4,GT63C4,GT63C4S,GT53C4,GT43C4,GT63C4SE,B250E,C230WZ,C300W,C300W4,C350W,C250W,C400W4,C63P,C450W4,C350WE,C63WS,C43W4,C63W,C63W4SE,E320W,E350W,E350W4,E550W,E63,E550W4,E400H,E350BTC,E250BTC,E63P,E400W,E400W4,E63W4S,E43W4,E300W4,E300W,E450W4,E53W4,E53EW4,EQE500V4,AMGEQEV4,EQE350V,EQE350V4,EQE350X,AMGEQEX4,EQE350X4,EQS580V4,AMGEQSV4,EQS450V,EQS450V4,S430V4,S550V,S550V4,S350BTC4,S63,S65V,S63V4,S600V,S600X,S550VE,S550X4,S560V,S450V,S650X,S560V4,S450V4,S560X4,S500V4,S580Z4,S580V4,S680Z4,S580EV4,S63EV4',
            'resvOnly': 'false',
            'sortBy': 'price',
            'start': page_index * 100,
            'withFilters': 'true',
            'zip': zip_code,
            'maxPrice': 35000,
            'minPrice': 0,
            'year': '2021,2022,2023,2024',
            'maxMileage': 30000
        }

        response = requests.get(self.url, params=params)
        if response.status_code == 200:
            data = response.json()
            if data['status']['code'] == 200:
                return data['result']['pagedVehicles']['records']
            else:
                print(f"Error in API response for ZIP {zip_code}")
                return []
        else:
            print(f"Error {response.status_code} for ZIP {zip_code}")
            return []
