# ui/surge_plot.py
import dearpygui.dearpygui as dpg  # ty:ignore[unresolved-import]
from db.repository import Database
import logging

logger = logging.getLogger(__name__)


class SurgePlot:
    """График газодинамических характеристик (ГДХ) с рабочей точкой"""
    
    def __init__(self, palette):
        self.palette = palette
        self.db = Database()
        
        self.gdx_curves = {}
        self.surge_line = {'x': [], 'y': []}
        self.operating_point = {'x': [0], 'y': [0]}
        
    def create(self, parent_tag):
        """Создаёт график ГДХ"""
        self._load_gdx_data()
        
        with dpg.plot(
            label="ГДХ компрессора",
            width=-1,
            height=-1,
            tag="gdx_plot",
            parent=parent_tag,
            no_title=True,
            no_menus=True
        ):
            dpg.add_plot_axis(dpg.mvXAxis, label="Расход Q, кг/с", tag="gdx_x_axis")
            dpg.add_plot_axis(dpg.mvYAxis, label="Напор H, кПа", tag="gdx_y_axis")
            
            # Кривые ГДХ
            colors = [(14, 165, 233), (16, 185, 129), (245, 158, 11), (239, 68, 68)]
            for idx, (rpm, data) in enumerate(self.gdx_curves.items()):
                color = colors[idx % len(colors)]
                
                dpg.add_line_series(
                    data['x'],
                    data['y'],
                    label=f"{rpm} об/мин",
                    parent="gdx_y_axis",
                    tag=f"gdx_curve_{rpm}"
                )
                
                with dpg.theme() as curve_theme:
                    with dpg.theme_component(dpg.mvLineSeries):
                        dpg.add_theme_color(dpg.mvPlotCol_Line, color + (255,))
                dpg.bind_item_theme(f"gdx_curve_{rpm}", curve_theme)
            
            # Линия помпажа
            if self.surge_line['x']:
                dpg.add_line_series(
                    self.surge_line['x'],
                    self.surge_line['y'],
                    label="Линия помпажа",
                    parent="gdx_y_axis",
                    tag="surge_line"
                )
                with dpg.theme() as surge_theme:
                    with dpg.theme_component(dpg.mvLineSeries):
                        dpg.add_theme_color(dpg.mvPlotCol_Line, (239, 68, 68, 255))
                dpg.bind_item_theme("surge_line", surge_theme)
            
            # Рабочая точка
            dpg.add_scatter_series(
                self.operating_point['x'],
                self.operating_point['y'],
                label="Рабочая точка",
                parent="gdx_y_axis",
                tag="operating_point"
            )
            with dpg.theme() as point_theme:
                with dpg.theme_component(dpg.mvScatterSeries):
                    dpg.add_theme_color(dpg.mvPlotCol_Line, (255, 255, 0, 255))
                    dpg.add_theme_color(dpg.mvPlotCol_Fill, (255, 255, 0, 255))
            dpg.bind_item_theme("operating_point", point_theme)
        
        #  УСТАНАВЛИВАЕМ НАЧАЛЬНЫЕ ГРАНИЦЫ (один раз при создании)
        dpg.set_axis_limits("gdx_x_axis", 0, 200)
        dpg.set_axis_limits("gdx_y_axis", 0, 10000)
        
        logger.info(f" График ГДХ создан: {len(self.gdx_curves)} кривых")
    
    def _load_gdx_data(self):
        """Загружает данные ГДХ из БД"""
        try:
            points = self.db.get_gdx_points(compressor_id=1)
            
            if not points:
                logger.warning("No GDX points in database! Run db/seed_gdx.py")
                return
            
            for point in points:
                rpm = point['rpm']
                if rpm not in self.gdx_curves:
                    self.gdx_curves[rpm] = {'x': [], 'y': []}
                self.gdx_curves[rpm]['x'].append(point['q'])
                self.gdx_curves[rpm]['y'].append(point['h'])
            
            surge_points = self.db.get_surge_boundary(compressor_id=1)
            for point in surge_points:
                self.surge_line['x'].append(point['q_surge'])
                self.surge_line['y'].append(point['h_surge'])
            
            logger.info(f" Загружено {len(points)} точек ГДХ и {len(surge_points)} точек помпажа")
        except Exception as e:
            logger.error(f" Ошибка загрузки данных ГДХ: {e}")
    
    def update_operating_point(self, q: float, h: float):
        """Обновляет позицию рабочей точки"""
        try:
            #  ЛОГИРОВАНИЕ для отладки
            logger.debug(f" Обновление точки: Q={q:.1f}, H={h:.1f}")
            
            if dpg.does_item_exist("operating_point"):
                self.operating_point['x'] = [q]  # ty:ignore[invalid-assignment]
                self.operating_point['y'] = [h]  # ty:ignore[invalid-assignment]
                dpg.set_value("operating_point", [self.operating_point['x'], self.operating_point['y']])
            else:
                logger.warning(" operating_point не существует!")
        except Exception as e:
            logger.error(f"Ошибка обновления рабочей точки: {e}")