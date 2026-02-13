from nicegui import ui, app, events
from db import create_session
from db import City as DbCity
from db import CityData as DbCityData
from pathlib import Path
from loguru import logger
from uuid import UUID
from random import randint
from attrs import define, field, Factory
from sqlalchemy import column, text, desc
import uuid
from typing import Optional

from typing import List

from opencity2k.Data.value_mappings import disaster_type, weather_type


from views import CityView
from models import CityModel

sess = create_session()
cities_dir = Path("cities")
city_images = Path("city_images")

@define
class City:
    city_id: uuid.UUID
    db_city: DbCity
    db_data: DbCityData

    @property
    def city_path(self):
        return self.db_city.city_path
    
    @property
    def image_path(self):
        return self.db_city.image_path
    
    @property
    def city_image(self):
        return city_images / Path(f"{self.city_id.hex}.jpg")
    
    @property
    def city_thumb_image(self):
        return city_images / Path(f"{self.city_id.hex}_t.jpg")

    @ui.refreshable
    def city_info(self):
        with ui.column() as ui_info:
            img = self.city_image
            try:
                ui.image(img).props('fit=scale-down')
            except FileNotFoundError:
                logger.error(f"image file not found: {img}")
                ui.icon("broken_image").classes('text-5xl outline')

            cols = [
                {"name": "name", "label": "City Name", "field": "name"},
                {"name": "population", "label": "Population", "field": "population"},
                # {"name": "arco_pop", "label": "Arco Pop", "field": "arco_pop"},
                # {"name": "started", "label": "Start Year", "field": "started"},
                {"name": "date", "label": "Date", "field": "date"},
                {"name": "funds", "label": "Funds", "field": "funds"},
                # {"name": "bonds", "label": "Bonds", "field": "bonds"},
                # {"name": "game_level", "label": "Level", "field": "game_level"},
                # {"name": "city_status", "label": "Status", "field": "city_status"},
                {"name": "crime", "label": "Crime", "field": "crime"},
                {"name": "traffic", "label": "Traffic", "field": "traffic"},
                {"name": "pollution", "label": "Pollution", "field": "pollution"},
                {"name": "value", "label": "Value", "field": "value"},
                {"name": "weather", "label": "Weather", "field": "weather"},
                {"name": "nat_pop", "label": "Nat'l Pop", "field": "nat_pop"},
                {"name": "nat_val", "label": "Nat'l Val", "field": "nat_val"},
                {"name": "disaster", "label": "Disaster", "field": "disaster"},
                {"name": "unemployment", "label": "Unemployment", "field": "unemployment"},
            ]

            d = self.db_data
            rows = [
                {"name": d.name,
                "population": f"{d.population + d.arco_pop:,}",
                # "arco_pop": f"{d.arco_pop:,}",
                "started": d.started, 
                "date": d.date,
                "funds": f"${d.funds:,}",
                "bonds": f"${d.bonds:,}",
                "game_level": f"{d.game_level:,}",
                "city_status": f"{d.city_status:,}",
                "crime": f"{d.crime:,}",
                "traffic": f"{d.traffic:,}",
                "pollution": f"{d.pollution:,}",
                "value": f"${d.value * 1000:,}",
                "weather": weather_type[int(d.weather)].title(),
                "nat_pop": f"{d.nat_pop * 1000:,}",
                "nat_val": f"${d.nat_val * 1000:,}",
                "disaster": disaster_type[int(d.disaster)].title(),
                "unemployment": f"{d.unemployment:,}",
                },
            ]
            ui.table(columns=cols, rows=rows)
            ui.label("Tags:")
            with ui.row().classes('gap-1'):
                ui.chip("test1", color="red")
                ui.chip("test2", color="orange")
                ui.chip("test3", color="yellow", text_color="black")
                ui.chip("test4", color="green")
                ui.chip("test5", color="blue")
                ui.chip("test6", color="purple")
            return ui_info
        
    @ui.refreshable
    def short_info(self, img: ui.image = None, stats: List = ["name"]):
        """stats is a list of stats to include."""
        with ui.row() as e:
            t_img = self.city_thumb_image
            if img is None:
                i = ui.image(t_img)
            else:
                i = ui.image(img)
            # with ui.column():
                # for x in stats:
            #         d = self.db_data
            #         ui.label(f"{x}: {getattr(d, x)}")
            cols = [{"name": x, "label": x.title(), "field": x} for x in stats]
            rows = []
            d = self.db_data
            for x in stats:
                rows += [{x: getattr(d, x)}]
            t = ui.table(columns=cols, rows=rows)
        return e, i, t


