from attrs import define, Factory, field

from uuid import UUID

from nicegui import ui

from models import CityModel

from loguru import logger

from opencity2k.Data.value_mappings import disaster_type, weather_type

@define
class CityView:
    model: CityModel

    @ui.refreshable
    def city_info(self):
        with ui.column() as ui_info:
            img = self.model.city_image
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
                {"name": "nat_pop", "label": "Nat'iona'l Pop", "field": "nat_pop"},
                {"name": "nat_val", "label": "Nat'l Val", "field": "nat_val"},
                {"name": "disaster", "label": "Disaster", "field": "disaster"},
                {"name": "unemployment", "label": "Unemployment", "field": "unemployment"},
            ]

            d = self.model.db_data
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
            t_img = self.model.city_thumb_image
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
            d = self.model.db_data
            for x in stats:
                rows += [{x: getattr(d, x)}]
            t = ui.table(columns=cols, rows=rows)
        return e, i, t