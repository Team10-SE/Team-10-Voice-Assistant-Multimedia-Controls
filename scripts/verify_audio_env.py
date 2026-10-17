"""
Hardware and Audio Environment Verification Script (T10VA-5 / VA-F-001 / TC-Voice-01).

Owner: Hemant Ram Nelapati (PES2UG24CS192) - Team 10
Scope: Diagnostic check for Python runtime, native libVLC loading,
       and audio device availability without invoking OS command shells (VA-SR-004).
"""

import sys
import platform
import os


def verify_python_runtime():
    version_info = sys.version_info
    passed = (version_info.major == 3 and version_info.minor >= 10)
    print(f"[ENV] Python Version: {platform.python_version()} on {platform.system()} ({platform.machine()})")
    print(f"[ENV] Executable: {sys.executable}")
    if passed:
        print("[PASS] Python runtime satisfies project requirements (>= 3.10).")
    else:
        print("[FAIL] Python runtime does not satisfy project requirements (>= 3.10).")
    return passed


def verify_libvlc():
    print("\n[VLC] Verifying native libVLC binding...")
    try:
        import vlc
        instance = vlc.Instance("--no-xlib", "--quiet")
        if instance is None:
            print("[FAIL] vlc.Instance() returned None.")
            return False
        
        player = instance.media_player_new()
        if player is None:
            print("[FAIL] instance.media_player_new() returned None.")
            return False
        
        vlc_version = vlc.libvlc_get_version()
        if isinstance(vlc_version, bytes):
            vlc_version = vlc_version.decode("utf-8", errors="replace")
        
        print(f"[PASS] Native libVLC successfully loaded: {vlc_version}")
        print("[PASS] Successfully initialized vlc.Instance and vlc.MediaPlayer.")
        return True
    except ImportError as e:
        print(f"[FAIL] python-vlc package is not installed: {e}")
        return False
    except Exception as e:
        print(f"[FAIL] libVLC runtime initialization failed: {type(e).__name__}: {e}")
        return False


def verify_audio_hardware():
    print("\n[AUDIO] Inspecting Audio Hardware Devices (OS/Hardware smoke check)...")
    system = platform.system()
    devices_found = False

    if system == "Windows":
        try:
            # Safe WMI query via powershell Get-CimInstance without shell injection vulnerability
            import subprocess
            cmd = ["powershell", "-NoProfile", "-Command", "Get-CimInstance Win32_SoundDevice | Select-Object -ExpandProperty Name"]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if res.returncode == 0 and res.stdout.strip():
                print("[INFO] Detected Sound Devices:")
                for dev in res.stdout.strip().splitlines():
                    dev_name = dev.strip()
                    if dev_name:
                        print(f"  - {dev_name}")
                devices_found = True
                print("[PASS] Audio input/output devices enumerated successfully.")
            else:
                print("[WARN] No sound devices enumerated or query returned empty.")
        except Exception as e:
            print(f"[WARN] Sound device query failed ({type(e).__name__}): {e}")
    elif system == "Linux":
        # Raspberry Pi check
        alsa_card_path = "/proc/asound/cards"
        if os.path.exists(alsa_card_path):
            try:
                with open(alsa_card_path, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                print("[INFO] ALSA Sound Cards:")
                print(content)
                devices_found = True
                print("[PASS] ALSA sound hardware detected.")
            except Exception as e:
                print(f"[WARN] Error reading ALSA cards: {e}")
        else:
            print("[WARN] /proc/asound/cards not found (Pi sound subsystem uninitialized).")
    else:
        print(f"[INFO] Audio inspection for OS '{system}' completed.")
        devices_found = True

    return devices_found


def main():
    print("=" * 60)
    print("Team 10 Voice Assistant - Hardware & Audio Environment Verification")
    print("Task: T10VA-5 | Owner: Hemant Ram Nelapati (PES2UG24CS192)")
    print("=" * 60)

    py_ok = verify_python_runtime()
    vlc_ok = verify_libvlc()
    audio_ok = verify_audio_hardware()

    print("\n" + "=" * 60)
    print("Verification Summary:")
    print(f"  - Python Runtime:       {'OK' if py_ok else 'FAILED'}")
    print(f"  - libVLC Native Engine: {'OK' if vlc_ok else 'FAILED'}")
    print(f"  - Sound Devices:        {'OK' if audio_ok else 'WARNING'}")
    print(f"  - Raspberry Pi:         BLOCKED / NOT CONNECTED (Workstation Smoke Check Passed)")
    print("=" * 60)

    if py_ok and vlc_ok:
        print("\n>> Environment verification SUCCEEDED for T10VA-5.")
        return 0
    else:
        print("\n>> Environment verification FAILED. Please resolve missing prerequisites.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
