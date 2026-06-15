[Setup]
AppName=Система защиты компрессора от помпажа
AppVersion=1.0.0
AppPublisher=Sharaga Entertainment
DefaultDirName={autopf}\TipisAntiSurge
DefaultGroupName=Tipis Anti-Surge System
AllowNoIcons=yes
OutputDir=C:\Users\nikso\Desktop\sharaga-entertaiment\tipis\tipis\installer_output
OutputBaseFilename=TipisAntiSurge_Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[Files]
Source: "C:\Users\nikso\Desktop\sharaga-entertaiment\tipis\tipis\src\ui\dist\DispatcherGUI.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Система защиты от помпажа"; Filename: "{app}\DispatcherGUI.exe"
Name: "{group}\{cm:UninstallProgram,Система защиты}"; Filename: "{uninstallexe}"
Name: "{commondesktop}\Система защиты от помпажа"; Filename: "{app}\DispatcherGUI.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Run]
Filename: "{app}\DispatcherGUI.exe"; Description: "{cm:LaunchProgram,Система защиты от помпажа}"; Flags: nowait postinstall skipifsilent