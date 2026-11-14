import os
import subprocess
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path

# ==========================================
# CONFIGURACIÓN DE RUTAS
# ==========================================
COMMUNITY_DIR = Path(
    r"C:\Users\dazz\AppData\Roaming\Microsoft Flight Simulator\Packages\Community")
CONFIG_BACKUP = Path(r"C:\ddsConvert\.last_airport_backup")
AIRPORT_BACKUP_FOLDER = "Z:/MSFS2020/Airports"

# Ruta habitual de WinRAR en Windows
WINRAR_PATH = Path(r"C:\Program Files\WinRAR\Rar.exe")
if not WINRAR_PATH.exists():
    WINRAR_PATH = Path(r"C:\Program Files (x86)\WinRAR\Rar.exe")


def get_saved_path() -> str:
    return AIRPORT_BACKUP_FOLDER
    # if CONFIG_BACKUP.exists():
    #     saved = CONFIG_BACKUP.read_text(encoding="utf-8").strip()
    #     if os.path.isdir(saved):
    #         return saved
    # return "C:\\"


def main():
    if not WINRAR_PATH.exists():
        messagebox.showerror("Error",
                             f"No se encuentra WinRAR (Rar.exe) en las rutas habituales.\nVerifica la instalación.")
        return

    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)

    # 1. Seleccionar la carpeta de backup del aeropuerto
    initial_dir = get_saved_path()
    backup_folder_str = filedialog.askdirectory(
        title="Selecciona la carpeta de respaldo del aeropuerto (ej. GCXO Tenerife Norte)",
        initialdir=initial_dir
    )

    if not backup_folder_str:
        print("Operación cancelada.")
        return

    backup_folder = Path(backup_folder_str)
    CONFIG_BACKUP.write_text(str(backup_folder), encoding="utf-8")

    # 2. Buscar archivo .rar activo (excluyendo los .off)
    rar_files = list(backup_folder.glob("*.rar"))
    valid_rars = [f for f in rar_files if not f.name.endswith(".rar.off")]

    target_archive = None
    is_already_off = False

    if valid_rars:
        original_rar = valid_rars[0]
        print(f"📦 RAR original detectado: {original_rar.name}")

        # PASO 1: Renombrar el RAR original a .rar.off PRIMERO (para no sobreescribir)
        disabled_rar_path = backup_folder / f"{original_rar.name}.off"
        try:
            if disabled_rar_path.exists():
                disabled_rar_path.unlink()
            original_rar.rename(disabled_rar_path)
            print(f"🔒 RAR original renombrado de forma segura a: {original_rar.name}.off")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo renombrar el RAR original a .off:\n{e}")
            return

        target_archive = disabled_rar_path
        base_rar_for_name = original_rar
    else:
        # Si no hay .rar activo, comprobamos si hay un .off para usarlo como base
        off_files = list(backup_folder.glob("*.rar.off"))
        if off_files:
            target_archive = off_files[0]
            # Extraer el nombre base quitando el sufijo .off (ej: archivo.rar.off -> archivo.rar)
            base_rar_for_name = Path(target_archive.name[:-4])
            print(f"⚠️ No hay .rar activo, pero se detectó el backup protegido: {target_archive.name}")
            is_already_off = True
        else:
            messagebox.showerror("Error", f"No se ha encontrado ningún archivo .rar ni .rar.off en:\n{backup_folder}")
            return

    # 3. Obtener el nombre de la carpeta interna analizando el archivo comprimido
    cmd_list = [str(WINRAR_PATH), "lb", str(target_archive)]
    result = subprocess.run(cmd_list, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    if result.returncode != 0:
        messagebox.showerror("Error", f"No se pudo leer el contenido del archivo comprimido:\n{result.stderr}")
        return

    lines = result.stdout.strip().splitlines()
    if not lines:
        messagebox.showerror("Error", "El archivo comprimido parece estar vacío.")
        return

    internal_folder_name = lines[0].split('/')[0].split('\\')[0]
    print(f"📁 Nombre de carpeta interna esperado: {internal_folder_name}")

    # 4. Buscar la carpeta correspondiente en Community (anteponiendo 'AIRPORT ')
    target_community_name = f"AIRPORT {internal_folder_name}"
    community_airport_path = COMMUNITY_DIR / target_community_name

    if not community_airport_path.exists():
        matching_dirs = [d for d in COMMUNITY_DIR.iterdir() if
                         d.is_dir() and internal_folder_name.lower() in d.name.lower()]
        if matching_dirs:
            community_airport_path = matching_dirs[0]
            print(f"🔍 Carpeta encontrada por coincidencia parcial: {community_airport_path.name}")
        else:
            messagebox.showerror("Error", f"No se encuentra la carpeta en Community para:\n'{target_community_name}'")
            return
    else:
        print(f"✅ Carpeta en Community localizada: {community_airport_path.name}")

    # 5. PASO 2: Copiar la carpeta desde Community a la del backup
    dest_copied_folder = backup_folder / community_airport_path.name
    print(f"📂 Copiando carpeta desde Community al backup (esto puede tardar unos segundos)...")

    if dest_copied_folder.exists():
        shutil.rmtree(dest_copied_folder)  # Limpiar si ya existiera una copia previa
    shutil.copytree(community_airport_path, dest_copied_folder)

    # 6. PASO 3: Renombrar la carpeta copiada quitándole el prefijo 'AIRPORT '
    clean_folder_path = backup_folder / internal_folder_name
    if clean_folder_path.exists():
        shutil.rmtree(clean_folder_path)

    dest_copied_folder.rename(clean_folder_path)
    print(f"🏷️ Carpeta renombrada limpiamente a: {internal_folder_name}")

    # 7. PASO 4: Comprimir la carpeta limpia añadiendo -SHRINKED al nombre del RAR nuevo
    new_rar_name = f"{base_rar_for_name.stem}-SHRINKED{base_rar_for_name.suffix}"
    new_rar_path = backup_folder / new_rar_name

    print(f"🗜️ Comprimiendo a {new_rar_name}...")
    cmd_compress = [
        str(WINRAR_PATH),
        "a",
        "-r",
        "-m5",
        str(new_rar_path),
        internal_folder_name
    ]

    comp_result = subprocess.run(
        cmd_compress,
        cwd=backup_folder,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    if comp_result.returncode != 0:
        messagebox.showerror("Error", f"Falló la compresión con WinRAR:\n{comp_result.stderr}")
        return

    # 8. Limpiar la carpeta temporal copiada para dejar el directorio de backup limpio
    print(f"🧹 Eliminando carpeta temporal intermedia...")
    shutil.rmtree(clean_folder_path)

    print(f"✨ ¡Proceso completado con estructura 100% limpia!")

    status_msg = f"El aeropuerto se ha empaquetado correctamente.\n\n• Nuevo backup (shrunk): {new_rar_name}"
    if is_already_off:
        status_msg += f"\n• Nota: El .rar original ya estaba en .off previamente."
    else:
        status_msg += f"\n• Original protegido como: {base_rar_for_name.name}.off"

    messagebox.showinfo("¡Proceso Completado!", status_msg)


if __name__ == "__main__":
    main()