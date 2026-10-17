import pygame
from SimConnect import SimConnect, AircraftRequests
import xml.etree.ElementTree as ET
from typing import Dict, Any
from controls import BaseControl

def load_configurations(xml_path: str, joysticks_dict: Dict[str, Any], aircraft_requests) -> Dict[str, BaseControl]:
    tree = ET.parse(xml_path)
    root = tree.getroot()
    controls: Dict[str, BaseControl] = {}

    for ctrl_elem in root.findall("control"):
        ctrl_id = ctrl_elem.get("id")
        # Delegate creation entirely to the base class
        controls[ctrl_id] = BaseControl.create(ctrl_elem, joysticks_dict, aircraft_requests)

    return controls

def main() -> None:
    pygame.init()
    pygame.joystick.init()

    joysticks: Dict[str, Any] = {
        pygame.joystick.Joystick(i).get_guid(): pygame.joystick.Joystick(i)
        for i in range(pygame.joystick.get_count())
    }

    for guid, js in joysticks.items():
        js.init()
        print(f"Joystick detected: {js.get_name()} [GUID: {guid}]")

    # Initialize SimConnect
    sm = SimConnect()
    aq = AircraftRequests(sm, _time=50)

    # Load OOP configurations from XML
    controls = load_configurations("mappings.xml", joysticks, aq)

    clock = pygame.time.Clock()
    print("Starting OOP hardware bridge main loop...")

    running = True
    while running:
        # print(f"Headlook={ aq.get("COCKPIT_CAMERA_HEADLOOK")} | Substate={aq.get("CAMERA_SUBSTATE")}")
        dt = clock.tick(60) / 1000.0  # Delta time in seconds (target 60 FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Update all loaded controls efficiently
        for ctrl_id, control_obj in controls.items():
            control_obj.update(aq, dt, joysticks)

    pygame.quit()


if __name__ == "__main__":
    main()