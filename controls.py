import time
import pygame
from typing import Dict, Optional, Any
from actions import Action
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional

class BaseControl:
    @staticmethod
    def create(ctrl_elem: Any, joysticks: Dict, aircraft_requests) -> "BaseControl":
        ctrl_type = ctrl_elem.get("type", "analog")

        if ctrl_type == "analog":
            return AnalogControl(ctrl_elem, joysticks, aircraft_requests)
        elif ctrl_type == "discrete":
            return DiscreteControl(ctrl_elem, joysticks, aircraft_requests)
        else:
            raise ValueError(f"Unknown control type: {ctrl_type}")

    def __init__(
            self,
            ctrl_elem: ET.Element,
            joysticks_dict: Dict[str, Any],
            aircraft_requests: Any
    ) -> None:

        self.id: str = ctrl_elem.get("id")
        self.sim_variables: List[str] = [
            elem.text.strip() for elem in ctrl_elem.findall("sim_variable") if elem.text
        ]
        self.control_type: str = ctrl_elem.get("type")
        self.actions: Dict[str, Action] = {}
        self.repeat: bool = (ctrl_elem.find("repeat").text.strip().lower() == "true") if ctrl_elem.find("repeat") is not None and ctrl_elem.find("repeat").text else False

        actions: Dict[str, Action] = {}
        for act_elem in ctrl_elem.findall("action"):
            act_id = act_elem.get("id")
            actions[act_id] = Action(act_elem, joysticks_dict)

        self.actions: Dict[str, Action] = actions

        self.init_value: float = float(ctrl_elem.find("init_value").text) if ctrl_elem.find("init_value") is not None else 0
        self.aircraft_requests = aircraft_requests

        temp_current_val = self.aircraft_requests.get(self.sim_variables[0]) if self.sim_variables else None
        self.current_value = temp_current_val if temp_current_val is not None else self.init_value

        self.last_active_action = None

    def _find_active_action(self):
        active_action_obj: Optional[Action] = None
        was_active_action = False

        for act_id, action in self.actions.items():
            was_active_action = action.was_active()
            if action.is_active():
                active_action_obj = action
                break

        return active_action_obj, was_active_action

    def update(self, aircraft: Any, dt: float, joysticks_dict: Dict[str, Any]) -> None:
        raise NotImplementedError("Implement in subclasses")

    # def update_threaded(self, aircraft: Any, dt: float, joysticks_dict: Dict[str, Any]):
    #     clock = pygame.time.Clock()
    #     print(f"Starting control {self.id}...")
    #
    #     running = True
    #     while running:
    #         dt = clock.tick(60) / 1000.0  # Delta time in seconds (target 60 FPS)
    #
    #         for event in pygame.event.get():
    #             if event.type == pygame.QUIT:
    #                 running = False
    #
    #         # If background monitor detected MSFS closure, break loop
    #         if not _msfs_is_running:
    #             print("MSFS closed. Shutting down bridge...")
    #             break
    #
    #         try:
    #             self.update(aq, dt, joysticks)
    #         except Exception as e:
    #             print(f"SimConnect connection lost: {e}")
    #             traceback.print_exc()
    #             break

