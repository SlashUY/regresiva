@echo off
chcp 65001 >nul 2>&1
echo.
echo  Creando acceso directo en el Escritorio...

set "TARGET=%~dp0iniciar.bat"
set "DESTINO=%USERPROFILE%\Desktop\Cuenta Regresiva.lnk"
set "ICONO=%SystemRoot%\System32\timedate.cpl"

powershell -NoProfile -Command ^
  "$ws = New-Object -ComObject WScript.Shell; " ^
  "$sc = $ws.CreateShortcut('%DESTINO%'); " ^
  "$sc.TargetPath = 'cmd.exe'; " ^
  "$sc.Arguments = '/c \"%TARGET%\"'; " ^
  "$sc.WorkingDirectory = '%~dp0'; " ^
  "$sc.IconLocation = '%ICONO%, 0'; " ^
  "$sc.Description = 'Cuenta Regresiva Retro'; " ^
  "$sc.WindowStyle = 1; " ^
  "$sc.Save()"

if exist "%DESTINO%" (
    echo.
    echo  [OK] Acceso directo creado en:
    echo       %DESTINO%
    echo.
    echo  El icono es el reloj del sistema de Windows.
    echo  Podes arrastrarlo a la barra de tareas o al menu Inicio.
) else (
    echo.
    echo  [ERROR] No se pudo crear el acceso directo.
    echo  Ejecuta este archivo como Administrador e intentalo de nuevo.
)
echo.
pause
