from dataclasses import dataclass, field
from datetime import datetime
from typing import List
import pandas as pd


@dataclass
class Report:
    """Encapsulates inventory report data and metadata"""
    brand: str
    timestamp: datetime
    duration: str
    total_vehicles: int
    price_changes: int
    average_price: float
    _dataframe: pd.DataFrame = field(
        default=None, repr=False)  # Private field for DataFrame

    @classmethod
    def from_dataframe(cls, df: pd.DataFrame, brand: str, duration: str) -> 'Report':
        """Create a Report instance from a DataFrame"""
        return cls(
            brand=brand,
            timestamp=datetime.now(),
            duration=duration,
            total_vehicles=len(df),
            price_changes=len(df[df['price_change'] != 0]),
            average_price=df['price'].mean(),
            _dataframe=df
        )

    def get_summary(self) -> str:
        """Get a human-readable summary of the report"""
        return f"""
        {self.brand} Inventory Report Summary:
        - Total Vehicles: {self.total_vehicles}
        - Vehicles with Price Changes: {self.price_changes}
        - Average Price: ${self.average_price:,.2f}
        - Report Duration: {self.duration}
        """

    def get_dataframe(self) -> pd.DataFrame:
        """Get the formatted DataFrame for email"""
        return self._dataframe
