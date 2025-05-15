import sqlite3
import pandas as pd
from typing import List, Dict, Any, Tuple
from models import Vehicle


class InventoryDatabase:
    def __init__(self, db_file: str):
        self.db_file = db_file
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute('''CREATE TABLE IF NOT EXISTS inventory (
                vin TEXT PRIMARY KEY,
                model TEXT,
                price REAL,
                odometer REAL,
                drivetrain TEXT,
                url TEXT,
                brand TEXT,
                series TEXT,           -- BMW specific
                cpo_status TEXT,       -- BMW specific
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(vin, brand)     -- Allow same VIN for different brands
            )''')
            conn.commit()

    def _vehicles_to_dataframe(self, vehicles: List[Vehicle]) -> pd.DataFrame:
        """Convert Vehicle objects to DataFrame"""
        return pd.DataFrame([{
            'vin': v.vin,
            'model': v.model,
            'price': v.price,
            'odometer': v.odometer,
            'drivetrain': v.drivetrain,
            'url': v.url,
            'brand': v.brand,
            'series': v.raw_data.get('series', ''),
            'cpo_status': v.raw_data.get('cpoStatus', '')
        } for v in vehicles])

    def _get_previous_inventory(self, brand: str) -> pd.DataFrame:
        """Get previous inventory for a specific brand"""
        with sqlite3.connect(self.db_file) as conn:
            return pd.read_sql_query(
                "SELECT * FROM inventory WHERE brand = ?",
                conn,
                params=(brand,)
            )

    def _calculate_price_changes(self, df_current: pd.DataFrame, df_previous: pd.DataFrame) -> pd.DataFrame:
        """Calculate price changes between current and previous inventory"""
        df_merged = df_current.merge(
            df_previous[['vin', 'price']],
            on='vin',
            how='left',
            suffixes=('', '_previous')
        )

        df_merged['price_change'] = df_merged['price'] - \
            df_merged['price_previous']
        df_merged['price_change_pct'] = (
            df_merged['price_change'] / df_merged['price_previous']
        ) * 100

        df_merged['price_change'] = df_merged['price_change'].fillna(0)
        df_merged['price_change_pct'] = df_merged['price_change_pct'].fillna(0)

        return df_merged

    def _update_database(self, df_current: pd.DataFrame):
        """Update database with current inventory"""
        with sqlite3.connect(self.db_file) as conn:
            for _, row in df_current.iterrows():
                conn.execute('''
                    INSERT INTO inventory (
                        vin, model, price, odometer, drivetrain, url, brand, series, cpo_status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(vin, brand) DO UPDATE SET
                        model = excluded.model,
                        price = excluded.price,
                        odometer = excluded.odometer,
                        drivetrain = excluded.drivetrain,
                        url = excluded.url,
                        series = excluded.series,
                        cpo_status = excluded.cpo_status,
                        last_updated = CURRENT_TIMESTAMP
                ''', (
                    row['vin'], row['model'], row['price'], row['odometer'],
                    row['drivetrain'], row['url'], row['brand'], row['series'],
                    row['cpo_status']
                ))
            conn.commit()

    def update_inventory(self, vehicles: List[Vehicle]) -> pd.DataFrame:
        """Update inventory and return DataFrame with price changes"""
        if not vehicles:
            return pd.DataFrame()

        # Convert vehicles to DataFrame
        df_current = self._vehicles_to_dataframe(vehicles)

        # Get previous inventory
        brand = vehicles[0].brand
        df_previous = self._get_previous_inventory(brand)

        # Calculate price changes
        df_with_changes = self._calculate_price_changes(
            df_current, df_previous)

        # Update database
        self._update_database(df_current)

        return df_with_changes

    def get_all_inventory(self) -> pd.DataFrame:
        """Get all inventory across all brands"""
        with sqlite3.connect(self.db_file) as conn:
            return pd.read_sql_query("SELECT * FROM inventory", conn)

    def get_brand_inventory(self, brand: str) -> pd.DataFrame:
        """Get inventory for a specific brand"""
        with sqlite3.connect(self.db_file) as conn:
            return pd.read_sql_query(
                "SELECT * FROM inventory WHERE brand = ?",
                conn,
                params=(brand,)
            )