def get_all_cities():
    cities = sess.query(DbCity).all()
    cities_data = sess.query(DbCityData).all()
    all_cities = {}
    for x, y in zip(cities, cities_data):
        assert x.id == y.id
        c_id = x.id
        c = City(c_id, x, y)
        all_cities[c_id] = c
    return all_cities


all_cities = get_all_cities()


@define
class RandomCity:
    city: City = field(init=None, default=None)
    ui_info: ui.row = field(init=None, default=None)
    search_res = field(init=None, default=None)

    @ui.refreshable
    def random_city(self, all_cities):
        if self.ui_info is not None:
            self.ui_info.delete()
        r = randint(0, len(all_cities))
        self.city = list(all_cities.values())[r]
        self.ui_info = self.city.city_info()

def city_search(all_cities, key, val):
    logger.info([key, val])
    res = []
    lightbox = CityScroller()
    for k, v in all_cities.items():
        # logger.info(v.db_data.weather)
        # logger.info(type(v.db_data.weather))
        if str(getattr(v.db_data, key)) == str(val):
            res += [v]
            lightbox.add_city(v).classes('w-[300px] h-[200px]')
    with ui.column() as search_res:
        logger.info(res)
        for x in res:
            with ui.expansion(x.db_data.name):
                x.city_info()
        
@define
class CityScroller:
    city_list: List[City] = field(default=Factory(list))
    dialog: ui.dialog = field(init=False)
    large_image: ui.image = field(init=False)

    def __attrs_post_init__(self):
        with ui.dialog().props('maximized').classes('bg-black') as self.dialog:
            ui.keyboard(self._handle_key)
            self.large_image = ui.image().props('no-spinner fit=scale-down')

    def add_city(self, city: City) -> ui.image:
        self.city_list += [city]
        img = city_images / Path(f"{city.city_id.hex}.jpg")
        # t_img = city_images / Path(f"{city.city_id.hex}_t.jpg")
        # with ui.button(on_click=lambda: self._open(img)).props('flat dense square'):
            # return ui.image(t_img)
            # return city.short_info(["name", "disaster"])
        e, i, t = city.short_info(img, ["name", "disaster"])
        with ui.button(on_click=lambda: self._open(img)).props('flat dense square'):
            return ui.image(img)
        return e
        # return ui.image(img)
        # return ui.image(city.image_path)

    def _handle_key(self, event_args: events.KeyEventArguments) -> None:
        if not event_args.action.keydown:
            return
        if event_args.key.escape:
            self.dialog.close()
        # image_index = self.image_list.index(self.large_image.source)
        # if event_args.key.arrow_left and image_index > 0:
        #     self._open(self.image_list[image_index - 1])
        # if event_args.key.arrow_right and image_index < len(self.image_list) - 1:
        #     self._open(self.image_list[image_index + 1])

    def _open(self, url: str) -> None:
        self.large_image.set_source(url)
        self.dialog.open()

app.add_static_files('/cities', 'cities')
sess = create_session()
cities_dir = Path("cities")
city_images = Path("city_images")


@define
class RandomView:
    all_cities: list[City]
    dl_path: str = ''
    r: RandomCity = field(init=None, default=RandomCity())

    def view(self):
        with ui.row():
            ui.button("Download City", on_click=lambda: ui.download(self.dl_path), icon="download")
            ui.button("Random", on_click=lambda: self.get_random_city(), color="secondary", icon="refresh")
        self.get_random_city()

    def get_random_city(self):
        self.r.random_city(self.all_cities)
        self.dl_path = self.r.city.city_path

# all_cities = sess.query(DbCity).all()


def view_city(city_id, all_cities):
    ui.label(f"city_id={city_id}")



