[Setup]
AppName=SIGNBRIDGE
AppVersion=1.0
DefaultDirName={pf}\SIGNBRIDGE
DefaultGroupName=SIGNBRIDGE
OutputDir=..\dist
OutputBaseFilename=SIGNBRIDGE-Setup
Compression=lzma2
SolidCompression=yes
PrivilegesRequired=lowest
ArchitecturesInstallIn64BitMode=x64
SetupIconFile=..\frontend\assets\favicon.ico
UninstallDisplayIcon={app}\SIGNBRIDGE.exe

[Files]
Source: "..\dist\SIGNBRIDGE\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\SIGNBRIDGE"; Filename: "{app}\SIGNBRIDGE.exe"
Name: "{commondesktop}\SIGNBRIDGE"; Filename: "{app}\SIGNBRIDGE.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional icons:"

[Run]
Filename: "{app}\SIGNBRIDGE.exe"; Description: "Launch SIGNBRIDGE"; Flags: nowait postinstall skipifsilent

[Code]
function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;
end;
