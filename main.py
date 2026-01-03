# cspell:ignore aarch aarch64 loongarch hppa Xtensa xtensa qapp powerdown virt QCOW qcow virtio whpx
import sys
import json
import shlex
import socket
import threading
import platform
import time
import shutil
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QLabel, QFileDialog, QSpinBox, QListWidget,
    QMessageBox, QPlainTextEdit, QTabWidget, QComboBox, QProgressBar, QFormLayout
)
from PySide6.QtCore import QProcess, QTimer
from PySide6.QtGui import QPalette
from json import JSONDecodeError

try:
    import psutil
except ImportError:
    psutil = None


class MguiQemu(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MGUI_QEMU - Professional Virtualization Control")
        self.setMinimumSize(1200, 900)

        # UI атрибути
        self.is_dark = False
        self.vm_list = None
        self.status_label = None
        self.cpu_bar = None
        self.ram_bar = None
        self.btn_run = None
        self.tabs = None
        self.tab_hw = None
        self.f_name = None
        self.f_arch = None
        self.f_machine = None
        self.f_cpu = None
        self.f_ram = None
        self.f_smp = None
        self.tab_disk = None
        self.f_disk = None
        self.f_boot = None
        self.tab_ex = None
        self.f_qemu_path = None
        self.f_extra = None
        self.cmd_preview = None

        self.qmp_port = 4444
        self.base_path = Path.home() / "MGUI_QEMU_VMs"
        self.base_path.mkdir(exist_ok=True)
        self.process = QProcess()

        self.arch_map = {
            "x86_64": "x86_64",
            "i386": "i386",
            "Arm (64-bit)": "aarch64",
            "Arm (32-bit)": "arm",
            "RISC-V (64-bit)": "riscv64",
            "RISC-V (32-bit)": "riscv32"
        }

        self.init_ui()
        self.apply_system_theme()

        # Сигнали
        self.process.started.connect(self.update_status_ui)
        self.process.finished.connect(lambda: self.on_process_finished())
        self.process.readyReadStandardError.connect(self.read_stderr)

        self.stats_timer = QTimer()
        self.stats_timer.timeout.connect(self.update_stats)
        self.stats_timer.start(2000)

    def apply_system_theme(self):
        qapp = QApplication.instance()
        if isinstance(qapp, QApplication):
            palette = qapp.palette()
            bg_color = palette.color(QPalette.ColorRole.Window).lightness()
            self.is_dark = bg_color < 128
        else:
            self.is_dark = False

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)

        # Sidebar
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
        for icon, cmd_name in [("⏸", "stop"), ("▶", "cont"), ("🛑", "system_powerdown")]:
            btn = QPushButton(icon)
            btn.clicked.connect(lambda chk=False, cmd=cmd_name: self.send_qmp_command({"execute": cmd}))
            qmp_group.addWidget(btn)
        sidebar.addLayout(qmp_group)

        self.btn_run = QPushButton("🚀 ЗАПУСТИТИ")
        self.btn_run.setFixedHeight(50)
        self.btn_run.setStyleSheet(
            "background: #1a4a7a; color: white; font-weight: bold; border-radius: 5px;"
        )
        self.btn_run.clicked.connect(self.run_vm)
        sidebar.addWidget(self.btn_run)

        main_layout.addLayout(sidebar, 1)

        # Tabs
        right_layout = QVBoxLayout()
        self.tabs = QTabWidget()

        # Tab Hardware
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

        # Tab Disk
        self.tab_disk = QWidget()
        disk_l = QVBoxLayout(self.tab_disk)
        h_disk = QHBoxLayout()
        self.f_disk = QLineEdit()
        btn_br = QPushButton("📁")
        btn_br.clicked.connect(lambda: self.select_file(self.f_disk))
        h_disk.addWidget(self.f_disk)
        h_disk.addWidget(btn_br)
        self.f_boot = QComboBox()
        self.f_boot.addItems(["Disk (c)", "CD-ROM (d)"])
        disk_l.addWidget(QLabel("Образ Диска / ISO:"))
        disk_l.addLayout(h_disk)
        disk_l.addWidget(QLabel("Завантаження з:"))
        disk_l.addWidget(self.f_boot)
        self.tabs.addTab(self.tab_disk, "Диски")

        # Tab Expert
        self.tab_ex = QWidget()
        ex_l = QVBoxLayout(self.tab_ex)
        self.f_qemu_path = QLineEdit()
        btn_qemu_br = QPushButton("Огляд")
        btn_qemu_br.clicked.connect(self.select_qemu_executable)
        path_h = QHBoxLayout()
        path_h.addWidget(self.f_qemu_path)
        path_h.addWidget(btn_qemu_br)
        ex_l.addWidget(QLabel("Шлях до QEMU (Binary):"))
        ex_l.addLayout(path_h)
        self.f_extra = QPlainTextEdit()
        ex_l.addWidget(QLabel("Додаткові аргументи:"))
        ex_l.addWidget(self.f_extra)
        self.tabs.addTab(self.tab_ex, "Експерт")

        right_layout.addWidget(self.tabs)

        self.cmd_preview = QPlainTextEdit()
        self.cmd_preview.setReadOnly(True)
        self.cmd_preview.setFixedHeight(80)
        self.cmd_preview.setStyleSheet(
            "background: #000; color: #0f0; font-family: 'Consolas'; font-size: 11px;"
        )
        right_layout.addWidget(QLabel("🛠 Поточна команда:"))
        right_layout.addWidget(self.cmd_preview)

        btn_save = QPushButton("💾 Зберегти конфігурацію")
        btn_save.clicked.connect(self.save_vm)
        right_layout.addWidget(btn_save)

        main_layout.addLayout(right_layout, 3)

        self.setup_connections()
        self.update_qemu_path_auto()
        self.refresh_list()

    def setup_connections(self):
        widgets = [
            self.f_arch, self.f_machine, self.f_cpu,
            self.f_ram, self.f_smp, self.f_boot,
            self.f_disk, self.f_extra, self.f_qemu_path
        ]
        for w in widgets:
            if isinstance(w, QComboBox):
                w.currentIndexChanged.connect(lambda _=None: self.update_preview())
            elif isinstance(w, QSpinBox):
                w.valueChanged.connect(lambda _=None: self.update_preview())
            elif isinstance(w, QLineEdit):
                w.textChanged.connect(lambda _: self.update_preview())
            elif isinstance(w, QPlainTextEdit):
                w.textChanged.connect(lambda: self.update_preview())

        self.f_arch.currentIndexChanged.connect(
            lambda _=None: (self.update_qemu_path_auto(), self.update_preview())
        )

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
        if file_path:
            self.f_qemu_path.setText(file_path)

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
        if extra:
            cmd.extend(shlex.split(extra))

        return cmd

    # Виправлені методи на рівні класу
    def update_preview(self):
        try:
            self.cmd_preview.setPlainText(" ".join(self.generate_command_list()))
        except (OSError, FileNotFoundError) as exc:
            self.cmd_preview.setPlainText(f"Помилка: {exc}")

    def run_vm(self):
        if self.process.state() == QProcess.ProcessState.Running:
            self.process.terminate()
            return

        self.qmp_port = self.find_free_port()
        args = self.generate_command_list()
        if not args:
            QMessageBox.critical(self, "Помилка", "Неможливо сформувати команду для запуску QEMU")
            return

        executable_path = shutil.which(str(args[0]))
        if not executable_path:
            QMessageBox.critical(
                self, "Помилка",
                f"QEMU не знайдено: {args[0]}\nПеревірте шлях у вкладці 'Експерт'."
            )
            return

        self.process.setProgram(executable_path)
        self.process.setArguments([str(arg) for arg in args[1:]])
        self.process.start()

    def on_process_finished(self):
        self.update_status_ui()
        print("QEMU завершив роботу.")

    def update_status_ui(self):
        is_run = self.process.state() == QProcess.ProcessState.Running
        self.btn_run.setText("🛑 ЗУПИНИТИ" if is_run else "🚀 ЗАПУСТИТИ")
        self.btn_run.setStyleSheet(
            f"background: {'#9e1a1a' if is_run else '#1a4a7a'}; color: white; font-weight: bold;"
        )
        self.status_label.setText(f"● Стан: {'ПРАЦЮЄ' if is_run else 'Зупинено'}")
        self.status_label.setStyleSheet(
            f"color: {'#00ff00' if is_run else 'gray'}; font-weight: bold;"
        )

    def read_stderr(self):
        err = self.process.readAllStandardError().data().decode(errors='replace')
        print(f"QEMU LOG: {err}")

    def update_stats(self):
        if psutil:
            self.cpu_bar.setValue(int(psutil.cpu_percent()))
            self.ram_bar.setValue(int(psutil.virtual_memory().percent))

    def send_qmp_command(self, command):
        port = self.qmp_port

        def _send():
            for i in range(5):
                try:
                    time.sleep(0.5)
                    with socket.create_connection(("127.0.0.1", port), timeout=1) as s:
                        data = s.recv(1024)
                        if b"QMP" not in data:
                            continue
                        s.sendall(json.dumps({"execute": "qmp_capabilities"}).encode())
                        s.recv(1024)
                        s.sendall(json.dumps(command).encode())
                        print(f"QMP: {command['execute']} надіслана успішно.")
                        return
                except OSError as exc:
                    print(f"QMP Retry {i + 1}: {exc}")

        if self.process.state() == QProcess.ProcessState.Running:
            threading.Thread(target=_send, daemon=True).start()

    def save_vm(self):
        name = self.f_name.text().strip() or "unnamed_vm"
        p = self.base_path / name
        try:
            p.mkdir(exist_ok=True)
            data = {
                "name": name,
                "arch": self.f_arch.currentText(),
                "ram": self.f_ram.value(),
                "smp": self.f_smp.value(),
                "boot": self.f_boot.currentText(),
                "disk": self.f_disk.text(),
                "cpu": self.f_cpu.currentText(),
                "machine": self.f_machine.currentText(),
                "qemu_path": self.f_qemu_path.text(),
                "extra": self.f_extra.toPlainText()
            }
            with open(p / "config.json", "w", encoding='utf-8') as f:
                json.dump(data, f, indent=4)
            self.refresh_list()
            QMessageBox.information(self, "Успіх", "Конфігурацію збережено!")
        except (OSError, FileNotFoundError) as exc:
            QMessageBox.critical(self, "Помилка", f"Не вдалося зберегти: {exc}")

    def load_vm(self, name):
        p = self.base_path / name / "config.json"
        if not p.exists():
            return
        try:
            with open(p, "r", encoding='utf-8') as f:
                d = json.load(f)
                self.f_name.setText(d.get("name", name))
                self.f_arch.setCurrentText(d.get("arch", "x86_64"))
                self.f_ram.setValue(d.get("ram", 2048))
                self.f_smp.setValue(d.get("smp", 2))
                self.f_boot.setCurrentText(d.get("boot", "Disk (c)"))
                self.f_disk.setText(d.get("disk", ""))
                self.f_cpu.setCurrentText(d.get("cpu", "host"))
                self.f_machine.setCurrentText(d.get("machine", "q35"))
                self.f_qemu_path.setText(d.get("qemu_path", ""))
                self.f_extra.setPlainText(d.get("extra", ""))
        except (OSError, JSONDecodeError) as exc:
            print(f"Помилка завантаження: {exc}")
        self.update_preview()

    def refresh_list(self):
        self.vm_list.clear()
        if self.base_path.exists():
            for d in self.base_path.iterdir():
                if d.is_dir() and (d / "config.json").exists():
                    self.vm_list.addItem(d.name)

    def select_file(self, line_edit):
        file_path, _ = QFileDialog.getOpenFileName(self, "Виберіть файл")
        if file_path:
            line_edit.setText(file_path)

    @staticmethod
    def find_free_port():
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('127.0.0.1', 0))
                return s.getsockname()[1]
        except OSError:
            return 4444


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MguiQemu()
    window.show()
    sys.exit(app.exec())
