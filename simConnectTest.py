import time
from SimConnect import SimConnect, AircraftRequests, AircraftEvents


def monitor_camera_state():
    print("Conectando a MSFS a través de SimConnect...")
    # Inicializar la conexión con SimConnect
    sm = SimConnect()
    aq = AircraftRequests(sm, _time=100)
    ae = AircraftEvents(sm)

    print("¡Conectado! Leyendo 'CAMERA STATE' cada 500ms durante 30 segundos...")
    print("Cambia de vista en el simulador para ver cómo cambia el valor.\n")

    start_time = time.time()
    duration = 300.0  # Duración total en segundos
    interval = 1  # Intervalo de 500 ms

    # sim_var = "CAMERA_SUBSTATE"
    # sim_var = "CAMERA_VIEW_TYPE_AND_INDEX_MAX"
    # sim_var = "CAMERA_REQUEST_ACTION"
    # sim_var = "CAMERA_VIEW_TYPE_AND_INDEX"
    # sim_var= "COCKPIT_CAMERA_HEADLOOK"
    # sim_var= "BRAKE_LEFT_POSITION"
    # sim_var2= "BRAKE_RIGHT_POSITION"
    # sim_var= "AXIS_LEFT_BRAKE_SET"
    sim_var= "TITLE"

    # time.sleep(2)
    # print(f"Was... [{time.strftime("%H:%M:%S")}] {sim_var} -> {aq.get(sim_var)}")
    # aq.set(sim_var, 1.0)
    # print(f"Is.... [{time.strftime("%H:%M:%S")}] {sim_var} -> {aq.get(sim_var)}")
    # time.sleep(2)
    # aq.set(sim_var, 2.0)
    # print(f"Is.... [{time.strftime("%H:%M:%S")}] {sim_var} -> {aq.get(sim_var)}")
    # time.sleep(2)

    # aq.set(sim_var, 1.0)

    sm = SimConnect()
    aq = AircraftRequests(sm, _time=100)
    ae = AircraftEvents(sm)

    brake_left = ae.find("AXIS_LEFT_BRAKE_SET")
    brake_left(-16383)
    time.sleep(1)

    print("Left pedal:", aq.get("A32NX_LEFT_BRAKE_PEDAL_INPUT"))

    brake_left(16383)
    time.sleep(1)

    print("Left pedal:", aq.get("A32NX_LEFT_BRAKE_PEDAL_INPUT"))

    # while time.time() - start_time < duration:
    #     # Obtener el valor de la variable CAMERA STATE del simulador
    #     state = aq.get(sim_var)
    #     # state = aq.set(sim_var, 0.1)
    #     state2 = ""
    #     timestamp = time.strftime("%H:%M:%S")
    #
    #     print(f"[{timestamp}] {sim_var} -> {state}")
    #     # print(f"[{timestamp}] {sim_var2} -> {state2}")
    #     # print(f"[{timestamp}] {sim_var2} -> {state2}")
    #
    #     time.sleep(interval)

    print("\nDone................")


if __name__ == "__main__":
    monitor_camera_state()