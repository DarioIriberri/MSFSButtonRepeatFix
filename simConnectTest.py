import time
from SimConnect import SimConnect, AircraftRequests


def monitor_camera_state():
    print("Conectando a MSFS a través de SimConnect...")
    # Inicializar la conexión con SimConnect
    sm = SimConnect()
    aq = AircraftRequests(sm, _time=100)

    print("¡Conectado! Leyendo 'CAMERA STATE' cada 500ms durante 30 segundos...")
    print("Cambia de vista en el simulador para ver cómo cambia el valor.\n")

    start_time = time.time()
    duration = 300.0  # Duración total en segundos
    interval = 0.2  # Intervalo de 500 ms

    # sim_var = "CAMERA_SUBSTATE"
    # sim_var = "CAMERA_VIEW_TYPE_AND_INDEX_MAX"
    # sim_var = "CAMERA_REQUEST_ACTION"
    # sim_var = "CAMERA_VIEW_TYPE_AND_INDEX"
    # sim_var= "COCKPIT_CAMERA_HEADLOOK"
    sim_var= "BRAKE_LEFT_POSITION"
    sim_var2= "BRAKE_RIGHT_POSITION"

    # time.sleep(2)
    # print(f"Was... [{time.strftime("%H:%M:%S")}] {sim_var} -> {aq.get(sim_var)}")
    # aq.set(sim_var, 1.0)
    # print(f"Is.... [{time.strftime("%H:%M:%S")}] {sim_var} -> {aq.get(sim_var)}")
    # time.sleep(2)
    # aq.set(sim_var, 2.0)
    # print(f"Is.... [{time.strftime("%H:%M:%S")}] {sim_var} -> {aq.get(sim_var)}")
    # time.sleep(2)

    aq.set(sim_var, 1.0)

    while time.time() - start_time < duration:
        # Obtener el valor de la variable CAMERA STATE del simulador
        state = aq.set(sim_var, 0)
        state2 = ""
        timestamp = time.strftime("%H:%M:%S")

        print(f"[{timestamp}] {sim_var} -> {state} --- {sim_var2} -> {state2}")
        # print(f"[{timestamp}] {sim_var2} -> {state2}")

        time.sleep(interval)

    print("\nDone................")


if __name__ == "__main__":
    monitor_camera_state()