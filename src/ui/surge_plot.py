import dearpygui.dearpygui as dpg  # ty:ignore[unresolved-import]

class SurgePlot:
    def __init__(self, palette):
        self.palette = palette

    def create(self, parent_tag):
        # ВАЖНО: используем parent=parent_tag, а не dpg.last_container()
        with dpg.plot(label="", height=-1, width=-1, parent=parent_tag):
            dpg.add_plot_axis(dpg.mvXAxis, label="Q, кг/с", tag="x_axis_flow")
            dpg.add_plot_axis(dpg.mvYAxis, label="H, кПа", tag="y_axis_flow")
            dpg.add_line_series([], [], label="Траектория", parent="y_axis_flow", tag="flow_plot")

    def update(self, x_data, y_data):
        try:
            dpg.set_value("flow_plot", [x_data, y_data])
        except Exception as e:
            print(f"Ошибка обновления графика: {e}")