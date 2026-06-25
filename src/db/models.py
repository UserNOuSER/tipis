from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, ForeignKeyConstraint, Text, DateTime, JSON, event
from sqlalchemy.orm import relationship, declarative_base  # ty:ignore[unresolved-import]
from sqlalchemy.dialects.postgresql import JSONB, ARRAY  # ty:ignore[unresolved-import]
from datetime import datetime

Base = declarative_base()

# --- Включение внешних ключей для SQLite ---
# Это критично, так как в SQLite FK по умолчанию отключены
def set_sqlite_pragma(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

# --- 1. Управление доступом ---
class UserRole(Base):
    __tablename__ = 'UserRole'
    RoleID = Column(Integer, primary_key=True, autoincrement=True) # SERIAL
    RoleName = Column(String(100), nullable=False)

class User(Base):
    __tablename__ = 'User'
    UserID = Column(Integer, primary_key=True, autoincrement=True)
    Name = Column(String(255))
    IsActive = Column(Boolean, default=True)
    RoleID = Column(Integer, ForeignKey('UserRole.RoleID'), nullable=False)
    
    role = relationship("UserRole")

class Credential(Base):
    __tablename__ = 'Credential'
    CredentialID = Column(Integer, primary_key=True, autoincrement=True)
    CredentialName = Column(String(255), nullable=False)

class RoleCredential(Base):
    __tablename__ = 'RoleCredential'
    RoleID = Column(Integer, ForeignKey('UserRole.RoleID'), primary_key=True)
    CredentialID = Column(Integer, ForeignKey('Credential.CredentialID'), primary_key=True)
    Allowed = Column(Boolean, default=True)

# --- 2. Справочники Оборудования и Газа ---
class Compressor(Base):
    __tablename__ = 'Compressor'
    CompressorID = Column(Integer, primary_key=True, autoincrement=True)
    Model = Column(String(100))
    NominalPower = Column(Float)
    IsActive = Column(Boolean, default=True)
    MaxTempDischarge = Column(Float)

class GasComposition(Base):
    __tablename__ = 'GasComposition'
    CompositionID = Column(Integer, primary_key=True, autoincrement=True)
    CH4 = Column(Float)
    C2H6 = Column(Float)
    C3H8 = Column(Float)
    CO2 = Column(Float)
    H2S = Column(Float)
    H2O = Column(Float)
    N2 = Column(Float)

# --- 3. Границы Помпажа и ГДХ ---
class SurgeBoundary(Base):
    __tablename__ = 'SurgeBoundary'
    BoundaryID = Column(Integer, primary_key=True, autoincrement=True)
    Q_surge = Column(Float)
    H_surge = Column(Float)
    # Магия SQLAlchemy: В Postgres это будет REAL[], в SQLite - JSON
    Coeffitients = Column(ARRAY(Float).with_variant(JSON, 'sqlite')) 
    CompressorID = Column(Integer, ForeignKey('Compressor.CompressorID'), nullable=False)
    CompositionID = Column(Integer, ForeignKey('GasComposition.CompositionID'), nullable=False)

class GDX_Header(Base):
    __tablename__ = 'GDX_Header'
    CurveID = Column(Integer, primary_key=True, autoincrement=True)
    RPM = Column(Integer)
    CompressorID = Column(Integer, ForeignKey('Compressor.CompressorID'), nullable=False)
    CompositionID = Column(Integer, ForeignKey('GasComposition.CompositionID'), nullable=False)

class GDX_Point(Base):
    __tablename__ = 'GDX_Point'
    GDX_ID = Column(Integer, primary_key=True, autoincrement=True)
    Q = Column(Float)
    H = Column(Float)
    Efficiency = Column(Float)
    Power = Column(Float)
    PointIndex = Column(Integer)
    CurveID = Column(Integer, ForeignKey('GDX_Header.CurveID'), nullable=False)

# --- 4. Нечеткая Логика ---
class FuzzyConfig(Base):
    __tablename__ = 'FuzzyConfig'
    # Составной первичный ключ
    ConfigID = Column(Integer, primary_key=True)
    Version = Column(String(50), primary_key=True)
    
    # JSONB в Postgres, JSON/TEXT в SQLite
    InputVars = Column(JSONB().with_variant(JSON, 'sqlite'))
    OutputVars = Column(JSONB().with_variant(JSON, 'sqlite'))
    MembershipParams = Column(Text)

class FuzzyRule(Base):
    __tablename__ = 'FuzzyRule'
    RuleID = Column(Integer, primary_key=True, autoincrement=True)
    AntecedentKey = Column(String(255))
    Consequent = Column(String(255))
    Weight = Column(Float)
    Priority = Column(Float)
    IsActive = Column(Boolean, default=True)
    
    ConfigID = Column(Integer, nullable=False)
    Version = Column(String(50), nullable=False)
    
    # Составной внешний ключ
    __table_args__ = (
        ForeignKeyConstraint(
            ['ConfigID', 'Version'],
            ['FuzzyConfig.ConfigID', 'FuzzyConfig.Version']
        ),
    )

# --- 5. Лог Событий ---
class EventLog(Base):
    __tablename__ = 'EventLog'
    EventID = Column(Integer, primary_key=True, autoincrement=True)
    Timestamp = Column(DateTime, default=datetime.utcnow)
    Q = Column(Float)
    H = Column(Float)
    P_in = Column(Float)
    P_out = Column(Float)
    T_in = Column(Float)
    Margin = Column(Float)
    dQdt = Column(Float)
    ValvePosition = Column(Float)
    RuleFired = Column(Integer, ForeignKey('FuzzyRule.RuleID'))
    Status = Column(Boolean)
    CompressorID = Column(Integer, ForeignKey('Compressor.CompressorID'), nullable=False)
    UserID = Column(Integer, ForeignKey('User.UserID'), nullable=False)