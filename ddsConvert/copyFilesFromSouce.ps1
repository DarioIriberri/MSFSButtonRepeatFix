# Forzar codificación UTF-8 en la consola para evitar caracteres extraños
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# Ruta base donde tienes tus carpetas IN-
$baseDir = "C:\ddsConvert"
$configFile = "$baseDir\.config_path"

# Comprobar la última ruta guardada
$initialDir = "C:\"
if (Test-Path $configFile) {
    $savedPath = Get-Content $configFile -ErrorAction SilentlyContinue
    if (Test-Path $savedPath) {
        $initialDir = $savedPath
    }
}

Add-Type -AssemblyName Microsoft.VisualBasic
Add-Type -AssemblyName System.Windows.Forms

# Preguntar si se quiere pegar la ruta o usar el explorador
$eleccion = [System.Windows.Forms.MessageBox]::Show(
    "¿Quieres pegar la ruta de la carpeta manualmente?`n`(Pulsa 'No' para abrir el explorador habitual)", 
    "Seleccionar origen de texturas", 
    [System.Windows.Forms.MessageBoxButtons]::YesNo, 
    [System.Windows.Forms.MessageBoxIcon]::Question
)

$sourceDir = $null

if ($eleccion -eq [System.Windows.Forms.DialogResult]::Yes) {
    # Cuadro de texto para pegar la ruta
    $sourceDir = [Microsoft.VisualBasic.Interaction]::InputBox(
        "Pega aquí la ruta completa de la carpeta de origen:", 
        "Pegar Ruta", 
        $initialDir
    )
} else {
    # Explorador de carpetas tradicional
    $folderBrowser = New-Object System.Windows.Forms.FolderBrowserDialog
    $folderBrowser.Description = "Selecciona la carpeta contenedora de texturas DDS"
    $folderBrowser.SelectedPath = $initialDir

    if ($folderBrowser.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {
        $sourceDir = $folderBrowser.SelectedPath
    }
}

# Validar si se introdujo una ruta válida
if ([string]::IsNullOrWhiteSpace($sourceDir) -or -not (Test-Path $sourceDir)) {
    Write-Host "Operación cancelada o ruta no válida." -ForegroundColor Yellow
    Exit
}

# Guardar la ruta seleccionada para la próxima vez
Set-Content -Path $configFile -Value $sourceDir

# Obtener todos los archivos .dds de la carpeta origen
$ddsFiles = Get-ChildItem -Path $sourceDir -Filter "*.dds" -File

if ($ddsFiles.Count -eq 0) {
    Write-Host "No se han encontrado archivos .dds en la carpeta seleccionada." -ForegroundColor Red
    Pause
    Exit
}

Write-Host "Procesando $($ddsFiles.Count) archivos desde: $sourceDir" -ForegroundColor Cyan

foreach ($file in $ddsFiles) {
    $size = $file.Length
    $targetSubFolder = $null

    # Clasificación exacta basada en los bytes indicados
    switch ($size) {
        89478640 { $targetSubFolder = "IN-8192" }
        44739384 { $targetSubFolder = "IN-8192-DXT1" }
        22369776 { $targetSubFolder = "IN-4096" }
        11184952 { $targetSubFolder = "IN-4096-DXT1" }
        5592560  { $targetSubFolder = "IN-2048" }
        2796344  { $targetSubFolder = "IN-2048-DXT1" }
        1398256  { $targetSubFolder = "IN-1024" }
        699192   { $targetSubFolder = "IN-1024-DXT1" }
    }

    if ($targetSubFolder) {
        $destinationPath = Join-Path $baseDir $targetSubFolder
        if (Test-Path $destinationPath) {
            Copy-Item -Path $file.FullName -Destination $destinationPath -Force
            Write-Host "Copiado: $($file.Name) -> $targetSubFolder" -ForegroundColor Green
        }
    }
}

Write-Host "`n¡Proceso de clasificación y copia finalizado con éxito!" -ForegroundColor Cyan
Pause