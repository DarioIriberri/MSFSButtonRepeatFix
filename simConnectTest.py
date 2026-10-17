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
    duration = 30.0  # Duración total en segundos
    interval = 2  # Intervalo de 500 ms

    cam = "CAMERA_SUBSTATE"
    cam = "CAMERA_VIEW_TYPE_AND_INDEX_MAX"
    cam = "CAMERA_REQUEST_ACTION"
    cam = "CAMERA_VIEW_TYPE_AND_INDEX"
    cam = "COCKPIT_CAMERA_HEADLOOK"

    time.sleep(2)
    aq.set(cam, 2.0)
    print(aq.get(cam))
    time.sleep(2)
    aq.set(cam, 1.0)
    print(aq.get(cam))
    time.sleep(2)
    aq.set(cam, 2.0)
    print(aq.get(cam))
    # time.sleep(2)
    # aq.set(cam, 1.0)
    # print(aq.get(cam))


# while time.time() - start_time < duration:
    #     # Obtener el valor de la variable CAMERA STATE del simulador
    #     camera_state = aq.get(cam)
    #     timestamp = time.strftime("%H:%M:%S")
    #     aq.set(cam, 1.0)
    #
    #     print(f"[{timestamp}] {cam} -> {camera_state}")
    #
    #     time.sleep(interval)
    #
    # print("\nMonitoreo de 30 segundos finalizado.")


if __name__ == "__main__":
    monitor_camera_state()