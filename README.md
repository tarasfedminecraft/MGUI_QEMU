# MGUI_QEMU 🚀

**Professional GUI for launching and managing QEMU virtual machines**

A lightweight, friendly desktop GUI written in Python (PySide6) for composing and launching QEMU instances. It focuses on an intuitive visual interface to build QEMU command lines, save VM profiles, control running VMs via QMP, and monitor basic host stats. This project is released under **GPL-2.0**.

---

## Key features ✨

* Graphical form for typical VM settings: architecture, machine type, CPU, RAM, SMP.
* Choose disk image or ISO and boot order.
* Auto-generated QEMU command preview (read-only) so you always know what runs.
* Start / stop / QMP controls (pause, continue, system_powerdown) for running VMs.
* Save and load VM profiles as `config.json` in a `MGUI_QEMU_VMs` folder.
* Optional psutil integration for live CPU/RAM percentage in the sidebar.
* Cross-platform awareness (attempts to auto-detect QEMU binary on common paths).

---

## Quick demo (what it does) 🎯

1. Fill the fields on the Hardware tab: name, arch, machine, CPU mode, RAM, SMP.
2. Select a disk or ISO on the Disks tab and choose the boot device.
3. Optionally tweak the QEMU binary path and extra args on the Expert tab.
4. Save the configuration or hit **Launch** to run QEMU with the generated command.
5. Use the sidebar controls to pause/continue or issue a graceful powerdown via QMP.

---

## Requirements

* Python 3.9+ (3.11 recommended)
* [PySide6] for the GUI: `pip install PySide6`
* Optional: `psutil` for CPU/RAM stats: `pip install psutil`
* QEMU installed on the system and available in PATH, or set the full path in the Expert tab.

> Tested on Linux, Windows, macOS. Behavior of accelerators differs per OS (KVM/WHv/WHPX/HVF).

---

## Installation

Clone the repo and install dependencies:

```bash
git clone <your-repo-url>
cd mgui_qemu
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

If you don't have a `requirements.txt`, at minimum install:

```bash
pip install PySide6
# optional
pip install psutil
```

---

## Run

```bash
python main.py
```

The window uses the Fusion style by default to keep the UI consistent across platforms.

---

## Command generation details

The GUI generates a QEMU command from the form and extra args. Example generated command:

```bash
qemu-system-x86_64 -enable-kvm -qmp tcp:127.0.0.1:4444,server,nowait -m 2048 -smp 2 -M q35 -cpu host -drive file=/path/to/disk.img,if=virtio -boot c
```

Notes:

* If an ISO is selected the GUI uses `-cdrom` instead of `-drive`.
* The `-qmp` socket is created on `127.0.0.1:<port>`; the GUI will pick a free port when launching.
* CPU acceleration flags are added automatically: `-enable-kvm` on Linux, `-accel whpx` on Windows, `-accel hvf` on macOS when `cpu=host` is selected.
* Extra advanced arguments may be provided in the Expert tab; they are split with `shlex.split`.

---

## VM profile (`config.json`) format

Saved VM profiles live under `~/MGUI_QEMU_VMs/<vm-name>/config.json` and look like this:

```json
{
    "name": "myvm",
    "arch": "x86_64",
    "ram": 2048,
    "smp": 2,
    "boot": "Disk (c)",
    "disk": "/path/to/image.qcow2",
    "cpu": "host",
    "machine": "q35",
    "qemu_path": "",
    "extra": "-device usb-ehci"
}
```

---

## QMP integration

* The GUI starts QEMU with a QMP TCP server on `127.0.0.1:<port>` and attempts to send QMP JSON commands after negotiating `qmp_capabilities`.
* Available quick controls in the sidebar: Pause (`stop`), Continue (`cont`), Powerdown (`system_powerdown`).
* QMP commands are sent from a background thread with retry logic.

Security note: The QMP interface is bound to localhost only. Do not expose the QMP TCP port to untrusted networks.

---

## Troubleshooting & common pitfalls 🩺

* **QEMU not found**: If the GUI cannot resolve the QEMU binary, set the full path in the Expert tab or ensure the binary (e.g. `qemu-system-x86_64`) is in PATH.
* **KVM/acceleration issues**: On Linux, ensure `/dev/kvm` exists and your user has permissions (you may need to be in the `kvm` group). On macOS use HVF; on Windows use WHPX/Hyper-V.
* **Port collisions**: The GUI attempts to pick a free port for QMP; if you use a fixed port in other tools, collisions may happen.
* **Missing psutil**: CPU/RAM bars are disabled if `psutil` is not installed. This is optional.
* **Malformed `extra` args**: The Expert tab uses `shlex.split` — unbalanced quotes will raise errors when generating the preview.

---

## Development & testing 🛠

* Project entrypoint: `main.py` (or whichever file contains the `if __name__ == "__main__"` block).
* Linting: run `flake8` / `ruff` if you want to keep things tidy.
* Packaging: build a single-file binary with `pyinstaller` or create platform-specific installers for end users.

Recommended dev tasks you can pick up:

* Add unit tests for command generation and config read/write.
* Add desktop integration (start menu / dock icons) for installers.
* Add support for passing a `--headless` or `--dry-run` flag for CI tests.

---

## Contributing 🤝

Contributions are welcome. This repository follows a standard workflow:

1. Fork the repo
2. Create a feature branch
3. Open a PR with a clear description and tests if possible

Keep changes small and focused. If you add new features, update the README and include examples.

---

## License

This project is licensed under the **GPL-2.0** license. Include the full `COPYING`/`LICENSE` file in the repository.

---

## Acknowledgements

Built with PySide6 and a healthy disdain for command-line copy/paste. Thanks to anyone who takes the time to make virtualization less miserable.

---

*Made for people who want a sane UI for QEMU. Enjoy, and try not to break anything important.*
