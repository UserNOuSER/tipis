import dearpygui.dearpygui as dpg  # ty:ignore[unresolved-import]
from db.repository import Database
import logging

logger = logging.getLogger(__name__)


class SurgePlot:
    """График газодинамических характеристик (ГДХ) с рабочей точкой"""
    
    def __init__(self, palette):
        self.palette = palette
        self.db = Database()
        
        # Данные для графика
        self.gdx_curves = {}  # {rpm: {'x': [...], 'y': [...]}}
        self.surge_line = {'x': [], 'y': []}
        self.operating_point = {'x': [0], 'y': [0]}
        
    def create(self, parent_tag):
        """Создаёт график ГДХ"""
        # Загружаем данные из БД
        self._load_gdx_data()
        
        # Создаём plot
        with dpg.plot(
            label="ГДХ компрессора",
            width=-1,
            height=-1,
            tag="gdx_plot",
            parent=parent_tag,
            no_title=True,
            no_menus=True
        ):
            # Оси
            dpg.add_plot_axis(dpg.mvXAxis, label="Расход Q, кг/с", tag="gdx_x_axis")
            dpg.add_plot_axis(dpg.mvYAxis, label="Напор H, кПа", tag="gdx_y_axis")
            
            # Рисуем кривые ГДХ для разных оборотов
            colors = [(14, 165, 233), (16, 185, 129), (245, 158, 11), (239, 68, 68)]
            for idx, (rpm, data) in enumerate(self.gdx_curves.items()):
                color = colors[idx % len(colors)]
                
                # Добавляем линию
                dpg.add_line_series(
                    data['x'],
                    data['y'],
                    label=f"{rpm} об/мин",
                    parent="gdx_y_axis",
                    tag=f"gdx_curve_{rpm}"
                )
                
                # ✅ ПРАВИЛЬНОЕ ПРИМЕНЕНИЕ ТЕМЫ
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
                # ✅ ПРАВИЛЬНОЕ ПРИМЕНЕНИЕ ТЕМЫ
                with dpg.theme() as surge_theme:
                    with dpg.theme_component(dpg.mvLineSeries):
                        dpg.add_theme_color(dpg.mvPlotCol_Line, (239, 68, 68, 255))
                dpg.bind_item_theme("surge_line", surge_theme)
            
            # Рабочая точка (обновляется в реальном времени)
            dpg.add_scatter_series(
                self.operating_point['x'],
                self.operating_point['y'],
                label="Рабочая точка",
                parent="gdx_y_axis",
                tag="operating_point"
            )
            # ✅ ПРАВИЛЬНОЕ ПРИМЕНЕНИЕ ТЕМЫ
            with dpg.theme() as point_theme:
                with dpg.theme_component(dpg.mvScatterSeries):
                    dpg.add_theme_color(dpg.mvPlotCol_Line, (255, 255, 0, 255))
                    dpg.add_theme_color(dpg.mvPlotCol_Fill, (255, 255, 0, 255))
            dpg.bind_item_theme("operating_point", point_theme)
        
        logger.info(f"✅ График ГДХ создан: {len(self.gdx_curves)} кривых")
    
    def _load_gdx_data(self):
        """Загружает данные ГДХ из БД"""
        try:
            # Загружаем точки ГДХ
            points = self.db.get_gdx_points(compressor_id=1)
            
            # Группируем по RPM
            for point in points:
                rpm = point['rpm']
                if rpm not in self.gdx_curves:
                    self.gdx_curves[rpm] = {'x': [], 'y': []}
                self.gdx_curves[rpm]['x'].append(point['q'])
                self.gdx_curves[rpm]['y'].append(point['h'])
            
            # Загружаем линию помпажа
            surge_points = self.db.get_surge_boundary(compressor_id=1)
            for point in surge_points:
                self.surge_line['x'].append(point['q_surge'])
                self.surge_line['y'].append(point['h_surge'])
            
            logger.info(f"📈 Загружено {len(points)} точек ГДХ и {len(surge_points)} точек помпажа")
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки данных ГДХ: {e}")
    
    def update_operating_point(self, q: float, h: float):
        """Обновляет позицию рабочей точки"""
        try:
            if dpg.does_item_exist("operating_point"):
                self.operating_point['x'] = [q]  # ty:ignore[invalid-assignment]
                self.operating_point['y'] = [h]  # ty:ignore[invalid-assignment]
                dpg.set_value("operating_point", [self.operating_point['x'], self.operating_point['y']])
        except Exception as e:
            logger.error(f"Ошибка обновления рабочей точки: {e}")