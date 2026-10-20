import os
import sys
import traceback
import subprocess
import threading
import time, datetime
import pygame
from SimConnect import SimConnect, AircraftRequests
import xml.etree.ElementTree as ET
from typing import Dict, Any
from controls import BaseControl

# Global flag to signal background process monitoring status
_msfs_is_running = True


def load_configurations(xml_path: str, joysticks_dict: Dict[str, Any], aircraft_requests) -> Dict[str, BaseControl]:
    """Load control configurations from the XML file."""
    tree = ET.parse(xml_path)
    root = tree.getroot()
    controls: Dict[str, BaseControl] = {}

    for ctrl_elem in root.findall("control"):
        ctrl_id = ctrl_elem.get("id")
        # Delegate creation entirely to the base class
        controls[ctrl_id] = BaseControl.create(ctrl_elem, joysticks_dict, aircraft_requests)

    return controls


def monitor_msfs_process() -> None:
    """Background thread function to check if MSFS is running without blocking the main loop."""
    global _msfs_is_running

    current_th = threading.current_thread()
    print(f"[BACKGROUND THREAD] Running in: {current_th.name} (ID: {current_th.ident})")

    while _msfs_is_running:
        try:
            # Query Windows tasklist for the MSFS process (runs safely in background)
            output = subprocess.check_output('tasklist /FI "IMAGENAME eq FlightSimulator.exe"', shell=True, text=True)
            # print('Checked MSFS .................................. ' + str(time.time() - t1))
            if "FlightSimulator.exe" not in output:
                print("MSFS process no longer detected in background monitor.")
                _msfs_is_running = False
                break
        except Exception:
            pass

        # Check every few seconds to minimize CPU overhead
        time.sleep(5.0)


def main() -> None:
    """Main execution loop for the hardware bridge."""
    global _msfs_is_running

    main_th = threading.current_thread()
    print(f"[MAIN THREAD] Running in: {main_th.name} (ID: {main_th.ident})")

    # Start the background monitoring thread so it never blocks the 60 FPS main loop
    monitor_thread = threading.Thread(target=monitor_msfs_process, daemon=True)
    monitor_thread.start()

    pygame.init()
    pygame.joystick.init()

    # Discover and map available joysticks by GUID
    joysticks: Dict[str, Any] = {
        pygame.joystick.Joystick(i).get_guid(): pygame.joystick.Joystick(i)
        for i in range(pygame.joystick.get_count())
    }

    for guid, js in joysticks.items():
        js.init()
        print(f"Joystick detected: {js.get_name()} [GUID: {guid}]")

    # Initialize SimConnect bridge
    sm = SimConnect()
    aq = AircraftRequests(sm, _time=50)

    # Determine absolute path for resources whether running as script or frozen .exe
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))

    mappings_file = os.path.join(base_path, "mappings.xml")

    # Load OOP configurations from XML using the robust absolute path
    controls = load_configurations(xml_path=mappings_file, joysticks_dict=joysticks, aircraft_requests=aq)

    clock = pygame.time.Clock()
    print("Starting OOP hardware bridge main loop...")

    running = True
    while running:
        dt = clock.tick(60) / 1000.0  # Delta time in seconds (target 60 FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # If background monitor detected MSFS closure, break loop
        if not _msfs_is_running:
            print("MSFS closed. Shutting down bridge...")
            break

        try:
            # Update all loaded controls efficiently each frame without lag
            for ctrl_id, control_obj in controls.items():
                control_obj.update(aq, dt, joysticks)
        except Exception as e:
            print(f"SimConnect connection lost: {e}")
            traceback.print_exc()
            break

    pygame.quit()


if __name__ == "__main__":
    # Determine base directory to save log.txt in the executable's folder
    if getattr(sys, 'frozen', False):
        app_dir = os.path.dirname(sys.executable)
    else:
        app_dir = os.path.dirname(os.path.abspath(__file__))

    log_file_path = os.path.join(app_dir, "log.txt")

    try:
        main()
    except Exception as e:
        # Get current date and time for the error record
        current_timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Catch any unhandled exception and write the timestamp and full traceback to log.txt
        with open(log_file_path, "w", encoding="utf-8") as log_file:
            log_file.write(f"=== UNHANDLED EXCEPTION OCCURRED AT [{current_timestamp}] ===\n\n")
            traceback.print_exc(file=log_file)

        # Also print to standard error output
        traceback.print_exc()
        sys.exit(1)