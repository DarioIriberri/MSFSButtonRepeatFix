import time
from SimConnect import SimConnect, AircraftRequests


def probar_simvar_camera_reset():
    print("Conectando con Microsoft Flight Simulator...")

    # Inicializar la conexión de SimConnect y las peticiones de aeronave
    sm = SimConnect()
    aircraft = AircraftRequests(sm, _time=200)

    # Nombre exacto de la variable según el SDK
    simvar = "ELEVATOR_TRIM_POSITION"
    simvar = "CAMERA_ACTION_COCKPIT_VIEW_RESET"
    simvar = "COCKPIT_CAMERA_HEADLOOK"

    try:
        # 1. Leer el valor inicial
        valor_actual = aircraft.get(simvar)
        next_val = 2.0
        print(f"Valor actual de [{simvar}]: {valor_actual}")

        # 2. Probar a escribir un valor (por ejemplo, ponerlo a 1 / True para disparar el reseteo)
        print(f"Estableciendo [{simvar}] a " + str(next_val))
        aircraft.set(simvar, next_val)

        # Esperar un breve instante para que el simulador procese la orden
        time.sleep(0.5)

        # 3. Volver a leer para comprobar el estado resultante
        valor_nuevo = aircraft.get(simvar)
        print(f"Valor tras el cambio: {valor_nuevo}")

        print("¡Prueba completada con éxito!")

    except Exception as e:
        print(f"Ocurrió un error al comunicarse con SimConnect: {e}")

    finally:
        # Cerrar la conexión limpiamente
        # sm.quit()
        pass


if __name__ == "__main__":
    probar_simvar_camera_reset()