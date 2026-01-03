import sys
import json
import shlex
import os
import socket
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
from PySide6.QtGui import QDesktopServices


class MGUI_QEMU(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MGUI_QEMU - Professional Virtualization Control")
        self.setMinimumSize(1150, 850)

        # Pre-declare UI/config fields to avoid "defined outside __init__" warnings
        self.f_name = None
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

        # QMP Quick Controls
        qmp_group = QVBoxLayout()
        qmp_group.addWidget(QLabel("⚡ Керування QMP (Live):"))
        h_qmp = QHBoxLayout()
        btn_pause = QPushButton("⏸")
        btn_pause.clicked.connect(lambda: self.send_qmp_command({"execute": "stop"}))
        btn_resume = QPushButton("▶")
        btn_resume.clicked.connect(lambda: self.send_qmp_command({"execute": "cont"}))
        btn_stop = QPushButton("🛑")
        btn_stop.clicked.connect(lambda: self.send_qmp_command({"execute": "system_powerdown"}))
        h_qmp.addWidget(btn_pause)
        h_qmp.addWidget(btn_resume)
        h_qmp.addWidget(btn_stop)
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

        # --- Main Tabs ---
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs, 3)

        self.init_basic_tab()
        self.init_storage_tab()
        self.init_network_tab()
        self.init_display_tab()
        self.init_advanced_tab()
        self.init_expert_tab()
        self.init_credits_tab()

        # Preview & Save
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

    # --- QMP Logic ---
    def send_qmp_command(self, command_dict):
        """Надсилає JSON команду до QEMU через TCP сокет"""
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.settimeout(1.0)
            client.connect(("127.0.0.1", 4444))
            # Читаємо вітання від QMP
            client.recv(1024)
            # Входимо в режим команд
            client.sendall(json.dumps({"execute": "qmp_capabilities"}).encode())
            client.recv(1024)
            # Надсилаємо саму команду
            client.sendall(json.dumps(command_dict).encode())
            client.close()
        except (OSError, socket.error) as e:
            QMessageBox.warning(self, "QMP Помилка", f"Не вдалося з'єднатися з VM: {e}\nПереконайтеся, що VM запущена.")

    def init_credits_tab(self):
        tab = QWidget()
        l = QVBoxLayout(tab)
        l.setAlignment(Qt.AlignCenter)

        title = QLabel("MGUI_QEMU")
        title.setStyleSheet("font-size: 48px; font-weight: bold; color: #1a4a7a;")

        desc = QLabel(
            "Ми зручна програма GUI для QEMU. Якщо ви запускаєте з Windows або MacOS — ви молодці, "
            "моя програма реально сумісна з цима операційними системами, але важливе АЛЕ... "
            "моя програма використовує нативні фічі LINUX для максимальної продуктивності."
        )
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet("font-size: 14px; margin: 20px;")

        dev_label = QLabel("Розробник: tarasfedminecraft")
        btn_repo = QPushButton("🔗 Репозиторій (GitHub)")
        btn_dev = QPushButton("👤 Профіль розробника")

        btn_repo.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl("https://github.com/tarasfedminecraft/MGUI_QEMU")))
        btn_dev.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://github.com/tarasfedminecraft")))

        l.addStretch()
        l.addWidget(title)
        l.addWidget(desc)
        l.addSpacing(20)
        l.addWidget(dev_label, alignment=Qt.AlignCenter)
        l.addWidget(btn_repo)
        l.addWidget(btn_dev)
        l.addStretch()
        self.tabs.addTab(tab, "🎉 Подяка")

    # --- Секція ініціалізації віджетів (Залишається як у вас, але з поправками на QMP) ---
    def init_basic_tab(self):
        tab = QWidget()
        l = QVBoxLayout(tab)
        self.f_name = QLineEdit()
        l.addWidget(QLabel("Назва проекту:"))
        l.addWidget(self.f_name)
        self.f_machine = QComboBox()
        self.f_machine.addItems(["q35", "pc", "virt"])
        l.addWidget(QLabel("Машина:"))
        l.addWidget(self.f_machine)
        self.f_cpu = QComboBox()
        self.f_cpu.addItems(["host", "max", "qemu64"])
        l.addWidget(QLabel("CPU:"))
        l.addWidget(self.f_cpu)
        self.f_accel = QComboBox()
        self.f_accel.addItems(["Auto (KVM -> TCG)", "kvm", "tcg"])
        l.addWidget(QLabel("Акселерація:"))
        l.addWidget(self.f_accel)
        self.f_ram = QSpinBox()
        self.f_ram.setRange(32, 128000)
        self.f_ram.setValue(2048)
        l.addWidget(QLabel("RAM (MB):"))
        l.addWidget(self.f_ram)
        self.f_smp = QSpinBox()
        self.f_smp.setRange(1, 128)
        self.f_smp.setValue(2)
        l.addWidget(QLabel("Ядра:"))
        l.addWidget(self.f_smp)
        l.addStretch()
        self.tabs.addTab(tab, "Залізо")

    def init_storage_tab(self):
        tab = QWidget()
        l = QVBoxLayout(tab)
        h = QHBoxLayout()
        self.f_disk = QLineEdit()
        btn_sel = QPushButton("📁")
        btn_sel.clicked.connect(lambda: self.select_file(self.f_disk))
        h.addWidget(self.f_disk)
        h.addWidget(btn_sel)
        l.addWidget(QLabel("Диск/ISO:"))
        l.addLayout(h)
        self.f_interface = QComboBox()
        self.f_interface.addItems(["virtio", "ide", "scsi"])
        l.addWidget(QLabel("Інтерфейс:"))
        l.addWidget(self.f_interface)
        self.f_boot = QComboBox()
        self.f_boot.addItems(["c (Disk)", "d (CD-ROM)"])
        l.addWidget(QLabel("Завантаження:"))
        l.addWidget(self.f_boot)
        self.f_snapshot = QCheckBox("Snapshot Mode")
        l.addWidget(self.f_snapshot)
        l.addStretch()
        self.tabs.addTab(tab, "Диски")

    def init_display_tab(self):
        tab = QWidget()
        l = QVBoxLayout(tab)
        self.f_vga = QComboBox()
        self.f_vga.addItems(["virtio", "std", "qxl"])
        l.addWidget(QLabel("VGA:"))
        l.addWidget(self.f_vga)
        self.f_display = QComboBox()
        self.f_display.addItems(["gtk", "sdl", "vnc=:1"])
        l.addWidget(QLabel("Дисплей:"))
        l.addWidget(self.f_display)
        self.f_gl = QCheckBox("OpenGL")
        self.f_fs = QCheckBox("Full Screen")
        l.addWidget(self.f_gl)
        l.addWidget(self.f_fs)
        l.addStretch()
        self.tabs.addTab(tab, "Графіка")

    def init_network_tab(self):
        tab = QWidget()
        l = QVBoxLayout(tab)
        self.f_net_type = QComboBox()
        self.f_net_type.addItems(["virtio-net-pci", "e1000"])
        l.addWidget(QLabel("Мережа:"))
        l.addWidget(self.f_net_type)
        self.f_net = QPlainTextEdit()
        l.addWidget(QLabel("Додатково:"))
        l.addWidget(self.f_net)
        self.tabs.addTab(tab, "Мережа")

    def init_advanced_tab(self):
        tab = QWidget()
        l = QVBoxLayout(tab)
        self.f_audio = QComboBox()
        self.f_audio.addItems(["pa", "alsa", "none"])
        l.addWidget(QLabel("Аудіо:"))
        l.addWidget(self.f_audio)
        self.f_usb = QCheckBox("USB 3.0 (XHCI)")
        self.f_usb.setChecked(True)
        self.f_tablet = QCheckBox("Tablet Mode")
        self.f_tablet.setChecked(True)
        l.addWidget(self.f_usb)
        l.addWidget(self.f_tablet)
        l.addStretch()
        self.tabs.addTab(tab, "Периферія")

    def init_expert_tab(self):
        tab = QWidget()
        l = QVBoxLayout(tab)
        self.f_extra = QPlainTextEdit()
        l.addWidget(QLabel("Extra Flags:"))
        l.addWidget(self.f_extra)
        self.tabs.addTab(tab, "Експерт")

    # --- Core Logic ---
    def generate_command_list(self):
        cmd = ["qemu-system-x86_64"]

        # QMP Support (Static Port 4444)
        cmd.extend(["-qmp", "tcp:localhost:4444,server,nowait"])

        # Accel
        is_kvm = os.path.exists('/dev/kvm')
        mode = self.f_accel.currentText()
        cmd.extend(["-accel", "kvm" if ("Auto" in mode and is_kvm) or mode == "kvm" else "tcg"])

        cmd.extend(["-m", str(self.f_ram.value())])
        cmd.extend(["-smp", str(self.f_smp.value())])
        cmd.extend(["-M", self.f_machine.currentText()])
        cmd.extend(["-cpu", self.f_cpu.currentText()])

        # Display
        disp = self.f_display.currentText()
        if self.f_gl.isChecked():
            disp += ",gl=on"
        cmd.extend(["-display", disp, "-vga", self.f_vga.currentText()])
        if self.f_fs.isChecked():
            cmd.append("-full-screen")

        # Storage
        if self.f_disk.text():
            p = self.f_disk.text()
            if p.lower().endswith(".iso"):
                cmd.extend(["-cdrom", p])
            else:
                iface = "virtio" if "virtio" in self.f_interface.currentText() else "ide"
                cmd.extend(["-drive", f"file={p},if={iface}"])

        if self.f_snapshot.isChecked():
            cmd.append("-snapshot")
        cmd.extend(["-boot", self.f_boot.currentText()[0]])

        # Net
        cmd.extend(["-netdev", "user,id=n1", "-device", f"{self.f_net_type.currentText()},netdev=n1"])

        if self.f_usb.isChecked():
            cmd.extend(["-device", "qemu-xhci,id=usb0"])
        if self.f_tablet.isChecked():
            cmd.extend(["-device", "usb-tablet"])

        extra = self.f_extra.toPlainText().strip()
        if extra:
            cmd.extend(shlex.split(extra))

        return cmd

    def run_vm(self):
        if self.process.state() == QProcess.ProcessState.Running:
            QMessageBox.information(self, "Інфо", "MGUI_QEMU вже виконує процес.")
            return

        # start process using program + args
        self.process.setProgram("qemu-system-x86_64")
        self.process.setArguments(self.generate_command_list()[1:])
        self.process.start()

    def update_status_ui(self):
        if self.process.state() == QProcess.ProcessState.Running:
            self.status_label.setText("● Стан: ПРАЦЮЄ")
            self.status_label.setStyleSheet("color: #00ff00; font-weight: bold;")
        else:
            self.status_label.setText("● Стан: Очікування")
            self.status_label.setStyleSheet("color: gray; font-weight: bold;")

    def save_vm(self):
        name = self.f_name.text().strip() or "unnamed_vm"
        p = self.base_path / name
        p.mkdir(exist_ok=True)
        config = {"name": name, "ram": self.f_ram.value(), "smp": self.f_smp.value(),
                  "disk": self.f_disk.text()}  # скорочено для прикладу
        with open(p / "config.json", "w") as f:
            json.dump(config, f, indent=4)
        self.refresh_list()
        QMessageBox.information(self, "MGUI_QEMU", f"Проект '{name}' збережено.")

    def load_vm(self, name):
        cfg_path = self.base_path / name / "config.json"
        if cfg_path.exists():
            with open(cfg_path, "r") as f:
                d = json.load(f)
                self.f_name.setText(d.get("name", ""))
                self.f_ram.setValue(d.get("ram", 2048))
        self.update_preview()

    def update_preview(self):
        self.cmd_preview.setPlainText(" ".join(self.generate_command_list()))

    def connect_all_signals(self):
        for w in [self.f_name, self.f_disk, self.f_ram, self.f_smp, self.f_machine, self.f_accel, self.f_gl, self.f_fs]:
            if hasattr(w, 'textChanged'):
                w.textChanged.connect(self.update_preview)
            if hasattr(w, 'valueChanged'):
                w.valueChanged.connect(self.update_preview)
            if hasattr(w, 'currentIndexChanged'):
                w.currentIndexChanged.connect(self.update_preview)
            if hasattr(w, 'stateChanged'):
                w.stateChanged.connect(self.update_preview)

    def refresh_list(self):
        self.vm_list.clear()
        if self.base_path.exists():
            for d in self.base_path.iterdir():
                if d.is_dir():
                    self.vm_list.addItem(d.name)

    def clear_fields(self):
        self.f_name.clear()
        self.f_disk.clear()
        self.update_preview()

    def select_file(self, line):
        f, _ = QFileDialog.getOpenFileName(self, "Вибрати файл")
        if f:
            line.setText(f)

    def export_script(self):
        """Export current qemu command to a .sh script file"""
        fname, _ = QFileDialog.getSaveFileName(self, "Експорт скрипта", filter="Shell Script (*.sh);;All Files (*)")
        if not fname:
            return
        if not fname.endswith(".sh"):
            fname += ".sh"
        cmd = " ".join(self.generate_command_list())
        try:
            with open(fname, "w") as fh:
                fh.write("#!/usr/bin/env bash\n")
                fh.write(cmd + "\n")
            QMessageBox.information(self, "Export", f"Скрипт збережено: {fname}")
        except OSError as e:
            QMessageBox.warning(self, "Export Error", f"Не вдалося зберегти файл: {e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = MGUI_QEMU()
    win.show()
    sys.exit(app.exec())