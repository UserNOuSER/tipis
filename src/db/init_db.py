import json
from sqlalchemy import create_engine, event  # ty:ignore[unresolved-import]
from sqlalchemy.orm import sessionmaker # ty:ignore[unresolved-import]
from db.models import Base, UserRole, User, Credential, RoleCredential, Compressor, GasComposition, FuzzyConfig, FuzzyRule

# Путь к локальной SQLite базе (для прототипа)
DB_URL = "sqlite:///anti_surge_prototype.db"

def initialize_database():
    """Создает таблицы и заполняет их демо-данными"""
    print("🔌 Подключение к базе данных...")
    engine = create_engine(DB_URL, echo=False)
    
    # Включаем поддержку Foreign Keys для SQLite
    event.listen(engine, "connect", lambda dbapi_conn, connection_record: dbapi_conn.execute("PRAGMA foreign_keys=ON"))

    print("🏗️ Создание таблиц (если их нет)...")
    Base.metadata.create_all(engine)
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Проверяем, не инициализирована ли БД уже
        if session.query(UserRole).count() == 0:
            print("🌱 Заполнение демо-данными...")
            
            # 1. Роли и Права
            op_role = UserRole(RoleName="OPERATOR")
            eng_role = UserRole(RoleName="ENGINEER")
            admin_role = UserRole(RoleName="ADMIN")
            session.add_all([op_role, eng_role, admin_role])
            session.flush() # Чтобы получить ID
            
            view_cred = Credential(CredentialName="view_dashboard")
            edit_cred = Credential(CredentialName="edit_rules")
            session.add_all([view_cred, edit_cred])
            session.flush()
            
            session.add_all([
                RoleCredential(RoleID=op_role.RoleID, CredentialID=view_cred.CredentialID, Allowed=True),
                RoleCredential(RoleID=eng_role.RoleID, CredentialID=view_cred.CredentialID, Allowed=True),
                RoleCredential(RoleID=eng_role.RoleID, CredentialID=edit_cred.CredentialID, Allowed=True),
                RoleCredential(RoleID=admin_role.RoleID, CredentialID=view_cred.CredentialID, Allowed=True),
                RoleCredential(RoleID=admin_role.RoleID, CredentialID=edit_cred.CredentialID, Allowed=True)
            ])
            
            # 2. Пользователи
            session.add_all([
                User(Name="Иванов Операторов", RoleID=op_role.RoleID),
                User(Name="Петров Инженеров", RoleID=eng_role.RoleID),
                User(Name="Сидоров Админов", RoleID=admin_role.RoleID)
            ])
            
            # 3. Компрессор и Газ
            comp = Compressor(Model="CC-45X", NominalPower=5000.0, MaxTempDischarge=120.0)
            session.add(comp)
            session.flush()
            
            gas = GasComposition(CH4=90.0, C2H6=5.0, C3H8=2.0, CO2=1.5, H2S=0.1, H2O=0.4, N2=1.0)
            session.add(gas)
            session.flush()
            
            # 4. Нечеткая логика (Правила)
            cfg = FuzzyConfig(
                ConfigID=1, 
                Version="1.0.0",
                InputVars=json.dumps({"margin": ["Low", "Mid", "High"], "dQdt": ["Neg", "Zero", "Pos"]}),
                OutputVars=json.dumps({"valve": ["Close", "Open_50", "Open_100"]}),
                MembershipParams="triangular"
            )
            session.add(cfg)
            session.flush()
            
            rules = [
                FuzzyRule(AntecedentKey="IF margin=Low AND dQdt=Neg", Consequent="THEN valve=Open_100", Weight=1.0, Priority=1.0, ConfigID=1, Version="1.0.0"),
                FuzzyRule(AntecedentKey="IF margin=Mid AND dQdt=Zero", Consequent="THEN valve=Open_50", Weight=0.8, Priority=2.0, ConfigID=1, Version="1.0.0"),
                FuzzyRule(AntecedentKey="IF margin=High", Consequent="THEN valve=Close", Weight=1.0, Priority=3.0, ConfigID=1, Version="1.0.0")
            ]
            session.add_all(rules)
            
            session.commit()
            print("✅ База данных успешно инициализирована и заполнена демо-данными!")
        else:
            print("ℹ️ База данных уже содержит данные. Пропуск инициализации.")
            
    except Exception as e:
        session.rollback()
        print(f"❌ Критическая ошибка инициализации БД: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    initialize_database()