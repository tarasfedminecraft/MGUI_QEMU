# cspell:ignore aarch loongarch hppa Xtensa xtensa qapp powerdown virt QCOW qcow virtio
import sys
import json
import shlex
import socket
import threading
import platform
import time  # Додано для пауз
from pathlib import Path
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QLineEdit, QPushButton, QLabel,
                               QFileDialog, QSpinBox, QListWidget, QMessageBox,
                               QPlainTextEdit, QTabWidget, QComboBox,
                               QProgressBar, QFormLayout)
from PySide6.QtCore import QProcess, QTimer, Qt
from PySide6.QtGui import QPalette

try:
    import psutil
except ImportError:
    psutil = None


class MguiQemu(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MGUI_QEMU - Professional Virtualization Control")
        self.setMinimumSize(1200, 900)

        # Ініціалізація змінних
        self.qmp_port = 4444
        self.base_path = Path.home() / "MGUI_QEMU_VMs"
        self.base_path.mkdir(exist_ok=True)
        self.process = QProcess()

        # Словник архітектур
        self.arch_map = {
            "x86_64": "x86_64", "i386": "i386", "Arm (64-bit)": "aarch64",
            "Arm (32-bit)": "arm", "RISC-V (64-bit)": "riscv64", "RISC-V (32-bit)": "riscv32"
        }

        self.init_ui()
        self.apply_system_theme()

        # Сигнали процесу
        self.process.started.connect(self.update_status_ui)
        self.process.finished.connect(self.on_process_finished)  # Оновлено
        self.process.readyReadStandardError.connect(self.read_stderr)

        # Таймер статистики
        self.stats_timer = QTimer()
        self.stats_timer.timeout.connect(self.update_stats)
        self.stats_timer.start(2000)

    def apply_system_theme(self):
        qapp = QApplication.instance()
        palette = qapp.palette()
        bg_color = palette.color(QPalette.ColorRole.Window).lightness()
        self.is_dark = bg_color < 128

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)

        sidebar = QVBoxLayout()
        self.vm_list = QListWidget()
        self.vm_list.currentTextChanged.connect(self.load_vm)

        self.status_label = QLabel("● Стан: Очікування")
        self.status_label.setStyleSheet("font-weight: bold; color: gray;")

        self.cpu_bar = QProgressBar()
        self.cpu_bar.setFormat("CPU: %p%")
        self.ram_bar = QProgressBar()
        self.ram_bar.setFormat("RAM: %p%")

        sidebar.addWidget(QLabel("📂 Ваші проекти:"))
        sidebar.addWidget(self.vm_list)
        sidebar.addWidget(self.status_label)
        sidebar.addWidget(self.cpu_bar)
        sidebar.addWidget(self.ram_bar)

        qmp_group = QHBoxLayout()
        for icon, cmd in [("⏸", "stop"), ("▶", "cont"), ("🛑", "system_powerdown")]:
            btn = QPushButton(icon)
            btn.clicked.connect(lambda chk=False, c=cmd: self.send_qmp_command({"execute": c}))
            qmp_group.addWidget(btn)
        sidebar.addLayout(qmp_group)

        self.btn_run = QPushButton("🚀 ЗАПУСТИТИ")
        self.btn_run.setFixedHeight(50)
        self.btn_run.setStyleSheet("background: #1a4a7a; color: white; font-weight: bold; border-radius: 5px;")
        self.btn_run.clicked.connect(self.run_vm)
        sidebar.addWidget(self.btn_run)

        main_layout.addLayout(sidebar, 1)

        right_layout = QVBoxLayout()
        self.tabs = QTabWidget()

        # Вкладка Залізо
        self.tab_hw = QWidget()
        hw_l = QFormLayout(self.tab_hw)
        self.f_name = QLineEdit()
        self.f_arch = QComboBox()
        self.f_arch.addItems(list(self.arch_map.keys()))
        self.f_machine = QComboBox()
        self.f_machine.addItems(["q35", "pc", "virt"])
        self.f_cpu = QComboBox()
        self.f_cpu.addItems(["host", "max", "qemu64"])
        self.f_ram = QSpinBox()
        self.f_ram.setRange(128, 64000)
        self.f_ram.setValue(2048)
        self.f_smp = QSpinBox()
        self.f_smp.setRange(1, 32)
        self.f_smp.setValue(2)
        hw_l.addRow("Назва:", self.f_name)
        hw_l.addRow("Архітектура:", self.f_arch)
        hw_l.addRow("Машина:", self.f_machine)
        hw_l.addRow("Процесор:", self.f_cpu)
        hw_l.addRow("RAM (MB):", self.f_ram)
        hw_l.addRow("Ядра (SMP):", self.f_smp)
        self.tabs.addTab(self.tab_hw, "Залізо")

        # Вкладка Диски
        self.tab_disk = QWidget()
        disk_l = QVBoxLayout(self.tab_disk)
        h_disk = QHBoxLayout()
        self.f_disk = QLineEdit()
        btn_br = QPushButton("📁")
        btn_br.clicked.connect(lambda: self.select_file(self.f_disk))
        h_disk.addWidget(self.f_disk)
        h_disk.addWidget(btn_br)
        disk_l.addWidget(QLabel("Образ Диска / ISO:"))
        disk_l.addLayout(h_disk)
        self.f_boot = QComboBox()
        self.f_boot.addItems(["Disk (c)", "CD-ROM (d)"])
        disk_l.addWidget(QLabel("Завантаження з:"))
        disk_l.addWidget(self.f_boot)
        self.tabs.addTab(self.tab_disk, "Диски")

        # Вкладка Експерт
        self.tab_ex = QWidget()
        ex_l = QVBoxLayout(self.tab_ex)
        path_group = QHBoxLayout()
        self.f_qemu_path = QLineEdit()
        btn_qemu_br = QPushButton("Огляд")
        btn_qemu_br.clicked.connect(self.select_qemu_executable)
        path_group.addWidget(self.f_qemu_path)
        path_group.addWidget(btn_qemu_br)
        ex_l.addWidget(QLabel("Шлях до QEMU (Binary):"))
        ex_l.addLayout(path_group)
        self.f_extra = QPlainTextEdit()
        ex_l.addWidget(QLabel("Додаткові аргументи:"))
        ex_l.addWidget(self.f_extra)
        self.tabs.addTab(self.tab_ex, "Експерт")

        right_layout.addWidget(self.tabs)

        self.cmd_preview = QPlainTextEdit()
        self.cmd_preview.setReadOnly(True)
        self.cmd_preview.setFixedHeight(80)
        self.cmd_preview.setStyleSheet("background: #000; color: #0f0; font-family: 'Consolas'; font-size: 11px;")
        right_layout.addWidget(QLabel("🛠 Поточна команда:"))
        right_layout.addWidget(self.cmd_preview)

        btn_save = QPushButton("💾 Зберегти конфігурацію")
        btn_save.clicked.connect(self.save_vm)
        right_layout.addWidget(btn_save)

        main_layout.addLayout(right_layout, 3)

        self.update_qemu_path_auto()

        # Зв'язки для оновлення
        for w in [self.f_arch, self.f_machine, self.f_cpu, self.f_ram, self.f_smp, self.f_boot]:
            if isinstance(w, QComboBox):
                w.currentIndexChanged.connect(self.update_preview)
            else:
                w.valueChanged.connect(self.update_preview)

        self.f_arch.currentIndexChanged.connect(self.update_qemu_path_auto)
        self.f_disk.textChanged.connect(self.update_preview)
        self.f_extra.textChanged.connect(self.update_preview)
        self.f_qemu_path.textChanged.connect(self.update_preview)

        self.refresh_list()
        self.update_preview()

    def update_qemu_path_auto(self):
        arch = self.arch_map.get(self.f_arch.currentText(), "x86_64")
        binary_name = f"qemu-system-{arch}"
        if platform.system() == "Windows":
            binary_name += ".exe"
            for base in [Path("C:/Program Files/qemu"), Path("C:/qemu")]:
                full_path = base / binary_name
                if full_path.exists():
                    self.f_qemu_path.setText(str(full_path).replace("\\", "/"))
                    return
        self.f_qemu_path.setText(binary_name)

    def select_qemu_executable(self):
        file_filter = "Executables (*.exe)" if platform.system() == "Windows" else "All Files (*)"
        file_path, _ = QFileDialog.getOpenFileName(self, "Виберіть бінарний файл QEMU", "", file_filter)
        if file_path: self.f_qemu_path.setText(file_path)

    def generate_command_list(self):
        qemu_bin = self.f_qemu_path.text().strip()
        if not qemu_bin:
            qemu_bin = f"qemu-system-{self.arch_map.get(self.f_arch.currentText(), 'x86_64')}"

        cmd = [qemu_bin]
        sys_os = platform.system()
        if self.f_cpu.currentText() == "host":
            if sys_os == "Linux":
                cmd.append("-enable-kvm")
            elif sys_os == "Windows":
                cmd.extend(["-accel", "whpx"])
            elif sys_os == "Darwin":
                cmd.extend(["-accel", "hvf"])

        # Використовуємо стабільний порт для сесії
        cmd.extend(["-qmp", f"tcp:127.0.0.1:{self.qmp_port},server,nowait"])

        cmd.extend(["-m", str(self.f_ram.value())])
        cmd.extend(["-smp", str(self.f_smp.value())])
        cmd.extend(["-M", self.f_machine.currentText()])
        cmd.extend(["-cpu", self.f_cpu.currentText()])

        path = self.f_disk.text()
        if path:
            if path.lower().endswith(".iso"):
                cmd.extend(["-cdrom", path])
            else:
                cmd.extend(["-drive", f"file={path},if=virtio"])

        boot_mode = "c" if "Disk" in self.f_boot.currentText() else "d"
        cmd.extend(["-boot", boot_mode])

        extra = self.f_extra.toPlainText().strip()
        if extra: cmd.extend(shlex.split(extra))
        return cmd

    def update_preview(self):
        try:
            self.cmd_preview.setPlainText(" ".join(self.generate_command_list()))
        except Exception as e:
            self.cmd_preview.setPlainText(f"Помилка: {e}")

    def run_vm(self):
        if self.process.state() == QProcess.ProcessState.Running:
            self.process.terminate()  # Надсилає Signal 15
            return

        self.qmp_port = self.find_free_port()  # Новий порт при кожному запуску
        args = self.generate_command_list()

        # Перевірка наявності файлу
        if not Path(args[0]).exists() and "/" in args[0]:
            QMessageBox.critical(self, "Помилка", f"Файл QEMU не знайдено: {args[0]}")
            return

        self.process.setProgram(args[0])
        self.process.setArguments(args[1:])
        self.process.start()

    def on_process_finished(self):
        self.update_status_ui()
        print("QEMU завершив роботу.")

    def update_status_ui(self):
        is_run = self.process.state() == QProcess.ProcessState.Running
        self.btn_run.setText("🛑 ЗУПИНИТИ" if is_run else "🚀 ЗАПУСТИТИ")
        self.btn_run.setStyleSheet(
            f"background: {'#9e1a1a' if is_run else '#1a4a7a'}; color: white; font-weight: bold;")
        self.status_label.setText(f"● Стан: {'ПРАЦЮЄ' if is_run else 'Зупинено'}")
        self.status_label.setStyleSheet(f"color: {'#00ff00' if is_run else 'gray'}; font-weight: bold;")

    def read_stderr(self):
        err = self.process.readAllStandardError().data().decode()
        if "address already in use" in err.lower():
            QMessageBox.warning(self, "Порт зайнятий", "QMP порт зайнятий. Спробуйте ще раз.")
        print(f"QEMU LOG: {err}")

    def update_stats(self):
        if psutil:
            self.cpu_bar.setValue(int(psutil.cpu_percent()))
            self.ram_bar.setValue(int(psutil.virtual_memory().percent))

    def send_qmp_command(self, command):
        def _send():
            # РОЗУМНЕ ПІДКЛЮЧЕННЯ: 5 спроб з паузою
            for i in range(5):
                try:
                    time.sleep(0.5)  # Пауза, щоб QEMU встиг відкрити сокет
                    with socket.create_connection(("127.0.0.1", self.qmp_port), timeout=1) as s:
                        s.recv(1024)  # Привітання
                        s.sendall(json.dumps({"execute": "qmp_capabilities"}).encode())
                        s.recv(1024)
                        s.sendall(json.dumps(command).encode())
                        print(f"QMP: Команда {command['execute']} надіслана.")
                        return
                except ConnectionRefusedError:
                    print(f"QMP: Спроба {i + 1} не вдалася (очікування сокета...)")
                except Exception as e:
                    print(f"QMP Error: {e}")
                    break

        if self.process.state() == QProcess.ProcessState.Running:
            threading.Thread(target=_send, daemon=True).start()
        else:
            print("QMP: Неможливо надіслати команду, ВМ не запущена.")

    # ... (решта методів save_vm, load_vm, refresh_list, find_free_port без змін) ...

    @staticmethod
    def find_free_port():
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('127.0.0.1', 0))
            return s.getsockname()[1]

    def save_vm(self):
        name = self.f_name.text() or "unnamed_vm"
        p = self.base_path / name
        p.mkdir(exist_ok=True)
        data = {
            "name": name, "arch": self.f_arch.currentText(),
            "ram": self.f_ram.value(), "disk": self.f_disk.text(),
            "cpu": self.f_cpu.currentText(), "smp": self.f_smp.value(),
            "qemu_path": self.f_qemu_path.text()
        }
        with open(p / "config.json", "w", encoding='utf-8') as f:
            json.dump(data, f, indent=4)
        self.refresh_list()
        QMessageBox.information(self, "Успіх", "Конфігурацію збережено!")

    def load_vm(self, name):
        p = self.base_path / name / "config.json"
        if p.exists():
            with open(p, "r", encoding='utf-8') as f:
                d = json.load(f)
                self.f_name.setText(d.get("name", ""))
                self.f_disk.setText(d.get("disk", ""))
                self.f_ram.setValue(d.get("ram", 2048))
                self.f_cpu.setCurrentText(d.get("cpu", "qemu64"))
                self.f_arch.setCurrentText(d.get("arch", "x86_64"))
                self.f_qemu_path.setText(d.get("qemu_path", ""))
        self.update_preview()

    def refresh_list(self):
        self.vm_list.clear()
        if self.base_path.exists():
            for d in self.base_path.iterdir():
                if d.is_dir(): self.vm_list.addItem(d.name)

    def select_file(self, line_edit):
        file_path, _ = QFileDialog.getOpenFileName(self, "Виберіть файл")
        if file_path: line_edit.setText(file_path)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MguiQemu()
    window.show()
    sys.exit(app.exec())