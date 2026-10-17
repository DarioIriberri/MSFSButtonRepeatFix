import ctypes
import time


def get_active_window_title() -> str:
    """Retrieves the title of the active window using the Windows API via ctypes."""
    hwnd = ctypes.windll.user32.GetForegroundWindow()
    length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
    buffer = ctypes.create_unicode_buffer(length + 1)
    ctypes.windll.user32.GetWindowTextW(hwnd, buffer, length + 1)
    return buffer.value


def main() -> None:
    print("[INFO] Starting test script to detect the active window...")
    print("[INFO] Switch between the simulator and other apps to see how it reacts. Press Ctrl+C to exit.\n")

    try:
        while True:
            title = get_active_window_title()
            is_msfs = "Microsoft Flight Simulator" in title

            if is_msfs:
                print(f"[DETECTED!] Active window: '{title}' ---> It's MSFS!")
            else:
                print(f"[Monitoring] Active window: '{title}'")

            time.sleep(1.0)  # 1-second sleep to avoid CPU spinning

    except KeyboardInterrupt:
        print("\n[INFO] Script terminated by user.")


if __name__ == "__main__":
    main()