import os
import sys
import traceback
import subprocess
import threading
import time, datetime
import logging
from time import sleep

import pygame
from SimConnect import SimConnect, AircraftRequests, AircraftEvents
import xml.etree.ElementTree as ET
from typing import Dict, Any
from controls import BaseControl

MAPPINGS_FILE_NAME = "mappings.xml"
POLLING_FREQUENCY = 60
DEBUG_MODE = False
# DEBUG_MODE = True

# Global flags to track MSFS state across threads
_msfs_is_running = True
_active_aircraft = ""


class ControlWrapper:
    def __init__(self, control_id: str, control_obj: BaseControl, control_thread: threading.Thread) -> None:
        self.control_id = control_id
        self.control_obj = control_obj
        self.control_thread = control_thread


def load_configurations(joysticks_dict: Dict[str, Any], aircraft_requests, aircraft_events) -> Dict[str, ControlWrapper]:
    global _active_aircraft

    """Load default control configurations and override with specific aircraft mappings if available."""
    logging.info(f"LOADING CONFIGURATIONS FOR AIRCRAFT: {_active_aircraft}")

    controls: Dict[str, ControlWrapper] = {}
    sim_lock = threading.Lock()

    # 1. Load default configurations (Global base mapping)
    # Determine absolute path for resources whether running as script or frozen.exe
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))

    default_xml_path = os.path.join(base_path, MAPPINGS_FILE_NAME)
    if os.path.exists(default_xml_path):
        tree = ET.parse(default_xml_path)
        root = tree.getroot()

        for ctrl_elem in root.findall("control"):
            ctrl_id = ctrl_elem.get("id")
            controls[ctrl_id] = ControlWrapper(
                ctrl_id,
                BaseControl.create(ctrl_elem, joysticks_dict, aircraft_requests, aircraft_events, sim_lock),
                None
            )

        # Check if the active aircraft has a specific folder mapped in the XML
        aircraft_folder = get_aircraft_folder_from_xml(root, _active_aircraft)
    else:
        logging.error(f"Default mappings file not found at {default_xml_path}")
        return controls

    # 2. Load and override with specific aircraft configurations if available
    if aircraft_folder:
        specific_xml_path = os.path.join(base_path, "Aircraft Mappings", aircraft_folder, MAPPINGS_FILE_NAME)
        if os.path.exists(specific_xml_path):
            logging.info(f"Applying specific controls from: {specific_xml_path}")
            aircraft_tree = ET.parse(specific_xml_path)
            aircraft_root = aircraft_tree.getroot()

            for ctrl_elem in aircraft_root.findall("control"):
                ctrl_id = ctrl_elem.get("id")
                # Overwrite or add specific controls for this aircraft
                controls[ctrl_id] = ControlWrapper(ctrl_id, BaseControl.create(ctrl_elem, joysticks_dict, aircraft_requests, aircraft_events, sim_lock),None)
                logging.info(f"Loaded control '{ctrl_id}' with specific aircraft configuration.")
        else:
            logging.warning(
                f"Aircraft folder mapped to '{aircraft_folder}', but no mappings.xml found at {specific_xml_path}")

    # 3. Create and start a dedicated thread for each control object in the final dictionary
    for control_id, control in controls.items():
        t = threading.Thread(
            target=control.control_obj.update_threaded,
            args=(POLLING_FREQUENCY,),
            daemon=True,
            name=f"ControlThread-{control_id}"
        )
        control.control_thread = t
        t.start()

    return controls


def get_aircraft_folder_from_xml(root: ET.Element, active_aircraft: Any) -> str | None:
    """Find and return the specific aircraft folder name based on the active aircraft title."""
    if not active_aircraft:
        return None

    # Decode bytes to string if necessary to avoid comparison mismatch
    if isinstance(active_aircraft, bytes):
        active_aircraft = active_aircraft.decode('utf-8', errors='ignore').strip()
    else:
        active_aircraft = str(active_aircraft).strip()

    mappings_elem = root.find("aircraft_mappings")
    if mappings_elem is not None:
        for aircraft_elem in mappings_elem.findall("aircraft"):
            folder_name = aircraft_elem.get("name")
            for id_elem in aircraft_elem.findall("aircraft_id"):
                if id_elem.text and id_elem.text.strip() == active_aircraft:
                    return folder_name

    return None


def get_log_path():
    if getattr(sys, 'frozen', False):
        app_dir = os.path.dirname(sys.executable)
    else:
        app_dir = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(app_dir, "log.txt")


def setup_logging(debug_mode: bool = False) -> None:
    level = logging.DEBUG if debug_mode else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s.%(msecs)03d [%(levelname)s] [%(threadName)s] %(message)s",
        datefmt="%H:%M:%S"
    )


