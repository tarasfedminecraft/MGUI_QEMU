import sys
import json
import subprocess
import shlex
import os
from pathlib import Path
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QLineEdit, QPushButton, QLabel,
                               QFileDialog, QSpinBox, QListWidget, QMessageBox,
                               QPlainTextEdit, QTabWidget, QCheckBox, QComboBox)
from PySide6.QtCore import Qt


class QemuNexus(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("QEMU Nexus Core - Universal Edition")
        self.setMinimumSize(1100, 800)

        self.base_path = Path.home() / "QEMU_VMs"
        self.base_path.mkdir(exist_ok=True)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)

        # --- Sidebar ---
        sidebar = QVBoxLayout()
        self.vm_list = QListWidget()
        self.vm_list.currentTextChanged.connect(self.load_vm)
        sidebar.addWidget(QLabel("📂 Ваші проекти:"))
        sidebar.addWidget(self.vm_list)

        btn_new = QPushButton("➕ Нова конфігурація")
        btn_new.clicked.connect(self.clear_fields)
        sidebar.addWidget(btn_new)

        self.btn_run = QPushButton("🚀 ЗАПУСТИТИ VM")
        self.btn_run.setStyleSheet("height: 60px; background: #1a4a7a; color: white; font-weight: bold;")
        self.btn_run.clicked.connect(self.run_vm)
        sidebar.addWidget(self.btn_run)
        main_layout.addLayout(sidebar, 1)

        # --- Tabs ---
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs, 3)

        self.init_basic_tab()
        self.init_storage_tab()
        self.init_network_tab()
        self.init_display_tab()
        self.init_advanced_tab()
        self.init_expert_tab()

        # --- Preview ---
        self.cmd_preview = QPlainTextEdit()
        self.cmd_preview.setReadOnly(True)
        self.cmd_preview.setFixedHeight(120)
        self.cmd_preview.setStyleSheet("background: #000; color: #0f0; font-family: 'Monospace'; font-size: 11px;")

        bottom_panel = QVBoxLayout()
        bottom_panel.addWidget(QLabel("🛠 Результуюча команда (адаптивна):"))
        bottom_panel.addWidget(self.cmd_preview)

        btn_save = QPushButton("💾 Зберегти налаштування")
        btn_save.clicked.connect(self.save_vm)
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
        """Перевірка підтримки апаратного прискорення на поточному залізі"""
        return os.path.exists('/dev/kvm') and os.access('/dev/kvm', os.R_OK | os.W_OK)


    def init_basic_tab(self):
        tab = QWidget()
        l = QVBoxLayout(tab)
        self.f_name = QLineEdit()
        l.addWidget(QLabel("Назва:"));
        l.addWidget(self.f_name)

        self.f_machine = QComboBox()
        self.f_machine.addItems(["q35 (Сучасна)", "pc (Стара/Сумісна)", "virt", "microvm"])
        l.addWidget(QLabel("Тип машини:"));
        l.addWidget(self.f_machine)

        self.f_cpu = QComboBox()
        # "host" - найкраще для нових, "qemu64" - заведеться навіть на Pentium 4
        self.f_cpu.addItems(["host (Як у мене)", "qemu64 (Універсальний)", "max", "486", "pentium3"])
        l.addWidget(QLabel("Процесор:"));
        l.addWidget(self.f_cpu)

        self.f_accel = QComboBox()
        self.f_accel.addItems(["Auto (KVM -> TCG)", "kvm (Тільки прискорення)", "tcg (Тільки емуляція)"])
        l.addWidget(QLabel("Режим роботи:"));
        l.addWidget(self.f_accel)

        self.f_ram = QSpinBox()
        self.f_ram.setRange(32, 131072);
        self.f_ram.setValue(2048)
        l.addWidget(QLabel("RAM (MB):"));
        l.addWidget(self.f_ram)

        self.f_smp = QSpinBox()
        self.f_smp.setRange(1, 128);
        self.f_smp.setValue(2)
        l.addWidget(QLabel("Ядра:"));
        l.addWidget(self.f_smp)
        l.addStretch();
        self.tabs.addTab(tab, "Залізо")

    def init_storage_tab(self):
        tab = QWidget()
        l = QVBoxLayout(tab)
        self.f_disk = QLineEdit()
        btn = QPushButton("📁 Образ диска/ISO");
        btn.clicked.connect(lambda: self.select_file(self.f_disk))
        l.addWidget(btn);
        l.addWidget(self.f_disk)

        self.f_interface = QComboBox()
        self.f_interface.addItems(["virtio (Швидкий)", "ide (Сумісний)", "scsi"])
        l.addWidget(QLabel("Інтерфейс диска:"));
        l.addWidget(self.f_interface)

        self.f_boot = QComboBox()
        self.f_boot.addItems(["c (Disk)", "d (CD-ROM)", "n (Network)"])
        l.addWidget(QLabel("Завантаження з:"));
        l.addWidget(self.f_boot)
        self.f_snapshot = QCheckBox("Snapshot (тимчасові зміни)")
        l.addWidget(self.f_snapshot)
        l.addStretch();
        self.tabs.addTab(tab, "Диски")

    def init_display_tab(self):
        tab = QWidget()
        l = QVBoxLayout(tab)
        self.f_vga = QComboBox()
        self.f_vga.addItems(["virtio", "std", "cirrus (Для дуже старих ОС)", "qxl", "vmware"])
        l.addWidget(QLabel("Відеокарта:"));
        l.addWidget(self.f_vga)

        self.f_display = QComboBox()
        self.f_display.addItems(["gtk", "sdl", "vnc=:1", "curses", "none"])
        l.addWidget(QLabel("Вивід зображення:"));
        l.addWidget(self.f_display)

        self.f_gl = QCheckBox("Увімкнути 3D прискорення (OpenGL)")
        l.addWidget(self.f_gl)
        self.f_fs = QCheckBox("Повний екран")
        l.addWidget(self.f_fs)
        l.addStretch();
        self.tabs.addTab(tab, "Графіка")

    def init_network_tab(self):
        tab = QWidget()
        l = QVBoxLayout(tab)
        self.f_net_type = QComboBox()
        self.f_net_type.addItems(["virtio-net-pci (Новий)", "e1000 (Intel)", "rtl8139 (Realtek - Універсальний)"])
        l.addWidget(QLabel("Мережева карта:"));
        l.addWidget(self.f_net_type)
        self.f_net = QPlainTextEdit()
        self.f_net.setPlaceholderText("Додаткові параметри мережі...")
        l.addWidget(self.f_net);
        self.tabs.addTab(tab, "Мережа")

    def init_advanced_tab(self):
        tab = QWidget()
        l = QVBoxLayout(tab)
        self.f_audio = QComboBox()
        self.f_audio.addItems(["pa (PulseAudio/Pipewire)", "alsa", "oss", "sdl", "none"])
        l.addWidget(QLabel("Звукова підсистема:"));
        l.addWidget(self.f_audio)
        self.f_usb = QCheckBox("USB Підтримка")
        self.f_usb.setChecked(True)
        l.addWidget(self.f_usb)
        self.f_tablet = QCheckBox("Планшет (виправляє курсор миші)")
        self.f_tablet.setChecked(True)
        l.addWidget(self.f_tablet)
        l.addStretch();
        self.tabs.addTab(tab, "Периферія")

    def init_expert_tab(self):
        tab = QWidget()
        l = QVBoxLayout(tab)
        self.f_extra = QPlainTextEdit()
        l.addWidget(QLabel("Додаткові прапорці:"));
        l.addWidget(self.f_extra)
        self.tabs.addTab(tab, "Експерт")

    def connect_all_signals(self):
        widgets = [self.f_name, self.f_disk, self.f_ram, self.f_smp, self.f_machine,
                   self.f_cpu, self.f_accel, self.f_boot, self.f_vga, self.f_display,
                   self.f_audio, self.f_snapshot, self.f_fs, self.f_usb, self.f_net,
                   self.f_extra, self.f_gl, self.f_interface, self.f_net_type, self.f_tablet]

        # use lambdas that accept arbitrary args to avoid signature mismatches
        for w in widgets:
            if isinstance(w, QLineEdit):
                w.textChanged.connect(lambda *a, _w=w: self.update_preview())
            elif isinstance(w, QPlainTextEdit):
                w.textChanged.connect(lambda *a, _w=w: self.update_preview())
            elif isinstance(w, QSpinBox):
                w.valueChanged.connect(lambda *a, _w=w: self.update_preview())
            elif isinstance(w, QComboBox):
                w.currentIndexChanged.connect(lambda *a, _w=w: self.update_preview())
            elif isinstance(w, QCheckBox):
                w.stateChanged.connect(lambda *a, _w=w: self.update_preview())

    def generate_command_list(self):
        cmd = ["qemu-system-x86_64"]

        # 1. Адаптивне прискорення
        has_kvm = self.check_kvm()
        accel_mode = self.f_accel.currentText()
        if "Auto" in accel_mode:
            if has_kvm:
                cmd.extend(["-accel", "kvm"])
            else:
                cmd.extend(["-accel", "tcg"])
        elif "kvm" in accel_mode:
            cmd.extend(["-accel", "kvm"])
        else:
            cmd.extend(["-accel", "tcg"])

        # 2. Базові ресурси
        cmd.extend(["-m", str(self.f_ram.value())])
        cmd.extend(["-smp", str(self.f_smp.value())])
        cmd.extend(["-M", self.f_machine.currentText().split()[0]])

        cpu_val = self.f_cpu.currentText().split()[0]
        cmd.extend(["-cpu", cpu_val])

        # 3. Графіка з перевіркою GL
        display_cfg = self.f_display.currentText()
        if self.f_gl.isChecked():
            display_cfg += ",gl=on"
        cmd.extend(["-display", display_cfg])
        cmd.extend(["-vga", self.f_vga.currentText()])

        # 4. Диски
        if self.f_disk.text():
            p = self.f_disk.text()
            if Path(p).suffix.lower() == ".iso":
                cmd.extend(["-cdrom", p])
            else:
                if "virtio" in self.f_interface.currentText():
                    cmd.extend(["-drive", f"file={p},if=virtio"])
                else:
                    cmd.extend(["-drive", f"file={p},if=ide"])

        # 5. Мережа
        net_card = self.f_net_type.currentText().split()[0]
        cmd.extend(["-netdev", "user,id=n1", "-device", f"{net_card},netdev=n1"])

        # 6. Додатково
        if self.f_snapshot.isChecked(): cmd.append("-snapshot")
        if self.f_fs.isChecked(): cmd.append("-full-screen")
        if self.f_usb.isChecked(): cmd.extend(["-device", "qemu-xhci,id=usb0"])
        if self.f_tablet.isChecked(): cmd.extend(["-device", "usb-tablet"])

        if self.f_audio.currentText() != "none":
            aud = self.f_audio.currentText().split()[0]
            cmd.extend(["-audiodev", f"{aud},id=snd0", "-device", "intel-hda", "-device", "hda-duplex,audiodev=snd0"])

        cmd.extend(["-boot", self.f_boot.currentText()[0]])

        # Експертні параметри
        extra = self.f_extra.toPlainText().strip()
        if extra:
            try:
                cmd.extend(shlex.split(extra))
            except ValueError:
                # malformed quoting in extra flags — ignore silently
                pass

        return cmd

    def update_preview(self):
        self.cmd_preview.setPlainText(" ".join(self.generate_command_list()))

    def save_vm(self):
        name = self.f_name.text().strip() or "unnamed_vm"
        p = self.base_path / name
        p.mkdir(exist_ok=True)
        config = {"name": name, "ram": self.f_ram.value(), "disk": self.f_disk.text(), "cpu": self.f_cpu.currentText()}
        with open(p / "config.json", "w") as f: json.dump(config, f)
        self.refresh_list()
        QMessageBox.information(self, "OK", "Збережено!")

    def load_vm(self, name):
        if not name: return
        cfg = self.base_path / name / "config.json"
        if cfg.exists():
            with open(cfg, "r") as f:
                d = json.load(f)
                self.f_name.setText(d.get("name", ""))
                self.f_disk.setText(d.get("disk", ""))
                self.f_ram.setValue(d.get("ram", 2048))
        self.update_preview()

    def run_vm(self):
        subprocess.Popen(self.generate_command_list())

    def refresh_list(self):
        self.vm_list.clear()
        for d in self.base_path.iterdir():
            if d.is_dir() and (d / "config.json").exists(): self.vm_list.addItem(d.name)

    def clear_fields(self):
        self.f_name.clear()
        self.f_disk.clear()
        self.update_preview()

    def select_file(self, line):
        f, _ = QFileDialog.getOpenFileName(self, "Файл")
        if f: line.setText(f)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = QemuNexus()
    window.show()
    sys.exit(app.exec())