with ui.header():
    with ui.tabs() as tabs:
        ui.tab("Search", icon="search")
        ui.tab("City", icon="location_city")
        ui.tab("Random", icon="shuffle")
        ui.tab("Featured", icon="star")
        ui.tab("Ranking", icon="timeline")
        ui.tab("Collections", icon="list")
        ui.tab("About", icon="question_mark")

with ui.tab_panels(tabs, value="Random").classes('w-full') as tp:
    with ui.tab_panel("Search"):
        ui.label("Search Cities")
        with ui.row():
            with ui.column():
                ui.label("Disaster")
                disaster = ui.select(disaster_type)
                ui.button(icon="search", on_click=lambda: city_search(all_cities, "disaster", disaster.value))
            with ui.column():
                ui.label("Weather")
                weather = ui.select(weather_type)
                ui.button(icon="search", on_click=lambda: city_search(all_cities, "weather", weather.value))

    with ui.tab_panel("Random"):
        rand = RandomView(all_cities)
        rand.view()


    with ui.tab_panel("Featured"):
        ui.label("Featured Cities")

    with ui.tab_panel("Ranking"):
        ui.label("Ranked Cities")
        all_cities_data = sess.query(DbCityData).all()
        with ui.expansion("Highest Population"):
            with ui.column():                
                x = sorted(all_cities_data, key=lambda a: a.arco_pop + a.population, reverse=True)
                i = 0
                for c in x:
                    ui.label(f"City: {c.name} has {c.arco_pop + c.population:,} sims.")
                    i += 1
                    if i == 10:
                        break

        with ui.expansion("Highest Funds"):
            with ui.column():
                x = sorted(all_cities_data, key=lambda a: a.funds, reverse=True)
                i = 0
                for c in x:
                    if c.funds >= 0x7fffffff:
                        continue
                    ui.label(f"City: {c.name} has ${c.funds:,}.")
                    i += 1
                    if i == 10:
                        break

        with ui.expansion("Highest Crime"):
            with ui.column():
                x = sorted(all_cities_data, key=lambda a: a.crime, reverse=True)
                i = 0
                for c in x:
                    ui.label(f"City: {c.name} has {c.crime:,}.")
                    i += 1
                    if i == 10:
                        break

        with ui.expansion("Highest Value"):
            with ui.column():
                x = sorted(all_cities_data, key=lambda a: a.value, reverse=True)
                i = 0
                for c in x:
                    ui.label(f"City: {c.name} has {c.value:,}.")
                    i += 1
                    if i == 10:
                        break

    with ui.tab_panel("Collections"):
        with ui.tabs() as coll_tabs:
            ui.tab("Scenarios", icon="volcano")
            ui.tab("Streets", icon="directions_car")
            ui.tab("Copter", icon="flight")  # Why doesn't icon="helicopter" work?
            ui.tab("Image", icon="photo")
            ui.tab("Classic", icon="corporate_fare")
            ui.tab("Other", icon="other_houses")

        with ui.tab_panels(coll_tabs, value="Scenarios").classes("w-full"):

            with ui.tab_panel("Scenarios"):
                ui.label("Scenarios")

            with ui.tab_panel("Streets"):
                ui.label("Streets Cities")

            with ui.tab_panel("Copter"):
                ui.label("Copter Cities")

            with ui.tab_panel("Image"):
                ui.label("Cities That Make an Image")

            with ui.tab_panel("Classic"):
                ui.label("SimCity Classic Cities")

            with ui.tab_panel("Other"):
                ui.label("Other Cities")
                
    with ui.tab_panel("About"):
        ui.label("About Page")
        ui.markdown("""
            Source code available on [GitHub](https://github.com/dfloer/SC2k-cities)
                    
            Uses [OpenCity2k](https://github.com/OpenCity2k/OpenCity2k) to render city images, which doesn't completely support everything the game does, and doesn't render exactly the same.
            
            Cities sourced from various spots, many are from [ClubOpolis](https://patcoston.com/co/download.aspx)
        """)

dark = ui.dark_mode()
dark.enable()
ui.run(port=8080, show=False)
