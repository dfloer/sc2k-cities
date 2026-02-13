from attrs import define, Factory, field
from uuid import UUID
from db import City as DbCity
from db import CityData as DbCityData
from pathlib import Path


@define
class CityModel:
    city_id: UUID
    db_city: DbCity
    db_data: DbCityData
    city_images: Path

    @property
    def city_path(self):
        return self.db_city.city_path
    
    @property
    def image_path(self):
        return self.db_city.image_path
    
    @property
    def city_image(self):
        return self.city_images / f"{self.city_id.hex}.jpg"
    
    @property
    def city_thumb_image(self):
        return self.city_images / f"{self.city_id.hex}_t.jpg"