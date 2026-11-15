import os
import time
import subprocess
import tkinter as tk
import sys
from tkinter import filedialog, messagebox
from pathlib import Path

# Configuración de rutas
BASE_DIR = Path(r"C:/ddsConvert")
TEXCONV_PATH = BASE_DIR / "C:/ddsConvert/texconv.exe"
CONFIG_SRC = BASE_DIR / ".last_src"
CONFIG_DST = BASE_DIR / ".last_dst"
FORCED_DDS_FORMAT = None
# FORCED_DDS_FORMAT = "BC1_UNORM"

# Mapa de tamaños en bytes -> (resolución_origen, formato_texconv)
SIZE_MAP = {
    89478640: (8192, "BC7_UNORM"),
    44739384: (8192, "BC1_UNORM"),
    22369776: (4096, "BC7_UNORM"),
    11184952: (4096, "BC1_UNORM"),
    5592560: (2048, "BC7_UNORM"),
    2796344: (2048, "BC1_UNORM"),
    1398256: (1024, "BC7_UNORM"),
    699192: (1024, "BC1_UNORM"),
}

def match_dds_size(file_size):
    for std_size, config in SIZE_MAP.items():
        # Permitimos un margen de tolerancia del 2% (2 por ciento)
        tolerance = std_size * 0.02
        if abs(file_size - std_size) <= tolerance:
            return std_size, config
    return None, None

def get_saved_path(config_file: Path) -> str:
    if config_file.exists():
        saved = config_file.read_text(encoding="utf-8").strip()
        if os.path.isdir(saved):
            return saved
    return "C:\\"


def select_folder(title: str, config_file: Path) -> Path | None:
    initial = get_saved_path(config_file)
    selected = filedialog.askdirectory(title=title, initialdir=initial)
    if selected:
        config_file.write_text(selected, encoding="utf-8")
        return Path(selected)
    return None


