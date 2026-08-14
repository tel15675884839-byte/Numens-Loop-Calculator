[Setup]
AppId={{B7A3F0D1-2E4C-4A5B-9F6D-1C8E3A7B5D9F}
AppName=Loop Calculator
AppVersion=1.1.1
AppPublisher=Numens
DefaultDirName={localappdata}\Programs\Loop Calculator
DefaultGroupName=Loop Calculator
OutputDir=..\dist-installer
OutputBaseFilename=LoopCalculatorSetup
Compression=lzma2
SolidCompression=yes
SetupIconFile=..\frontend\public\app.ico
UninstallDisplayIcon={app}\LoopCalculatorDesktop.exe
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
WizardStyle=modern

[Files]
Source: "..\dist-desktop\LoopCalculatorDesktop.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\dist-desktop\LoopCalculatorBackend.exe"; DestDir: "{app}"; Flags: ignoreversion

[Dirs]
Name: "{app}\data"

[Icons]
Name: "{group}\Loop Calculator"; Filename: "{app}\LoopCalculatorDesktop.exe"
Name: "{group}\Uninstall Loop Calculator"; Filename: "{uninstallexe}"
Name: "{userdesktop}\Loop Calculator"; Filename: "{app}\LoopCalculatorDesktop.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional icons:"

[Run]
Filename: "{app}\LoopCalculatorDesktop.exe"; Description: "Launch Loop Calculator"; Flags: nowait postinstall skipifsilent
