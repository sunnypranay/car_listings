from dataclasses import dataclass
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod


@dataclass
class Vehicle:
    vin: str
    model: str
    price: float
    odometer: float
    drivetrain: str
    url: str
    brand: str
    raw_data: Dict[str, Any]  # Store original data for reference


class VehicleTransformer(ABC):
    """Abstract base class for transforming raw vehicle data into our standard format"""

    @abstractmethod
    def transform(self, raw_data: Dict[str, Any]) -> Vehicle:
        """Transform raw vehicle data into our standard Vehicle format"""
        pass


class BMWVehicleTransformer(VehicleTransformer):
    def transform(self, raw_data: Dict[str, Any]) -> Vehicle:
        return Vehicle(
            vin=raw_data['vin'],
            model=raw_data['model'],
            price=float(raw_data['internetPrice']),
            odometer=float(raw_data['odometer']),
            drivetrain=raw_data['drivetrain'],
            url=raw_data['vdpUrl'],
            brand='BMW',
            raw_data=raw_data
        )


class MercedesVehicleTransformer(VehicleTransformer):
    def transform(self, raw_data: Dict[str, Any]) -> Vehicle:
        # Extract vehicle details from Mercedes API response
        used_attrs = raw_data.get('usedVehicleAttributes', {})

        # Get drivetrain from properties
        drivetrain = 'Unknown'
        for prop in raw_data.get('properties', []):
            if prop.get('name') == 'AUTOMATIC_TRANSMISSION':
                drivetrain = prop.get('value', 'Unknown')
                break

        return Vehicle(
            vin=raw_data['vin'],
            model=raw_data['modelName'],
            price=float(raw_data['dsrp']),
            odometer=float(used_attrs.get('mileage', 0)),
            drivetrain=drivetrain,
            url=raw_data['eLink'],
            brand='Mercedes',
            raw_data=raw_data
        )
