import keyboard
from typing import Dict, List, Optional, Tuple, Any
import xml.etree.ElementTree as ET

KEY_MAP: Dict[str, int] = {
    # 1. ALPHANUMERIC & SYMBOLS
    "a": 30, "b": 48, "c": 46, "d": 32, "e": 18, "f": 33, "g": 34, "h": 35,
    "i": 23, "j": 36, "k": 37, "l": 38, "m": 50, "n": 49, "o": 24, "p": 25,
    "q": 16, "r": 19, "s": 31, "t": 20, "u": 22, "v": 47, "w": 17, "x": 45,
    "y": 21, "z": 44,
    "0": 11, "1": 2, "2": 3, "3": 4, "4": 5, "5": 6, "6": 7, "7": 8,
    "8": 9, "9": 10,
    ".": 52, ",": 51, "minus": 12, "plus": 27, "_": 53,

    # 2. NUMERIC KEYPAD (NUMPAD)
    "num_0": 82, "num_1": 79, "num_2": 80, "num_3": 81, "num_4": 75,
    "num_5": 76, "num_6": 77, "num_7": 71, "num_8": 72, "num_9": 73,
    "num_decimal": 83, "num_+": 78, "num_-": 74,

    # 3. FUNCTION KEYS
    "f1": 59, "f2": 60, "f3": 61, "f4": 62, "f5": 63, "f6": 64,
    "f7": 65, "f8": 66, "f9": 67, "f10": 68, "f11": 87, "f12": 88,

    # 4. NAVIGATION & EDITING KEYS
    "insert": 82, "home": 71, "end": 79, "page_up": 73,
    "page_down": 78, "delete": 83,

    # 5. ARROW KEYS
    "up": 72, "down": 80, "left": 75, "right": 77,

    # 6. SPECIAL CONTROL & EDITING KEYS
    "space": 57, "enter": 28, "tab": 15, "backspace": 14,
    "esc": 1, "caps_lock": 58,

    # 7. SYSTEM & MULTIMEDIA KEYS
    "print_screen": 55, "scroll_lock": 70, "pause": 69, "num_lock": 69,

    # 8. MODIFIERS
    "shift": 42, "left_shift": 42, "right_shift": 54, "ctrl": 29, "alt": 56,
}

class Action:
    def __init__(
            self, action_elem: ET.Element,
            joysticks_dict: Dict[str, Any]
    )-> None:

        self.action_id: str = action_elem.get("id")
        self.inputs: List[InputBinding] = []
        self.direction: int = int(action_elem.find("direction").text if action_elem.find("direction") is not None else 0)
        self.ctrl_value: float = float(action_elem.find("ctrl_value").text) if action_elem.find("ctrl_value") is not None else 0

        joystick_elem = action_elem.find("joystick_mapping")
        if joystick_elem is not None:
            self.inputs.append(JoystickInput(joystick_elem, joysticks_dict))

        key_mapping_elem = action_elem.find("key_mapping")
        if key_mapping_elem is not None:
            self.inputs.append(KeyInput(key_mapping_elem))

        self._was_active = False

        key_press_elem = action_elem.find("key_press")
        if key_press_elem:
            self.key_press_name: str = key_press_elem.find("key").text.strip().lower()
            self.ctrl = "ctrl+" if (e := key_press_elem.find("ctrl")) is not None and (e.text or "").strip().lower() == "true" else ""
            self.shift = "shift+" if (e := key_press_elem.find("shift")) is not None and (e.text or "").strip().lower() == "true" else ""
            self.alt = "alt+" if (e := key_press_elem.find("alt")) is not None and (e.text or "").strip().lower() == "true" else ""

    def is_active(self) -> bool:
        is_active = any(inp.is_active() for inp in self.inputs)
        self._was_active = is_active
        return is_active

    def was_active(self) -> bool:
        return self._was_active

    def get_active_trigger_description(self) -> str:
        for inp in self.inputs:
            if inp.is_active():
                # Si es una tecla del teclado
                if isinstance(inp, KeyInput):
                    return f"Key: {inp.key_code}"
                # Si es un joystick (puedes adaptarlo según los atributos que tenga JoystickInput)
                elif isinstance(inp, JoystickInput):
                    return f"Joystick (Button/Hat)"
        return "Unknown"

    def execute(self):
        if self.key_press_name:
            key_send = self.ctrl + self.shift + self.alt + self.key_press_name
            keyboard.send(key_send)

class InputBinding:
    def is_active(self) -> bool:
        raise NotImplementedError("Implementar en subclases de entrada")


class JoystickInput(InputBinding):
    def __init__(
            self,
            js_elem: ET.Element,
            joysticks_dict: Dict[str, Any]
    ) -> None:

        name_elem = js_elem.find("joystick_name")
        guid_elem = js_elem.find("joystick_guid")
        btn_elem = js_elem.find("button_mapping")
        hat_elem = js_elem.find("hat_mapping")

        self.joystick_name: str = name_elem.text.strip() if name_elem is not None and name_elem.text else ""
        self.joystick_guid: str = guid_elem.text.strip() if guid_elem is not None and guid_elem.text else ""
        self.buttons: List[int] = [int(b.text) for b in btn_elem.findall("button")] if btn_elem is not None else []

        self.hat: Optional[Tuple[int, int, int]] = None
        if hat_elem is not None and hat_elem.find("hat_index") is not None:
            self.hat = (
                int(hat_elem.find("hat_index").text),
                int(hat_elem.find("hat_x").text),
                int(hat_elem.find("hat_y").text)
            )

        self.target_joystick: Optional[Any] = self._find_matching_joystick(joysticks_dict)

    def _find_matching_joystick(self, joysticks_dict: Dict[str, Any]) -> Optional[Any]:
        for js_id, js_obj in joysticks_dict.items():
            js_name = js_obj.get_name()
            if self.joystick_guid and self.joystick_guid == js_id:
                return js_obj
            if not self.joystick_guid and self.joystick_name and self.joystick_name in js_name:
                return js_obj
        return None

    def is_active(self) -> bool:
        if not self.target_joystick:
            return False

        buttons_active = False
        if self.buttons:
            buttons_active = all(
                btn < self.target_joystick.get_numbuttons() and self.target_joystick.get_button(btn)
                for btn in self.buttons
            )

        hat_active = False
        if self.hat:
            hat_idx, target_x, target_y = self.hat
            if hat_idx < self.target_joystick.get_numhats():
                hx, hy = self.target_joystick.get_hat(hat_idx)
                if hx == target_x and hy == target_y:
                    hat_active = True

        return buttons_active or hat_active


class KeyInput(InputBinding):
    def __init__(
            self,
            key_elem: ET.Element

    ) -> None:

        key_name = key_elem.find("key").text.strip().lower() if key_elem.find("key") is not None else ""
        self.key_code: Optional[int] = KEY_MAP.get(key_name)
        self.shift: bool = key_elem.find("shift").text.lower() == "true" if key_elem.find("shift") is not None else False
        self.ctrl: bool = key_elem.find("ctrl").text.lower() == "true" if key_elem.find("ctrl") is not None else False
        self.alt: bool = key_elem.find("alt").text.lower() == "true" if key_elem.find("alt") is not None else False

    def is_active(self) -> bool:
        if not self.key_code:
            return False

        shift_ok = keyboard.is_pressed("shift") == self.shift
        ctrl_ok = keyboard.is_pressed("ctrl") == self.ctrl
        alt_ok = keyboard.is_pressed("alt") == self.alt
        if keyboard.is_pressed(self.key_code) and shift_ok and ctrl_ok and alt_ok:
            return True