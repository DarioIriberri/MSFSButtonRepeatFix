import pygame


def main() -> None:
    # Initialize pygame and the joystick module
    pygame.init()
    pygame.joystick.init()

    # No display window needed; running completely headless for console logging
    num_joysticks = pygame.joystick.get_count()
    print(f"\n[INFO] Joysticks detected: {num_joysticks}")
    print("=" * 60)

    joysticks = {}
    for i in range(num_joysticks):
        js = pygame.joystick.Joystick(i)
        js.init()
        # Map instance id to the joystick object for event handling
        joysticks[js.get_instance_id()] = js

        print(f"  [{i}] Device: {js.get_name()}")
        print(f"       GUID: {js.get_guid()}")
        print(f"       Total Buttons: {js.get_numbuttons()} | Total Hats: {js.get_numhats()}")
        print("-" * 60)

    if num_joysticks == 0:
        print("[WARNING] No joysticks detected.")
    else:
        print(
            "\nListening for events... (Press buttons or move the hat. Close the terminal or press Ctrl+C to exit).\n")

    clock = pygame.time.Clock()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # Triggered when a button is pressed down
            elif event.type == pygame.JOYBUTTONDOWN:
                js = joysticks.get(event.instance_id)
                name = js.get_name() if js else "Unknown"
                guid = js.get_guid() if js else "Unknown"
                print(f"[BUTTON PRESSED] Device: '{name}' | GUID: {guid} --> Button Index: {event.button}")

            # Triggered when a button is released (optional debug)
            elif event.type == pygame.JOYBUTTONUP:
                js = joysticks.get(event.instance_id)
                name = js.get_name() if js else "Unknown"
                # print(f"[BUTTON RELEASED] Device: '{name}' --> Button Index: {event.button}")

            # Triggered when a hat (D-pad) is moved
            elif event.type == pygame.JOYHATMOTION:
                js = joysticks.get(event.instance_id)
                name = js.get_name() if js else "Unknown"
                guid = js.get_guid() if js else "Unknown"
                hat_x, hat_y = event.value
                if not (hat_x == 0 and hat_y == 0):
                    print(
                        f"[HAT MOVED] Device: '{name}' | GUID: {guid} --> Hat Index: {event.hat} | X: {hat_x}, Y: {hat_y}")

            # Keep a small sleep-equivalent via the clock tick to prevent CPU spinning
            clock.tick(60)

    pygame.quit()
    print("[INFO] Joystick diagnostic tool closed.")


if __name__ == "__main__":
    main()