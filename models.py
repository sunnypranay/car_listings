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
        # Implement Mercedes-specific transformation
        # This is a placeholder - adjust according to actual Mercedes API response format
        return Vehicle(
            vin=raw_data['vin'],
            model=raw_data['model'],
            price=float(raw_data['price']),
            odometer=float(raw_data['mileage']),
            drivetrain=raw_data['driveType'],
            url=raw_data['vehicleUrl'],
            brand='Mercedes',
            raw_data=raw_data
        )