def main():
    if not TEXCONV_PATH.exists():
        print(f"ERROR: No se encuentra texconv.exe en {TEXCONV_PATH}")
        input("Pulsa Enter para salir...")
        return

    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)

    src_dir = select_folder("1. Selecciona la carpeta ORIGEN con los DDS", CONFIG_SRC)
    if not src_dir:
        print("Operación cancelada.")
        return

    # dst_dir = select_folder("2. Selecciona la carpeta DESTINO para guardar los DDS reducidos", CONFIG_DST)
    dst_dir = Path(get_saved_path(CONFIG_DST))
    if not dst_dir:
        print("Operación cancelada.")
        return

    dds_files = list(src_dir.glob("*.dds"))
    total_files = len(dds_files)

    if total_files == 0:
        print("No se encontraron archivos .dds en la carpeta de origen.")
        input("Pulsa Enter para salir...")
        return

    # Limpiar carpetas IN- y OUT- antes de comenzar
    print("Vaciando carpetas de trabajo anteriores (IN- y OUT-)...")
    for item in BASE_DIR.iterdir():
        if item.is_dir() and (item.name.startswith("IN-") or item.name.startswith("OUT-")):
            for sub_file in item.glob("*.*"):
                try:
                    sub_file.unlink()
                except Exception as e:
                    print(f"  [AVISO] No se pudo borrar {sub_file.name}: {e}")

    print(f"\nOrigen:  {src_dir}")
    print(f"Destino: {dst_dir}")
    print(f"Iniciando conversión de {total_files} archivos...\n")

    # Iniciar cronómetro
    start_time = time.time()

    converted_count = 0
    verified_count = 0
    skipped_count = 0
    total_original_bytes = 0
    total_new_bytes = 0

    for index, file_path in enumerate(dds_files, start=1):
        if any(sufix in file_path.name.upper() for sufix in ["_NORMAL", "_NORM", "_NOMAL", "_COMP", "_MTL", "_METALIC", "_LM"]):
            continue  # Saltar y no tocar

        orig_size = file_path.stat().st_size
        progress_pct = (index / total_files) * 100

        matched_orig_size, config = match_dds_size(orig_size)

        if not config:
            skipped_count += 1
            print(
                f"[{index}/{total_files} - {progress_pct:.1f}%] IGNORADO (Tamaño fuera de rango: {orig_size:,} bytes): {file_path.name}")
            continue

        orig_res, dds_format = config
        target_res = orig_res // 2
        output_file_path = dst_dir / file_path.name

        if FORCED_DDS_FORMAT is not None:
            dds_format = FORCED_DDS_FORMAT

        cmd = [
            str(TEXCONV_PATH),
            "-w", str(target_res),
            "-h", str(target_res),
            "-f", dds_format,
            "-m", "0",
            "-if", "CUBIC",
            "-y",
            "-o", str(dst_dir),
            str(file_path)
        ]

        # Ejecutar conversión con texconv
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if result.returncode == 0:
            converted_count += 1

            # Verificación de tamaño post-conversión
            if output_file_path.exists():
                new_size = output_file_path.stat().st_size
                expected_size = orig_size / 4.0
                actual_ratio = (new_size / orig_size) * 100
                tolerance = expected_size * 0.02

                if abs(new_size - expected_size) <= tolerance:
                    verified_count += 1
                    print(
                        f"[{index}/{total_files} - {progress_pct:.1f}%] [OK] {file_path.name} ({orig_res}->{target_res} | Ratio: {actual_ratio:.2f}%)")
                else:
                    print(
                        f"[{index}/{total_files} - {progress_pct:.1f}%] [AVISO] {file_path.name} | Ratio obtenido: {actual_ratio:.2f}% (Esperado ~25%)")
            else:
                print(
                    f"[{index}/{total_files} - {progress_pct:.1f}%] [ERROR] No se encuentra el archivo de salida para {file_path.name}")
        else:
            print(
                f"[{index}/{total_files} - {progress_pct:.1f}%] [ERROR] Falló la conversión de {file_path.name}: {result.stderr.strip()}")

        total_original_bytes += orig_size
        total_new_bytes += output_file_path.stat().st_size

    # Detener cronómetro y calcular tiempo transcurrido
    end_time = time.time()
    elapsed_seconds = end_time - start_time

    # Detener cronómetro y calcular tiempo transcurrido
    end_time = time.time()
    elapsed_seconds = end_time - start_time

    minutes = int(elapsed_seconds // 60)
    seconds = elapsed_seconds % 60

    # Cálculo de espacio ahorrado
    saved_bytes = total_original_bytes - total_new_bytes
    saved_mb = saved_bytes / (1024 * 1024)
    orig_mb = total_original_bytes / (1024 * 1024)
    new_mb = total_new_bytes / (1024 * 1024)
    reduction_pct = (saved_bytes / total_original_bytes * 100) if total_original_bytes > 0 else 0

    print("\n" + "=" * 65)
    print(f"Proceso finalizado con éxito.")
    print(f" - Archivos procesados con éxito: {converted_count}")
    print(f" - Verificados a ratio 1/4 exacto: {verified_count}")
    print(f" - Ignorados (otros tamaños): {skipped_count}")
    print("-" * 65)
    print(f"📊 BALANCE DE ESPACIO EN DISCO:")
    print(f" - Tamaño original total : {orig_mb:.2f} MB")
    print(f" - Tamaño reducido total : {new_mb:.2f} MB")
    print(f" - Espacio total ahorrado: {saved_mb:.2f} MB ({reduction_pct:.1f}% menos)")
    print("-" * 65)
    if minutes > 0:
        print(f" ⏱️ Tiempo total empleado: {minutes} minutos y {seconds:.2f} segundos ({elapsed_seconds:.2f}s)")
    else:
        print(f" ⏱️ Tiempo total empleado: {seconds:.2f} segundos")
    print("=" * 65)

    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)

    respuesta = messagebox.askyesno(
        "Sobrescribir originales",
        f"¿Deseas copiar los {converted_count} archivos convertidos a la carpeta de origen:\n\n{src_dir}\n\n(Esto sobrescribirá los archivos DDS originales)"
    )

    if respuesta:
        print("\n🔄 Copiando archivos convertidos al directorio de origen (sobrescribiendo)...")
        copiados_origen = 0
        for conv_file in dst_dir.glob("*.dds"):
            try:
                # Copiar cada archivo de destino a origen sobrescribiendo el original
                destination_original = src_dir / conv_file.name
                with open(conv_file, 'rb') as fsrc, open(destination_original, 'wb') as fdst:
                    fdst.write(fsrc.read())
                copiados_origen += 1
            except Exception as e:
                print(f"  [ERROR] No se pudo sobrescribir {conv_file.name}: {e}")
        print(f"✅ ¡Se han sobrescrito {copiados_origen} archivos en la carpeta de origen con éxito!")

        respuesta = messagebox.askyesno(
            "Lanzar backup",
            f"¿Deseas ejecutar el script de backup de aeropuerto?"
        )

        if respuesta:
            print("\n🚀 Lanzando el script de backup del aeropuerto...")
            # Asumiendo que el script de backup está en la misma carpeta base (C:/ddsConvert)
            backup_script_path = BASE_DIR / "BackupShrinkedAirport.py"

            if backup_script_path.exists():
                try:
                    # Ejecuta el script de backup en una nueva ventana de consola o esperando a que termine
                    subprocess.run([sys.executable, str(backup_script_path)], check=True)
                    print("✅ ¡Script de backup finalizado con éxito!")
                except Exception as e:
                    print(f"  [ERROR] Hubo un problema al ejecutar el script de backup: {e}")
            else:
                print(f"  [ERROR] No se encuentra el archivo en la ruta: {backup_script_path}")

    else:
        print("\n📁 Los archivos convertidos se quedan únicamente en la carpeta de destino.")

    input("\nPulsa Enter para salir...")


if __name__ == "__main__":
    main()