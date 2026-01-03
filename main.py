import sys
import json
import shlex
import os
import socket
import base64
from pathlib import Path

try:
    import psutil
except ImportError:
    psutil = None

from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QLineEdit, QPushButton, QLabel,
                               QFileDialog, QSpinBox, QListWidget, QMessageBox,
                               QPlainTextEdit, QTabWidget, QCheckBox, QComboBox)
from PySide6.QtCore import QProcess, Qt, QUrl
from PySide6.QtGui import QDesktopServices, QIcon, QPixmap


class MguiQemu(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MGUI_QEMU - Professional Virtualization Control")
        self.setMinimumSize(1150, 850)

        # Конфігурація архітектур
        self.arch_map = {
            "x86_64": "x86_64", "i386": "i386", "Arm (64-bit)": "aarch64",
            "Arm (32-bit)": "arm", "RISC-V (64-bit)": "riscv64", "RISC-V (32-bit)": "riscv32",
            "PowerPC": "ppc", "PowerPC 64": "ppc64", "MIPS": "mips", "MIPS 64": "mips64",
            "LoongArch": "loongarch64", "SPARC": "sparc", "SPARC 64": "sparc64",
            "Alpha": "alpha", "AVR": "avr", "m68k": "m68k", "PA-RISC": "hppa",
            "s390x": "s390x", "SH4": "sh4", "OpenRISC": "or1k", "Xtensa": "xtensa"
        }

        self.f_name = None
        self.f_arch = None  # Нове поле
        self.f_machine = None
        self.f_cpu = None
        self.f_accel = None
        self.f_ram = None
        self.f_smp = None
        self.f_disk = None
        self.f_interface = None
        self.f_boot = None
        self.f_snapshot = None
        self.f_vga = None
        self.f_display = None
        self.f_gl = None
        self.f_fs = None
        self.f_net_type = None
        self.f_net = None
        self.f_audio = None
        self.f_usb = None
        self.f_tablet = None
        self.f_extra = None

        self.base_path = Path.home() / "MGUI_QEMU_VMs"
        self.base_path.mkdir(exist_ok=True)

        self.process = QProcess()
        self.process.started.connect(self.update_status_ui)
        self.process.finished.connect(self.update_status_ui)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)

        # --- Sidebar ---
        sidebar = QVBoxLayout()
        self.vm_list = QListWidget()
        self.vm_list.currentTextChanged.connect(self.load_vm)
        self.status_label = QLabel("● Стан: Очікування")
        self.status_label.setStyleSheet("color: gray; font-weight: bold;")

        sidebar.addWidget(QLabel("📂 Ваші проекти MGUI_QEMU:"))
        sidebar.addWidget(self.vm_list)
        sidebar.addWidget(self.status_label)

        qmp_group = QVBoxLayout()
        qmp_group.addWidget(QLabel("⚡ Керування QMP (Live):"))
        h_qmp = QHBoxLayout()
        for btn_info in [("⏸", "stop"), ("▶", "cont"), ("🛑", "system_powerdown")]:
            btn = QPushButton(btn_info[0])
            btn.clicked.connect(lambda checked=False, cmd=btn_info[1]: self.send_qmp_command({"execute": cmd}))
            h_qmp.addWidget(btn)
        qmp_group.addLayout(h_qmp)
        sidebar.addLayout(qmp_group)

        btn_new = QPushButton("➕ Нова конфігурація")
        btn_new.clicked.connect(self.clear_fields)
        sidebar.addWidget(btn_new)

        self.btn_run = QPushButton("🚀 ЗАПУСТИТИ MGUI_QEMU")
        self.btn_run.setStyleSheet(
            "height: 60px; background: #1a4a7a; color: white; font-weight: bold; border-radius: 5px;")
        self.btn_run.clicked.connect(self.run_vm)
        sidebar.addWidget(self.btn_run)

        btn_export = QPushButton("📤 Експорт у .sh скрипт")
        btn_export.clicked.connect(self.export_script)
        sidebar.addWidget(btn_export)
        main_layout.addLayout(sidebar, 1)

        # --- Tabs ---
        self.tabs = QTabWidget()
        self.init_basic_tab()
        self.init_storage_tab()
        self.init_network_tab()
        self.init_display_tab()
        self.init_advanced_tab()
        self.init_expert_tab()
        self.init_credits_tab()

        # Preview & Bottom Panel
        self.cmd_preview = QPlainTextEdit()
        self.cmd_preview.setReadOnly(True)
        self.cmd_preview.setFixedHeight(80)
        self.cmd_preview.setStyleSheet("background: #000; color: #0f0; font-family: 'Monospace'; font-size: 10px;")

        bottom_panel = QVBoxLayout()
        bottom_panel.addWidget(QLabel("🛠 Поточна команда:"))
        bottom_panel.addWidget(self.cmd_preview)

        btn_save = QPushButton("💾 Зберегти налаштування проекту")
        btn_save.clicked.connect(self.save_vm)
        btn_save.setStyleSheet("height: 40px; background: #2d5a27; color: white; font-weight: bold;")
        bottom_panel.addWidget(btn_save)

        layout_right = QVBoxLayout()
        layout_right.addWidget(self.tabs)
        layout_right.addLayout(bottom_panel)
        main_layout.addLayout(layout_right, 3)

        self.refresh_list()
        self.connect_all_signals()
        self.update_preview()
        self.load_icon_from_base64()

    def init_basic_tab(self):
        tab = QWidget()
        l = QVBoxLayout(tab)
        self.f_name = QLineEdit()
        l.addWidget(QLabel("Назва проекту:"))
        l.addWidget(self.f_name)

        self.f_arch = QComboBox()
        self.f_arch.addItems(list(self.arch_map.keys()))
        l.addWidget(QLabel("Архітектура гостьової ОС (Емуляція/Віртуалізація):"))
        l.addWidget(self.f_arch)

        self.f_machine = QComboBox()
        self.f_machine.addItems(["q35", "pc", "virt", "any"])
        l.addWidget(QLabel("Машина (-M):"))
        l.addWidget(self.f_machine)

        self.f_cpu = QComboBox()
        self.f_cpu.addItems(["host", "max", "qemu64", "cortex-a57"])
        l.addWidget(QLabel("Процесор (-cpu):"))
        l.addWidget(self.f_cpu)

        self.f_accel = QComboBox()
        self.f_accel.addItems(["Auto (KVM -> TCG)", "kvm", "tcg"])
        l.addWidget(QLabel("Прискорювач:"))
        l.addWidget(self.f_accel)

        self.f_ram = QSpinBox()
        self.f_ram.setRange(32, 128000)
        self.f_ram.setValue(2048)
        l.addWidget(QLabel("RAM (MB):"))
        l.addWidget(self.f_ram)

        self.f_smp = QSpinBox()
        self.f_smp.setRange(1, 128)
        self.f_smp.setValue(2)
        l.addWidget(QLabel("Ядра (SMP):"))
        l.addWidget(self.f_smp)
        l.addStretch()
        self.tabs.addTab(tab, "Залізо")

    def generate_command_list(self):
        # Визначаємо бінарний файл на основі вибраної архітектури
        selected_arch = self.arch_map.get(self.f_arch.currentText(), "x86_64")
        qemu_bin = f"qemu-system-{selected_arch}"

        cmd = [qemu_bin]
        cmd.extend(["-qmp", "tcp:localhost:4444,server,nowait"])

        # Логіка акселерації
        is_kvm_available = os.path.exists('/dev/kvm')
        mode = self.f_accel.currentText()
        # KVM працює тільки якщо архітектура гостя збігається з хостом (зазвичай x86_64)
        if ("Auto" in mode and is_kvm_available and selected_arch == "x86_64") or mode == "kvm":
            cmd.extend(["-accel", "kvm"])
        else:
            cmd.extend(["-accel", "tcg"])  # Емуляція

        cmd.extend(["-m", str(self.f_ram.value())])
        cmd.extend(["-smp", str(self.f_smp.value())])
        cmd.extend(["-M", self.f_machine.currentText()])
        cmd.extend(["-cpu", self.f_cpu.currentText()])

        # Дисплей та відео
        disp = self.f_display.currentText()
        if self.f_gl.isChecked(): disp += ",gl=on"
        cmd.extend(["-display", disp, "-vga", self.f_vga.currentText()])
        if self.f_fs.isChecked(): cmd.append("-full-screen")

        # Диски
        if self.f_disk.text():
            path_val = self.f_disk.text()
            if path_val.lower().endswith(".iso"):
                cmd.extend(["-cdrom", path_val])
            else:
                iface = "virtio" if "virtio" in self.f_interface.currentText() else "ide"
                cmd.extend(["-drive", f"file={path_val},if={iface}"])

        if self.f_snapshot.isChecked(): cmd.append("-snapshot")
        cmd.extend(["-boot", self.f_boot.currentText()[0]])

        # Мережа
        cmd.extend(["-netdev", "user,id=n1", "-device", f"{self.f_net_type.currentText()},netdev=n1"])

        # Периферія
        if self.f_usb.isChecked(): cmd.extend(["-device", "qemu-xhci,id=usb0"])
        if self.f_tablet.isChecked(): cmd.extend(["-device", "usb-tablet"])

        extra = self.f_extra.toPlainText().strip()
        if extra: cmd.extend(shlex.split(extra))

        return cmd

    def run_vm(self):
        if self.process.state() == QProcess.ProcessState.Running:
            QMessageBox.warning(self, "Увага", "Екземпляр уже запущено!")
            return

        args = self.generate_command_list()
        self.process.setProgram(args[0])
        self.process.setArguments(args[1:])
        self.process.start()

    # --- Решта методів (init_storage_tab, save_vm, load_vm тощо) залишаються такими ж ---
    def init_storage_tab(self):
        tab = QWidget();
        l = QVBoxLayout(tab)
        h = QHBoxLayout();
        self.f_disk = QLineEdit()
        btn_sel = QPushButton("📁");
        btn_sel.clicked.connect(lambda: self.select_file(self.f_disk))
        h.addWidget(self.f_disk);
        h.addWidget(btn_sel)
        l.addWidget(QLabel("Диск/ISO:"));
        l.addLayout(h)
        self.f_interface = QComboBox();
        self.f_interface.addItems(["virtio", "ide", "scsi"])
        l.addWidget(QLabel("Інтерфейс:"));
        l.addWidget(self.f_interface)
        self.f_boot = QComboBox();
        self.f_boot.addItems(["c (Disk)", "d (CD-ROM)"])
        l.addWidget(QLabel("Завантаження:"));
        l.addWidget(self.f_boot)
        self.f_snapshot = QCheckBox("Snapshot Mode");
        l.addWidget(self.f_snapshot);
        l.addStretch()
        self.tabs.addTab(tab, "Диски")

    def init_display_tab(self):
        tab = QWidget();
        l = QVBoxLayout(tab)
        self.f_vga = QComboBox();
        self.f_vga.addItems(["virtio", "std", "qxl"])
        l.addWidget(QLabel("VGA:"));
        l.addWidget(self.f_vga)
        self.f_display = QComboBox();
        self.f_display.addItems(["gtk", "sdl", "vnc=:1"])
        l.addWidget(QLabel("Дисплей:"));
        l.addWidget(self.f_display)
        self.f_gl = QCheckBox("OpenGL");
        self.f_fs = QCheckBox("Full Screen")
        l.addWidget(self.f_gl);
        l.addWidget(self.f_fs);
        l.addStretch()
        self.tabs.addTab(tab, "Графіка")

    def init_network_tab(self):
        tab = QWidget();
        l = QVBoxLayout(tab)
        self.f_net_type = QComboBox();
        self.f_net_type.addItems(["virtio-net-pci", "e1000"])
        l.addWidget(QLabel("Мережева карта:"));
        l.addWidget(self.f_net_type)
        self.f_net = QPlainTextEdit();
        l.addWidget(QLabel("Додаткові параметри мережі:"));
        l.addWidget(self.f_net)
        self.tabs.addTab(tab, "Мережа")

    def init_advanced_tab(self):
        tab = QWidget();
        l = QVBoxLayout(tab)
        self.f_audio = QComboBox();
        self.f_audio.addItems(["pa", "alsa", "none"])
        l.addWidget(QLabel("Аудіо:"));
        l.addWidget(self.f_audio)
        self.f_usb = QCheckBox("USB 3.0 (XHCI)");
        self.f_usb.setChecked(True)
        self.f_tablet = QCheckBox("Tablet Mode (Mouse Sync)");
        self.f_tablet.setChecked(True)
        l.addWidget(self.f_usb);
        l.addWidget(self.f_tablet);
        l.addStretch()
        self.tabs.addTab(tab, "Периферія")

    def init_expert_tab(self):
        tab = QWidget();
        l = QVBoxLayout(tab)
        self.f_extra = QPlainTextEdit();
        l.addWidget(QLabel("Додаткові прапорці QEMU:"));
        l.addWidget(self.f_extra)
        self.tabs.addTab(tab, "Експерт")

    def init_credits_tab(self):
        tab = QWidget();
        l = QVBoxLayout(tab);
        l.setAlignment(Qt.AlignmentFlag.AlignCenter)
        t = QLabel("MGUI_QEMU");
        t.setStyleSheet("font-size: 40px; font-weight: bold; color: #1a4a7a;")
        d = QLabel("Професійний інструмент для керування віртуалізацією та емуляцією.");
        d.setWordWrap(True)
        l.addStretch();
        l.addWidget(t);
        l.addWidget(d);
        l.addStretch()
        self.tabs.addTab(tab, "🎉 Подяка")

    def send_qmp_command(self, command_dict):
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.settimeout(0.5);
            client.connect(("127.0.0.1", 4444))
            client.recv(1024);
            client.sendall(json.dumps({"execute": "qmp_capabilities"}).encode())
            client.recv(1024);
            client.sendall(json.dumps(command_dict).encode());
            client.close()
        except Exception:
            pass

    def update_status_ui(self):
        is_run = self.process.state() == QProcess.ProcessState.Running
        self.status_label.setText(f"● Стан: {'ПРАЦЮЄ' if is_run else 'Очікування'}")
        self.status_label.setStyleSheet(f"color: {'#00ff00' if is_run else 'gray'}; font-weight: bold;")

    def save_vm(self):
        name = self.f_name.text().strip() or "unnamed"
        p = self.base_path / name;
        p.mkdir(exist_ok=True)
        cfg = {"name": name, "arch": self.f_arch.currentText(), "ram": self.f_ram.value(), "disk": self.f_disk.text()}
        with open(p / "config.json", "w") as f: json.dump(cfg, f, indent=4)
        self.refresh_list();
        QMessageBox.information(self, "Збережено", f"Проект {name} готовий.")

    def load_vm(self, name):
        p = self.base_path / name / "config.json"
        if p.exists():
            with open(p, "r") as f:
                d = json.load(f)
                self.f_name.setText(d.get("name", ""))
                idx = self.f_arch.findText(d.get("arch", "x86_64"))
                if idx >= 0: self.f_arch.setCurrentIndex(idx)
        self.update_preview()

    def update_preview(self):
        self.cmd_preview.setPlainText(" ".join(self.generate_command_list()))

    def refresh_list(self):
        self.vm_list.clear()
        if self.base_path.exists():
            for d in self.base_path.iterdir():
                if d.is_dir(): self.vm_list.addItem(d.name)

    def clear_fields(self):
        self.f_name.clear(); self.f_disk.clear(); self.update_preview()

    def select_file(self, line):
        path, _ = QFileDialog.getOpenFileName(self, "Вибрати образ");
        if path: line.setText(path); self.update_preview()

    def connect_all_signals(self):
        for w in [self.f_name, self.f_arch, self.f_disk, self.f_ram, self.f_smp, self.f_machine, self.f_accel]:
            if hasattr(w, 'textChanged'): w.textChanged.connect(self.update_preview)
            if hasattr(w, 'currentIndexChanged'): w.currentIndexChanged.connect(self.update_preview)
            if hasattr(w, 'valueChanged'): w.valueChanged.connect(self.update_preview)

    def export_script(self):
        path, _ = QFileDialog.getSaveFileName(self, "Експорт", filter="Shell (*.sh)")
        if path:
            if not path.endswith(".sh"): path += ".sh"
            with open(path, "w") as f:
                f.write("#!/bin/bash\n" + " ".join(self.generate_command_list()))

    def load_icon_from_base64(self):
        pass


if __name__ == "__main__":
    app = QApplication(sys.argv);
    app.setStyle("Fusion")
    win = MguiQemu();
    win.show();
    sys.exit(app.exec())