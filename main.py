import pygame
from SimConnect import SimConnect, AircraftRequests
import xml.etree.ElementTree as ET
from typing import Dict, Any
from controls import BaseControl

def load_configurations(xml_path: str, joysticks_dict: Dict[str, Any]) -> Dict[str, BaseControl]:
    tree = ET.parse(xml_path)
    root = tree.getroot()
    controls: Dict[str, BaseControl] = {}

    for ctrl_elem in root.findall("control"):
        ctrl_id = ctrl_elem.get("id")
        # Delegamos completamente la creación en la clase base
        controls[ctrl_id] = BaseControl.create(ctrl_elem, joysticks_dict)

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
        print(f"Joystick detectado: {js.get_name()} [GUID: {guid}]")

    # Inicializar SimConnect
    sm = SimConnect()
    aq = AircraftRequests(sm, _time=50)

    # Cargar configuraciones OOP desde el XML
    controls = load_configurations("mappings.xml", joysticks)

    clock = pygame.time.Clock()
    print("Iniciando bucle principal del puente de hardware OOP...")

    running = True
    while running:
        dt = clock.tick(60) / 1000.0  # Delta time en segundos (60 FPS objetivo)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Actualizar todos los controles cargados de forma eficiente
        for ctrl_id, control_obj in controls.items():
            control_obj.update(aq, dt, joysticks)

    pygame.quit()


if __name__ == "__main__":
    main()