def monitor_msfs_process() -> None:
    """Background thread function to check if MSFS is running without blocking the main loop."""
    global _msfs_is_running

    current_th = threading.current_thread()
    logging.info(f"[MSFS MONITOR THREAD] Running in: {current_th.name} (ID: {current_th.ident})")

    while _msfs_is_running:
        try:
            # Query Windows tasklist for the MSFS process safely in the background
            output = subprocess.check_output(args='tasklist /FI "IMAGENAME eq FlightSimulator.exe"', shell=True, text=True)
            _msfs_is_running = "FlightSimulator.exe" in output
            # logging.debug(f"MSFS is running = {_msfs_is_running}")

        except Exception:
            _msfs_is_running = False
            logging.error("FATAL ERROR IN MSFS MONITOR THREAD. CLOSING")
            traceback.print_exc()

        time.sleep(5)  # Check every 5 seconds without blocking main 60 FPS loop


def monitor_active_aircraft(aq: AircraftRequests) -> None:
    """Background thread function to check if MSFS is running without blocking the main loop."""
    global _active_aircraft
    global _msfs_is_running

    current_th = threading.current_thread()
    logging.info(f"[ACTIVE AIRCRAFT MONITOR THREAD] Running in: {current_th.name} (ID: {current_th.ident})")

    while _msfs_is_running:
        try:
            _active_aircraft = aq.get('TITLE')
            # logging.info(f"Active Aircraft is {_active_aircraft}")

        except Exception:
            logging.error("FATAL ERROR IN ACTIVE AIRCRAFT MONITOR THREAD. CLOSING")
            traceback.print_exc()

        time.sleep(5)  # Check every 5 seconds without blocking main 60 FPS loop


def kill_control_threads(controls: Dict[str, ControlWrapper]):
    if controls:
        for control_id, control in controls.items():
            # Signal all control threads to stop
            control.control_obj.running = False
            # Wait for all threads to finish gracefully
            # control.control_thread.join(timeout=0)
            logging.info(f"Waiting for control thread {control_id} to die...")
            control.control_thread.join()

    logging.info("All control threads successfully killed...")


def main() -> None:
    """Main execution loop for the hardware bridge."""
    global _msfs_is_running
    global _active_aircraft

    main_th = threading.current_thread()
    logging.info(f"[MAIN THREAD] Running in: {main_th.name} (ID: {main_th.ident})")

    # Initialize SimConnect bridge
    sm = SimConnect()
    aq = AircraftRequests(sm, _time=50)
    ae = AircraftEvents(sm)

    # Start the background monitoring threads so it never blocks the 60 FPS main loop
    msfs_monitor_thread = threading.Thread(target=monitor_msfs_process, daemon=True)
    msfs_monitor_thread.start()

    active_aircraft_monitor_thread = threading.Thread(target=monitor_active_aircraft, args=(aq,), daemon=True)
    active_aircraft_monitor_thread.start()

    pygame.init()
    pygame.joystick.init()

    # Discover and map available joysticks by GUID
    joysticks: Dict[str, Any] = {
        pygame.joystick.Joystick(i).get_guid(): pygame.joystick.Joystick(i)
        for i in range(pygame.joystick.get_count())
    }

    for guid, js in joysticks.items():
        js.init()
        logging.info(f"Joystick detected: {js.get_name()} [GUID: {guid}]")

    clock = pygame.time.Clock()
    logging.info("Starting OOP hardware bridge main loop...")

    controls = None
    previous_active_aircraft = None

    if _active_aircraft is not None and _active_aircraft.strip() != "":
        controls: Dict[str, ControlWrapper] = load_configurations(joysticks_dict=joysticks, aircraft_requests=aq, aircraft_events=ae)
        previous_active_aircraft = _active_aircraft

    while _msfs_is_running:
        # Refresh Pygame events and joystick states safely on the main thread
        pygame.event.pump()
        clock.tick(POLLING_FREQUENCY) / 1000.0  # Calculate delta time in seconds

        if _active_aircraft is not None and  _active_aircraft.strip() != "" and _active_aircraft != previous_active_aircraft:
            kill_control_threads(controls)
            load_configurations(joysticks, aq, ae)
            previous_active_aircraft = _active_aircraft

    # If background monitor detected MSFS closure, break loop
    logging.info("MSFS closed. Terminating control threads and exiting...")

    logging.info('Bye!!!!!!!!!!!!!!!!!!!!')
    pygame.quit()


if __name__ == "__main__":
    setup_logging(debug_mode=DEBUG_MODE)

    try:
        main()
    except Exception as e:
        # Get current date and time for the error record
        current_timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Catch any unhandled exception and write the timestamp and full traceback to log.txt
        with open(get_log_path(), "w", encoding="utf-8") as log_file:
            traceback.print_exc(file=log_file)
            log_file.write(f"=== UNHANDLED EXCEPTION OCCURRED AT [{current_timestamp}] ===\n\n")

        # Also print to standard error output
        traceback.print_exc()
        sys.exit(1)