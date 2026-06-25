PRAGMA foreign_keys = ON;

CREATE TABLE UserRole (
    RoleID SERIAL PRIMARY KEY,
    RoleName VARCHAR(100) NOT NULL
);

CREATE TABLE "User" (
    UserID SERIAL PRIMARY KEY,
    Name VARCHAR(255),
    IsActive BOOLEAN DEFAULT TRUE,
    RoleID INTEGER NOT NULL,
    CONSTRAINT FK_User_Role FOREIGN KEY (RoleID) REFERENCES UserRole(RoleID)
);

CREATE TABLE Credential (
    CredentialID SERIAL PRIMARY KEY,
    CredentialName VARCHAR(255) NOT NULL
);

CREATE TABLE RoleCredential (
    RoleID INTEGER NOT NULL,
    CredentialID INTEGER NOT NULL,
    Allowed BOOLEAN DEFAULT TRUE,
    PRIMARY KEY (RoleID, CredentialID),
    CONSTRAINT FK_RoleCred_Role FOREIGN KEY (RoleID) REFERENCES UserRole(RoleID),
    CONSTRAINT FK_RoleCred_Cred FOREIGN KEY (CredentialID) REFERENCES Credential(CredentialID)
);

-- Справочники Оборудования и Газа
CREATE TABLE Compressor (
    CompressorID SERIAL PRIMARY KEY,
    Model VARCHAR(100),
    NominalPower REAL,
    IsActive BOOLEAN DEFAULT TRUE,
    MaxTempDischarge REAL
);

CREATE TABLE GasComposition (
    CompositionID SERIAL PRIMARY KEY,
    CH4 REAL,
    C2H6 REAL,
    C3H8 REAL,
    CO2 REAL,
    H2S REAL,
    H2O REAL,
    N2 REAL
);

-- Границы Помпажа (Surge Boundary)
CREATE TABLE SurgeBoundary (
    BoundaryID SERIAL PRIMARY KEY,
    Q_surge REAL,
    H_surge REAL,
    Coeffitients REAL[], -- Массив чисел
    CompressorID INTEGER NOT NULL,
    CompositionID INTEGER NOT NULL,
    CONSTRAINT FK_Surge_Comp FOREIGN KEY (CompressorID) REFERENCES Compressor(CompressorID),
    CONSTRAINT FK_Surge_Gas FOREIGN KEY (CompositionID) REFERENCES GasComposition(CompositionID)
);

-- Характеристики Компрессора (GDX - Gas Dynamic Characteristics)
CREATE TABLE GDX_Header (
    CurveID SERIAL PRIMARY KEY,
    RPM INTEGER,
    CompressorID INTEGER NOT NULL,
    CompositionID INTEGER NOT NULL,
    CONSTRAINT FK_GDX_Comp FOREIGN KEY (CompressorID) REFERENCES Compressor(CompressorID),
    CONSTRAINT FK_GDX_Gas FOREIGN KEY (CompositionID) REFERENCES GasComposition(CompositionID)
);

CREATE TABLE GDX_Point (
    GDX_ID SERIAL PRIMARY KEY,
    Q REAL,
    H REAL,
    Efficiency REAL,
    Power REAL,
    PointIndex INTEGER,
    CurveID INTEGER NOT NULL,
    CONSTRAINT FK_Point_Header FOREIGN KEY (CurveID) REFERENCES GDX_Header(CurveID)
);

-- Нечеткая Логика (Fuzzy Logic)
CREATE TABLE FuzzyConfig (
    ConfigID INTEGER NOT NULL,
    Version VARCHAR(50) NOT NULL,
    InputVars JSONB, -- Используем JSONB
    OutputVars JSONB,
    MembershipParams TEXT,
    PRIMARY KEY (ConfigID, Version)
);

CREATE TABLE FuzzyRule (
    RuleID SERIAL PRIMARY KEY,
    AntecedentKey VARCHAR(255),
    Consequent VARCHAR(255),
    Weight REAL,
    Priority REAL,
    IsActive BOOLEAN DEFAULT TRUE,
    ConfigID INTEGER NOT NULL,
    Version VARCHAR(50) NOT NULL,
    CONSTRAINT FK_Rule_Config FOREIGN KEY (ConfigID, Version) REFERENCES FuzzyConfig(ConfigID, Version)
);

-- Лог Событий (Event Log)
CREATE TABLE EventLog (
    EventID SERIAL PRIMARY KEY,
    Timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    Q REAL,
    H REAL,
    P_in REAL,
    P_out REAL,
    T_in REAL,
    Margin REAL,
    dQdt REAL,
    ValvePosition REAL,
    RuleFired INTEGER,
    Status BOOLEAN,
    CompressorID INTEGER NOT NULL,
    UserID INTEGER NOT NULL,
    
    CONSTRAINT FK_Log_Rule FOREIGN KEY (RuleFired) REFERENCES FuzzyRule(RuleID),
    CONSTRAINT FK_Log_Comp FOREIGN KEY (CompressorID) REFERENCES Compressor(CompressorID),
    CONSTRAINT FK_Log_User FOREIGN KEY (UserID) REFERENCES "User"(UserID)
);
