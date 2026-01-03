# cspell:ignore aarch loongarch hppa Xtensa xtensa qapp powerdown virt QCOW qcow virtio
import sys
import json
import shlex
import socket
import threading
from pathlib import Path
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QLineEdit, QPushButton, QLabel,
                               QFileDialog, QSpinBox, QListWidget, QMessageBox,
                               QPlainTextEdit, QTabWidget, QComboBox,
                               QProgressBar, QFormLayout)
from PySide6.QtCore import QProcess, QTimer
from PySide6.QtGui import QPalette

try:
    import psutil
except ImportError:
    psutil = None


class MguiQemu(QMainWindow):
    # explicit attribute annotations help static checkers resolve Signals and widget methods
    vm_list: QListWidget
    status_label: QLabel
    cpu_bar: QProgressBar
    ram_bar: QProgressBar
    btn_run: QPushButton
    tabs: QTabWidget
    cmd_preview: QPlainTextEdit
    f_name: QLineEdit
    f_arch: QComboBox
    f_machine: QComboBox
    f_cpu: QComboBox
    f_ram: QSpinBox
    f_smp: QSpinBox
    f_disk: QLineEdit
    f_boot: QComboBox
    conv_src: QLineEdit
    conv_fmt: QComboBox
    f_extra: QPlainTextEdit
    is_dark: bool
    qmp_port: int
    process: QProcess

    def __init__(self):
        super().__init__()

        # Initialize all UI attributes with correct widget types
        self.is_dark = False
        self.vm_list = QListWidget()
        self.status_label = QLabel()
        self.cpu_bar = QProgressBar()
        self.ram_bar = QProgressBar()
        self.btn_run = QPushButton()
        self.tabs = QTabWidget()
        self.cmd_preview = QPlainTextEdit()
        self.f_name = QLineEdit()
        self.f_arch = QComboBox()
        self.f_machine = QComboBox()
        self.f_cpu = QComboBox()
        self.f_ram = QSpinBox()
        self.f_smp = QSpinBox()
        self.f_disk = QLineEdit()
        self.f_boot = QComboBox()
        self.conv_src = QLineEdit()
        self.conv_fmt = QComboBox()
        self.f_extra = QPlainTextEdit()

        self.setWindowTitle("MGUI_QEMU - Professional Virtualization Control")
        self.setMinimumSize(1200, 900)

        # get palette safely and avoid shadowing the module-level 'app' name
        self.apply_system_theme()

        self.arch_map = {
            "x86_64": "x86_64", "i386": "i386", "Arm (64-bit)": "aarch64",
            "Arm (32-bit)": "arm", "RISC-V (64-bit)": "riscv64", "RISC-V (32-bit)": "riscv32",
            "PowerPC": "ppc", "PowerPC 64": "ppc64", "MIPS": "mips", "MIPS 64": "mips64",
            "LoongArch": "loongarch64", "SPARC": "sparc", "SPARC 64": "sparc64",
            "Alpha": "alpha", "AVR": "avr", "m68k": "m68k", "PA-RISC": "hppa",
            "s390x": "s390x", "SH4": "sh4", "OpenRISC": "or1k", "Xtensa": "xtensa"
        }

        self.qmp_port = 4444
        self.base_path = Path.home() / "MGUI_QEMU_VMs"
        self.base_path.mkdir(exist_ok=True)

        self.process = QProcess()
        self.process.started.connect(self.update_status_ui)  # type: ignore
        self.process.finished.connect(self.update_status_ui)  # type: ignore
        self.process.readyReadStandardError.connect(self.read_stderr)  # type: ignore

        self.init_ui()

        self.stats_timer = QTimer()
        self.stats_timer.timeout.connect(self.update_stats)  # type: ignore
        self.stats_timer.start(2000)

    def apply_system_theme(self):
        # be explicit about the application type so type checkers know palette() is available
        qapp = QApplication.instance()
        if not isinstance(qapp, QApplication):
            self.is_dark = False
            return
        palette = qapp.palette()
        # use ColorRole enum variant to avoid unresolved attribute complaints
        bg_color = palette.color(QPalette.ColorRole.Window).lightness()
        self.is_dark = bg_color < 128

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)

        sidebar = QVBoxLayout()
        self.vm_list = QListWidget()
        self.vm_list.currentTextChanged.connect(self.load_vm)  # type: ignore

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
            btn.clicked.connect(lambda chk=False, c=cmd: self.send_qmp_command({"execute": c}))  # type: ignore
            qmp_group.addWidget(btn)
        sidebar.addLayout(qmp_group)

        self.btn_run = QPushButton("🚀 ЗАПУСТИТИ")
        self.btn_run.setFixedHeight(50)
        self.btn_run.setStyleSheet("background: #1a4a7a; color: white; font-weight: bold;")
        self.btn_run.clicked.connect(self.run_vm)  # type: ignore
        sidebar.addWidget(self.btn_run)

        main_layout.addLayout(sidebar, 1)

        right_layout = QVBoxLayout()
        self.tabs = QTabWidget()

        self.init_basic_tab()
        self.init_storage_tab()
        self.init_tools_tab()
        self.init_expert_tab()

        right_layout.addWidget(self.tabs)

        self.cmd_preview = QPlainTextEdit()
        self.cmd_preview.setReadOnly(True)
        self.cmd_preview.setFixedHeight(60)
        self.cmd_preview.setStyleSheet("background: black; color: #0f0; font-family: monospace;")

        right_layout.addWidget(QLabel("🛠 Команда:"))
        right_layout.addWidget(self.cmd_preview)

        btn_save = QPushButton("💾 Зберегти конфігурацію")
        btn_save.clicked.connect(self.save_vm)  # type: ignore
        right_layout.addWidget(btn_save)

        main_layout.addLayout(right_layout, 3)
        self.refresh_list()

    def init_basic_tab(self):
        tab = QWidget()
        l = QFormLayout(tab)
        self.f_name = QLineEdit()
        self.f_arch = QComboBox()
        self.f_arch.addItems(list(self.arch_map.keys()))
        self.f_machine = QComboBox()
        self.f_machine.addItems(["q35", "pc", "virt", "mac99"])
        self.f_cpu = QComboBox()
        self.f_cpu.addItems(["host", "max", "qemu64", "cortex-a57"])
        self.f_ram = QSpinBox()
        self.f_ram.setRange(128, 256000)
        self.f_ram.setValue(2048)
        self.f_smp = QSpinBox()
        self.f_smp.setRange(1, 64)
        self.f_smp.setValue(2)

        l.addRow("Назва:", self.f_name)
        l.addRow("Архітектура:", self.f_arch)
        l.addRow("Машина:", self.f_machine)
        l.addRow("Процесор:", self.f_cpu)
        l.addRow("RAM (MB):", self.f_ram)
        l.addRow("Ядра:", self.f_smp)

        self.tabs.addTab(tab, "Залізо")
        for w in [self.f_name, self.f_arch, self.f_ram, self.f_smp]:
            if hasattr(w, "textChanged"):
                w.textChanged.connect(self.update_preview)  # type: ignore
            if hasattr(w, "currentIndexChanged"):
                w.currentIndexChanged.connect(self.update_preview)  # type: ignore
            if hasattr(w, "valueChanged"):
                w.valueChanged.connect(self.update_preview)  # type: ignore

    def init_storage_tab(self):
        tab = QWidget()
        l = QVBoxLayout(tab)

        h = QHBoxLayout()
        self.f_disk = QLineEdit()
        btn_browse = QPushButton("📁")
        btn_browse.clicked.connect(lambda: self.select_file(self.f_disk))  # type: ignore
        h.addWidget(self.f_disk)
        h.addWidget(btn_browse)

        l.addWidget(QLabel("Образ Диска / ISO:"))
        l.addLayout(h)

        self.f_boot = QComboBox()
        self.f_boot.addItems(["Disk (c)", "CD-ROM (d)"])
        l.addWidget(QLabel("Пріоритет завантаження:"))
        l.addWidget(self.f_boot)

        btn_create = QPushButton("💎 Створити новий порожній диск (QCOW2)")
        btn_create.clicked.connect(self.tool_create_disk)  # type: ignore
        l.addWidget(btn_create)

        l.addStretch()
        self.tabs.addTab(tab, "Диски")

    def init_tools_tab(self):
        tab = QWidget()
        l = QVBoxLayout(tab)

        l.addWidget(QLabel("⚡ Конвертація образів (qemu-img):"))

        self.conv_src = QLineEdit()
        btn_src = QPushButton("Вибрати джерело")
        btn_src.clicked.connect(lambda: self.select_file(self.conv_src))  # type: ignore

        self.conv_fmt = QComboBox()
        self.conv_fmt.addItems(["qcow2", "raw", "vmdk", "vdi", "iso"])

        btn_do_conv = QPushButton("🔄 Почати конвертацію")
        btn_do_conv.clicked.connect(self.tool_convert_disk)  # type: ignore

        l.addWidget(self.conv_src)
        l.addWidget(btn_src)
        l.addWidget(QLabel("Цільовий формат:"))
        l.addWidget(self.conv_fmt)
        l.addWidget(btn_do_conv)
        l.addStretch()
        self.tabs.addTab(tab, "Інструменти")

    def init_expert_tab(self):
        tab = QWidget()
        l = QVBoxLayout(tab)
        self.f_extra = QPlainTextEdit()
        l.addWidget(QLabel("Додаткові прапорці:"))
        l.addWidget(self.f_extra)
        self.tabs.addTab(tab, "Експерт")

    @staticmethod
    def find_free_port():
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.bind(('127.0.0.1', 0))
            port = s.getsockname()[1]
        finally:
            s.close()
        return port

    def generate_command_list(self):
        arch = self.arch_map.get(self.f_arch.currentText(), "x86_64")
        cmd = [f"qemu-system-{arch}"]

        self.qmp_port = self.find_free_port()
        cmd.extend(["-qmp", f"tcp:localhost:{self.qmp_port},server,nowait"])

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

        cmd.extend(["-boot", "c" if "Disk" in self.f_boot.currentText() else "d"])

        extra = self.f_extra.toPlainText().strip()
        if extra:
            cmd.extend(shlex.split(extra))

        return cmd

    def run_vm(self):
        if self.process.state() == QProcess.ProcessState.Running:
            return

        args = self.generate_command_list()
        self.process.setProgram(args[0])
        self.process.setArguments(args[1:])
        self.process.start()

    def send_qmp_command(self, command):
        def _send():
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(1.0)
                s.connect(("127.0.0.1", self.qmp_port))
                # initial greeting
                try:
                    s.recv(1024)
                except socket.timeout:
                    pass
                s.sendall(json.dumps({"execute": "qmp_capabilities"}).encode())
                try:
                    s.recv(1024)
                except socket.timeout:
                    pass
                s.sendall(json.dumps(command).encode())
                s.close()
            except (socket.timeout, ConnectionRefusedError, OSError) as e:
                # log/debug only; avoid silencing all exceptions
                print("QMP send failed:", e)

        threading.Thread(target=_send, daemon=True).start()

    def update_stats(self):
        # avoid calling psutil when it's not available and narrow caught exceptions
        if psutil and hasattr(psutil, "virtual_memory"):
            try:
                self.cpu_bar.setValue(int(psutil.cpu_percent()))
                self.ram_bar.setValue(int(psutil.virtual_memory().percent))
            except (AttributeError, OSError) as e:
                # log minimal info for debugging
                print("psutil stats failed:", e)

    def tool_create_disk(self):
        path, _ = QFileDialog.getSaveFileName(self, "Зберегти диск", "", "QEMU Image (*.qcow2)")
        if path:
            reply = QMessageBox.question(
                self,
                "Розмір",
                "Створити диск на 20ГБ?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            s_val = "20G" if reply == QMessageBox.StandardButton.Yes else "40G"
            QProcess.execute("qemu-img", ["create", "-f", "qcow2", path, s_val])
            self.f_disk.setText(path)

    def tool_convert_disk(self):
        src = self.conv_src.text()
        if not src: return
        fmt = self.conv_fmt.currentText()
        dst = src.rsplit('.', 1)[0] + f".{fmt}"
        QProcess.startDetached("qemu-img", ["convert", "-f", "auto", "-O", fmt, src, dst])
        QMessageBox.information(self, "Готово", f"Конвертацію запущено.\nФайл: {dst}")

    def read_stderr(self):
        err = self.process.readAllStandardError().data().decode()
        print(f"QEMU LOG: {err}")

    def update_status_ui(self):
        running = self.process.state() == QProcess.ProcessState.Running
        self.status_label.setText(f"● Стан: {'ПРАЦЮЄ' if running else 'Зупинено'}")
        self.status_label.setStyleSheet(f"color: {'green' if running else 'gray'}; font-weight: bold;")

    def save_vm(self):
        name = self.f_name.text() or "unnamed"
        p = self.base_path / name
        p.mkdir(exist_ok=True)
        data = {
            "name": name,
            "arch": self.f_arch.currentText(),
            "ram": self.f_ram.value(),
            "disk": self.f_disk.text()
        }
        with open(p / "config.json", "w") as f:
            json.dump(data, f)
        self.refresh_list()

    def load_vm(self, name):
        p = self.base_path / name / "config.json"
        if p.exists():
            with open(p, "r") as f:
                d = json.load(f)
                self.f_name.setText(d.get("name", ""))
                self.f_disk.setText(d.get("disk", ""))
        self.update_preview()

    def refresh_list(self):
        self.vm_list.clear()
        if self.base_path.exists():
            for d in self.base_path.iterdir():
                if d.is_dir(): self.vm_list.addItem(d.name)

    def select_file(self, line):
        f, _ = QFileDialog.getOpenFileName(self, "Виберіть файл")
        if f:
            line.setText(f)
            self.update_preview()

    def update_preview(self):
        # narrow exception types; preview generation rarely fails with ValueError/OSError
        try:
            self.cmd_preview.setPlainText(" ".join(self.generate_command_list()))
        except (ValueError, OSError) as e:
            print("Preview update failed:", e)

    def clear_fields(self):
        self.f_name.clear()
        self.f_disk.clear()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MguiQemu()
    window.show()
    sys.exit(app.exec())