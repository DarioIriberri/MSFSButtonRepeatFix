import time
from SimConnect import SimConnect, AircraftRequests


def monitor_camera_state():
    print("Conectando a MSFS a través de SimConnect...")
    try:
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

        while time.time() - start_time < duration:
            # Obtener el valor de la variable CAMERA STATE del simulador
            camera_state = aq.get("CAMERA_SUBSTATE")
            timestamp = time.strftime("%H:%M:%S")

            print(f"[{timestamp}] {cam} -> {camera_state}")

            time.sleep(interval)

        print("\nMonitoreo de 30 segundos finalizado.")

    except Exception as e:
        print(f"Error de conexión o ejecución: {e}")
    finally:
        # Asegurar un cierre limpio de la conexión
        try:
            sm.exit()
            print("Conexión con SimConnect cerrada correctamente.")
        except:
            pass


if __name__ == "__main__":
    monitor_camera_state()