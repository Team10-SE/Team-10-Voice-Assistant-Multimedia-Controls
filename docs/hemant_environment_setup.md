# Environment & Audio Setup Documentation (T10VA-5)

**Project:** Team 10 Voice-Controlled Media Player Mini Project  
**Task ID:** T10VA-5 (Raspberry Pi/Microphone & Audio Environment Setup)  
**Author / Component Owner:** Hemant Ram Nelapati (PES2UG24CS192)  
**Date:** October 14, 2026  
**Scope Boundary:** Hemant-owned environment setup and checks only.  

---

## 1. System Environment & Tooling Verification

| Component | Target Spec | Detected / Verified Value | Status |
| :--- | :--- | :--- | :--- |
| **Operating System** | Windows / Linux (Pi OS) | Windows 11 Enterprise (64-bit) | **Verified** |
| **Python Version** | Python 3.11.x | Python 3.11.8 (64-bit) at `.venv` | **Verified** |
| **Git CLI** | Git 2.x | git version 2.56.0.windows.2 | **Verified** |
| **VLC / libVLC Runtime** | VLC Media Player (libvlc 3.x) | VideoLAN VLC v3.0.x (`C:\Program Files\VideoLAN\VLC\libvlc.dll`) | **Verified** |
| **Python VLC Binding** | python-vlc | `python-vlc==3.0.21203` | **Verified** |
| **Test Runner** | pytest | `pytest==9.1.1` | **Verified** |
| **Audio Output Device** | Stereo / Headphone out | Realtek High Definition Audio & USB Audio 2.0 | **Verified** |
| **Microphone Device** | USB Microphone / Digital Array | Intel Smart Sound Mic Array & USB Audio 2.0 | **Verified** |
| **Raspberry Pi Hardware** | Raspberry Pi 4 / 5 | Hardware not connected / no authorized SSH target configured | **Blocked / Not Tested** |

---

## 2. Virtual Environment & Dependency Installation

To isolate dependencies and ensure reproducibility across development workstations and the Raspberry Pi deployment, a dedicated Python 3.11 virtual environment is created:

```powershell
# 1. Create Python 3.11 virtual environment
py -3.11 -m venv .venv

# 2. Activate virtual environment (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# (On Linux / Raspberry Pi OS)
# python3 -m venv .venv
# source .venv/bin/activate

# 3. Install Hemant-scoped media controller dependencies
pip install -r requirements.txt
```

### Verified Installed Packages (`pip list`):
- `colorama==0.4.6`
- `iniconfig==2.3.1`
- `packaging==26.3`
- `pluggy==1.6.0`
- `pygments==2.21.0`
- `pytest==9.1.1`
- `python-vlc==3.0.21203`

---

## 3. libVLC Runtime Load Verification

A successful Python package import alone does not prove that the underlying native `libvlc` shared library can load. The native library was verified with:

```python
import vlc
instance = vlc.Instance("--no-xlib", "--quiet")
player = instance.media_player_new()
assert instance is not None
assert player is not None
```

- **Result:** Successful. `vlc.Instance` and `vlc.MediaPlayer` instantiated without dynamic-link or missing library errors.

---

## 4. Audio Input/Output Hardware Devices

Local audio hardware was inspected using Windows Management Instrumentation (WMI / `Win32_SoundDevice`):

- **Realtek High Definition Audio:** Verified onboard speakers/headphones output.
- **USB Audio 2.0:** Verified external USB audio interface (combined input/output).
- **Intel Smart Sound Technology for Digital Microphones:** Verified onboard microphone array.

---

## 5. Raspberry Pi Status & Target Deployment Instructions

### Current Status: **BLOCKED / NOT TESTED**
- **Reason:** The Raspberry Pi hardware is not physically connected or accessible via an authorized SSH or Tailscale configuration on this workstation. Per project safety and ethics rules, network scanning or unauthorized credential guessing was strictly avoided.
- **Evidence:** SSH config check and local Tailscale daemon inspection confirmed no active connection to the Pi.

### Raspberry Pi Deployment & Setup Guide (For Handover):
When running on the physical Raspberry Pi 4/5 hardware under Raspberry Pi OS:

1. **Install system-level libVLC dependencies:**
   ```bash
   sudo apt update
   sudo apt install -y vlc libvlc-dev python3-vlc alsa-utils
   ```
2. **Verify USB Microphone detection:**
   ```bash
   arecord -l
   ```
3. **Verify Audio Output detection:**
   ```bash
   aplay -l
   ```
4. **Set up Python Virtual Environment:**
   ```bash
   python3 -m venv .venv --system-site-packages
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
5. **Run Media Controller Test Suite:**
   ```bash
   pytest -v
   ```
