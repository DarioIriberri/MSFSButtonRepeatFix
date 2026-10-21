import os
import sys
import traceback
import subprocess
import threading
import time, datetime
from time import sleep

import pygame
from SimConnect import SimConnect, AircraftRequests
import xml.etree.ElementTree as ET
from typing import Dict, Any
from controls import BaseControl

POLLING_FREQUENCY = 60

# Global flag to track MSFS state across threads
_msfs_is_running = True

def load_configurations(xml_path: str, joysticks_dict: Dict[str, Any], aircraft_requests, sim_lock) -> Dict[str, BaseControl]:
    """Load control configurations from the XML file."""
    tree = ET.parse(xml_path)
    root = tree.getroot()
    controls: Dict[str, BaseControl] = {}

    for ctrl_elem in root.findall("control"):
        ctrl_id = ctrl_elem.get("id")
        # Delegate creation entirely to the base class
        controls[ctrl_id] = BaseControl.create(ctrl_elem, joysticks_dict, aircraft_requests, sim_lock)

    return controls


def monitor_msfs_process() -> None:
    """Background thread function to check if MSFS is running without blocking the main loop."""
    global _msfs_is_running

    current_th = threading.current_thread()
    print(f"[BACKGROUND THREAD] Running in: {current_th.name} (ID: {current_th.ident})")

    while _msfs_is_running:
        try:
            # Query Windows tasklist for the MSFS process safely in the background
            output = subprocess.check_output(args='tasklist /FI "IMAGENAME eq FlightSimulator.exe"', shell=True, text=True)
            _msfs_is_running = "FlightSimulator.exe" in output
            # print(f"MSFS is running = {_msfs_is_running}")

        except Exception:
            pass
        time.sleep(5)  # Check every 5 seconds without blocking main 60 FPS loop


def main() -> None:
    """Main execution loop for the hardware bridge."""
    global _msfs_is_running

    main_th = threading.current_thread()
    print(f"[MAIN THREAD] Running in: {main_th.name} (ID: {main_th.ident})")

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

    sim_lock = threading.Lock()
    # Load OOP configurations from XML using the robust absolute path
    controls = load_configurations(xml_path=mappings_file, joysticks_dict=joysticks, aircraft_requests=aq, sim_lock=sim_lock)

    clock = pygame.time.Clock()
    print("Starting OOP hardware bridge main loop...")

    # Start the background monitoring thread so it never blocks the 60 FPS main loop
    monitor_thread = threading.Thread(target=monitor_msfs_process, daemon=True)
    monitor_thread.start()

    # Create a shared lock for thread-safe SimConnect operations
    # Create and start a dedicated thread for each control object
    control_threads = []
    for ctrl_id, control_obj in controls.items():
        t = threading.Thread(
            target=control_obj.update_threaded,
            args=(POLLING_FREQUENCY,),
            daemon=True,
            name=f"ControlThread-{ctrl_id}"
        )
        control_threads.append(t)
        t.start()

    while _msfs_is_running:
        # Refresh Pygame events and joystick states safely on the main thread
        pygame.event.pump()
        clock.tick(POLLING_FREQUENCY) / 1000.0  # Calculate delta time in seconds

    # If background monitor detected MSFS closure, break loop
    print("MSFS closed. Terminating control threads and exiting...")

    # Signal all control threads to stop
    for ctrl_id, control_obj in controls.items():
        control_obj.running = False

    # Wait for all threads to finish gracefully
    for t in control_threads:
        t.join(timeout=1.0)

    print('Bye!!!!!!!!!!!!!!!!!!!!')
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