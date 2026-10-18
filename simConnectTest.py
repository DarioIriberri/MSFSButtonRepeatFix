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
    interval = 0.5  # Intervalo de 500 ms

    # sim_var = "CAMERA_SUBSTATE"
    # sim_var = "CAMERA_VIEW_TYPE_AND_INDEX_MAX"
    # sim_var = "CAMERA_REQUEST_ACTION"
    # sim_var = "CAMERA_VIEW_TYPE_AND_INDEX"
    sim_var= "COCKPIT_CAMERA_HEADLOOK"

    time.sleep(2)
    print(f"Was... [{time.strftime("%H:%M:%S")}] {sim_var} -> {aq.get(sim_var)}")
    aq.set(sim_var, 1.0)
    print(f"Is.... [{time.strftime("%H:%M:%S")}] {sim_var} -> {aq.get(sim_var)}")
    time.sleep(2)
    aq.set(sim_var, 2.0)
    print(f"Is.... [{time.strftime("%H:%M:%S")}] {sim_var} -> {aq.get(sim_var)}")
    time.sleep(2)
    # print(aq.get(sim_var))
    # time.sleep(2)
    # aq.set(sim_var, 1.0)
    # print(aq.get(sim_var))
    # time.sleep(2)
    # aq.set(sim_var, 2.0)
    # print(aq.get(sim_var))
    # time.sleep(2)
    # aq.set(sim_var, 1.0)
    # print(aq.get(sim_var))


    # while time.time() - start_time < duration:
    #     # Obtener el valor de la variable CAMERA STATE del simulador
    #     camera_state = aq.get(sim_var)
    #     timestamp = time.strftime("%H:%M:%S")
    #     # aq.set(sim_var, 1.0)
    #
    #     print(f"[{timestamp}] {sim_var} -> {camera_state}")
    #
    #     time.sleep(interval)
    #
    # print("\nMonitoreo de 30 segundos finalizado.")


if __name__ == "__main__":
    monitor_camera_state()