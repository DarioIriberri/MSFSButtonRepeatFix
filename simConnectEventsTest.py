from SimConnect import SimConnect, Event
import time


def main() -> None:
    """Test continuous rapid-firing of EYEPOINT_FORWARD with a value argument."""
    print("[INFO] Initializing SimConnect for continuous movement testing...")

    try:
        sm = SimConnect()
    except Exception as e:
        print(f"[ERROR] Failed to connect to SimConnect: {e}")
        return

    event_bytes = b"EYEPOINT_RIGHT"
    print(f"[INFO] Rapidly triggering '{event_bytes.decode()}' for 3 seconds (simulating button hold)...")

    try:
        ev = Event(event_bytes, sm)

        # Simulate holding a button down: send the event rapidly every 50ms (20 times/sec)
        start_time = time.time()
        while time.time() - start_time < 13.0:
            ev(1)  # Passing 1 as magnitude/value
            time.sleep(0.05)

        print("[INFO] Rapid test finished. Did the eyepoint move forward?")

    except KeyboardInterrupt:
        print("\n[INFO] Testing terminated by user.")


if __name__ == "__main__":
    time.sleep(3)
    main()