# Infraestructura/Gestores/Bootstrap/Scripts/matar_todo.ps1
#
# Mata todos los procesos python.exe de ESTE proyecto que sigan vivos
# (sectores, logica_mundo, gestor_mundo, gestor_bots, hypervisores,
# comunicaciones_remoto) - pensado para cuando un cierre anomalo
# (crash, Ctrl+C que no llega a tiempo, fallo de bind como el de
# hv_000) deja procesos huerfanos que bootstrap.py ya no controla.
#
# Filtra por CommandLine conteniendo "Infraestructura\Gestores" para
# NO tocar otros procesos python.exe ajenos al proyecto (ej. el
# lsp_server de la extension de VSCode) aunque esten corriendo a la
# vez.
'''
Ejecucion en terminal:
.\Infraestructura\Gestores\Bootstrap\Scripts\matar_todo.ps1
'''
$patron = "Infraestructura\\Gestores"

$procesos = Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" |
    Where-Object { $_.CommandLine -match $patron }

if (-not $procesos) {
    Write-Host "No se encontro ningun proceso del stack corriendo."
    exit 0
}

Write-Host "Procesos encontrados:"
$procesos | Select-Object ProcessId, CommandLine | Format-Table -AutoSize

foreach ($p in $procesos) {
    try {
        Stop-Process -Id $p.ProcessId -Force -ErrorAction Stop
        Write-Host "Matado PID $($p.ProcessId)"
    } catch {
        Write-Warning "No se pudo matar PID $($p.ProcessId): $_"
    }
}

Write-Host "`nHecho. Verificando puertos del stack..."
foreach ($puerto in 50051, 50100, 50200, 50250, 50300, 50400, 50500) {
    $ocupado = Test-NetConnection -ComputerName localhost -Port $puerto -WarningAction SilentlyContinue |
        Where-Object TcpTestSucceeded
    if ($ocupado) {
        Write-Warning "Puerto $puerto sigue ocupado tras matar procesos - revisa manualmente."
    }
}
Write-Host "Verificacion de puertos completada."