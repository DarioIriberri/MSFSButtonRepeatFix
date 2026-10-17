import keyboard, pydirectinput, time, ctypes, psutil
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import xml.etree.ElementTree as ET

class ConditionType(str, Enum):
    KEY_ACTIVATED = "key_activated"
    JOYSTICK_ACTIVATED = "joystick_activated"
    SIMVAR_CHECK = "simvar_check"

pydirectinput.PAUSE = 0.02

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
    "esc": 1, "caps_lock": 58, "`": 41, # 41 is grave or tilde

    # 7. SYSTEM & MULTIMEDIA KEYS
    "print_screen": 55, "scroll_lock": 70, "pause": 69, "num_lock": 69,

    # 8. MODIFIERS
    "shift": 42, "left_shift": 42, "right_shift": 54, "ctrl": 29, "alt": 56,
}


class Action:
    def __init__(
            self,
            action_elem: ET.Element,
            joysticks_dict: Dict[str, Any]
    ) -> None:

        self.action_id: str = action_elem.get("id")
        self.inputs: List[InputBinding] = []

        # Direction and analog control value (if applicable)
        dir_elem = action_elem.find("direction")
        self.direction: int = int(dir_elem.text) if dir_elem is not None and dir_elem.text else 0

        ctrl_elem = action_elem.find("ctrl_value")
        self.ctrl_value: float = float(ctrl_elem.text) if ctrl_elem is not None and ctrl_elem.text else 0

        # Joystick mapping
        joystick_elem = action_elem.find("joystick_mapping")
        if joystick_elem is not None:
            self.inputs.append(JoystickInput(joystick_elem, joysticks_dict))

        # Main activation key mapping
        key_mapping_elem = action_elem.find("key_mapping")
        if key_mapping_elem is not None:
            self.inputs.append(KeyInput(key_mapping_elem))

        self._was_active = False

        # Unified list of execution steps based on the 'type' attribute
        self.execution_steps: List[Dict[str, Any]] = []

        for exec_elem in action_elem.findall("execution"):
            exec_type = exec_elem.get("type")
            r_elem = exec_elem.find("repeats")
            d_elem = exec_elem.find("delay_ms_after_pressed")

            # Parse common conditions for this execution step
            step_conditions = []
            conds_elem = exec_elem.find("conditions")
            if conds_elem is not None:
                for cond_elem in conds_elem.findall("condition"):
                    raw_type = cond_elem.get("type")
                    try:
                        cond_type = ConditionType(raw_type)
                    except ValueError:
                        raise ValueError(f"Unknown condition type in XML: {raw_type}")

                    step_conditions.append({
                        "type": cond_type,
                        "id": cond_elem.get("id"),
                        "value": cond_elem.find("value").text.strip() if cond_elem.find(
                            "value") is not None and cond_elem.find("value").text else ""
                    })

            # Base step structure
            step_data = {
                "type": exec_type,
                "repeats": int(r_elem.text.strip()) if r_elem is not None and r_elem.text else 1,
                "delay_ms": int(d_elem.text.strip()) if d_elem is not None and d_elem.text else 0,
                "conditions": step_conditions
            }

            # Fill specific data based on execution type
            if exec_type == "key_press":
                k_elem = exec_elem.find("key")
                s_elem = exec_elem.find("shift")
                c_elem = exec_elem.find("ctrl")
                a_elem = exec_elem.find("alt")

                step_data.update({
                    "key_name": k_elem.text.strip().lower() if k_elem is not None and k_elem.text else None,
                    "shift": s_elem.text.strip().lower() == "true" if s_elem is not None and s_elem.text else False,
                    "ctrl": c_elem.text.strip().lower() == "true" if c_elem is not None and c_elem.text else False,
                    "alt": a_elem.text.strip().lower() == "true" if a_elem is not None and a_elem.text else False,
                })

            elif exec_type == "sim_var":
                name_elem = exec_elem.find("sim_var_name")
                val_elem = exec_elem.find("value")  # Optional in case you want to pass a direct value

                step_data.update({
                    "name": name_elem.text.strip() if name_elem is not None and name_elem.text else None,
                    "value": float(val_elem.text.strip()) if val_elem is not None and val_elem.text else 1.0
                })

            self.execution_steps.append(step_data)

    def is_active(self) -> bool:
        is_active = any(inp.is_active() for inp in self.inputs)
        self._was_active = is_active
        return is_active

    def was_active(self) -> bool:
        return self._was_active

    def get_active_trigger_description(self) -> str:
        for inp in self.inputs:
            if inp.is_active():
                # If it is a keyboard key
                if isinstance(inp, KeyInput):
                    return f"Key: {inp.key_code}"
                # If it is a joystick (you can adapt it according to JoystickInput attributes)
                elif isinstance(inp, JoystickInput):
                    return f"Joystick (Button/Hat)"
        return "Unknown"

    def _is_msfs_active(self) -> bool:
        """Retrieves the title of the active window using the Windows API via ctypes."""
        try:
            hwnd = ctypes.windll.user32.GetForegroundWindow()
            if not hwnd:
                return False

            pid = ctypes.c_ulong()
            ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))

            process = psutil.Process(pid.value)
            return process.name().lower() == "flightsimulator.exe"
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            return False
        except Exception:
            return False

    def execute(self, aircraft: Any) -> bool:
        """Iterate and execute all sequential steps defined in the XML."""
        if not hasattr(self, "execution_steps") or not self.execution_steps:
            print(f"[Action {self.action_id}] No execution steps defined.")
            return False

        print(f"\n[Action {self.action_id}] Starting sequence of {len(self.execution_steps)} step(s)...")

        triggered = False

        if not self._is_msfs_active():
            print(f"     [X] MSFS Window not active!!!!!!!!!!!!!!!!!!!!! Skipping...")
            return False

        for idx, step in enumerate(self.execution_steps):
            step_type = step["type"]
            print(f"  -> [Step {idx + 1}] Type: '{step_type}'")

            # 1. Validate the specific conditions of this step before executing it
            if not self._check_conditions(step["conditions"], aircraft):
                print(f"     [X] Condition NOT met for step {idx + 1} ({step_type}). Skipping...")
                continue

            print(f"     [OK] Conditions passed for step {idx + 1}.")
            repeats = step["repeats"]
            delay_sec = step["delay_ms"] / 1000.0  # Convert milliseconds to seconds

            # 2. Execution based on step type
            if step_type == "key_press":
                key_name = step["key_name"]

                if not key_name:
                    print(f"     [!] 'key_name' empty in step {idx + 1}. Skipping.")
                    continue

                shift = step["shift"]
                ctrl = step["ctrl"]
                alt = step["alt"]
                print(f"     [Keypress] Key: '{key_name}' | Modifiers -> Shift: {shift}, Ctrl: {ctrl}, Alt: {alt} | Repeats: {repeats}")

                # Activate global modifiers for this block
                if shift: pydirectinput.keyDown('shift')
                if ctrl: pydirectinput.keyDown('ctrl')
                if alt: pydirectinput.keyDown('alt')

                print('Now press key.....')
                for r in range(repeats):
                    pydirectinput.press(key_name)
                    print(f"       -> Key '{key_name}' pressed (Repetition {r + 1}/{repeats})")
                    if delay_sec > 0:
                        time.sleep(delay_sec)

                # Release modifiers
                if shift: pydirectinput.keyUp('shift')
                if ctrl: pydirectinput.keyUp('ctrl')
                if alt: pydirectinput.keyUp('alt')

                triggered = True

            elif step_type == "sim_var":
                sim_name = step["name"]
                sim_val = step["value"]
                if not sim_name:
                    print(f"     [!] 'sim_var_name' empty in step {idx + 1}. Skipping.")
                    continue

                print(f"     [SimVar] Writing '{sim_name}' = {sim_val} | Repeats: {repeats}")
                for r in range(repeats):
                    try:
                        aircraft.set(sim_name, sim_val)
                        triggered = True
                        print(f"       -> Written {sim_name} = {sim_val} (Repetition {r + 1}/{repeats})")
                        if delay_sec > 0:
                            time.sleep(delay_sec)
                    except Exception as e:
                        print(f"     [Error] Error writing sim_var {sim_name}: {e}")

                    if delay_sec > 0:
                        time.sleep(delay_sec)

        print(f"[Action {self.action_id}] Execution sequence finished.\n")
        return triggered


    def _check_conditions(self, conditions: List[Dict[str, Any]], aircraft: Any) -> bool:
        """Evaluate a list of conditions against the current state and trigger."""
        if not conditions:
            return True

        current_trigger = self.get_action_trigger_type()

        for cond in conditions:
            ctype = cond["type"]
            cval = cond["value"].lower()

            if ctype == ConditionType.KEY_ACTIVATED:
                expected = (cval == "true")
                is_key_active = (current_trigger == ConditionType.KEY_ACTIVATED)
                if is_key_active != expected:
                    return False

            elif ctype == ConditionType.JOYSTICK_ACTIVATED:
                expected = (cval == "true")
                is_joystick_active = (current_trigger == ConditionType.JOYSTICK_ACTIVATED)
                if is_joystick_active != expected:
                    return False

            elif ctype == ConditionType.SIMVAR_CHECK:
                sim_var = cond["id"]
                try:
                    current_val = aircraft.get(sim_var)
                    if str(current_val).lower() != cval:
                        return False
                except Exception:
                    return False

        return True

    def get_action_trigger_type(self) -> str:
        for inp in self.inputs:
            if inp.is_active():
                if isinstance(inp, KeyInput):
                    return "key_activated"
                elif isinstance(inp, JoystickInput):
                    return "joystick_activated"
        return "none"

