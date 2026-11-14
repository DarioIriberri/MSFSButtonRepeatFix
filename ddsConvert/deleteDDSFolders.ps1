# Ruta base donde se encuentran las carpetas
$rutaBase = "C:\ddsConvert"

# Comprobar que la ruta existe
if (Test-Path $rutaBase) {
    # Buscar todas las carpetas que comiencen por IN- o OUT-
    $carpetas = Get-ChildItem -Path $rutaBase -Directory | Where-Object { $_.Name -match '^(IN|OUT)-' }

    foreach ($carpeta in $carpetas) {
        Write-Host "Vaciando: $($carpeta.FullName)" -ForegroundColor Cyan
        # Borra todos los archivos de la carpeta y subcarpetas sin borrar los directorios
        Get-ChildItem -Path $carpeta.FullName -Recurse -File | Remove-Item -Force
    }

    Write-Host "`¡Limpieza completada con éxito!" -ForegroundColor Green
} else {
    Write-Host "La ruta $rutaBase no existe." -ForegroundColor Red
}

Pause