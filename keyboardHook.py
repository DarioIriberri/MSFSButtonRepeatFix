import keyboard

print("=== INSPECTOR DE TECLAS ===")
print("Presiona cualquier tecla para ver sus datos.")
print("Pulsa Ctrl + C en la terminal para salir.\n")

try:
    while True:
        event = keyboard.read_event()
        if event.event_type == keyboard.KEY_DOWN:
            print(f"Tecla: '{event.name}' | Scan Code: {event.scan_code}")

except KeyboardInterrupt:
    print("\nSaliendo del inspector de teclas...")