from typing import Dict, Any, List, Union, Optional
from pathlib import Path
from sqlalchemy import ForeignKey, String, UUID, create_engine, JSON, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, Session
import uuid
from loguru import logger
import os
from PIL import Image
import hashlib

import opencity2k.sc2_parse as sc2p
import opencity2k.city_preview as cp


cities_dir = Path("cities")
city_images = Path("city_images")
sprites_path = Path("sprites")
db_dir = Path("db")
db_fn = "sc2k.sqlite"
thumb_width = 300

def convert_date(base_year, cycles):
    """
    Converts a data. Note that years have 300 days, which is divided into 12 months of 25 days each.
    Args:
        base_year (int): Year the city was started.
        cycles (int): days since the city was started.
    Returns:
        String date of the form "July 13, 2305"
    """
    year = (cycles // 300) + base_year
    days_passed_year = (cycles - ((year - base_year) * 300))
    month = days_passed_year // 25 + 1
    month_lookup = {1: "January", 2: "February", 3: "March", 4: "April", 5: "May", 6: "June", 7: "July", 8: "August", 9: "September", 10: "October", 11: "November", 12: "December"}
    day = days_passed_year - ((month - 1) * 25) + 1
    return f"{month_lookup[month]} {day}, {year}"


def file_hash(filename: Path) -> str:
    with open(filename, 'rb', buffering=0) as f:
        # MD5 should be fine for this.
        # Can always switch to SHA256, which will take 2x the storage.
        h = hashlib.file_digest(f, "md5")
        return h.hexdigest()


class Base(DeclarativeBase):
     type_annotation_map = {
        dict[str, Any]: JSON
    }


class City(Base):
    __tablename__ = "cities"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    hash: Mapped[str]
    city_path: Mapped[str]
    image_path: Mapped[str]
    city_tags: Mapped[List["CityTags"]] = relationship(back_populates="city")

class CityData(Base):
    __tablename__ = "city_data"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)

    name: Mapped[str]
    population: Mapped[int]
    arco_pop: Mapped[int]
    started: Mapped[int]
    date: Mapped[int]
    funds: Mapped[int]
    bonds: Mapped[int]
    game_level: Mapped[int]
    city_status: Mapped[int]
    crime: Mapped[int]
    traffic: Mapped[int]
    pollution: Mapped[int]
    value: Mapped[int]
    weather: Mapped[str]
    nat_pop: Mapped[int]
    nat_val: Mapped[int]
    disaster: Mapped[int]
    unemployment: Mapped[int]


class Tags(Base):
    __tablename__ = "tags"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)

    name: Mapped[str]
    description: Mapped[str]
    style: Mapped[dict[str, Any]]
    city_tags: Mapped[List["CityTags"]] = relationship(back_populates="tag")

class CityTags(Base):
    __tablename__ = "city_tags"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    tag_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tags.id"))
    city_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cities.id"))
    tag: Mapped["Tags"] = relationship(back_populates="city_tags")
    city: Mapped["City"] = relationship(back_populates="city_tags")


def create_db(db_path):
    engine = create_engine(f"sqlite:///{db_path}", echo=True)
    Base.metadata.create_all(engine)

def parse_cities(p, db_session):
    all_cities = list(p.rglob("*.sc2"))
    failed = []
    skipped = []
    logger.info(f"Found {len(all_cities)} cities.")
    # cities = {}
    for c in all_cities:
        city_hash = file_hash(c)
        exists = db_session.query(City.hash).filter_by(hash=city_hash).first() is not None
        if exists:
            logger.warning(f"City {c} already seen with hash: {city_hash}. Skipping.")
            skipped += [c]
            continue

        try:
            city = sc2p.City()
            city.create_city_from_file(c)
            # cities[c] = city
        except Exception as e:
            logger.error(f"Failed reading {c}, error: {e}")
            failed += [c]
            continue

        city_id = uuid.uuid4()

        img_path = city_images / Path(city_id.hex)

        output_file = img_path
        logger.info(img_path)
        cp.render_city_image(None, output_file, sprites_path, city, False, True, False, "jpg")

        # Create thumbnail version.
        img = Image.open(img_path.with_suffix(".jpg"))
        w_pct = thumb_width / float(img.size[0])
        h = int(img.size[1] * w_pct)
        img = img.resize((thumb_width, h), Image.Resampling.LANCZOS)
        img.save(city_images / Path(f"{city_id.hex}_t").with_suffix(".jpg"))


        name = city.city_name
        population = city.city_attributes['TotalPop']
        arco_pop = city.city_attributes['GlobalArcoPop']
        start_year = city.city_attributes["baseYear"]
        date = convert_date(start_year, city.city_attributes["simCycle"])
        funds = city.city_attributes['TotalFunds']
        bonds = city.city_attributes['TotalBonds']
        game_level = city.city_attributes['GameLevel']
        city_status = city.city_attributes['CityStatus']
        crime = city.city_attributes['CrimeCount']
        traffic = city.city_attributes['TrafficCount']
        pollution = city.city_attributes['Pollution']
        value = city.city_attributes['CityValue']
        weather = city.city_attributes['weatherTrend']
        nat_pop = city.city_attributes['NationalPop']
        nat_val = city.city_attributes['NationalValue']
        disaster = city.city_attributes['CurrentDisaster']
        unemployment = city.city_attributes['unemployed']


        cd = CityData(
            id=city_id,
            name=name,
            population=population,
            arco_pop=arco_pop,
            started=start_year,
            date=date,
            funds=funds,
            bonds=bonds,
            game_level=game_level,
            city_status=city_status,
            crime=crime,
            traffic=traffic,
            pollution=pollution,
            value=value,
            weather=weather,
            nat_pop=nat_pop,
            nat_val=nat_val,
            disaster=disaster,
            unemployment=unemployment
        )
        db_session.add(cd)
        db_session.commit()

        db_city = City(id=city_id, hash=city_hash, city_path=str(c), image_path=str(output_file))
        db_session.add(db_city)

        db_session.commit()        

    logger.info(f"Errors: {len(failed)}, skipped: {len(skipped)}.")

def check_db_images(db_session):
    """Checks to make sure that the database and images are good."""
    a = [x.id.hex for x in db_session.query(CityData).all()]
    b = [x.id.hex for x in db_session.query(CityData).all()]
    c = [x.stem for x in city_images.iterdir() if x.is_file()]
    logger.info([len(a), len(b), len(c)])



def create_session(p=None):
    if p is None:
        p = Path(db_dir) / db_fn
    engine = create_engine(f"sqlite:///{p}", echo=False)
    db_session = Session(engine)
    return db_session



if __name__ == "__main__":
    p = Path(db_dir) / db_fn
    create_db(p)
    db_session = create_session(p)
    parse_cities(cities_dir, db_session)
    check_db_images(db_session)
