import sys
import json
import subprocess
import shlex
import os
from pathlib import Path
try:
    import psutil
except ImportError:
    psutil = None
import base64
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QLineEdit, QPushButton, QLabel,
                               QFileDialog, QSpinBox, QListWidget, QMessageBox,
                               QPlainTextEdit, QTabWidget, QCheckBox, QComboBox, QInputDialog)
from PySide6.QtCore import QProcess, QByteArray
from PySide6.QtGui import QIcon, QPixmap


class QemuNexus(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("QEMU Nexus Core - Professional Edition")
        self.setMinimumSize(1150, 850)

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

        self.base_path = Path.home() / "QEMU_VMs"
        self.base_path.mkdir(exist_ok=True)

        self.process = QProcess()
        self.process.started.connect(self.update_status_ui)
        self.process.finished.connect(self.update_status_ui)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)

        sidebar = QVBoxLayout()
        self.vm_list = QListWidget()
        self.vm_list.currentTextChanged.connect(self.load_vm)

        self.status_label = QLabel("● Стан: Очікування")
        self.status_label.setStyleSheet("color: gray; font-weight: bold;")

        sidebar.addWidget(QLabel("📂 Ваші проекти:"))
        sidebar.addWidget(self.vm_list)
        sidebar.addWidget(self.status_label)

        btn_new = QPushButton("➕ Нова конфігурація")
        btn_new.clicked.connect(self.clear_fields)
        sidebar.addWidget(btn_new)

        self.btn_run = QPushButton("🚀 ЗАПУСТИТИ VM")
        self.btn_run.setStyleSheet(
            "height: 60px; background: #1a4a7a; color: white; font-weight: bold; border-radius: 5px;")
        self.btn_run.clicked.connect(self.run_vm)
        sidebar.addWidget(self.btn_run)

        btn_export = QPushButton("📤 Експорт у .sh скрипт")
        btn_export.clicked.connect(self.export_script)
        sidebar.addWidget(btn_export)

        main_layout.addLayout(sidebar, 1)

        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs, 3)

        self.init_basic_tab()
        self.init_storage_tab()
        self.init_network_tab()
        self.init_display_tab()
        self.init_advanced_tab()
        self.init_expert_tab()

        self.cmd_preview = QPlainTextEdit()
        self.cmd_preview.setReadOnly(True)
        self.cmd_preview.setFixedHeight(100)
        self.cmd_preview.setStyleSheet("background: #000; color: #0f0; font-family: 'Monospace'; font-size: 11px;")

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

    @staticmethod
    def check_kvm():
        return os.path.exists('/dev/kvm') and os.access('/dev/kvm', os.R_OK | os.W_OK)

    def init_basic_tab(self):
        tab = QWidget()
        l = QVBoxLayout(tab)
        self.f_name = QLineEdit()
        l.addWidget(QLabel("Назва проекту:"))
        l.addWidget(self.f_name)

        self.f_machine = QComboBox()
        self.f_machine.addItems(["q35", "pc", "virt", "microvm"])
        l.addWidget(QLabel("Архітектура машини:"))
        l.addWidget(self.f_machine)

        self.f_cpu = QComboBox()
        self.f_cpu.addItems(["host", "qemu64", "max", "Ryzen", "Haswell-noTSX-IBRS"])
        l.addWidget(QLabel("Модель CPU:"))
        l.addWidget(self.f_cpu)

        self.f_accel = QComboBox()
        self.f_accel.addItems(["Auto (KVM -> TCG)", "kvm", "tcg"])
        l.addWidget(QLabel("Акселерація:"))
        l.addWidget(self.f_accel)

        self.f_ram = QSpinBox()
        self.f_ram.setRange(32, 128000)
        self.f_ram.setValue(2048)
        self.f_ram.setSuffix(" MB")
        l.addWidget(QLabel("Виділена пам'ять (RAM):"))
        l.addWidget(self.f_ram)

        self.f_smp = QSpinBox()
        self.f_smp.setRange(1, 128)
        self.f_smp.setValue(2)
        l.addWidget(QLabel("Кількість ядер:"))
        l.addWidget(self.f_smp)
        l.addStretch()
        self.tabs.addTab(tab, "Залізо")

    def init_storage_tab(self):
        tab = QWidget()
        l = QVBoxLayout(tab)

        h_disk = QHBoxLayout()
        self.f_disk = QLineEdit()
        btn_sel = QPushButton("📁 Вибрати")
        btn_sel.clicked.connect(lambda: self.select_file(self.f_disk))
        btn_create = QPushButton("✨ Створити .qcow2")
        btn_create.clicked.connect(self.create_disk_dialog)
        btn_create.setStyleSheet("background: #4a1a4a; color: white;")
        h_disk.addWidget(self.f_disk)
        h_disk.addWidget(btn_sel)
        h_disk.addWidget(btn_create)

        l.addWidget(QLabel("Файл образу диска або ISO:"))
        l.addLayout(h_disk)

        self.f_interface = QComboBox()
        self.f_interface.addItems(["virtio", "ide", "scsi"])
        l.addWidget(QLabel("Інтерфейс контролера:"))
        l.addWidget(self.f_interface)

        self.f_boot = QComboBox()
        self.f_boot.addItems(["c (Disk)", "d (CD-ROM)", "n (Network)"])
        l.addWidget(QLabel("Пріоритет завантаження:"))
        l.addWidget(self.f_boot)

        self.f_snapshot = QCheckBox("Режим Snapshot (не зберігати зміни в файл)")
        l.addWidget(self.f_snapshot)
        l.addStretch()
        self.tabs.addTab(tab, "Диски")

    def init_display_tab(self):
        tab = QWidget()
        l = QVBoxLayout(tab)
        self.f_vga = QComboBox()
        self.f_vga.addItems(["virtio", "std", "qxl", "cirrus", "vmware"])
        l.addWidget(QLabel("Відеоадаптер:"))
        l.addWidget(self.f_vga)
        self.f_display = QComboBox()
        self.f_display.addItems(["gtk", "sdl", "vnc=:1", "none"])
        l.addWidget(QLabel("Тип дисплея:"))
        l.addWidget(self.f_display)
        self.f_gl = QCheckBox("OpenGL (3D прискорення)")
        l.addWidget(self.f_gl)
        self.f_fs = QCheckBox("Повний екран (-full-screen)")
        l.addWidget(self.f_fs)
        l.addStretch()
        self.tabs.addTab(tab, "Графіка")

    def init_network_tab(self):
        tab = QWidget()
        l = QVBoxLayout(tab)
        self.f_net_type = QComboBox()
        self.f_net_type.addItems(["virtio-net-pci", "e1000", "rtl8139"])
        l.addWidget(QLabel("Мережева карта:"))
        l.addWidget(self.f_net_type)
        self.f_net = QPlainTextEdit()
        self.f_net.setPlaceholderText("-netdev user,id=n1...")
        l.addWidget(QLabel("Додаткові налаштування мережі:"))
        l.addWidget(self.f_net)
        self.tabs.addTab(tab, "Мережа")

    def init_advanced_tab(self):
        tab = QWidget()
        l = QVBoxLayout(tab)
        self.f_audio = QComboBox()
        self.f_audio.addItems(["pa", "alsa", "none", "sdl"])
        l.addWidget(QLabel("Аудіо драйвер:"))
        l.addWidget(self.f_audio)
        self.f_usb = QCheckBox("XHCI (USB 3.0) Підтримка")
        self.f_usb.setChecked(True)
        l.addWidget(self.f_usb)
        self.f_tablet = QCheckBox("Покращена синхронізація миші (Tablet)")
        self.f_tablet.setChecked(True)
        l.addWidget(self.f_tablet)
        l.addStretch()
        self.tabs.addTab(tab, "Периферія")

    def init_expert_tab(self):
        tab = QWidget()
        l = QVBoxLayout(tab)
        self.f_extra = QPlainTextEdit()
        l.addWidget(QLabel("Додаткові прапорці QEMU:"))
        l.addWidget(self.f_extra)
        self.tabs.addTab(tab, "Експерт")

    def create_disk_dialog(self):
        size, ok = QInputDialog.getText(self, "Новий диск", "Введіть розмір (напр. 20G):")
        if ok and size:
            save_path, _ = QFileDialog.getSaveFileName(self, "Зберегти образ", str(self.base_path),
                                                       "QEMU Disk (*.qcow2)")
            if save_path:
                try:
                    subprocess.run(["qemu-img", "create", "-f", "qcow2", save_path, size], check=True)
                    self.f_disk.setText(save_path)
                    QMessageBox.information(self, "Успіх", f"Диск {size} створено.")
                except (subprocess.CalledProcessError, FileNotFoundError) as e:
                    QMessageBox.critical(self, "Помилка", f"Не вдалося створити диск: {e}")

    @staticmethod
    def get_available_ram_mb() -> float:
        if psutil is not None and hasattr(psutil, "virtual_memory"):
            try:
                return psutil.virtual_memory().available / (1024 ** 2)
            except (AttributeError, OSError):
                pass
        try:
            with open("/proc/meminfo", "r") as f:
                for line in f:
                    if line.startswith("MemAvailable:"):
                        parts = line.split()
                        return int(parts[1]) / 1024.0
        except (FileNotFoundError, ValueError, OSError):
            pass
        return float("inf")

    def run_vm(self):
        avail_ram = self.get_available_ram_mb()
        if self.f_ram.value() > avail_ram:
            res = QMessageBox.warning(self, "Увага",
                                      f"Ви виділяєте {self.f_ram.value()}MB, а вільно лише {int(avail_ram)}MB.\nПродовжити?",
                                      QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if res == QMessageBox.StandardButton.No:
                return

        running_state = getattr(QProcess, "ProcessState", None)
        if running_state is not None:
            running_state = QProcess.ProcessState.Running
        else:
            running_state = getattr(QProcess, "Running", 2)

        if self.process.state() == running_state:
            QMessageBox.information(self, "Інфо", "VM вже запущена.")
            return

        self.process.setProgram("qemu-system-x86_64")
        self.process.setArguments(self.generate_command_list()[1:])
        self.process.start()

        if not self.process.waitForStarted(3000):
            QMessageBox.critical(self, "Помилка", "QEMU не зміг стартувати!")

    def update_status_ui(self):
        running_state = getattr(QProcess, "ProcessState", None)
        if running_state is not None:
            running_state = QProcess.ProcessState.Running
        else:
            running_state = getattr(QProcess, "Running", 2)

        if self.process.state() == running_state:
            self.status_label.setText("● Стан: ПРАЦЮЄ")
            self.status_label.setStyleSheet("color: #00ff00; font-weight: bold;")
        else:
            self.status_label.setText("● Стан: Очікування")
            self.status_label.setStyleSheet("color: gray; font-weight: bold;")

    def export_script(self):
        path, _ = QFileDialog.getSaveFileName(self, "Експорт", "", "Shell Script (*.sh)")
        if path:
            cmd = " ".join(self.generate_command_list())
            with open(path, "w") as f:
                f.write(f"#!/bin/bash\n# QEMU Nexus Core Generated Script\n\n{cmd}\n")
            os.chmod(path, 0o755)
            QMessageBox.information(self, "Успіх", "Скрипт збережено та зроблено виконуваним.")

    def save_vm(self):
        name = self.f_name.text().strip() or "unnamed_vm"
        p = self.base_path / name
        p.mkdir(exist_ok=True)

        config = {
            "name": name, "machine": self.f_machine.currentText(), "cpu": self.f_cpu.currentText(),
            "accel": self.f_accel.currentText(), "ram": self.f_ram.value(), "smp": self.f_smp.value(),
            "disk": self.f_disk.text(), "interface": self.f_interface.currentText(),
            "boot": self.f_boot.currentText(), "vga": self.f_vga.currentText(),
            "display": self.f_display.currentText(), "gl": self.f_gl.isChecked(),
            "fs": self.f_fs.isChecked(), "net_type": self.f_net_type.currentText(),
            "net_extra": self.f_net.toPlainText(), "audio": self.f_audio.currentText(),
            "usb": self.f_usb.isChecked(), "tablet": self.f_tablet.isChecked(),
            "extra": self.f_extra.toPlainText()
        }

        with open(p / "config.json", "w") as f:
            json.dump(config, f, indent=4)
        self.refresh_list()
        QMessageBox.information(self, "Збережено", f"Проект '{name}' готовий.")

    def load_vm(self, name):
        if not name:
            return
        cfg_path = self.base_path / name / "config.json"
        if not cfg_path.exists():
            return

        with open(cfg_path, "r") as f:
            d = json.load(f)
            self.f_name.setText(d.get("name", ""))
            self.f_ram.setValue(d.get("ram", 2048))
            self.f_smp.setValue(d.get("smp", 2))
            self.f_disk.setText(d.get("disk", ""))
            self.f_machine.setCurrentText(d.get("machine", "q35"))
            self.f_cpu.setCurrentText(d.get("cpu", "host"))
            self.f_accel.setCurrentText(d.get("accel", "Auto (KVM -> TCG)"))
            self.f_interface.setCurrentText(d.get("interface", "virtio"))
            self.f_boot.setCurrentText(d.get("boot", "c (Disk)"))
            self.f_vga.setCurrentText(d.get("vga", "virtio"))
            self.f_display.setCurrentText(d.get("display", "gtk"))
            self.f_gl.setChecked(d.get("gl", False))
            self.f_fs.setChecked(d.get("fs", False))
            self.f_net_type.setCurrentText(d.get("net_type", "virtio-net-pci"))
            self.f_net.setPlainText(d.get("net_extra", ""))
            self.f_audio.setCurrentText(d.get("audio", "pa"))
            self.f_usb.setChecked(d.get("usb", True))
            self.f_tablet.setChecked(d.get("tablet", True))
            self.f_extra.setPlainText(d.get("extra", ""))
        self.update_preview()

    def generate_command_list(self):
        cmd = ["qemu-system-x86_64"]

        kvm = self.check_kvm()
        mode = self.f_accel.currentText()
        if "Auto" in mode:
            cmd.extend(["-accel", "kvm" if kvm else "tcg"])
        else:
            cmd.extend(["-accel", mode])

        cmd.extend(["-m", str(self.f_ram.value())])
        cmd.extend(["-smp", str(self.f_smp.value())])
        cmd.extend(["-M", self.f_machine.currentText()])
        cmd.extend(["-cpu", self.f_cpu.currentText()])

        disp = self.f_display.currentText()
        if self.f_gl.isChecked():
            disp += ",gl=on"
        cmd.extend(["-display", disp])
        cmd.extend(["-vga", self.f_vga.currentText()])
        if self.f_fs.isChecked():
            cmd.append("-full-screen")

        if self.f_disk.text():
            p = self.f_disk.text()
            if Path(p).suffix.lower() == ".iso":
                cmd.extend(["-cdrom", p])
            else:
                iface = "virtio" if "virtio" in self.f_interface.currentText() else "ide"
                cmd.extend(["-drive", f"file={p},if={iface}"])

        if self.f_snapshot.isChecked():
            cmd.append("-snapshot")
        cmd.extend(["-boot", self.f_boot.currentText()[0]])

        net_dev = self.f_net_type.currentText()
        cmd.extend(["-netdev", "user,id=n1", "-device", f"{net_dev},netdev=n1"])

        if self.f_usb.isChecked():
            cmd.extend(["-device", "qemu-xhci,id=usb0"])
        if self.f_tablet.isChecked():
            cmd.extend(["-device", "usb-tablet"])
        if self.f_audio.currentText() != "none":
            aud = self.f_audio.currentText()
            cmd.extend(["-audiodev", f"{aud},id=s0", "-device", "intel-hda", "-device", "hda-duplex,audiodev=s0"])

        extra = self.f_extra.toPlainText().strip()
        if extra:
            try:
                cmd.extend(shlex.split(extra))
            except ValueError:
                pass

        return cmd

    def update_preview(self):
        self.cmd_preview.setPlainText(" ".join(self.generate_command_list()))

    def connect_all_signals(self):
        widgets = [self.f_name, self.f_disk, self.f_ram, self.f_smp, self.f_machine,
                   self.f_cpu, self.f_accel, self.f_boot, self.f_vga, self.f_display,
                   self.f_audio, self.f_snapshot, self.f_fs, self.f_usb, self.f_net,
                   self.f_extra, self.f_gl, self.f_interface, self.f_net_type, self.f_tablet]
        for w in widgets:
            if isinstance(w, QLineEdit):
                w.textChanged.connect(lambda *a: self.update_preview())
            elif isinstance(w, QPlainTextEdit):
                w.textChanged.connect(lambda *a: self.update_preview())
            elif isinstance(w, QSpinBox):
                w.valueChanged.connect(lambda *a: self.update_preview())
            elif isinstance(w, QComboBox):
                w.currentIndexChanged.connect(lambda *a: self.update_preview())
            elif isinstance(w, QCheckBox):
                w.stateChanged.connect(lambda *a: self.update_preview())

    def refresh_list(self):
        self.vm_list.clear()
        for d in self.base_path.iterdir():
            if d.is_dir() and (d / "config.json").exists():
                self.vm_list.addItem(d.name)

    def clear_fields(self):
        self.f_name.clear()
        self.f_disk.clear()
        self.update_preview()

    def select_file(self, line):
        f, _ = QFileDialog.getOpenFileName(self, "Файл")
        if f:
            line.setText(f)


# -------------------- ICON: load from icon.txt --------------------


def read_icon_base64_from_file() -> str:
    """Шукає icon.txt у тій же папці, що й скрипт, або в поточній робочій директорії.
    Повертає рядок base64 (без коментарів/порожніх рядків) або порожній рядок якщо не знайдено/помилка.
    """
    candidates = [Path(__file__).parent / "icon.txt", Path.cwd() / "icon.txt"]
    for p in candidates:
        if p.exists():
            try:
                raw = p.read_text(encoding="utf-8")
                # прибираємо коментарі (рядки що починаються з #) та порожні рядки
                lines = [ln.strip() for ln in raw.splitlines() if ln.strip() and not ln.strip().startswith('#')]
                return ''.join(lines)
            except Exception:
                continue
    return ''


def load_window_icon_from_base64(b64: str) -> QIcon:
    """Декодує base64 і повертає QIcon. Без тимчасових файлів."""
    try:
        raw = base64.b64decode(b64.encode('utf-8'))
    except Exception:
        # якщо base64 некоректний — повернути пусту іконку
        return QIcon()
    pixmap = QPixmap()
    # QPixmap.loadFromData в PySide6 приймає bytes або QByteArray
    pixmap.loadFromData(QByteArray(raw))
    return QIcon(pixmap)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # намагаємось прочитати icon.txt у тій же папці, що й скрипт
    b64 = read_icon_base64_from_file()
    icon = load_window_icon_from_base64(b64) if b64 else QIcon()
    app.setWindowIcon(icon)

    window = QemuNexus()
    window.setWindowIcon(icon)
    window.show()
    sys.exit(app.exec())