class InputBinding:
    def is_active(self) -> bool:
        raise NotImplementedError("Implement in input subclasses")


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
            num_buttons = self.target_joystick.get_numbuttons()
            buttons_active = True
            for i in range(num_buttons):
                pressed = self.target_joystick.get_button(i)
                should_press = i in self.buttons
                if pressed != should_press:
                    buttons_active = False
                    break

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

        # if keyboard.is_pressed(57):

        # print('****************************************************************************')
        # print('keyboard.is_pressed("shift") = ' + str(keyboard.is_pressed("shift")))
        # print('keyboard.is_pressed("ctrl") = ' + str(keyboard.is_pressed("ctrl")))
        # print('keyboard.is_pressed("alt") = ' + str(keyboard.is_pressed("alt")))
        # print('self.shift ' + str(self.shift))
        # print('self.ctrl ' + str(self.ctrl))
        # print('self.alt ' + str(self.alt))
        # print('space PRESSED!!!!!!!!!!!!')
        # print('----------------------')
        # print('----------------------')
        # print('shift_ok) = ' + str(shift_ok))
        # print('ctrl_ok) = ' + str(ctrl_ok))
        # print('alt_ok) = ' + str(alt_ok))
        # print('----------------------')
        # print('-------------------------------------------------------------------------')
        # print('keyboard.is_pressed("shift") = ' + str(keyboard.is_pressed("shift")))
        # print('keyboard.is_pressed("ctrl") = ' + str(keyboard.is_pressed("ctrl")))
        # print('keyboard.is_pressed("alt") = ' + str(keyboard.is_pressed("alt")))
        # print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')

        if keyboard.is_pressed(self.key_code) and shift_ok and ctrl_ok and alt_ok:
            # print('returning trueeeeeeeeee')
            return True