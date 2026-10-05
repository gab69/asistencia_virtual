; Script de Inno Setup: crea Instalador_MarcadorAsistencia.exe
; No requiere Python ni permisos de administrador en el equipo destino.

#define NombreApp "Marcador de asistencia"
#define Version "1.1.0"
#define Exe "MarcadorAsistencia.exe"

[Setup]
AppId={{B7D1E5C2-4F3A-4C8E-9A61-2D5E7F0A1B34}
AppName={#NombreApp}
AppVersion={#Version}
AppPublisher=@GabRC
DefaultDirName={autopf}\{#NombreApp}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=Output
OutputBaseFilename=Instalador_MarcadorAsistencia
SetupIconFile=icono.ico
UninstallDisplayIcon={app}\{#Exe}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "iniciar"; Description: "Iniciar con Windows (recomendado)"; GroupDescription: "Opciones:"
Name: "escritorio"; Description: "Crear acceso directo en el escritorio"; GroupDescription: "Opciones:"; Flags: unchecked

[Files]
Source: "dist\MarcadorAsistencia\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#NombreApp}"; Filename: "{app}\{#Exe}"
Name: "{autodesktop}\{#NombreApp}"; Filename: "{app}\{#Exe}"; Tasks: escritorio

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "MarcadorAsistencia"; ValueData: """{app}\{#Exe}"" --minimizado"; Flags: uninsdeletevalue; Tasks: iniciar

[Run]
Filename: "{app}\{#Exe}"; Description: "Abrir {#NombreApp}"; Flags: nowait postinstall skipifsilent

[UninstallRun]
Filename: "{sys}\taskkill.exe"; Parameters: "/F /IM {#Exe}"; Flags: runhidden; RunOnceId: "CerrarMarcador"

[UninstallDelete]
Type: files; Name: "{%USERPROFILE}\marcador_asistencia.json"

[Code]
// Cierra el programa si está abierto, para poder actualizarlo sin errores.
function InitializeSetup(): Boolean;
var
  CodigoSalida: Integer;
begin
  Exec(ExpandConstant('{sys}\taskkill.exe'), '/F /IM {#Exe}', '', SW_HIDE, ewWaitUntilTerminated, CodigoSalida);
  Result := True;
end;
