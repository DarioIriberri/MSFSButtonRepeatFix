import os
import subprocess
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path

# ==========================================
# PATH CONFIGURATION
# ==========================================
COMMUNITY_DIR = Path(
    r"C:\Users\dazz\AppData\Roaming\Microsoft Flight Simulator\Packages\Community")
CONFIG_BACKUP = Path(r"C:\ddsConvert\.last_airport_backup")
AIRPORT_BACKUP_FOLDER = "Z:/MSFS2020/Airports"

# Default WinRAR path on Windows
WINRAR_PATH = Path(r"C:\Program Files\WinRAR\Rar.exe")
if not WINRAR_PATH.exists():
    WINRAR_PATH = Path(r"C:\Program Files (x86)\WinRAR\Rar.exe")


def get_saved_path() -> str:
    return AIRPORT_BACKUP_FOLDER
    # if CONFIG_BACKUP.exists():
    #     saved = CONFIG_BACKUP.read_text(encoding="utf-8").strip()
    #     if os.path.isdir(saved):
    #         return saved
    # return "C:\"


def main():
    if not WINRAR_PATH.exists():
        messagebox.showerror("Error",
                             f"WinRAR (Rar.exe) could not be found in standard paths.\nVerify the installation.")
        return

    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)

    # 1. Select the airport backup folder
    initial_dir = get_saved_path()
    backup_folder_str = filedialog.askdirectory(
        title="Select airport backup folder (e.g. GCXO Tenerife Norte)",
        initialdir=initial_dir
    )

    if not backup_folder_str:
        print("Operation cancelled.")
        return

    backup_folder = Path(backup_folder_str)
    CONFIG_BACKUP.write_text(str(backup_folder), encoding="utf-8")

    # 2. Search for active .rar file (excluding .off files)
    rar_files = list(backup_folder.glob("*.rar"))
    valid_rars = [f for f in rar_files if not f.name.endswith(".rar.off")]

    target_archive = None
    is_already_off = False

    if valid_rars:
        original_rar = valid_rars[0]
        print(f"📦 Original RAR detected: {original_rar.name}")

        # STEP 1: Rename the original RAR to .rar.off FIRST (to avoid overwriting)
        disabled_rar_path = backup_folder / f"{original_rar.name}.off"
        try:
            if disabled_rar_path.exists():
                disabled_rar_path.unlink()
            original_rar.rename(disabled_rar_path)
            print(f"🔒 Original RAR safely renamed to: {original_rar.name}.off")
        except Exception as e:
            messagebox.showerror("Error", f"Could not rename original RAR to .off:\n{e}")
            return

        target_archive = disabled_rar_path
        base_rar_for_name = original_rar
    else:
        # If no active .rar, check if there is an .off to use as a base
        off_files = list(backup_folder.glob("*.rar.off"))
        if off_files:
            target_archive = off_files[0]
            # Extract base name by removing .off suffix (e.g.: file.rar.off -> file.rar)
            base_rar_for_name = Path(target_archive.name[:-4])
            print(f"⚠️ No active .rar, but protected backup detected: {target_archive.name}")
            is_already_off = True
        else:
            messagebox.showerror("Error", f"No .rar or .rar.off file found in:\n{backup_folder}")
            return

    # 3. Get the internal folder name by inspecting the archive
    cmd_list = [str(WINRAR_PATH), "lb", str(target_archive)]
    result = subprocess.run(cmd_list, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    if result.returncode != 0:
        messagebox.showerror("Error", f"Could not read compressed archive contents:\n{result.stderr}")
        return

    lines = result.stdout.strip().splitlines()
    if not lines:
        messagebox.showerror("Error", "The compressed archive appears to be empty.")
        return

    internal_folder_name = lines[0].split('/')[0].split('\\')[0]
    print(f"📁 Expected internal folder name: {internal_folder_name}")

    # 4. Search for the corresponding folder in Community (prefixing with 'AIRPORT ')
    target_community_name = f"AIRPORT {internal_folder_name}"
    community_airport_path = COMMUNITY_DIR / target_community_name

    if not community_airport_path.exists():
        matching_dirs = [d for d in COMMUNITY_DIR.iterdir() if
                         d.is_dir() and internal_folder_name.lower() in d.name.lower()]
        if matching_dirs:
            community_airport_path = matching_dirs[0]
            print(f"🔍 Folder found by partial match: {community_airport_path.name}")
        else:
            messagebox.showerror("Error", f"Community folder not found for:\n'{target_community_name}'")
            return
    else:
        print(f"✅ Community folder located: {community_airport_path.name}")

    # 5. STEP 2: Copy the folder from Community to the backup directory
    dest_copied_folder = backup_folder / community_airport_path.name
    print(f"📂 Copying folder from Community to backup (this may take a few seconds)...")

    if dest_copied_folder.exists():
        shutil.rmtree(dest_copied_folder)  # Clean up if a previous copy exists
    shutil.copytree(community_airport_path, dest_copied_folder)

    # 6. STEP 3: Rename the copied folder by removing the 'AIRPORT ' prefix
    clean_folder_path = backup_folder / internal_folder_name
    if clean_folder_path.exists():
        shutil.rmtree(clean_folder_path)

    dest_copied_folder.rename(clean_folder_path)
    print(f"🏷️ Folder cleanly renamed to: {internal_folder_name}")

    # 7. STEP 4: Compress the clean folder, adding -SHRINKED to the new RAR name
    new_rar_name = f"{base_rar_for_name.stem}-SHRINKED{base_rar_for_name.suffix}"
    new_rar_path = backup_folder / new_rar_name

    print(f"🗜️ Compressing to {new_rar_name}...")
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
        messagebox.showerror("Error", f"WinRAR compression failed:\n{comp_result.stderr}")
        return

    # 8. Clean up temporary copied folder to leave the backup directory clean
    print(f"🧹 Removing temporary intermediate folder...")
    shutil.rmtree(clean_folder_path)

    print(f"✨ Process completed with 100% clean structure!")

    status_msg = f"The airport has been successfully packaged.\n\n• New backup (shrunk): {new_rar_name}"
    if is_already_off:
        status_msg += f"\n• Note: The original .rar was already set to .off previously."
    else:
        status_msg += f"\n• Original protected as: {base_rar_for_name.name}.off"

    messagebox.showinfo("Process Completed!", status_msg)


if __name__ == "__main__":
    main()