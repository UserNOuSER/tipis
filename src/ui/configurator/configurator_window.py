import dearpygui.dearpygui as dpg  # ty:ignore[unresolved-import]
import sys
from ui.configurator.rules_editor import RulesEditor
from ui.configurator.test_modal import TestModal


class ConfiguratorWindow:
    """Главное окно конфигуратора нечёткой логики"""
    
    def __init__(self, palette, configurator_controller, app_controller=None, event_log_window=None):
        self.palette = palette
        self.controller = configurator_controller
        self._app_controller = app_controller
        self._event_log_window = event_log_window 
        
        self.rules_editor = RulesEditor(palette, configurator_controller)
        self.test_modal = TestModal(palette, configurator_controller)
        
        self.compressors = []
        self.profiles = []
        
        # Состояние выбора
        self.selected_compressor_id = None
        self.selected_profile_id = None
        self.deleting_profile_id = None  
        
        # Размеры
        self.window_width = 1200
        self.window_height = 750
        self.left_panel_width = 280
    
    def create(self):
        """Создаёт окно конфигуратора"""
        with dpg.window(
            label="Конфигуратор (Инженер, Админ)",
            tag="configurator_window",
            show=False,
            width=self.window_width,
            height=self.window_height,
            no_scrollbar=True,
            no_collapse=True
        ):
            # Заголовок
            dpg.add_text("КОНФИГУРАТОР СИСТЕМЫ НЕЧЁТКОГО ВЫВОДА", 
                        color=self.palette.primary + (255,))
            dpg.add_separator()
            dpg.add_spacer(height=8)
            
            # === ОСНОВНАЯ ЧАСТЬ ===
            with dpg.group(horizontal=True):
                
                # ЛЕВАЯ ПАНЕЛЬ: ДВЕ независимые секции со своим скроллом
                with dpg.child_window(
                    width=self.left_panel_width,
                    height=580,
                    tag="left_panel",
                    no_scrollbar=True  # Отключаем общий скролл панели
                ):
                    # ==========================================
                    # СЕКЦИЯ 1: КОМПРЕССОРЫ (верхняя половина)
                    # ==========================================
                    dpg.add_text("КОМПРЕССОРЫ", 
                                color=self.palette.primary + (255,))
                    dpg.add_separator()
                    
                    # Контейнер со скроллом для списка компрессоров
                    with dpg.child_window(
                        height=240,
                        tag="compressors_container",
                        border=False
                    ):
                        dpg.add_group(tag="compressors_list_group")
                    
                    dpg.add_spacer(height=10)
                    
                    # ==========================================
                    # СЕКЦИЯ 2: ПРОФИЛИ (нижняя половина)
                    # ==========================================
                    dpg.add_text("ПРОФИЛИ", 
                                color=self.palette.primary + (255,))
                    dpg.add_separator()
                    
                    # Контейнер со скроллом для списка профилей
                    with dpg.child_window(
                        height=240,
                        tag="profiles_container",
                        border=False
                    ):
                        dpg.add_group(tag="profiles_list_group")
                
                # ПРАВАЯ ЧАСТЬ: База правил
                with dpg.child_window(
                    width=-1,
                    height=580,
                    tag="rules_panel"
                ):
                    # Информация о текущем компрессоре и профиле
                    with dpg.group(horizontal=True):
                        dpg.add_text("Компрессор:", color=self.palette.text_primary + (255,))
                        dpg.add_text("—", tag="current_compressor_text", 
                                    color=self.palette.primary + (255,))
                        dpg.add_spacer(width=20)
                        dpg.add_text("Профиль:", color=self.palette.text_primary + (255,))
                        dpg.add_text("—", tag="current_profile_text", 
                                    color=self.palette.primary + (255,))
                        dpg.add_button(
                            label="[Назначить этот профиль выбранному компрессору]",
                            callback=self._assign_profile_to_compressor,
                            width=400
                        )
                    
                    dpg.add_separator()
                    dpg.add_spacer(height=8)
                    
                    dpg.add_text("База правил нечеткого вывода", 
                                color=self.palette.primary + (255,))
                    dpg.add_spacer(height=5)
                    self.rules_editor.create(parent_tag=dpg.last_container())
            
            dpg.add_spacer(height=10)
            
            # === НИЖНЯЯ ПАНЕЛЬ ===
            with dpg.group(horizontal=True):
                dpg.add_button(label="Добавить профиль", 
                              callback=self._show_add_profile_modal, 
                              width=200, height=50)
                
                dpg.add_spacer(width=300)
                
                dpg.add_button(label="Сохранить в БД", 
                              callback=self._save_to_db, 
                              width=200, height=50)
                dpg.add_spacer(width=15)
                dpg.add_button(label="Тест на истории", 
                              callback=self._run_test, 
                              width=200, height=50)
                dpg.add_spacer(width=15)
                dpg.add_button(label="Добавить правило", 
                              callback=self.rules_editor.show_add_modal, 
                              width=200, height=50)
        
        # Модалки
        self.rules_editor.create_modals()
        self.test_modal.create()
        self._create_add_profile_modal()
        self._create_delete_profile_modal() 
        
        # Загружаем данные
        self._load_compressors()
        self._load_profiles()
    
    # ==========================================
    # Загрузка данных
    # ==========================================
    def _load_compressors(self):
        """Загружает список компрессоров из БД"""
        self.compressors = self.controller.get_all_compressors()
        
        # Очищаем группу
        if dpg.does_item_exist("compressors_list_group"):
            children = dpg.get_item_children("compressors_list_group", slot=1)
            for child in children:
                dpg.delete_item(child)
        
        # Добавляем компрессоры
        for comp in self.compressors:
            with dpg.group(horizontal=True, parent="compressors_list_group"):
                dpg.add_selectable(
                    label=comp["name"],
                    tag=f"comp_{comp['compressor_id']}",
                    default_value=False,
                    callback=self._on_compressor_selected,
                    user_data=comp["compressor_id"],
                    width=150
                )
                # Показываем текущий профиль компрессора
                dpg.add_text(
                    f"[{comp['profile_name']}]",
                    color=self.palette.text_disabled + (255,),
                    tag=f"comp_profile_{comp['compressor_id']}"
                )
        
        # Автоматически выбираем первый компрессор
        if self.compressors:
            first_comp = self.compressors[0]
            self._on_compressor_selected(f"comp_{first_comp['compressor_id']}", None, first_comp['compressor_id'])
    
    def _load_profiles(self):
        """Загружает список профилей из БД"""
        self.profiles = self.controller.get_all_profiles()
        
        # Очищаем группу
        if dpg.does_item_exist("profiles_list_group"):
            children = dpg.get_item_children("profiles_list_group", slot=1)
            for child in children:
                dpg.delete_item(child)
        
        # Добавляем профили
        for profile in self.profiles:
            with dpg.group(horizontal=True, parent="profiles_list_group"):
                dpg.add_selectable(
                    label=profile["name"],
                    tag=f"profile_{profile['profile_id']}",
                    default_value=False,
                    callback=self._on_profile_selected,
                    user_data=profile["profile_id"],
                    width=180
                )
                #  КНОПКА УДАЛЕНИЯ
                dpg.add_button(
                    label="[X]",
                    callback=self._show_delete_profile_modal,
                    user_data=profile,
                    width=30, height=22
                )
    
    # ==========================================
    # Обработчики выбора
    # ==========================================
    def _on_compressor_selected(self, sender, app_data, user_data):
        """Обработчик выбора компрессора"""
        comp_id = user_data
        
        # Снимаем выделение со всех
        for comp in self.compressors:
            if dpg.does_item_exist(f"comp_{comp['compressor_id']}"):
                dpg.set_value(f"comp_{comp['compressor_id']}", False)
        
        # Выделяем выбранный
        dpg.set_value(sender, True)
        
        if self.controller.select_compressor(comp_id):
            self.selected_compressor_id = comp_id
            self.rules_editor.refresh()
            self._update_info_labels()
            self._highlight_current_profile()
            
            #  Уведомляем AppController о смене компрессора
            if self._app_controller:
                self._app_controller.set_current_compressor(comp_id)
            
            #  Уведомляем журнал событий о смене компрессора
            if self._event_log_window:
                self._event_log_window.set_compressor(comp_id)
            
            print(f" Выбран компрессор: {self.controller.current_compressor_name} "
                  f"(профиль: {self.controller.current_profile_name})", file=sys.stderr)

    def _on_profile_selected(self, sender, app_data, user_data):
        """Обработчик выбора профиля из списка"""
        profile_id = user_data
        
        # Снимаем выделение со всех профилей
        for profile in self.profiles:
            if dpg.does_item_exist(f"profile_{profile['profile_id']}"):
                dpg.set_value(f"profile_{profile['profile_id']}", False)
        
        # Выделяем выбранный
        dpg.set_value(sender, True)
        self.selected_profile_id = profile_id
        
        # Загружаем профиль напрямую (без привязки к компрессору)
        if self.controller._load_profile(profile_id):
            self.rules_editor.refresh()
            self._update_info_labels()
            print(f" Выбран профиль: {self.controller.current_profile_name}", file=sys.stderr)
    
    def _highlight_current_profile(self):
        """Подсвечивает текущий профиль в списке"""
        # Снимаем выделение со всех
        for profile in self.profiles:
            if dpg.does_item_exist(f"profile_{profile['profile_id']}"):
                dpg.set_value(f"profile_{profile['profile_id']}", False)
        
        # Выделяем текущий
        if self.selected_profile_id and dpg.does_item_exist(f"profile_{self.selected_profile_id}"):
            dpg.set_value(f"profile_{self.selected_profile_id}", True)
    
    def _update_info_labels(self):
        """Обновляет текстовые метки"""
        info = self.controller.get_current_info()
        
        if dpg.does_item_exist("current_compressor_text"):
            dpg.set_value("current_compressor_text", info["compressor_name"] or "—")
        if dpg.does_item_exist("current_profile_text"):
            dpg.set_value("current_profile_text", info["profile_name"] or "—")
    
    # ==========================================
    # Назначение профиля компрессору
    # ==========================================
    def _assign_profile_to_compressor(self, sender=None, app_data=None):
        """Назначает текущий выбранный профиль выбранному компрессору"""
        if self.selected_compressor_id is None:
            print("Select a compressor", file=sys.stderr)
            return
        
        if self.selected_profile_id is None:
            print("Select a profile", file=sys.stderr)
            return
        
        # Проверяем, не тот ли это уже профиль
        comp = next((c for c in self.compressors if c["compressor_id"] == self.selected_compressor_id), None)
        if comp and comp["profile_id"] == self.selected_profile_id:
            print("This profile is already assigned to the compressor", file=sys.stderr)
            return
        
        if self.controller.assign_profile(self.selected_compressor_id, self.selected_profile_id):
            profile_name = next((p["name"] for p in self.profiles if p["profile_id"] == self.selected_profile_id), "?")
            comp_name = comp["name"] if comp else "?"
            print(f" Компрессору {comp_name} назначен профиль '{profile_name}'", file=sys.stderr)
            
            # Обновляем список компрессоров (чтобы отобразить новый профиль)
            self._load_compressors()
            self._update_info_labels()
        else:
            print(" Ошибка назначения профиля", file=sys.stderr)
    
    # ==========================================
    # Действия
    # ==========================================
    def _save_to_db(self, sender=None, app_data=None):
        """Сохраняет правила текущего профиля в БД"""
        if self.controller.current_profile_id is None:
            print("Profile not selected", file=sys.stderr)
            return
        
        try:
            rules = self.rules_editor.get_rules()
            if self.controller.save_rules(rules):
                print(f" Правила сохранены в профиль '{self.controller.current_profile_name}'", 
                      file=sys.stderr)
                self.rules_editor.refresh()
            else:
                print(" Ошибка сохранения правил", file=sys.stderr)
        except Exception as e:
            print(f" Ошибка: {e}", file=sys.stderr)
    
    def _run_test(self, sender=None, app_data=None):
        """Запускает тест на истории ВЫБРАННОГО компрессора"""
        if self.controller.current_compressor_id is None:
            print("Compressor not selected", file=sys.stderr)
            return
        
        try:
            results = self.controller.run_test_on_history(events_count=50)
            self.test_modal.show_results(results)
        except Exception as e:
            print(f" Ошибка тестирования: {e}", file=sys.stderr)
    
    # ==========================================
    # Модалка добавления профиля
    # ==========================================
    def _create_add_profile_modal(self):
        """Создаёт модалку добавления нового профиля"""
        with dpg.window(
            label="Добавить профиль",
            tag="add_profile_modal",
            show=False,
            modal=True,
            no_move=True,
            width=450,
            height=250
        ):
            dpg.add_text("Имя профиля:")
            dpg.add_input_text(tag="new_profile_name", width=-1, hint="Например: Агрессивный")
            
            dpg.add_spacer(height=10)
            dpg.add_text("Описание:")
            dpg.add_input_text(tag="new_profile_description", width=-1, multiline=True, height=80)
            
            dpg.add_spacer(height=15)
            with dpg.group(horizontal=True):
                dpg.add_button(label="[OK] Создать", callback=self._create_profile, width=180)
                dpg.add_button(label="[X] Отмена", 
                              callback=lambda: dpg.configure_item("add_profile_modal", show=False), 
                              width=180)
    
    def _show_add_profile_modal(self, sender=None, app_data=None):
        """Показывает модалку добавления профиля"""
        dpg.set_value("new_profile_name", "")
        dpg.set_value("new_profile_description", "")
        dpg.configure_item("add_profile_modal", show=True)
    
    def _create_profile(self, sender=None, app_data=None):
        """Создаёт новый профиль"""
        name = dpg.get_value("new_profile_name").strip()
        description = dpg.get_value("new_profile_description").strip()
        
        if not name:
            print("Имя профиля не может быть пустым", file=sys.stderr)
            return
        
        # Создаём профиль с дефолтными переменными
        default_input = {"margin": ["Low", "Mid", "High"], "dQdt": ["Neg", "Zero", "Pos"]}
        default_output = {"valve": ["Close", "Open_25", "Open_50", "Open_75", "Open_100"]}
        
        profile_id = self.controller.db.create_profile(
            name=name,
            description=description,
            input_vars=default_input,
            output_vars=default_output
        )
        
        if profile_id:
            print(f" Профиль '{name}' создан (ID={profile_id})", file=sys.stderr)
            dpg.configure_item("add_profile_modal", show=False)
            self._load_profiles()
        else:
            print(" Ошибка создания профиля", file=sys.stderr)

    # ==========================================
    # Модалка удаления профиля
    # ==========================================
    def _create_delete_profile_modal(self):
        """Создаёт модалку подтверждения удаления профиля"""
        with dpg.window(
            label="Подтверждение удаления профиля",
            tag="delete_profile_modal",
            show=False,
            modal=True,
            no_move=True,
            width=500,
            height=200
        ):
            dpg.add_text("Вы уверены, что хотите удалить профиль?", 
                        color=self.palette.error + (255,))
            dpg.add_spacer(height=10)
            dpg.add_text("Профиль:", color=self.palette.text_primary + (255,))
            dpg.add_text("", tag="delete_profile_preview", 
                        color=self.palette.primary + (255,))
            dpg.add_spacer(height=5)
            dpg.add_text("", tag="delete_profile_warning", 
                        color=self.palette.warning + (255,))
            
            dpg.add_spacer(height=15)
            with dpg.group(horizontal=True):
                dpg.add_button(label="[Удалить]", callback=self._confirm_delete_profile, width=180)
                dpg.add_button(label="[X] Отмена", 
                              callback=lambda: dpg.configure_item("delete_profile_modal", show=False), 
                              width=180)
    
    def _show_delete_profile_modal(self, sender, app_data, user_data):
        """Показывает модалку удаления профиля"""
        profile = user_data
        if profile is None:
            return
        
        self.deleting_profile_id = profile["profile_id"]
        
        dpg.set_value("delete_profile_preview", profile["name"])
        
        # Предупреждение: если профиль назначен компрессорам
        linked = [c for c in self.compressors if c["profile_id"] == profile["profile_id"]]
        if linked:
            names = ", ".join([c["name"] for c in linked])
            dpg.set_value("delete_profile_warning", 
                         f"Внимание: профиль назначен компрессорам: {names}")
        else:
            dpg.set_value("delete_profile_warning", "")
        
        dpg.configure_item("delete_profile_modal", show=True)
    
    def _confirm_delete_profile(self, sender=None, app_data=None):
        """Подтверждает удаление профиля"""
        if self.deleting_profile_id is None:
            return
        
        success, message = self.controller.db.delete_profile(self.deleting_profile_id)
        
        if success:
            print(f" {message}", file=sys.stderr)
            
            # Если удалили текущий профиль — сбрасываем состояние
            if self.deleting_profile_id == self.selected_profile_id:
                self.selected_profile_id = None
            
            # Перезагружаем списки
            self._load_profiles()
            self._load_compressors()
        else:
            print(f" {message}", file=sys.stderr)
        
        self.deleting_profile_id = None
        dpg.configure_item("delete_profile_modal", show=False)
    
    def show(self):
        """Показывает окно конфигуратора"""
        self._load_compressors()
        self._load_profiles()
        dpg.configure_item("configurator_window", show=True)