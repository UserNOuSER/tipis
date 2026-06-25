import dearpygui.dearpygui as dpg  # ty:ignore[unresolved-import]

class SurgePlot:
    def __init__(self, palette):
        self.palette = palette
        self.tag_plot = "main_plot"
        self.tag_series = "flow_plot"

    def create(self, parent_tag):
        with dpg.plot(label="Газодинамическая характеристика", 
                     height=-1, width=-1, parent=parent_tag, tag=self.tag_plot):
            dpg.add_plot_axis(dpg.mvXAxis, label="Q, отн. ед.", tag="x_axis")
            dpg.add_plot_axis(dpg.mvYAxis, label="H, отн. ед.", tag="y_axis")
            dpg.add_line_series([], [], label="Рабочая точка", 
                               parent="y_axis", tag=self.tag_series)

    def update(self, x_data, y_data):
        try:
            dpg.set_value(self.tag_series, [x_data, y_data])
        except Exception as e:
            print(f"Ошибка обновления графика: {e}")