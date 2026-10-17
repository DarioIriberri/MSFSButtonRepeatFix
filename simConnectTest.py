import ctypes
import time


# Define the 3D structure (X, Y, Z) expected by SimConnect for structural offsets
class SIMCONNECT_DATA_XYZ(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_double),  # Lateral (Left/Right)
        ("y", ctypes.c_double),  # Vertical (Up/Down)
        ("z", ctypes.c_double)  # Longitudinal (Forward/Backward)
    ]


def main() -> None:
    dll_path = r"C:\Games\Microsoft Flight Simulator SDK\SimConnect SDK\lib\SimConnect.dll"
    print(f"[INFO] Loading native SimConnect DLL from: {dll_path}")

    try:
        sc_dll = ctypes.WinDLL(dll_path)
        print("[OK] SimConnect.dll loaded successfully!")
    except Exception as e:
        print(f"[ERROR] Failed to load DLL: {e}")
        return

    # --- DECLARAR LOS PROTOTIPOS (argtypes y restype) PARA EVITAR ERRORES DE MARSHALLING ---

    # SimConnect_Open
    sc_dll.SimConnect_Open.argtypes = [
        ctypes.c_void_p,  # phSimConnect
        ctypes.c_char_p,  # szName
        ctypes.c_void_p,  # hWnd
        ctypes.c_uint,  # UserEventWin32
        ctypes.c_void_p,  # hEventHandle
        ctypes.c_uint  # ConfigIndex
    ]
    sc_dll.SimConnect_Open.restype = ctypes.c_long

    # SimConnect_Close
    sc_dll.SimConnect_Close.argtypes = [ctypes.c_void_p]
    sc_dll.SimConnect_Close.restype = ctypes.c_long

    # SimConnect_AddToDataDefinition
    sc_dll.SimConnect_AddToDataDefinition.argtypes = [
        ctypes.c_void_p,  # hSimConnect
        ctypes.c_uint,  # DefineID
        ctypes.c_char_p,  # DatumName
        ctypes.c_char_p,  # UnitsName
        ctypes.c_uint,  # DatumType
        ctypes.c_float,  # fDatumDefault
        ctypes.c_uint  # DatumID
    ]
    sc_dll.SimConnect_AddToDataDefinition.restype = ctypes.c_long

    # SimConnect_SetDataOnSimObject
    sc_dll.SimConnect_SetDataOnSimObject.argtypes = [
        ctypes.c_void_p,  # hSimConnect
        ctypes.c_uint,  # DefineID
        ctypes.c_uint,  # ObjectID
        ctypes.c_uint,  # Flags
        ctypes.c_uint,  # ArrayCount
        ctypes.c_uint,  # cbUnitSize
        ctypes.c_void_p  # pDataSet
    ]
    sc_dll.SimConnect_SetDataOnSimObject.restype = ctypes.c_long

    # -----------------------------------------------------------------------------------

    hSimConnect = ctypes.c_void_p(None)

    print("[INFO] Opening connection to MSFS...")
    hr = sc_dll.SimConnect_Open(
        ctypes.byref(hSimConnect),
        b"PythonNativeEyepoint",
        None,
        0,
        None,
        0
    )

    if hr != 0:
        print(f"[ERROR] SimConnect_Open failed with HRESULT: {hr:#010x}. Is MSFS running?")
        return

    print("[SUCCESS] Connected to MSFS via native C-API!")

    DEFINE_ID = 100

    print("[INFO] Adding data definition for STRUCT EYEPOINT DYNAMIC OFFSET...")
    # SIMCONNECT_DATATYPE_FLOAT64 = 3
    hr = sc_dll.SimConnect_AddToDataDefinition(
        hSimConnect,
        DEFINE_ID,
        b"STRUCT EYEPOINT DYNAMIC OFFSET",
        b"Meters",
        3,  # FLOAT64
        0.0,  # fDatumDefault (now correctly typed as c_float)
        0  # DatumID
    )

    print(f"[INFO] AddToDataDefinition result code: {hr:#010x}")

    try:
        print("[INFO] Sending smooth forward offset steps...")
        current_z = 0.0

        for _ in range(5):
            current_z += 0.01  # 1 cm step
            offset_data = SIMCONNECT_DATA_XYZ(x=0.0, y=0.0, z=current_z)

            hr = sc_dll.SimConnect_SetDataOnSimObject(
                hSimConnect,
                DEFINE_ID,
                0,  # User aircraft
                0,  # Flags
                1,  # Array count
                ctypes.sizeof(offset_data),
                ctypes.byref(offset_data)
            )

            print(f"  -> Sent Z offset: {current_z:.3f}m (Result code: {hr})")
            time.sleep(0.2)

        time.sleep(1.0)

        print("[INFO] Resetting offset...")
        offset_data = SIMCONNECT_DATA_XYZ(x=0.0, y=0.0, z=0.0)
        sc_dll.SimConnect_SetDataOnSimObject(
            hSimConnect, DEFINE_ID, 0, 0, 1, ctypes.sizeof(offset_data), ctypes.byref(offset_data)
        )

    except Exception as e:
        print(f"[ERROR] Exception during execution: {e}")

    finally:
        sc_dll.SimConnect_Close(hSimConnect)
        print("[INFO] SimConnect connection closed.")


if __name__ == "__main__":
    main()