class AnalogControl(BaseControl):
    def __init__(
            self,
            ctrl_elem: ET.Element,
            joysticks_dict: Dict[str, Any],
            aircraft_requests: Any
    ) -> None:

        super().__init__(ctrl_elem, joysticks_dict, aircraft_requests)
        self.step_fine: float = float(ctrl_elem.find("step_fine").text) if ctrl_elem.find("step_fine") is not None else 0
        self.step_medium: float = float(ctrl_elem.find("step_medium").text) if ctrl_elem.find("step_medium") is not None else self.step_fine
        self.step_fast: float = float(ctrl_elem.find("step_fast").text) if ctrl_elem.find("step_fast") is not None else self.step_medium
        self.time_threshold_1: float = float(ctrl_elem.find("time_threshold_1").text) if ctrl_elem.find("time_threshold_1") is not None else 0
        self.time_threshold_2: float = float(ctrl_elem.find("time_threshold_2").text) if ctrl_elem.find("time_threshold_2") is not None else 0
        self.min_value: float = float(ctrl_elem.find("min_value").text) if ctrl_elem.find("min_value") is not None else 0
        self.max_value: float = float(ctrl_elem.find("max_value").text) if ctrl_elem.find("max_value") is not None else 0

        self.t1 = 0.0

        speed_multiplier_config: Dict[str, Any] = {}
        mult_elem = ctrl_elem.find("speed_multiplier")
        if mult_elem is not None:
            factor_elem = mult_elem.find("multiplier_factor")
            key_mult_elem = mult_elem.find("key_multiplier")
            btn_mult_elem = mult_elem.find("button_multiplier")

            btn_data: Dict[str, Any] = {}
            if btn_mult_elem is not None:
                name_el = btn_mult_elem.find("joystick_name")
                btn_el = btn_mult_elem.find("button")
                btn_data = {
                    "name": name_el.text.strip() if name_el is not None and name_el.text else "",
                    "button": int(btn_el.text) if btn_el is not None and btn_el.text else 0
                }

            speed_multiplier_config = {
                "factor": float(factor_elem.text) if factor_elem is not None and factor_elem.text else 1.0,
                "key_multiplier": key_mult_elem.text.strip().lower() if key_mult_elem is not None and key_mult_elem.text else None,
                "button_multiplier": btn_data
            }

        self.speed_multiplier_config: Dict[str, Any] = speed_multiplier_config or {}
        self.joysticks: Dict[str, Any] = joysticks_dict

        self.press_timers: Dict[str, float] = {action_id: 0.0 for action_id in self.actions}


    def update(self, aircraft: Any, dt: float, joysticks_dict: Dict[str, Any]) -> None:
        active_action_obj, was_active_action = self._find_active_action()

        if active_action_obj and (self.repeat or not was_active_action):
            self.last_active_action = active_action_obj
            trigger_info = active_action_obj.get_active_trigger_description()
            live_value = None
            if not active_action_obj.ignore_live_value:
                live_value = aircraft.get(self.sim_variables[0])
                self.current_value = live_value
                # print(f"LIVE VALUE ============= {live_value}")

            # Sync self.current_value with the sim's
            self.press_timers[active_action_obj.action_id] += dt
            duration = self.press_timers[active_action_obj.action_id]

            for sim_variable in self.sim_variables:
                if active_action_obj.forced_value_on_press is not None:
                    print(f"FORCING VALUE!!!!!!!!!!!!! {sim_variable} [{trigger_info}] --- {self.current_value}")
                    self.current_value = active_action_obj.forced_value_on_press
                else:
                    step = self.step_fine

                    if self.repeat:
                        if duration > self.time_threshold_2:
                            step = self.step_fast
                        elif duration > self.time_threshold_1:
                            step = self.step_medium

                        multiplier = self._check_speed_multiplier(joysticks_dict)
                        step *= multiplier

                    step *= active_action_obj.direction

                    self.current_value += step
                    self.current_value = max(self.current_value, self.min_value)
                    self.current_value = min(self.current_value, self.max_value)
                    print(f"{sim_variable} [{trigger_info}] --- step = {step} --- current.value = {self.current_value}")
                try:
                    if active_action_obj.ignore_live_value or self.current_value != live_value:
                        # print(f"Elaped =========== {time.time() - self.t1}")
                        aircraft.set(sim_variable, self.current_value)
                        self.t1 = time.time()
                except Exception as e:
                    print(f"Error writing {sim_variable}: {e}")
        else:
            if self.last_active_action is not None:
                if self.last_active_action.forced_value_on_release is not None:
                    self.current_value = self.last_active_action.forced_value_on_release
                    for sim_variable in self.sim_variables:
                        try:
                            aircraft.set(sim_variable, self.last_active_action.forced_value_on_release)
                        except Exception as e:
                            print(f"Error writing {sim_variable}: {e}")

                for act_id in self.press_timers:
                    self.press_timers[act_id] = 0.0

                self.last_active_action = None

    def _check_speed_multiplier(self, joysticks_dict: Dict[str, Any]) -> float:
        mult_cfg = self.speed_multiplier_config
        if not mult_cfg:
            return 1.0

        btn_cfg = mult_cfg.get("button_multiplier")
        if btn_cfg and btn_cfg.get("button") is not None:
            target_name = btn_cfg.get("name", "")
            target_btn = btn_cfg.get("button")
            for js_id, js_obj in joysticks_dict.items():
                if target_name in js_obj.get_name():
                    if target_btn < js_obj.get_numbuttons() and js_obj.get_button(target_btn):
                        return float(mult_cfg.get("factor", 1.0))

        key_mult = mult_cfg.get("key_multiplier")
        if key_mult:
            keys = pygame.key.get_pressed()
            if key_mult == "shift" and (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]):
                return float(mult_cfg.get("factor", 1.0))
            elif key_mult == "ctrl" and (keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]):
                return float(mult_cfg.get("factor", 1.0))
            elif key_mult == "alt" and (keys[pygame.K_LALT] or keys[pygame.K_RALT]):
                return float(mult_cfg.get("factor", 1.0))

        return 1.0

class DiscreteControl(BaseControl):
    def __init__(
            self,
            ctrl_elem: ET.Element,
            joysticks_dict: Dict[str, Any],
            aircraft_requests
    ) -> None:

        super().__init__(ctrl_elem, joysticks_dict, aircraft_requests)

    def update(self, aircraft: Any, dt: float, joysticks_dict: Dict[str, Any]) -> None:
        # try:
        active_action_obj, was_active_action = self._find_active_action()

        if active_action_obj and (self.repeat or not was_active_action):
            for sim_variable in self.sim_variables:
                if active_action_obj.ctrl_value:
                    aircraft.set(sim_variable, active_action_obj.ctrl_value)

            triggered = active_action_obj.execute(aircraft)

            if triggered:
                trigger_info = active_action_obj.get_active_trigger_description()
                print(f"{active_action_obj.action_id} [{trigger_info}] --- {self.current_value}")

        # except Exception as e:
        #     print(f"Error writing {self.sim_variable}: {e}")