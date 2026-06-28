import logging
from typing import Optional, Dict, Any
from db.repository import Database

logger = logging.getLogger(__name__)


class AuthController:
    """Контроллер аутентификации и управления сессией"""
    
    def __init__(self):
        self.db = Database()
        self.current_user: Optional[Dict[str, Any]] = None
    
    def login(self, username: str, password: str) -> bool:
        """Пытается авторизовать пользователя"""
        user_data = self.db.authenticate_user(username, password)
        if user_data:
            self.current_user = user_data
            logger.info(f" Пользователь {username} авторизован (роль: {user_data['role']})")
            return True
        return False
    
    def logout(self):
        """Завершает сессию пользователя"""
        if self.current_user:
            logger.info(f" Пользователь {self.current_user['username']} вышел из системы")
        self.current_user = None
    
    def is_authenticated(self) -> bool:
        """Проверяет, авторизован ли пользователь"""
        return self.current_user is not None
    
    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """Возвращает данные текущего пользователя"""
        return self.current_user
    
    def get_username(self) -> str:
        """Возвращает имя текущего пользователя"""
        return self.current_user["username"] if self.current_user else "Гость"
    
    def get_role(self) -> str:
        """Возвращает роль текущего пользователя"""
        return self.current_user["role"] if self.current_user else "GUEST"
    
    def can_access_configurator(self) -> bool:
        """Проверяет, имеет ли пользователь доступ к конфигуратору"""
        if not self.current_user:
            return False
        return self.current_user["role"] in ("ADMIN", "ENGINEER")
    
    def can_edit_rules(self) -> bool:
        """Проверяет, может ли пользователь редактировать правила"""
        if not self.current_user:
            return False
        return self.current_user["role"] == "ENGINEER"