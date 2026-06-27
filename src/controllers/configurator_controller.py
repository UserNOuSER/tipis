import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from simpful import FuzzySystem, AutoTriangle  # ty:ignore[unresolved-import]
from db.repository import Database

logger = logging.getLogger(__name__)


class ConfiguratorController:
    """
    Контроллер конфигуратора нечёткой логики.
    Работает с профилями правил и компрессорами.
    """
    
    def __init__(self):
        self.db = Database()
        
        # Текущий выбранный компрессор и его профиль
        self.current_compressor_id = None
        self.current_profile_id = None
        self.current_compressor_name = None
        self.current_profile_name = None
        
        # Локальный FuzzySystem для тестирования
        self.test_fs = None
        
        # Кэш текущей конфигурации
        self._current_config = None
        self._current_rules = []
    
    # ==========================================
    # Работа с компрессорами
    # ==========================================
    def get_all_compressors(self) -> List[Dict]:
        """Получает список всех компрессоров с их профилями"""
        return self.db.get_all_compressors()
    
    def select_compressor(self, compressor_id: int) -> bool:
        """
        Выбирает компрессор и загружает его профиль.
        Возвращает True, если успешно.
        """
        # 1. Получаем данные компрессора
        comp_data = self.db.get_compressor(compressor_id)
        if not comp_data:
            logger.error(f"Компрессор {compressor_id} не найден")
            return False
        
        self.current_compressor_id = compressor_id
        self.current_compressor_name = comp_data["name"]
        self.current_profile_id = comp_data["profile_id"]
        self.current_profile_name = comp_data.get("profile_name", f"Профиль #{self.current_profile_id}")
        
        logger.info(f"🔧 Выбран компрессор: {self.current_compressor_name} (профиль: {self.current_profile_name})")
        
        # 2. Загружаем профиль
        return self._load_profile(self.current_profile_id)
    
    def assign_profile(self, compressor_id: int, profile_id: int) -> bool:
        """Назначает профиль компрессору"""
        if self.db.assign_profile_to_compressor(compressor_id, profile_id):
            # Если это текущий компрессор — обновляем кэш
            if compressor_id == self.current_compressor_id:
                self.current_profile_id = profile_id
                self._load_profile(profile_id)
            return True
        return False
    
    # ==========================================
    # Работа с профилями
    # ==========================================
    def get_all_profiles(self) -> List[Dict]:
        """Получает список всех профилей"""
        return self.db.get_all_profiles()
    
    def _load_profile(self, profile_id: int) -> bool:
        """Загружает профиль из БД"""
        config = self.db.load_profile_config(profile_id)
        if not config:
            logger.error(f"Профиль {profile_id} не найден")
            return False
        
        self._current_config = config
        self._current_rules = config.get("rules", [])
        self.current_profile_name = config.get("name", f"Профиль #{profile_id}")
        
        self._rebuild_fuzzy_system()
        return True
    
    # ==========================================
    # Перестройка FuzzySystem
    # ==========================================
    def _rebuild_fuzzy_system(self):
        """Перестраивает FuzzySystem из simpful на основе текущего профиля"""
        if not self._current_config:
            return
        
        try:
            self.test_fs = FuzzySystem(show_banner=False)
            
            # Нормализуем переменные
            input_vars = self._normalize_vars(self._current_config.get("input_vars", {}))
            output_vars = self._normalize_vars(self._current_config.get("output_vars", {}))
            
            logger.info(f"📊 Переменные: input={list(input_vars.keys())}, output={list(output_vars.keys())}")
            
            # Создаём лингвистические переменные
            for var_name, var_info in {**input_vars, **output_vars}.items():
                universe = var_info.get("universe", [0, 100])
                terms = var_info.get("terms", [])
                
                if not terms:
                    logger.warning(f"⚠️ У переменной {var_name} нет термов — пропускаем")
                    continue
                
                lv = AutoTriangle(
                    n_sets=len(terms),
                    terms=terms,
                    universe_of_discourse=universe
                )
                self.test_fs.add_linguistic_variable(var_name, lv)
            
            # Добавляем правила с нормализацией
            rules_added = 0
            for rule in self._current_rules:
                antecedent = rule.get("antecedent", "")
                consequent = rule.get("consequent", "")
                
                if not antecedent or not consequent:
                    continue
                
                norm_antecedent = self._normalize_rule_part(antecedent, strip_prefix="IF")
                norm_consequent = self._normalize_rule_part(consequent, strip_prefix="THEN")
                
                if norm_antecedent and norm_consequent:
                    rule_str = f"IF ({norm_antecedent}) THEN ({norm_consequent})"
                    try:
                        self.test_fs.add_rules([rule_str])
                        rules_added += 1
                    except Exception as e:
                        logger.warning(f"⚠️ Пропущено правило: {rule_str} (ошибка: {e})")
            
            logger.info(f"✅ FuzzySystem перестроен: {rules_added} из {len(self._current_rules)} правил")
        except Exception as e:
            logger.error(f"❌ Ошибка перестройки FuzzySystem: {e}")
            import traceback
            traceback.print_exc()
            self.test_fs = None
    
    def _normalize_vars(self, vars_data) -> dict:
        """Нормализует данные переменных к единому формату словаря"""
        if isinstance(vars_data, dict):
            result = {}
            for key, value in vars_data.items():
                if isinstance(value, dict):
                    result[key] = value
                elif isinstance(value, list):
                    if all(isinstance(item, str) for item in value):
                        result[key] = {"terms": value, "universe": [0, 100]}
                    else:
                        result[key] = {"terms": [], "universe": [0, 100]}
                elif isinstance(value, str):
                    result[key] = {"terms": [value], "universe": [0, 100]}
                else:
                    result[key] = {"terms": [], "universe": [0, 100]}
            return result
        
        if isinstance(vars_data, list):
            result = {}
            for item in vars_data:
                if isinstance(item, dict):
                    name = item.get("name") or item.get("var_name")
                    if name:
                        result[name] = {
                            "terms": item.get("terms", []),
                            "universe": item.get("universe", [0, 100])
                        }
                elif isinstance(item, str):
                    result[item] = {"terms": [], "universe": [0, 100]}
            return result
        
        return {}
    
    def _normalize_rule_part(self, text: str, strip_prefix: str = "") -> str:
        """Нормализует часть правила (antecedent или consequent)"""
        if not text or not isinstance(text, str):
            return ""
        
        text = text.strip()
        
        # Убираем префикс IF/THEN
        if strip_prefix:
            upper_text = text.upper()
            if upper_text.startswith(strip_prefix.upper() + " "):
                text = text[len(strip_prefix) + 1:].strip()
            elif upper_text.startswith(strip_prefix.upper()):
                text = text[len(strip_prefix):].strip()
        
        # Если уже есть IS — формат правильный
        if " IS " in text.upper():
            return text
        
        # Преобразуем "var=value" в "(var IS value)"
        import re
        pattern = r'(\w+)\s*=\s*([A-Za-z0-9_А-Яа-яёЁ]+)'
        
        def replace_match(match):
            var_name = match.group(1)
            term_name = match.group(2)
            return f"({var_name} IS {term_name})"
        
        normalized = re.sub(pattern, replace_match, text)
        
        if normalized == text:
            logger.warning(f"⚠️ Не удалось преобразовать: {text}")
            return ""
        
        return normalized
    
    # ==========================================
    # Сохранение изменений
    # ==========================================
    def save_rules(self, rules: List[Dict]) -> bool:
        """Сохраняет правила в текущий профиль"""
        if self.current_profile_id is None:
            logger.error("Профиль не выбран")
            return False
        
        try:
            success = self.db.update_profile(
                profile_id=self.current_profile_id,
                input_vars=self._current_config.get("input_vars", {}),  # ty:ignore[unresolved-attribute]
                output_vars=self._current_config.get("output_vars", {}),  # ty:ignore[unresolved-attribute]
                membership_params=self._current_config.get("membership_params", {}),  # ty:ignore[unresolved-attribute]
                rules=rules,
                updated_by="system"  # TODO: передать реального пользователя
            )
            
            if success:
                self._current_rules = rules
                self._rebuild_fuzzy_system()
            
            return success
        except Exception as e:
            logger.error(f"Ошибка сохранения правил: {e}")
            return False
    
    def save_membership_params(self, membership_params: Dict) -> bool:
        """Сохраняет параметры функций принадлежности в текущий профиль"""
        if self.current_profile_id is None:
            return False
        
        try:
            success = self.db.update_profile(
                profile_id=self.current_profile_id,
                input_vars=self._current_config.get("input_vars", {}),  # ty:ignore[unresolved-attribute]
                output_vars=self._current_config.get("output_vars", {}),  # ty:ignore[unresolved-attribute]
                membership_params=membership_params,
                rules=self._current_rules,
                updated_by="system"
            )
            
            if success:
                self._current_config["membership_params"] = membership_params  # ty:ignore[invalid-assignment]
                self._rebuild_fuzzy_system()
            
            return success
        except Exception as e:
            logger.error(f"Ошибка сохранения ФП: {e}")
            return False
    
    # ==========================================
    # Тестирование на исторических данных
    # ==========================================
    def run_test_on_history(self, events_count: int = 50) -> List[Dict]:
        """
        Прогоняет последние N событий ВЫБРАННОГО компрессора через текущий профиль.
        """
        if not self.test_fs:
            logger.error("FuzzySystem не инициализирован")
            return []
        
        if self.current_compressor_id is None:
            logger.error("Компрессор не выбран")
            return []
        
        try:
            # ✅ Загружаем события именно этого компрессора
            events = self.db.get_event_log(
                compressor_id=self.current_compressor_id,
                limit=events_count
            )
            
            if not events:
                logger.warning(f"Нет событий для компрессора {self.current_compressor_name}")
                return []
            
            results = []
            for event in events:
                try:
                    self.test_fs.set_variable("margin", event.get("margin", 0))
                    self.test_fs.set_variable("dqdt", event.get("dqdt", 0))
                    
                    output = self.test_fs.Mamdani_inference(["valve"])
                    new_valve = output.get("valve", 0)
                    
                    margin = event.get("margin", 0)
                    if margin < 5:
                        new_status = "SURGE"
                    elif margin < 10:
                        new_status = "WARNING"
                    else:
                        new_status = "NORMAL"
                    
                    results.append({
                        "timestamp": event["timestamp"],
                        "margin": margin,
                        "dqdt": event.get("dqdt", 0),
                        "old_valve": event.get("valve_position", 0),
                        "new_valve": new_valve,
                        "old_status": "SURGE" if event.get("status") else "NORMAL",
                        "new_status": new_status,
                        "valve_diff": new_valve - event.get("valve_position", 0)
                    })
                except Exception as e:
                    logger.warning(f"Ошибка обработки события: {e}")
                    continue
            
            logger.info(f"✅ Тест для {self.current_compressor_name}: {len(results)} событий")
            return results
        except Exception as e:
            logger.error(f"Ошибка тестирования: {e}")
            return []
    
    # ==========================================
    # Геттеры для UI
    # ==========================================
    def get_current_rules(self) -> List[Dict]:
        return self._current_rules
    
    def get_current_membership_params(self) -> Dict:
        if not self._current_config:
            return {}
        return self._current_config.get("membership_params", {})
    
    def get_variables_info(self) -> Dict:
        if not self._current_config:
            return {}
        input_vars = self._current_config.get("input_vars", {})
        output_vars = self._current_config.get("output_vars", {})
        return {**input_vars, **output_vars}
    
    def get_current_info(self) -> Dict:
        """Возвращает информацию о текущем компрессоре и профиле"""
        return {
            "compressor_id": self.current_compressor_id,
            "compressor_name": self.current_compressor_name,
            "profile_id": self.current_profile_id,
            "profile_name": self.current_profile_name,
        }