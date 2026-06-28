from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, Text, ForeignKey  # ty:ignore[unresolved-import]
from sqlalchemy.sql import func  # ty:ignore[unresolved-import]
from sqlalchemy.orm import relationship  # ty:ignore[unresolved-import]
from db.init_db import Base


class FuzzyConfig(Base):
    """Конфигурация нечеткой логики (теперь это 'Профиль правил')"""
    __tablename__ = 'FuzzyConfigs'
    
    ConfigID = Column(Integer, primary_key=True, autoincrement=True)
    Version = Column(String(50), nullable=False, default="1.0.0")
    InputVars = Column(Text)  # JSON
    OutputVars = Column(Text)  # JSON
    MembershipParams = Column(Text)  # JSON
    
    # ✅ НОВОЕ ПОЛЕ: Имя профиля для читаемости
    Name = Column(String(100), nullable=True)
    Description = Column(String(500), nullable=True)
    
    UpdatedAt = Column(DateTime, default=func.now(), onupdate=func.now())
    UpdatedBy = Column(String(100), nullable=True)
    
    # Связь с правилами
    rules = relationship("FuzzyRule", back_populates="config", cascade="all, delete-orphan")
    # Связь с компрессорами
    compressors = relationship("Compressor", back_populates="profile")


class FuzzyRule(Base):
    """Правило нечеткого вывода"""
    __tablename__ = 'FuzzyRules'
    
    RuleID = Column(Integer, primary_key=True, autoincrement=True)
    ConfigID = Column(Integer, ForeignKey('FuzzyConfigs.ConfigID'), nullable=False)
    Version = Column(String(50), nullable=False, default="1.0.0")
    AntecedentKey = Column(String(500), nullable=False)
    Consequent = Column(String(500), nullable=False)
    Weight = Column(Float, default=1.0)
    Priority = Column(Integer, default=1)
    IsActive = Column(Boolean, default=True)
    
    config = relationship("FuzzyConfig", back_populates="rules")


class Compressor(Base):
    """Компрессор с привязкой к профилю правил"""
    __tablename__ = 'Compressors'
    
    CompressorID = Column(Integer, primary_key=True, autoincrement=True)
    Name = Column(String(100), nullable=False, unique=True)  # CC-45X, SK-600B, ...
    Model = Column(String(100), nullable=True)
    InstallDate = Column(DateTime, nullable=True)
    
    # ✅ Связь с профилем правил
    ProfileID = Column(Integer, ForeignKey('FuzzyConfigs.ConfigID'), nullable=False)
    
    profile = relationship("FuzzyConfig", back_populates="compressors")


class EventLog(Base):
    __tablename__ = 'EventLog'
    
    EventID = Column(Integer, primary_key=True, autoincrement=True)
    Timestamp = Column(DateTime, nullable=False)
    Q = Column(Float)
    H = Column(Float)
    P_in = Column(Float)
    P_out = Column(Float)
    T_in = Column(Float)
    Margin = Column(Float)
    dQdt = Column(Float)
    ValvePosition = Column(Float)
    RuleFired = Column(String)
    Status = Column(Boolean)
    CompressorID = Column(Integer, ForeignKey('Compressors.CompressorID'))
    UserID = Column(Integer, ForeignKey('Users.UserID'))
    
    ReactionTime = Column(Float, default=0.0)      # Время реакции в мс
    GasComposition = Column(String, default="")    # Состав газа


class GDX_Header(Base):
    """Заголовок кривой ГДХ"""
    __tablename__ = 'GDX_Headers'
    
    CurveID = Column(Integer, primary_key=True, autoincrement=True)
    CompressorID = Column(Integer, nullable=False)
    CompositionID = Column(Integer, nullable=True)
    RPM = Column(Integer, nullable=False)
    
    points = relationship("GDX_Point", back_populates="header", cascade="all, delete-orphan")


class GDX_Point(Base):
    """Точка на кривой ГДХ"""
    __tablename__ = 'GDX_Points'
    
    PointID = Column(Integer, primary_key=True, autoincrement=True)
    CurveID = Column(Integer, ForeignKey('GDX_Headers.CurveID'), nullable=False)
    PointIndex = Column(Integer, nullable=False)
    Q = Column(Float, nullable=False)
    H = Column(Float, nullable=False)
    Efficiency = Column(Float, nullable=True)
    Power = Column(Float, nullable=True)
    
    header = relationship("GDX_Header", back_populates="points")


class SurgeBoundary(Base):
    """Граница помпажа"""
    __tablename__ = 'SurgeBoundaries'
    
    BoundaryID = Column(Integer, primary_key=True, autoincrement=True)
    CompressorID = Column(Integer, nullable=False)
    Q_surge = Column(Float, nullable=False)
    H_surge = Column(Float, nullable=False)


class User(Base):
    """Пользователь системы"""
    __tablename__ = 'Users'
    
    UserID = Column(Integer, primary_key=True, autoincrement=True)
    Username = Column(String(100), nullable=False, unique=True)
    PasswordHash = Column(String(255), nullable=False)
    Role = Column(String(50), nullable=False, default='OPERATOR')
    IsActive = Column(Boolean, default=True)