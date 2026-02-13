from attrs import Factory, field, define
from typing import Dict, Any, List, Union
from pathlib import Path
from sqlalchemy import create_engine


cities_dir = Path("cities")
db_dir = Path("db")
db_fn = "sc2k_cities.sqlite"

@define
class CityList:
    cities: Dict[str, Any]
    _db = field(default=None, init=False)


    def __attrs_post_init__(self):
        db = "sqlite://db/sc2k_cities.sqlite"
        self._db = create_engine(db, echo=True)

# class City:
