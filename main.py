import json
import platform
import shlex
import shutil
import sys
from json import JSONDecodeError
from pathlib import Path

from PySide6.QtCore import QProcess
from PySide6.QtGui import QPalette
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QLabel, QFileDialog, QSpinBox, QListWidget,
    QMessageBox, QPlainTextEdit, QTabWidget, QComboBox, QFormLayout,
    QScrollArea, QCheckBox
)


class MguiQemu(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MGUI_QEMU - Launch Configuration")
        self.setMinimumSize(1000, 800)

        # UI attributes
        self.is_dark = False
        self.vm_list = None
        self.status_label = None
        self.btn_run = None
        self.tabs = None
        self.f_mode = None
        
        self.hw_layout = None
        self.storage_layout = None
        self.net_layout = None
        self.gfx_layout = None
        self.input_layout = None
        self.boot_layout = None
        self.audio_layout = None
        self.debug_layout = None
        self.expert_layout = None

        # Hardware
        self.f_name = None
        self.f_arch = None
        self.f_machine = None
        self.f_cpu = None
        self.f_accel = None
        self.f_ram = None
        self.f_smp = None
        self.f_uuid = None
        self.f_nodefaults = None
        self.f_no_user_config = None
        self.f_S = None
        self.f_no_acpi = None
        self.f_no_hpet = None
        self.f_no_shutdown = None
        self.f_no_reboot = None
        self.f_daemonize = None
        self.f_pidfile = None
        self.f_mem_path = None
        self.f_mem_prealloc = None
        self.f_numa = None

        # Storage
        self.f_hda = None
        self.f_hdb = None
        self.f_hdc = None
        self.f_hdd = None
        self.f_cdrom = None
        self.f_fda = None
        self.f_fdb = None
        self.f_mtdblock = None
        self.f_pflash = None
        self.f_sd = None
        self.f_snapshot = None
        self.f_boot = None

        # Network
        self.f_net_type = None
        self.f_net_device = None
        self.f_hostfwd = None
        self.f_hostname = None
        self.f_redir = None
        self.f_nic = None

        # Graphics
        self.f_display = None
        self.f_vga = None
        self.f_vnc = None
        self.f_fullscreen = None

        # Input / USB
        self.f_usb = None
        self.f_usb_device = None
        self.f_kbd_layout = None
        self.f_usbdevice = None

        # Kernel / Boot
        self.f_kernel = None
        self.f_initrd = None
        self.f_append = None
        self.f_dtb = None
        self.f_bios = None
        self.f_L = None

        # Debug
        self.f_debug_item = None
        self.f_debug_log = None
        self.f_gdb = None
        self.f_trace = None
        self.f_trace_file = None

        # Audio
        self.f_audio_drv = None
        self.f_soundhw = None

        # Expert
        self.f_qemu_path = None
        self.f_extra = None
        self.f_object = None
        self.f_global = None
        self.f_add_fd = None
        self.f_audiodev = None
        self.f_device_extra = None
        self.cmd_preview = None
        self.log_output = None

        # Language and Mode
        self.f_lang = None
        self.f_intuitive = None
        
        self.label_saved_vms = None
        self.label_cmd_preview = None
        self.label_qemu_logs = None
        self.label_qemu_bin = None
        self.label_extra_args = None
        
        self.lang_data = {
            "en": {
                "window_title": "MGUI_QEMU - Launch Configuration",
                "saved_vms": "📂 Saved VMs:",
                "delete_vm": "🗑 Delete VM",
                "launch": "🚀 LAUNCH",
                "stop": "🛑 STOP VM",
                "status_idle": "● Status: Idle",
                "status_running": "● Status: RUNNING",
                "work_mode": "⚙️ Operation Mode:",
                "mode_emu": "Emulation (TCG)",
                "mode_virt": "Virtualization (KVM/WHPX/HVF)",
                "tab_hw": "Hardware",
                "tab_storage": "Storage",
                "tab_net": "Network",
                "tab_gfx": "Graphics",
                "tab_input": "Input/USB",
                "tab_boot": "Boot/Kernel",
                "tab_audio": "Audio",
                "tab_debug": "Debug",
                "tab_expert": "Expert",
                "cmd_preview": "🛠 Command Preview:",
                "logs": "📜 QEMU Logs:",
                "save_config": "💾 Save Configuration",
                "intuitive_mode": "✨ Intuitive Mode",
                "vm_name": "VM Name:",
                "arch": "Architecture:",
                "machine": "Machine Type:",
                "cpu": "CPU Model:",
                "accel": "Accelerator:",
                "ram": "RAM Size:",
                "cores": "Cores:",
                "uuid": "UUID:",
                "pid_file": "PID File:",
                "mem_path": "Mem Path:",
                "numa": "NUMA:",
                "no_defaults": "No Defaults",
                "no_user_config": "No User Config",
                "freeze_cpu": "Freeze CPU on start",
                "disable_acpi": "Disable ACPI",
                "disable_hpet": "Disable HPET",
                "no_shutdown": "No Shutdown",
                "no_reboot": "No Reboot",
                "daemonize": "Daemonize",
                "prealloc_ram": "Prealloc RAM",
                "hda": "Hard Disk A:",
                "hdb": "Hard Disk B:",
                "hdc": "Hard Disk C:",
                "hdd": "Hard Disk D:",
                "cdrom": "CD-ROM ISO:",
                "fda": "Floppy A:",
                "fdb": "Floppy B:",
                "mtd": "MTD Block:",
                "pflash": "Parallel Flash:",
                "sd": "SD Card:",
                "snapshot": "Snapshot Mode",
                "boot_order": "Boot Order:",
                "net_backend": "Network Backend:",
                "net_device": "Network Device:",
                "nic_combined": "Combined NIC:",
                "host_fwd": "Host Forward:",
                "port_redir": "Port Redir:",
                "dhcp_hostname": "DHCP Hostname:",
                "display_type": "Display Type:",
                "vga_card": "VGA Card:",
                "vnc_display": "VNC Display:",
                "fullscreen": "Full Screen",
                "enable_usb": "Enable USB",
                "usb_device": "USB Device:",
                "old_usb": "Old USB Dev:",
                "kbd_layout": "Keyboard Layout:",
                "kernel": "Linux Kernel:",
                "initrd": "Initrd:",
                "kernel_cmdline": "Kernel Cmdline:",
                "dtb": "Device Tree:",
                "bios": "BIOS/Firmware:",
                "rom_path": "BIOS/ROM Path:",
                "audio_drv": "Audio Driver:",
                "audio_dev": "Audio Dev:",
                "sound_hw": "Sound Hardware:",
                "debug_items": "Log Items:",
                "debug_log": "Debug Log File:",
                "gdb_dev": "GDB Dev:",
                "trace": "Trace:",
                "trace_file": "Trace File:",
                "qemu_bin": "QEMU Binary Path:",
                "object": "Object:",
                "global_props": "Global:",
                "add_fd": "Add FD:",
                "add_device": "Add Device:",
                "extra_args": "Additional Arguments:",
                "browse": "Browse...",
                # Intuitive overrides
                "intuitive_ram": "Memory (RAM):",
                "intuitive_cores": "Processor Power:",
                "intuitive_hda": "Main System Disk:",
                "intuitive_cdrom": "Installation Disk (ISO):",
                "intuitive_display": "Video Window:",
                "intuitive_sound": "Enable Sound:",
                "success": "Success",
                "saved_ok": "Configuration saved successfully!",
                "confirm_del": "Confirm Delete",
                "delete_ask": "Are you sure you want to delete '{}'?",
                "err": "Error",
                "tab_templates": "Templates",
                "apply_template": "Apply Template",
                "select_template": "Select a Template to apply:",
                "clear": "Clear All Fields"
            },
            "ua": {
                "window_title": "MGUI_QEMU - Налаштування запуску",
                "saved_vms": "📂 Збережені VM:",
                "delete_vm": "🗑 Видалити VM",
                "launch": "🚀 ЗАПУСК",
                "stop": "🛑 ЗУПИНИТИ VM",
                "status_idle": "● Статус: Очікування",
                "status_running": "● Статус: ЗАПУЩЕНО",
                "work_mode": "⚙️ Режим роботи:",
                "mode_emu": "Емуляція (TCG)",
                "mode_virt": "Віртуалізація (KVM/WHPX/HVF)",
                "tab_hw": "Залізо",
                "tab_storage": "Диски",
                "tab_net": "Мережа",
                "tab_gfx": "Графіка",
                "tab_input": "Ввід/USB",
                "tab_boot": "Завантаження",
                "tab_audio": "Звук",
                "tab_debug": "Відладка",
                "tab_expert": "Експерт",
                "tab_templates": "Шаблони",
                "cmd_preview": "🛠 Попередній перегляд команди:",
                "logs": "📜 Логи QEMU:",
                "save_config": "💾 Зберегти конфігурацію",
                "intuitive_mode": "✨ Інтуїтивний режим",
                "vm_name": "Назва VM:",
                "arch": "Архітектура:",
                "machine": "Тип машини:",
                "cpu": "Модель CPU:",
                "accel": "Прискорювач:",
                "ram": "Об'єм ОЗП:",
                "cores": "Ядра:",
                "uuid": "UUID:",
                "pid_file": "PID файл:",
                "mem_path": "Шлях пам'яті:",
                "numa": "NUMA:",
                "no_defaults": "Без стандартних пристроїв",
                "no_user_config": "Без конфігу користувача",
                "freeze_cpu": "Заморозити CPU при старті",
                "disable_acpi": "Вимкнути ACPI",
                "disable_hpet": "Вимкнути HPET",
                "no_shutdown": "Не вимикати автоматично",
                "no_reboot": "Без перезавантаження",
                "daemonize": "У фоновому режимі",
                "prealloc_ram": "Попередньо виділити ОЗП",
                "hda": "Жорсткий диск A:",
                "hdb": "Жорсткий диск B:",
                "hdc": "Жорсткий диск C:",
                "hdd": "Жорсткий диск D:",
                "cdrom": "ISO образ CD-ROM:",
                "fda": "Дискета A:",
                "fdb": "Дискета B:",
                "mtd": "MTD блок:",
                "pflash": "Паралельний Flash:",
                "sd": "SD карта:",
                "snapshot": "Режим знімка",
                "boot_order": "Порядок завантаження:",
                "net_backend": "Мережевий бекенд:",
                "net_device": "Мережевий пристрій:",
                "nic_combined": "Комбінований NIC:",
                "host_fwd": "Прокидання портів:",
                "port_redir": "Перенаправлення портів:",
                "dhcp_hostname": "Ім'я хоста DHCP:",
                "display_type": "Тип дисплея:",
                "vga_card": "Відеокарта:",
                "vnc_display": "VNC дисплей:",
                "fullscreen": "Повний екран",
                "enable_usb": "Увімкнути USB",
                "usb_device": "USB пристрій:",
                "old_usb": "Старий USB пристрій:",
                "kbd_layout": "Розкладка клавіатури:",
                "kernel": "Ядро Linux:",
                "initrd": "Initrd:",
                "kernel_cmdline": "Параметри ядра:",
                "dtb": "Дерево пристроїв (DTB):",
                "bios": "BIOS/Firmware:",
                "rom_path": "Шлях BIOS/ROM:",
                "audio_drv": "Аудіо драйвер:",
                "audio_dev": "Аудіо пристрій:",
                "sound_hw": "Звукова плата:",
                "debug_items": "Елементи логування:",
                "debug_log": "Файл логів відладки:",
                "gdb_dev": "GDB пристрій:",
                "trace": "Трасування:",
                "trace_file": "Файл трасування:",
                "qemu_bin": "Шлях до QEMU:",
                "object": "Об'єкт:",
                "global_props": "Глобальні:",
                "add_fd": "Додати FD:",
                "add_device": "Додати пристрій:",
                "extra_args": "Додаткові аргументи:",
                "browse": "Огляд...",
                "intuitive_ram": "Оперативна пам'ять:",
                "intuitive_cores": "Потужність процесора:",
                "intuitive_hda": "Головний диск системи:",
                "intuitive_cdrom": "Диск встановлення (ISO):",
                "intuitive_display": "Вікно відео:",
                "intuitive_sound": "Увімкнути звук:",
                "success": "Успіх",
                "saved_ok": "Конфігурацію успішно збережено!",
                "confirm_del": "Підтвердження видалення",
                "delete_ask": "Ви впевнені, що хочете видалити '{}'?",
                "err": "Помилка",
                "apply_template": "Застосувати шаблон",
                "select_template": "Виберіть шаблон для застосування:",
                "clear": "Очистити поля"
            },
            "de": {
                "window_title": "MGUI_QEMU - Startkonfiguration",
                "saved_vms": "📂 Gespeicherte VMs:",
                "delete_vm": "🗑 VM löschen",
                "launch": "🚀 STARTEN",
                "stop": "🛑 VM STOPPEN",
                "status_idle": "● Status: Leerlauf",
                "status_running": "● Status: LÄUFT",
                "work_mode": "⚙️ Betriebsmodus:",
                "mode_emu": "Emulation (TCG)",
                "mode_virt": "Virtualisierung (KVM/WHPX/HVF)",
                "tab_hw": "Hardware",
                "tab_storage": "Speicher",
                "tab_net": "Netzwerk",
                "tab_gfx": "Grafik",
                "tab_input": "Eingabe/USB",
                "tab_boot": "Boot/Kernel",
                "tab_audio": "Audio",
                "tab_debug": "Debug",
                "tab_expert": "Experte",
                "tab_templates": "Vorlagen",
                "cmd_preview": "🛠 Befehlsvorschau:",
                "logs": "📜 QEMU-Logs:",
                "save_config": "💾 Konfiguration speichern",
                "intuitive_mode": "✨ Intuitiver Modus",
                "vm_name": "VM-Name:",
                "arch": "Architektur:",
                "machine": "Maschinentyp:",
                "cpu": "CPU-Modell:",
                "accel": "Beschleuniger:",
                "ram": "RAM-Größe:",
                "cores": "Kerne:",
                "uuid": "UUID:",
                "pid_file": "PID-Datei:",
                "mem_path": "Speicherpfad:",
                "numa": "NUMA:",
                "no_defaults": "Keine Standards",
                "no_user_config": "Keine Benutzerkonfig",
                "freeze_cpu": "CPU beim Start einfrieren",
                "disable_acpi": "ACPI deaktivieren",
                "disable_hpet": "HPET deaktivieren",
                "no_shutdown": "Kein Herunterfahren",
                "no_reboot": "Kein Neustart",
                "daemonize": "Daemonisieren",
                "prealloc_ram": "RAM vorab zuweisen",
                "hda": "Festplatte A:",
                "hdb": "Festplatte B:",
                "hdc": "Festplatte C:",
                "hdd": "Festplatte D:",
                "cdrom": "CD-ROM ISO:",
                "fda": "Diskette A:",
                "fdb": "Diskette B:",
                "mtd": "MTD-Block:",
                "pflash": "Paralleler Flash:",
                "sd": "SD-Karte:",
                "snapshot": "Snapshot-Modus",
                "boot_order": "Boot-Reihenfolge:",
                "net_backend": "Netzwerk-Backend:",
                "net_device": "Netzwerkgerät:",
                "nic_combined": "Kombiniertes NIC:",
                "host_fwd": "Port-Weiterleitung:",
                "port_redir": "Port-Redir:",
                "dhcp_hostname": "DHCP-Hostname:",
                "display_type": "Anzeigetyp:",
                "vga_card": "VGA-Karte:",
                "vnc_display": "VNC-Anzeige:",
                "fullscreen": "Vollbild",
                "enable_usb": "USB aktivieren",
                "usb_device": "USB-Gerät:",
                "old_usb": "Altes USB-Gerät:",
                "kbd_layout": "Tastaturlayout:",
                "kernel": "Linux-Kernel:",
                "initrd": "Initrd:",
                "kernel_cmdline": "Kernel-Parameter:",
                "dtb": "Device Tree:",
                "bios": "BIOS/Firmware:",
                "rom_path": "BIOS/ROM Pfad:",
                "audio_drv": "Audiotreiber:",
                "audio_dev": "Audiogerät:",
                "sound_hw": "Soundkarte:",
                "debug_items": "Log-Elemente:",
                "debug_log": "Debug-Logdatei:",
                "gdb_dev": "GDB-Gerät:",
                "trace": "Trace:",
                "trace_file": "Trace-Datei:",
                "qemu_bin": "QEMU-Pfad:",
                "object": "Objekt:",
                "global_props": "Global:",
                "add_fd": "FD hinzufügen:",
                "add_device": "Gerät hinzufügen:",
                "extra_args": "Zusätzliche Argumente:",
                "browse": "Durchsuchen...",
                "intuitive_ram": "Arbeitsspeicher:",
                "intuitive_cores": "Prozessorleistung:",
                "intuitive_hda": "Hauptsystemplatte:",
                "intuitive_cdrom": "Installations-ISO:",
                "intuitive_display": "Videofenster:",
                "intuitive_sound": "Ton aktivieren:",
                "success": "Erfolg",
                "saved_ok": "Konfiguration erfolgreich gespeichert!",
                "confirm_del": "Löschen bestätigen",
                "delete_ask": "Sind Sie sicher, dass Sie '{}' löschen möchten?",
                "err": "Fehler",
                "apply_template": "Vorlage anwenden",
                "select_template": "Wählen Sie eine Vorlage zum Anwenden:",
                "clear": "Felder löschen"
            },
            "zh": {
                "window_title": "MGUI_QEMU - 启动配置",
                "saved_vms": "📂 已保存的虚拟机:",
                "delete_vm": "🗑 删除虚拟机",
                "launch": "🚀 启动",
                "stop": "🛑 停止虚拟机",
                "status_idle": "● 状态: 空闲",
                "status_running": "● 状态: 正在运行",
                "work_mode": "⚙️ 运行模式:",
                "mode_emu": "模拟 (TCG)",
                "mode_virt": "虚拟化 (KVM/WHPX/HVF)",
                "tab_hw": "硬件",
                "tab_storage": "存储",
                "tab_net": "网络",
                "tab_gfx": "图形",
                "tab_input": "输入/USB",
                "tab_boot": "启动/内核",
                "tab_audio": "音频",
                "tab_debug": "调试",
                "tab_expert": "专家",
                "tab_templates": "模板",
                "cmd_preview": "🛠 命令预览:",
                "logs": "📜 QEMU 日志:",
                "save_config": "💾 保存配置",
                "intuitive_mode": "✨ 直观模式",
                "vm_name": "虚拟机名称:",
                "arch": "架构:",
                "machine": "机器类型:",
                "cpu": "CPU 型号:",
                "accel": "加速器:",
                "ram": "内存大小:",
                "cores": "核心数:",
                "uuid": "UUID:",
                "pid_file": "PID 文件:",
                "mem_path": "内存路径:",
                "numa": "NUMA:",
                "no_defaults": "无默认设备",
                "no_user_config": "无用户配置",
                "freeze_cpu": "启动时冻结 CPU",
                "disable_acpi": "禁用 ACPI",
                "disable_hpet": "禁用 HPET",
                "no_shutdown": "不自动关闭",
                "no_reboot": "不重启",
                "daemonize": "后台运行",
                "prealloc_ram": "预分配内存",
                "hda": "硬盘 A:",
                "hdb": "硬盘 B:",
                "hdc": "硬盘 C:",
                "hdd": "硬盘 D:",
                "cdrom": "CD-ROM 镜像:",
                "fda": "软盘 A:",
                "fdb": "软盘 B:",
                "mtd": "MTD 块:",
                "pflash": "并行闪存:",
                "sd": "SD 卡:",
                "snapshot": "快照模式",
                "boot_order": "启动顺序:",
                "net_backend": "网络后端:",
                "net_device": "网络设备:",
                "nic_combined": "组合 NIC:",
                "host_fwd": "端口转发:",
                "port_redir": "端口重定向:",
                "dhcp_hostname": "DHCP 主机名:",
                "display_type": "显示类型:",
                "vga_card": "显卡:",
                "vnc_display": "VNC 显示:",
                "fullscreen": "全屏",
                "enable_usb": "启用 USB",
                "usb_device": "USB 设备:",
                "old_usb": "旧版 USB 设备:",
                "kbd_layout": "键盘布局:",
                "kernel": "Linux 内核:",
                "initrd": "Initrd:",
                "kernel_cmdline": "内核命令行:",
                "dtb": "设备树:",
                "bios": "BIOS/固件:",
                "rom_path": "BIOS/ROM 路径:",
                "audio_drv": "音频驱动:",
                "audio_dev": "音频设备:",
                "sound_hw": "声卡:",
                "debug_items": "日志项:",
                "debug_log": "调试日志文件:",
                "gdb_dev": "GDB 设备:",
                "trace": "追踪:",
                "trace_file": "追踪文件:",
                "qemu_bin": "QEMU 二进制路径:",
                "object": "对象:",
                "global_props": "全局:",
                "add_fd": "添加 FD:",
                "add_device": "添加设备:",
                "extra_args": "附加参数:",
                "browse": "浏览...",
                "intuitive_ram": "内存:",
                "intuitive_cores": "处理器性能:",
                "intuitive_hda": "主系统盘:",
                "intuitive_cdrom": "安装盘 (ISO):",
                "intuitive_display": "视频窗口:",
                "intuitive_sound": "启用声音:",
                "success": "成功",
                "saved_ok": "配置保存成功！",
                "confirm_del": "确认删除",
                "delete_ask": "您确定要删除“{}”吗？",
                "err": "错误",
                "apply_template": "应用模板",
                "select_template": "选择要应用的模板：",
                "clear": "清除所有字段"
            },
            "ru": {
                "window_title": "MGUI_QEMU - Настройка запуска",
                "saved_vms": "📂 Сохраненные VM:",
                "delete_vm": "🗑 Удалить VM",
                "launch": "🚀 ЗАПУСК",
                "stop": "🛑 ОСТАНОВИТЬ VM",
                "status_idle": "● Статус: Ожидание",
                "status_running": "● Статус: ЗАПУЩЕНО",
                "work_mode": "⚙️ Режим работы:",
                "mode_emu": "Эмуляция (TCG)",
                "mode_virt": "Виртуализация (KVM/WHPX/HVF)",
                "tab_hw": "Железо",
                "tab_storage": "Диски",
                "tab_net": "Мережа",
                "tab_gfx": "Графика",
                "tab_input": "Ввод/USB",
                "tab_boot": "Загрузка",
                "tab_audio": "Звук",
                "tab_debug": "Отладка",
                "tab_expert": "Эксперт",
                "tab_templates": "Шаблоны",
                "cmd_preview": "🛠 Предпросмотр команды:",
                "logs": "📜 Логи QEMU:",
                "save_config": "💾 Сохранить конфигурацию",
                "intuitive_mode": "✨ Интуитивный режим",
                "vm_name": "Имя VM:",
                "arch": "Архитектура:",
                "machine": "Тип машины:",
                "cpu": "Модель CPU:",
                "accel": "Ускоритель:",
                "ram": "Объем ОЗУ:",
                "cores": "Ядра:",
                "uuid": "UUID:",
                "pid_file": "PID файл:",
                "mem_path": "Путь памяти:",
                "numa": "NUMA:",
                "no_defaults": "Без станд. устройств",
                "no_user_config": "Без конфига пользователя",
                "freeze_cpu": "Заморозить CPU при старте",
                "disable_acpi": "Выключить ACPI",
                "disable_hpet": "Выключить HPET",
                "no_shutdown": "Не выключать автоматически",
                "no_reboot": "Без перезагрузки",
                "daemonize": "В фоновом режиме",
                "prealloc_ram": "Предварительно выделить ОЗУ",
                "hda": "Жесткий диск A:",
                "hdb": "Жесткий диск B:",
                "hdc": "Жесткий диск C:",
                "hdd": "Жесткий диск D:",
                "cdrom": "ISO образ CD-ROM:",
                "fda": "Дискета A:",
                "fdb": "Дискета B:",
                "mtd": "MTD блок:",
                "pflash": "Параллельный Flash:",
                "sd": "SD карта:",
                "snapshot": "Режим снимка",
                "boot_order": "Порядок загрузки:",
                "net_backend": "Сетевой бекенд:",
                "net_device": "Сетевое устройство:",
                "nic_combined": "Комбинированный NIC:",
                "host_fwd": "Проброс портов:",
                "port_redir": "Перенаправление портов:",
                "dhcp_hostname": "Имя хоста DHCP:",
                "display_type": "Тип дисплея:",
                "vga_card": "Видеокарта:",
                "vnc_display": "VNC дисплей:",
                "fullscreen": "Полный экран",
                "enable_usb": "Включить USB",
                "usb_device": "USB устройство:",
                "old_usb": "Старое USB устройство:",
                "kbd_layout": "Раскладка клавиатуры:",
                "kernel": "Ядро Linux:",
                "initrd": "Initrd:",
                "kernel_cmdline": "Параметры ядра:",
                "dtb": "Дерево устройств (DTB):",
                "bios": "BIOS/Firmware:",
                "rom_path": "Путь BIOS/ROM:",
                "audio_drv": "Аудио драйвер:",
                "audio_dev": "Аудио устройство:",
                "sound_hw": "Звуковая плата:",
                "debug_items": "Элементы логирования:",
                "debug_log": "Файл логов отладки:",
                "gdb_dev": "GDB устройство:",
                "trace": "Трассировка:",
                "trace_file": "Файл трассировки:",
                "qemu_bin": "Путь к QEMU:",
                "object": "Объект:",
                "global_props": "Глобальные:",
                "add_fd": "Добавить FD:",
                "add_device": "Добавить устройство:",
                "extra_args": "Доп. аргументы:",
                "browse": "Обзор...",
                "intuitive_ram": "Оперативная память:",
                "intuitive_cores": "Мощность процессора:",
                "intuitive_hda": "Главный диск системы:",
                "intuitive_cdrom": "Диск установки (ISO):",
                "intuitive_display": "Окно видео:",
                "intuitive_sound": "Включить звук:",
                "success": "Успех",
                "saved_ok": "Конфигурация успешно сохранена!",
                "confirm_del": "Подтверждение удаления",
                "delete_ask": "Вы уверены, что хотите удалить '{}'?",
                "err": "Ошибка",
                "apply_template": "Применить шаблон",
                "select_template": "Выберите шаблон для применения:",
                "clear": "Очистить поля"
            }
        }

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

        # Signals
        self.process.started.connect(self.update_status_ui)
        self.process.finished.connect(lambda: self.on_process_finished())
        self.process.readyReadStandardError.connect(self.read_output)
        self.process.readyReadStandardOutput.connect(self.read_output)

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

        self.status_label = QLabel("● Status: Idle")
        self.status_label.setStyleSheet("font-weight: bold; color: gray;")

        self.label_saved_vms = QLabel("📂 Saved VMs:")
        sidebar.addWidget(self.label_saved_vms)
        sidebar.addWidget(self.vm_list)

        btn_del_vm = QPushButton("🗑 Delete VM")
        btn_del_vm.clicked.connect(self.delete_vm)
        sidebar.addWidget(btn_del_vm)

        sidebar.addStretch()
        sidebar.addWidget(self.status_label)

        self.btn_run = QPushButton("🚀 LAUNCH")
        self.btn_run.setFixedHeight(50)
        self.btn_run.setStyleSheet(
            "background: #1a4a7a; color: white; font-weight: bold; border-radius: 5px;"
        )
        self.btn_run.clicked.connect(self.run_vm)
        sidebar.addWidget(self.btn_run)

        main_layout.addLayout(sidebar, 1)

        # Right side
        right_layout = QVBoxLayout()

        # Top Bar (Language, Mode, Intuitive)
        top_bar = QHBoxLayout()
        
        top_bar.addWidget(QLabel("🌐 Language:"))
        self.f_lang = QComboBox()
        self.f_lang.addItems(["English", "Українська", "Deutsch", "简体中文", "Русский"])
        self.f_lang.currentIndexChanged.connect(self.retranslate_ui)
        top_bar.addWidget(self.f_lang)

        top_bar.addSpacing(20)
        
        top_bar.addWidget(QLabel("⚙️ Mode:"))
        self.f_mode = QComboBox()
        self.f_mode.addItems(["Emulation (TCG)", "Virtualization (KVM/WHPX)"])
        self.f_mode.currentIndexChanged.connect(self.on_mode_changed)
        top_bar.addWidget(self.f_mode)

        top_bar.addSpacing(20)

        self.f_intuitive = QCheckBox("✨ Intuitive Mode")
        self.f_intuitive.stateChanged.connect(self.retranslate_ui)
        top_bar.addWidget(self.f_intuitive)
        
        top_bar.addStretch()
        right_layout.addLayout(top_bar)

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_hw_tab(), "Hardware")
        self.tabs.addTab(self.create_storage_tab(), "Storage")
        self.tabs.addTab(self.create_network_tab(), "Network")
        self.tabs.addTab(self.create_graphics_tab(), "Graphics")
        self.tabs.addTab(self.create_input_tab(), "Input/USB")
        self.tabs.addTab(self.create_boot_tab(), "Boot/Kernel")
        self.tabs.addTab(self.create_audio_tab(), "Audio")
        self.tabs.addTab(self.create_debug_tab(), "Debug")
        self.tabs.addTab(self.create_expert_tab(), "Expert")
        self.tabs.addTab(self.create_templates_tab(), "Templates")
        right_layout.addWidget(self.tabs)

        self.cmd_preview = QPlainTextEdit()
        self.cmd_preview.setReadOnly(True)
        self.cmd_preview.setFixedHeight(60)
        self.cmd_preview.setStyleSheet(
            "background: #000; color: #0f0; font-family: 'Consolas'; font-size: 10px;"
        )
        self.label_cmd_preview = QLabel("🛠 Command Preview:")
        right_layout.addWidget(self.label_cmd_preview)
        right_layout.addWidget(self.cmd_preview)

        self.log_output = QPlainTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setFixedHeight(120)
        self.log_output.setStyleSheet("background: #1e1e1e; color: #d4d4d4; font-family: 'Consolas';")
        self.label_qemu_logs = QLabel("📜 QEMU Logs:")
        right_layout.addWidget(self.label_qemu_logs)
        right_layout.addWidget(self.log_output)

        btn_save = QPushButton("💾 Save Configuration")
        btn_save.clicked.connect(self.save_vm)
        right_layout.addWidget(btn_save)

        main_layout.addLayout(right_layout, 3)

        self.setup_connections()
        self.update_qemu_path_auto()
        self.on_mode_changed()
        self.retranslate_ui()
        self.refresh_list()

    @staticmethod
    def create_scroll_widget(layout):
        container = QWidget()
        container.setLayout(layout)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(container)
        return scroll

    def on_mode_changed(self):
        is_virt = self.f_mode.currentIndex() == 1
        self.f_accel.clear()
        self.f_arch.clear()

        if is_virt:
            self.f_accel.addItems(["kvm", "whpx", "hvf", "hax"])
            native = self.get_native_arch()
            self.f_arch.addItem(native)
            self.f_cpu.setCurrentText("host")
        else:
            self.f_accel.addItem("tcg")
            self.f_arch.addItems(list(self.arch_map.keys()))
            if self.f_cpu.findText("qemu64") >= 0:
                self.f_cpu.setCurrentText("qemu64")

    @staticmethod
    def get_native_arch():
        m = platform.machine().lower()
        if m in ["x86_64", "amd64"]:
            return "x86_64"
        if m in ["i386", "i686"]:
            return "i386"
        if m in ["aarch64", "arm64"]:
            return "Arm (64-bit)"
        return "x86_64"

    def create_hw_tab(self):
        self.hw_layout = QFormLayout()
        layout = self.hw_layout
        self.f_name = QLineEdit()
        self.f_arch = QComboBox()
        # Початкове заповнення буде в on_mode_changed

        self.f_machine = QComboBox()
        self.f_machine.addItems(["q35", "pc", "virt", "microvm"])
        self.f_cpu = QComboBox()
        self.f_cpu.setEditable(True)
        self.f_cpu.addItems(["host", "max", "qemu64", "qemu32", "pentium3"])

        self.f_accel = QComboBox()
        self.f_ram = QSpinBox()
        self.f_ram.setRange(128, 1024 * 128)
        self.f_ram.setValue(2048)
        self.f_ram.setSuffix(" MB")
        self.f_smp = QSpinBox()
        self.f_smp.setRange(1, 256)
        self.f_smp.setValue(2)
        self.f_uuid = QLineEdit()

        self.f_nodefaults = QCheckBox("No Defaults (-nodefaults)")
        self.f_no_user_config = QCheckBox("No User Config (-no-user-config)")
        self.f_S = QCheckBox("Freeze CPU on start (-S)")
        self.f_no_acpi = QCheckBox("Disable ACPI (-no-acpi)")
        self.f_no_hpet = QCheckBox("Disable HPET (-no-hpet)")
        self.f_no_shutdown = QCheckBox("No Shutdown (-no-shutdown)")
        self.f_no_reboot = QCheckBox("No Reboot (-no-reboot)")
        self.f_daemonize = QCheckBox("Daemonize (-daemonize)")
        self.f_mem_prealloc = QCheckBox("Prealloc RAM (-mem-prealloc)")

        self.f_pidfile = QLineEdit()
        self.f_mem_path = QLineEdit()
        self.f_numa = QLineEdit()
        self.f_numa.setPlaceholderText("node,nodeid=0,cpus=0-1,mem=1G")

        layout.addRow("VM Name:", self.f_name)
        layout.addRow("Architecture:", self.f_arch)
        layout.addRow("Machine Type (-machine):", self.f_machine)
        layout.addRow("CPU Model (-cpu):", self.f_cpu)
        layout.addRow("Accelerator (-accel):", self.f_accel)
        layout.addRow("RAM Size (-m):", self.f_ram)
        layout.addRow("Cores (-smp):", self.f_smp)
        layout.addRow("UUID (-uuid):", self.f_uuid)
        layout.addRow("PID File (-pidfile):", self.add_browse(self.f_pidfile))
        layout.addRow("Mem Path (-mem-path):", self.f_mem_path)
        layout.addRow("NUMA (-numa):", self.f_numa)

        layout.addRow(self.f_nodefaults)
        layout.addRow(self.f_no_user_config)
        layout.addRow(self.f_S)
        layout.addRow(self.f_no_acpi)
        layout.addRow(self.f_no_hpet)
        layout.addRow(self.f_no_shutdown)
        layout.addRow(self.f_no_reboot)
        layout.addRow(self.f_daemonize)
        layout.addRow(self.f_mem_prealloc)

        return self.create_scroll_widget(layout)

    def create_storage_tab(self):
        self.storage_layout = QFormLayout()
        layout = self.storage_layout
        self.f_hda = QLineEdit()
        layout.addRow("Hard Disk A (-hda):", self.add_browse(self.f_hda))
        self.f_hdb = QLineEdit()
        layout.addRow("Hard Disk B (-hdb):", self.add_browse(self.f_hdb))
        self.f_hdc = QLineEdit()
        layout.addRow("Hard Disk C (-hdc):", self.add_browse(self.f_hdc))
        self.f_hdd = QLineEdit()
        layout.addRow("Hard Disk D (-hdd):", self.add_browse(self.f_hdd))
        self.f_cdrom = QLineEdit()
        layout.addRow("CD-ROM ISO (-cdrom):", self.add_browse(self.f_cdrom))
        self.f_fda = QLineEdit()
        layout.addRow("Floppy A (-fda):", self.add_browse(self.f_fda))
        self.f_fdb = QLineEdit()
        layout.addRow("Floppy B (-fdb):", self.add_browse(self.f_fdb))
        self.f_mtdblock = QLineEdit()
        layout.addRow("MTD Block (-mtdblock):", self.add_browse(self.f_mtdblock))
        self.f_pflash = QLineEdit()
        layout.addRow("Parallel Flash (-pflash):", self.add_browse(self.f_pflash))
        self.f_sd = QLineEdit()
        layout.addRow("SD Card (-sd):", self.add_browse(self.f_sd))
        self.f_snapshot = QCheckBox("Snapshot Mode (-snapshot)")
        self.f_boot = QComboBox()
        self.f_boot.addItems(["", "a (Floppy)", "c (Hard Disk)", "d (CD-ROM)", "n (Network)"])

        layout.addRow(self.f_snapshot)
        layout.addRow("Boot Order (-boot):", self.f_boot)
        return self.create_scroll_widget(layout)

    def create_network_tab(self):
        self.net_layout = QFormLayout()
        layout = self.net_layout
        self.f_net_type = QComboBox()
        self.f_net_type.addItems(["user", "tap", "bridge", "socket", "stream", "vde", "none"])

        self.f_net_device = QComboBox()
        self.f_net_device.addItems(["virtio-net-pci", "e1000", "rtl8139", "pcnet", "vmxnet3"])

        self.f_nic = QLineEdit()
        self.f_nic.setPlaceholderText("model=virtio-net-pci,netdev=n1")

        self.f_hostfwd = QLineEdit()
        self.f_hostfwd.setPlaceholderText("tcp::2222-:22")
        self.f_hostname = QLineEdit()
        self.f_redir = QLineEdit()
        self.f_redir.setPlaceholderText("tcp:2222::22")

        layout.addRow("Network Backend (-netdev):", self.f_net_type)
        layout.addRow("Network Device (-device):", self.f_net_device)
        layout.addRow("Combined NIC (-nic):", self.f_nic)
        layout.addRow("Host Forward (hostfwd=):", self.f_hostfwd)
        layout.addRow("Port Redir (-redir):", self.f_redir)
        layout.addRow("DHCP Hostname:", self.f_hostname)
        return self.create_scroll_widget(layout)

    def create_graphics_tab(self):
        self.gfx_layout = QFormLayout()
        layout = self.gfx_layout
        self.f_display = QComboBox()
        self.f_display.addItems(["gtk", "sdl", "curses", "spice-app", "egl-headless", "none"])

        self.f_vga = QComboBox()
        self.f_vga.addItems(["virtio", "std", "vmware", "qxl", "none"])
        self.f_vnc = QLineEdit()
        self.f_vnc.setPlaceholderText(":1,password=on")
        self.f_fullscreen = QCheckBox("Full Screen (-full-screen)")

        layout.addRow("Display Type (-display):", self.f_display)
        layout.addRow("VGA Card (-vga):", self.f_vga)
        layout.addRow("VNC Display (-vnc):", self.f_vnc)
        layout.addRow(self.f_fullscreen)
        return self.create_scroll_widget(layout)

    def create_input_tab(self):
        self.input_layout = QFormLayout()
        layout = self.input_layout
        self.f_usb = QCheckBox("Enable USB (-usb)")
        self.f_usb_device = QComboBox()
        self.f_usb_device.addItems(["", "usb-tablet", "usb-mouse", "usb-kbd", "usb-host"])
        self.f_kbd_layout = QLineEdit()
        self.f_kbd_layout.setPlaceholderText("en-us")

        self.f_usbdevice = QLineEdit()
        self.f_usbdevice.setPlaceholderText("tablet OR host:bus.addr")

        layout.addRow(self.f_usb)
        layout.addRow("USB Device (-device):", self.f_usb_device)
        layout.addRow("Old USB Dev (-usbdevice):", self.f_usbdevice)
        layout.addRow("Keyboard Layout (-k):", self.f_kbd_layout)
        return self.create_scroll_widget(layout)

    def create_boot_tab(self):
        self.boot_layout = QFormLayout()
        layout = self.boot_layout
        self.f_kernel = QLineEdit()
        layout.addRow("Linux Kernel (-kernel):", self.add_browse(self.f_kernel))
        self.f_initrd = QLineEdit()
        layout.addRow("Initrd (-initrd):", self.add_browse(self.f_initrd))
        self.f_append = QLineEdit()
        layout.addRow("Kernel Cmdline (-append):", self.f_append)
        self.f_dtb = QLineEdit()
        layout.addRow("Device Tree (-dtb):", self.add_browse(self.f_dtb))
        self.f_bios = QLineEdit()
        layout.addRow("BIOS/Firmware (-bios):", self.add_browse(self.f_bios))
        self.f_L = QLineEdit()
        layout.addRow("BIOS/ROM Path (-L):", self.add_browse(self.f_L))
        return self.create_scroll_widget(layout)

    def create_audio_tab(self):
        self.audio_layout = QFormLayout()
        layout = self.audio_layout
        self.f_audio_drv = QComboBox()
        self.f_audio_drv.addItems(["none", "pa", "alsa", "oss", "sdl", "dsound", "coreaudio"])
        self.f_soundhw = QComboBox()
        self.f_soundhw.addItems(["none", "intel-hda", "ac97", "sb16", "all"])

        self.f_audiodev = QLineEdit()
        self.f_audiodev.setPlaceholderText("pa,id=snd0,server=127.0.0.1")

        layout.addRow("Audio Driver (-audio):", self.f_audio_drv)
        layout.addRow("Audio Dev (-audiodev):", self.f_audiodev)
        layout.addRow("Sound Hardware (-soundhw):", self.f_soundhw)
        return self.create_scroll_widget(layout)

    def create_debug_tab(self):
        self.debug_layout = QFormLayout()
        layout = self.debug_layout
        self.f_debug_item = QLineEdit()
        self.f_debug_item.setPlaceholderText("cpu,int,pcall")
        self.f_debug_log = QLineEdit()
        layout.addRow("Debug Log File (-D):", self.add_browse(self.f_debug_log))
        self.f_gdb = QLineEdit()
        self.f_gdb.setPlaceholderText("tcp::1234")
        self.f_trace = QLineEdit()
        self.f_trace.setPlaceholderText("events=my_events.txt")
        self.f_trace_file = QLineEdit()
        layout.addRow("Trace File (-T):", self.add_browse(self.f_trace_file))

        layout.addRow("Log Items (-d):", self.f_debug_item)
        layout.addRow("GDB Dev (-gdb):", self.f_gdb)
        layout.addRow("Trace (-trace):", self.f_trace)
        return self.create_scroll_widget(layout)

    def create_expert_tab(self):
        self.expert_layout = QVBoxLayout()
        layout = self.expert_layout
        self.f_qemu_path = QLineEdit()
        btn_qemu_br = QPushButton("Browse...")
        btn_qemu_br.clicked.connect(self.select_qemu_executable)
        path_h = QHBoxLayout()
        path_h.addWidget(self.f_qemu_path)
        path_h.addWidget(btn_qemu_br)
        self.label_qemu_bin = QLabel("QEMU Binary Path:")
        layout.addWidget(self.label_qemu_bin)
        layout.addLayout(path_h)

        form = QFormLayout()
        self.f_object = QLineEdit()
        self.f_object.setPlaceholderText("secret,id=sec0,data=123456")
        self.f_global = QLineEdit()
        self.f_global.setPlaceholderText("virtio-net-pci.vectors=0")
        self.f_add_fd = QLineEdit()
        self.f_add_fd.setPlaceholderText("fd=3,set=1")
        self.f_device_extra = QLineEdit()
        self.f_device_extra.setPlaceholderText("virtio-blk-pci,drive=drive0")

        form.addRow("Object (-object):", self.f_object)
        form.addRow("Global (-global):", self.f_global)
        form.addRow("Add FD (-add-fd):", self.f_add_fd)
        form.addRow("Add Device (-device):", self.f_device_extra)
        layout.addLayout(form)

        self.f_extra = QPlainTextEdit()
        self.label_extra_args = QLabel("Additional Arguments:")
        layout.addWidget(self.label_extra_args)
        layout.addWidget(self.f_extra)
        return self.create_scroll_widget(layout)

    def create_templates_tab(self):
        layout = QVBoxLayout()
        
        self.label_select_template = QLabel("Select a Template to apply:")
        self.label_select_template.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(self.label_select_template)
        
        self.template_buttons = []
        templates = [
            ("Debian Linux", self.apply_debian_template),
            ("Fedora Linux", self.apply_fedora_template),
            ("Arch Linux", self.apply_arch_template),
            ("Windows 10/11", self.apply_windows_template),
            ("MacOS (OSX-KVM)", self.apply_macos_template)
        ]
        
        for name, func in templates:
            btn = QPushButton(name)
            btn.setFixedHeight(40)
            btn.clicked.connect(func)
            layout.addWidget(btn)
            self.template_buttons.append((btn, name)) # Store original name as fallback
            
        layout.addSpacing(20)
        self.btn_clear = QPushButton("Clear All Fields")
        self.btn_clear.setFixedHeight(45)
        self.btn_clear.setStyleSheet("background-color: #f44336; color: white; font-weight: bold;")
        self.btn_clear.clicked.connect(self.clear_all_fields)
        layout.addWidget(self.btn_clear)
            
        layout.addStretch()
        return self.create_scroll_widget(layout)

    def apply_debian_template(self):
        self.f_name.setText("Debian_VM")
        self.f_arch.setCurrentText("x86_64")
        self.f_machine.setCurrentText("q35")
        self.f_cpu.setCurrentText("host")
        self.f_ram.setValue(2048)
        self.f_smp.setValue(2)
        self.f_net_type.setCurrentText("user")
        self.f_net_device.setCurrentText("virtio-net-pci")
        self.f_display.setCurrentText("gtk")
        self.f_vga.setCurrentText("virtio")
        self.update_preview()

    def apply_fedora_template(self):
        self.f_name.setText("Fedora_VM")
        self.f_arch.setCurrentText("x86_64")
        self.f_machine.setCurrentText("q35")
        self.f_cpu.setCurrentText("host")
        self.f_ram.setValue(4096)
        self.f_smp.setValue(2)
        self.f_net_type.setCurrentText("user")
        self.f_net_device.setCurrentText("virtio-net-pci")
        self.f_display.setCurrentText("gtk")
        self.f_vga.setCurrentText("virtio")
        self.update_preview()

    def apply_arch_template(self):
        self.f_name.setText("Arch_VM")
        self.f_arch.setCurrentText("x86_64")
        self.f_machine.setCurrentText("q35")
        self.f_cpu.setCurrentText("host")
        self.f_ram.setValue(2048)
        self.f_smp.setValue(2)
        self.f_net_type.setCurrentText("user")
        self.f_net_device.setCurrentText("virtio-net-pci")
        self.f_display.setCurrentText("gtk")
        self.f_vga.setCurrentText("virtio")
        self.update_preview()

    def apply_windows_template(self):
        self.f_name.setText("Windows_VM")
        self.f_arch.setCurrentText("x86_64")
        self.f_machine.setCurrentText("q35")
        self.f_cpu.setCurrentText("host")
        self.f_ram.setValue(4096)
        self.f_smp.setValue(4)
        self.f_net_type.setCurrentText("user")
        self.f_net_device.setCurrentText("e1000-82545em")
        self.f_display.setCurrentText("gtk")
        self.f_vga.setCurrentText("qxl")
        self.f_usb.setChecked(True)
        self.f_usb_device.setCurrentText("usb-tablet")
        self.update_preview()

    def apply_macos_template(self):
        # Switch to Virtualization mode to enable KVM
        self.f_mode.setCurrentIndex(1)
        
        self.f_name.setText("MacOS_VM")
        self.f_arch.setCurrentText("x86_64")
        self.f_machine.setCurrentText("q35")
        
        # MacOS requirements based on OSX-KVM
        # Using a more comprehensive CPU string from OpenCore-Boot.sh
        cpu_val = "Haswell-noTSX,vendor=GenuineIntel,+invtsc,vmware-cpuid-freq=on,+ssse3,+sse4.2,+popcnt,+avx,+aes,+xsave,+xsaveopt,check,kvm=on"
        self.f_cpu.setEditable(True)
        self.f_cpu.setCurrentText(cpu_val)
        
        self.f_ram.setValue(4096)
        self.f_smp.setValue(4)
        
        # Force KVM
        self.f_accel.setCurrentText("kvm")
        self.f_net_type.setCurrentText("user")
        self.f_net_device.setCurrentText("vmxnet3")
        self.f_hostfwd.setText("tcp::2222-:22")
        
        self.f_display.setCurrentText("gtk")
        self.f_vga.setCurrentText("virtio")
        self.f_usb.setChecked(True)
        self.f_usb_device.setCurrentText("usb-tablet")
        
        # MacOS specific flags based on OSX-KVM
        osk = "ourhardworkbythesewordsguardedpleasedontsteal(c)AppleComputerInc"
        self.f_device_extra.setText(f"isa-applesmc,osk=\"{osk}\"")
        
        # Add common objects and arguments from OSX-KVM
        extra_args = [
            "-smbios type=2",
            "-global ICH9-LPC.acpi-pci-hotplug-with-bridge-support=off",
            "-device pcie-root-port,id=pcie.1,bus=pcie.0,slot=1,chassis=1",
            "-device pcie-root-port,id=pcie.2,bus=pcie.0,slot=2,chassis=2",
            "# --- MacOS Boot & Storage Configuration ---",
            "# You MUST provide paths to these files for macOS to boot:",
            "# -drive if=pflash,format=raw,readonly=on,file=\"OVMF_CODE.fd\"",
            "# -drive if=pflash,format=raw,file=\"OVMF_VARS-1024x768.fd\"",
            "# -device ide-hd,bus=sata.2,drive=OpenCoreBoot",
            "# -drive id=OpenCoreBoot,if=none,snapshot=on,format=qcow2,file=\"OpenCore.qcow2\"",
            "# -device ide-hd,bus=sata.3,drive=InstallMedia",
            "# -drive id=InstallMedia,if=none,snapshot=on,format=raw,file=\"BaseSystem.img\"",
            "# -device ide-hd,bus=sata.4,drive=SystemDisk",
            "# -drive id=SystemDisk,if=none,format=qcow2,file=\"mac_hdd_ng.img\""
        ]
        self.f_extra.setPlainText("\n".join(extra_args))
        
        self.f_vga.setCurrentText("vmware")
        self.f_display.setCurrentText("gtk")
        self.f_nodefaults.setChecked(True)
        
        QMessageBox.information(self, "MacOS Template (OSX-KVM)", 
            "MacOS template applied! 🚀\n\n"
            "Settings adjusted to match OSX-KVM project requirements:\n"
            "• Mode: Virtualization (KVM)\n"
            "• CPU: Haswell-noTSX (with invtsc and kvm=on)\n"
            "• Machine: q35\n"
            "• Net: vmxnet3\n"
            "• SMC: OSK string included\n\n"
            "Note: You still need to provide:\n"
            "1. OpenCore boot image (BaseSystem.img)\n"
            "2. MacOS Virtual Disk (qcow2)\n"
            "3. OVMF UEFI Firmware\n\n"
            "Recommended host tweak:\n"
            "sudo modprobe kvm; echo 1 | sudo tee /sys/module/kvm/parameters/ignore_msrs")
        self.update_preview()

    def clear_all_fields(self):
        # Reset LineEdits
        line_edits = [
            self.f_name, self.f_uuid, self.f_pidfile, self.f_mem_path, self.f_numa,
            self.f_hda, self.f_hdb, self.f_hdc, self.f_hdd, self.f_cdrom,
            self.f_fda, self.f_fdb, self.f_mtdblock, self.f_pflash, self.f_sd,
            self.f_hostfwd, self.f_hostname, self.f_redir, self.f_nic,
            self.f_vnc, self.f_usbdevice, self.f_kbd_layout,
            self.f_kernel, self.f_initrd, self.f_append, self.f_dtb, self.f_bios, self.f_L,
            self.f_audiodev, self.f_debug_item, self.f_debug_log, self.f_gdb, self.f_trace, self.f_trace_file,
            self.f_object, self.f_global, self.f_add_fd, self.f_device_extra
        ]
        for w in line_edits:
            if w:
                w.clear()

        # Reset ComboBoxes
        combos = [
            self.f_arch, self.f_machine, self.f_cpu, self.f_accel, self.f_boot,
            self.f_net_type, self.f_net_device, self.f_display, self.f_vga,
            self.f_usb_device, self.f_audio_drv, self.f_soundhw
        ]
        for w in combos:
            if w:
                w.setCurrentIndex(0)

        # Reset SpinBoxes
        if self.f_ram: self.f_ram.setValue(1024)
        if self.f_smp: self.f_smp.setValue(1)

        # Reset CheckBoxes
        checkboxes = [
            self.f_nodefaults, self.f_no_user_config, self.f_S, self.f_no_acpi,
            self.f_no_hpet, self.f_no_shutdown, self.f_no_reboot, self.f_daemonize,
            self.f_mem_prealloc, self.f_snapshot, self.f_fullscreen, self.f_usb
        ]
        for w in checkboxes:
            if w:
                w.setChecked(False)

        # Reset PlainTextEdit
        if self.f_extra: self.f_extra.clear()

        # Reset mode to Emulation
        if self.f_mode: self.f_mode.setCurrentIndex(0)

        # Reset QEMU path to auto
        self.update_qemu_path_auto()

        # Update preview
        self.update_preview()

    def add_browse(self, line_edit):
        w = QWidget()
        l = QHBoxLayout(w)
        l.setContentsMargins(0, 0, 0, 0)
        l.addWidget(line_edit)
        btn = QPushButton("📁")
        btn.setFixedWidth(30)
        btn.clicked.connect(lambda: self.select_file(line_edit))
        l.addWidget(btn)
        return w

    def setup_connections(self):
        widgets = [
            self.f_arch, self.f_machine, self.f_cpu, self.f_accel,
            self.f_ram, self.f_smp, self.f_boot, self.f_uuid,
            self.f_nodefaults, self.f_no_user_config, self.f_S,
            self.f_no_acpi, self.f_no_hpet, self.f_no_shutdown,
            self.f_no_reboot, self.f_daemonize, self.f_mem_prealloc,
            self.f_pidfile, self.f_mem_path, self.f_numa,
            self.f_hda, self.f_hdb, self.f_hdc, self.f_hdd, self.f_cdrom,
            self.f_fda, self.f_fdb, self.f_mtdblock, self.f_pflash, self.f_sd, self.f_snapshot,
            self.f_net_type, self.f_net_device, self.f_hostfwd, self.f_hostname,
            self.f_redir, self.f_nic,
            self.f_display, self.f_vga, self.f_vnc, self.f_fullscreen,
            self.f_usb, self.f_usb_device, self.f_usbdevice, self.f_kbd_layout,
            self.f_kernel, self.f_initrd, self.f_append, self.f_dtb, self.f_bios, self.f_L,
            self.f_audio_drv, self.f_audiodev, self.f_soundhw,
            self.f_debug_item, self.f_debug_log, self.f_gdb, self.f_trace, self.f_trace_file,
            self.f_object, self.f_global, self.f_add_fd, self.f_device_extra,
            self.f_extra, self.f_qemu_path
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
            elif isinstance(w, QCheckBox):
                w.stateChanged.connect(lambda _: self.update_preview())

        self.f_arch.currentIndexChanged.connect(
            lambda _=None: (self.update_qemu_path_auto(), self.update_preview())
        )

    def retranslate_ui(self):
        lang_code = ["en", "ua", "de", "zh", "ru"][self.f_lang.currentIndex()]
        d = self.lang_data[lang_code]
        is_intuitive = self.f_intuitive.isChecked()

        self.setWindowTitle(d["window_title"])
        self.label_saved_vms.setText(d["saved_vms"])
        self.label_cmd_preview.setText(d["cmd_preview"])
        self.label_qemu_logs.setText(d["logs"])
        
        # Sidebar & Buttons
        # Finding Delete button is slightly tricky, let's just find it by type in sidebar
        for i in range(self.centralWidget().layout().itemAt(0).layout().count()):
            w = self.centralWidget().layout().itemAt(0).layout().itemAt(i).widget()
            if isinstance(w, QPushButton) and w != self.btn_run:
                w.setText(d["delete_vm"])

        self.btn_run.setText(d["stop"] if self.process.state() == QProcess.ProcessState.Running else d["launch"])
        self.status_label.setText(d["status_running"] if self.process.state() == QProcess.ProcessState.Running else d["status_idle"])

        # Mode text
        curr_mode = self.f_mode.currentIndex()
        self.f_mode.setItemText(0, d["mode_emu"])
        self.f_mode.setItemText(1, d["mode_virt"])
        self.f_mode.setCurrentIndex(curr_mode)

        # Tabs
        self.tabs.setTabText(0, d["tab_hw"])
        self.tabs.setTabText(1, d["tab_storage"])
        self.tabs.setTabText(2, d["tab_net"])
        self.tabs.setTabText(3, d["tab_gfx"])
        self.tabs.setTabText(4, d["tab_input"])
        self.tabs.setTabText(5, d["tab_boot"])
        self.tabs.setTabText(6, d["tab_audio"])
        self.tabs.setTabText(7, d["tab_debug"])
        self.tabs.setTabText(8, d["tab_expert"])
        self.tabs.setTabText(9, d["tab_templates"])

        # HW
        hw = self.hw_layout
        hw.labelForField(self.f_name).setText(d["vm_name"])
        hw.labelForField(self.f_arch).setText(d["arch"])
        hw.labelForField(self.f_machine).setText(d["machine"])
        hw.labelForField(self.f_cpu).setText(d["cpu"])
        hw.labelForField(self.f_accel).setText(d["accel"])
        hw.labelForField(self.f_ram).setText(d["intuitive_ram"] if is_intuitive else d["ram"])
        hw.labelForField(self.f_smp).setText(d["intuitive_cores"] if is_intuitive else d["cores"])
        hw.labelForField(self.f_uuid).setText(d["uuid"])
        hw.itemAt(hw.getWidgetPosition(self.f_pidfile.parentWidget())[0], QFormLayout.ItemRole.LabelRole).widget().setText(d["pid_file"])
        hw.labelForField(self.f_mem_path).setText(d["mem_path"])
        hw.labelForField(self.f_numa).setText(d["numa"])
        
        self.f_nodefaults.setText(d["no_defaults"])
        self.f_no_user_config.setText(d["no_user_config"])
        self.f_S.setText(d["freeze_cpu"])
        self.f_no_acpi.setText(d["disable_acpi"])
        self.f_no_hpet.setText(d["disable_hpet"])
        self.f_no_shutdown.setText(d["no_shutdown"])
        self.f_no_reboot.setText(d["no_reboot"])
        self.f_daemonize.setText(d["daemonize"])
        self.f_mem_prealloc.setText(d["prealloc_ram"])

        tech_hw = [
            self.f_arch, self.f_machine, self.f_cpu, self.f_accel, self.f_uuid, 
            self.f_pidfile.parentWidget(), self.f_mem_path, self.f_numa,
            self.f_nodefaults, self.f_no_user_config, self.f_S, self.f_no_acpi,
            self.f_no_hpet, self.f_no_shutdown, self.f_no_reboot, self.f_daemonize,
            self.f_mem_prealloc
        ]
        for w in tech_hw:
            l = hw.labelForField(w)
            if l: l.setVisible(not is_intuitive)
            w.setVisible(not is_intuitive)

        # Storage
        st = self.storage_layout
        st.itemAt(st.getWidgetPosition(self.f_hda.parentWidget())[0], QFormLayout.ItemRole.LabelRole).widget().setText(d["intuitive_hda"] if is_intuitive else d["hda"])
        st.itemAt(st.getWidgetPosition(self.f_hdb.parentWidget())[0], QFormLayout.ItemRole.LabelRole).widget().setText(d["hdb"])
        st.itemAt(st.getWidgetPosition(self.f_hdc.parentWidget())[0], QFormLayout.ItemRole.LabelRole).widget().setText(d["hdc"])
        st.itemAt(st.getWidgetPosition(self.f_hdd.parentWidget())[0], QFormLayout.ItemRole.LabelRole).widget().setText(d["hdd"])
        st.itemAt(st.getWidgetPosition(self.f_cdrom.parentWidget())[0], QFormLayout.ItemRole.LabelRole).widget().setText(d["intuitive_cdrom"] if is_intuitive else d["cdrom"])
        st.itemAt(st.getWidgetPosition(self.f_fda.parentWidget())[0], QFormLayout.ItemRole.LabelRole).widget().setText(d["fda"])
        st.itemAt(st.getWidgetPosition(self.f_fdb.parentWidget())[0], QFormLayout.ItemRole.LabelRole).widget().setText(d["fdb"])
        st.itemAt(st.getWidgetPosition(self.f_mtdblock.parentWidget())[0], QFormLayout.ItemRole.LabelRole).widget().setText(d["mtd"])
        st.itemAt(st.getWidgetPosition(self.f_pflash.parentWidget())[0], QFormLayout.ItemRole.LabelRole).widget().setText(d["pflash"])
        st.itemAt(st.getWidgetPosition(self.f_sd.parentWidget())[0], QFormLayout.ItemRole.LabelRole).widget().setText(d["sd"])
        st.labelForField(self.f_boot).setText(d["boot_order"])
        self.f_snapshot.setText(d["snapshot"])

        st_tech = [
            self.f_hdb.parentWidget(), self.f_hdc.parentWidget(), self.f_hdd.parentWidget(),
            self.f_fda.parentWidget(), self.f_fdb.parentWidget(), self.f_mtdblock.parentWidget(),
            self.f_pflash.parentWidget(), self.f_sd.parentWidget(), self.f_boot, self.f_snapshot
        ]
        for w in st_tech:
            l = st.labelForField(w)
            if l: l.setVisible(not is_intuitive)
            w.setVisible(not is_intuitive)

        # Net
        nt = self.net_layout
        nt.labelForField(self.f_net_type).setText(d["net_backend"])
        nt.labelForField(self.f_net_device).setText(d["net_device"])
        nt.labelForField(self.f_nic).setText(d["nic_combined"])
        nt.labelForField(self.f_hostfwd).setText(d["host_fwd"])
        nt.labelForField(self.f_redir).setText(d["port_redir"])
        nt.labelForField(self.f_hostname).setText(d["dhcp_hostname"])
        self.tabs.setTabVisible(2, not is_intuitive)

        # Graphics
        gx = self.gfx_layout
        gx.labelForField(self.f_display).setText(d["intuitive_display"] if is_intuitive else d["display_type"])
        gx.labelForField(self.f_vga).setText(d["vga_card"])
        gx.labelForField(self.f_vnc).setText(d["vnc_display"])
        self.f_fullscreen.setText(d["fullscreen"])
        
        gx_tech = [self.f_vga, self.f_vnc, self.f_fullscreen]
        for w in gx_tech:
            l = gx.labelForField(w)
            if l: l.setVisible(not is_intuitive)
            w.setVisible(not is_intuitive)

        # Audio (intuitive sound reused from Input for better tab structure)
        au = self.audio_layout
        au.labelForField(self.f_audio_drv).setText(d["audio_drv"])
        au.labelForField(self.f_audiodev).setText(d["audio_dev"])
        au.labelForField(self.f_soundhw).setText(d["sound_hw"])
        
        # Templates
        if hasattr(self, 'label_select_template'):
            self.label_select_template.setText(d["select_template"])
        if hasattr(self, 'btn_clear'):
            self.btn_clear.setText(d["clear"])

        # Expert
        self.label_qemu_bin.setText(d["qemu_bin"])
        self.label_extra_args.setText(d["extra_args"])
        # Finding browse button in expert path_h
        # ... skipped for now or add direct ref
        
        # Bottom Save button
        for i in range(self.tabs.parent().layout().count()):
            w = self.tabs.parent().layout().itemAt(i).widget()
            if isinstance(w, QPushButton) and w != self.btn_run:
                w.setText(d["save_config"])

        # Hide complex tabs
        self.tabs.setTabVisible(4, not is_intuitive) # Input
        self.tabs.setTabVisible(5, not is_intuitive) # Boot
        self.tabs.setTabVisible(6, not is_intuitive) # Audio
        self.tabs.setTabVisible(7, not is_intuitive) # Debug
        self.tabs.setTabVisible(8, not is_intuitive) # Expert
        
        self.update_preview()

    def update_qemu_path_auto(self):
        arch_code = self.arch_map.get(self.f_arch.currentText(), "x86_64")
        binary_name = f"qemu-system-{arch_code}"
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
        file_path, _ = QFileDialog.getOpenFileName(self, "Select QEMU Executable", "", file_filter)
        if file_path:
            self.f_qemu_path.setText(file_path)

    def generate_command_list(self):
        qemu_bin = self.f_qemu_path.text().strip()
        if not qemu_bin:
            arch_code = self.arch_map.get(self.f_arch.currentText(), self.f_arch.currentText() or "x86_64")
            qemu_bin = f"qemu-system-{arch_code}"

        cmd = [qemu_bin]

        # System & CPU
        if self.f_name.text():
            cmd.extend(["-name", self.f_name.text()])

        cmd.extend(["-m", str(self.f_ram.value())])
        cmd.extend(["-smp", str(self.f_smp.value())])
        
        # Determine acceleration and machine type
        machine = self.f_machine.currentText() if isinstance(self.f_machine, QComboBox) else self.f_machine.text()
        accel = self.f_accel.currentText()
        
        if accel == "kvm":
            cmd.extend(["-machine", f"{machine},accel=kvm"])
        else:
            cmd.extend(["-machine", machine])
            cmd.extend(["-accel", accel])

        cmd.extend(["-cpu", self.f_cpu.currentText()])

        uuid_val = self.f_uuid.text().strip()
        if uuid_val: cmd.extend(["-uuid", uuid_val])

        pidfile = self.f_pidfile.text().strip()
        if pidfile: cmd.extend(["-pidfile", pidfile])

        mem_path = self.f_mem_path.text().strip()
        if mem_path: cmd.extend(["-mem-path", mem_path])

        numa = self.f_numa.text().strip()
        if numa: cmd.extend(["-numa", numa])

        if self.f_nodefaults.isChecked(): cmd.append("-nodefaults")
        if self.f_no_user_config.isChecked(): cmd.append("-no-user-config")
        if self.f_S.isChecked(): cmd.append("-S")
        if self.f_no_acpi.isChecked(): cmd.append("-no-acpi")
        if self.f_no_hpet.isChecked(): cmd.append("-no-hpet")
        if self.f_no_shutdown.isChecked(): cmd.append("-no-shutdown")
        if self.f_no_reboot.isChecked(): cmd.append("-no-reboot")
        if self.f_daemonize.isChecked(): cmd.append("-daemonize")
        if self.f_mem_prealloc.isChecked(): cmd.append("-mem-prealloc")

        # Storage
        for flag, widget in [
            ("-hda", self.f_hda), ("-hdb", self.f_hdb), ("-hdc", self.f_hdc), ("-hdd", self.f_hdd),
            ("-cdrom", self.f_cdrom), ("-fda", self.f_fda), ("-fdb", self.f_fdb),
            ("-mtdblock", self.f_mtdblock), ("-pflash", self.f_pflash), ("-sd", self.f_sd)
        ]:
            path = widget.text().strip()
            if path: cmd.extend([flag, path])

        if self.f_snapshot.isChecked(): cmd.append("-snapshot")

        boot_val = self.f_boot.currentText()
        if boot_val:
            cmd.extend(["-boot", boot_val.split()[0]])

        # Network
        net_type = self.f_net_type.currentText()
        if net_type != "none":
            netdev_id = "net0"
            net_opts = f"{net_type},id={netdev_id}"
            hostfwd = self.f_hostfwd.text().strip()
            if net_type == "user" and hostfwd:
                net_opts += f",hostfwd={hostfwd}"
            hostname = self.f_hostname.text().strip()
            if net_type == "user" and hostname:
                net_opts += f",hostname={hostname}"

            cmd.extend(["-netdev", net_opts])
            cmd.extend(["-device", f"{self.f_net_device.currentText()},netdev={netdev_id}"])

        nic_val = self.f_nic.text().strip()
        if nic_val: cmd.extend(["-nic", nic_val])
        redir_val = self.f_redir.text().strip()
        if redir_val: cmd.extend(["-redir", redir_val])

        # Graphics
        display_val = self.f_display.currentText()
        if display_val != "none":
            cmd.extend(["-display", display_val])
        else:
            cmd.append("-nographic")

        vga_val = self.f_vga.currentText()
        if vga_val != "none":
            cmd.extend(["-vga", vga_val])

        vnc_val = self.f_vnc.text().strip()
        if vnc_val: cmd.extend(["-vnc", vnc_val])
        if self.f_fullscreen.isChecked(): cmd.append("-full-screen")

        # Input
        if self.f_usb.isChecked(): cmd.append("-usb")
        usb_dev = self.f_usb_device.currentText()
        if usb_dev: cmd.extend(["-device", usb_dev])
        usbdevice_val = self.f_usbdevice.text().strip()
        if usbdevice_val: cmd.extend(["-usbdevice", usbdevice_val])
        kbd_layout = self.f_kbd_layout.text().strip()
        if kbd_layout: cmd.extend(["-k", kbd_layout])

        # Kernel & Boot
        for flag, widget in [
            ("-kernel", self.f_kernel), ("-initrd", self.f_initrd), ("-dtb", self.f_dtb),
            ("-bios", self.f_bios), ("-L", self.f_L)
        ]:
            path = widget.text().strip()
            if path: cmd.extend([flag, path])

        append_val = self.f_append.text().strip()
        if append_val: cmd.extend(["-append", append_val])

        # Audio
        audio_drv = self.f_audio_drv.currentText()
        soundhw = self.f_soundhw.currentText()
        if audio_drv != "none":
            cmd.extend(["-audio", f"driver={audio_drv},model={soundhw}"])
        elif soundhw != "none":
            cmd.extend(["-soundhw", soundhw])

        audiodev = self.f_audiodev.text().strip()
        if audiodev: cmd.extend(["-audiodev", audiodev])

        # Debug
        debug_items = self.f_debug_item.text().strip()
        if debug_items: cmd.extend(["-d", debug_items])
        debug_log = self.f_debug_log.text().strip()
        if debug_log: cmd.extend(["-D", debug_log])
        gdb_val = self.f_gdb.text().strip()
        if gdb_val:
            if gdb_val == "s":
                cmd.append("-s")
            else:
                cmd.extend(["-gdb", gdb_val])
        trace_val = self.f_trace.text().strip()
        if trace_val: cmd.extend(["-trace", trace_val])
        trace_file = self.f_trace_file.text().strip()
        if trace_file: cmd.extend(["-T", trace_file])

        # Expert
        obj_val = self.f_object.text().strip()
        if obj_val: cmd.extend(["-object", obj_val])
        glob_val = self.f_global.text().strip()
        if glob_val: cmd.extend(["-global", glob_val])
        fd_val = self.f_add_fd.text().strip()
        if fd_val: cmd.extend(["-add-fd", fd_val])
        dev_extra = self.f_device_extra.text().strip()
        if dev_extra: cmd.extend(["-device", dev_extra])

        extra = self.f_extra.toPlainText().strip()
        if extra:
            cmd.extend(shlex.split(extra))

        return cmd

    # Corrected methods at class level
    def update_preview(self):
        try:
            self.cmd_preview.setPlainText(" ".join(self.generate_command_list()))
        except (OSError, FileNotFoundError) as exc:
            self.cmd_preview.setPlainText(f"Error: {exc}")

    def run_vm(self):
        lang_code = ["en", "ua", "de"][self.f_lang.currentIndex()]
        d = self.lang_data[lang_code]
        if self.process.state() == QProcess.ProcessState.Running:
            self.process.terminate()
            if not self.process.waitForFinished(3000):
                self.process.kill()
            return

        args = self.generate_command_list()
        if not args:
            QMessageBox.critical(self, d["err"], "Unable to generate QEMU launch command")
            return

        # Check binary existence
        qemu_bin = str(args[0])
        executable_path = shutil.which(qemu_bin)

        # Fallback for Windows if only name is provided
        if not executable_path and platform.system() == "Windows" and not qemu_bin.lower().endswith(".exe"):
            executable_path = shutil.which(qemu_bin + ".exe")

        if not executable_path:
            # If still not found, check if it's an absolute path that exists
            bin_path = Path(qemu_bin)
            if bin_path.exists():
                executable_path = str(bin_path)
            else:
                QMessageBox.critical(
                    self, d["err"],
                    f"QEMU binary not found: {qemu_bin}\nPlease check the path in the 'Expert' tab."
                )
                return

        self.log_output.clear()
        self.log_output.appendPlainText(f"Starting: {' '.join(args)}")
        self.process.setProgram(executable_path)
        self.process.setArguments([str(arg) for arg in args[1:]])
        self.process.start()

        if not self.process.waitForStarted(5000):
            QMessageBox.critical(self, d["err"], f"Failed to start QEMU: {self.process.errorString()}")

    def on_process_finished(self):
        self.update_status_ui()
        print("QEMU process finished.")

    def update_status_ui(self):
        lang_code = ["en", "ua", "de"][self.f_lang.currentIndex()]
        d = self.lang_data[lang_code]
        is_run = self.process.state() == QProcess.ProcessState.Running
        self.btn_run.setText(d["stop"] if is_run else d["launch"])
        self.btn_run.setStyleSheet(
            f"background: {'#9e1a1a' if is_run else '#1a4a7a'}; color: white; font-weight: bold;"
        )
        self.status_label.setText(d["status_running"] if is_run else d["status_idle"])
        self.status_label.setStyleSheet(
            f"color: {'#00ff00' if is_run else 'gray'}; font-weight: bold;"
        )

    def read_output(self):
        try:
            err = self.process.readAllStandardError().data().decode(errors='replace')
            out = self.process.readAllStandardOutput().data().decode(errors='replace')
            if err:
                self.log_output.appendPlainText(err.strip())
            if out:
                self.log_output.appendPlainText(out.strip())
        except Exception as e:
            print(f"Read output error: {e}")

    def delete_vm(self):
        lang_code = ["en", "ua", "de"][self.f_lang.currentIndex()]
        d = self.lang_data[lang_code]
        name = self.vm_list.currentItem()
        if not name: return
        name = name.text()
        reply = QMessageBox.question(self, d['confirm_del'], d['delete_ask'].format(name),
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            p = self.base_path / name
            if p.exists():
                shutil.rmtree(p)
                self.refresh_list()

    def save_vm(self):
        lang_code = ["en", "ua", "de"][self.f_lang.currentIndex()]
        d = self.lang_data[lang_code]
        name = self.f_name.text().strip() or "unnamed_vm"
        p = self.base_path / name
        try:
            p.mkdir(exist_ok=True)
            data = {
                "lang_idx": self.f_lang.currentIndex(),
                "intuitive": self.f_intuitive.isChecked(),
                "name": name,
                "mode": self.f_mode.currentIndex(),
                "arch": self.f_arch.currentText(),
                "machine": self.f_machine.currentText(),
                "cpu": self.f_cpu.currentText(),
                "accel": self.f_accel.currentText(),
                "ram": self.f_ram.value(),
                "smp": self.f_smp.value(),
                "uuid": self.f_uuid.text(),
                "pidfile": self.f_pidfile.text(),
                "mem_path": self.f_mem_path.text(),
                "numa": self.f_numa.text(),
                "nodefaults": self.f_nodefaults.isChecked(),
                "no_user_config": self.f_no_user_config.isChecked(),
                "S": self.f_S.isChecked(),
                "no_acpi": self.f_no_acpi.isChecked(),
                "no_hpet": self.f_no_hpet.isChecked(),
                "no_shutdown": self.f_no_shutdown.isChecked(),
                "no_reboot": self.f_no_reboot.isChecked(),
                "daemonize": self.f_daemonize.isChecked(),
                "mem_prealloc": self.f_mem_prealloc.isChecked(),

                "hda": self.f_hda.text(),
                "hdb": self.f_hdb.text(),
                "hdc": self.f_hdc.text(),
                "hdd": self.f_hdd.text(),
                "cdrom": self.f_cdrom.text(),
                "fda": self.f_fda.text(),
                "fdb": self.f_fdb.text(),
                "mtdblock": self.f_mtdblock.text(),
                "pflash": self.f_pflash.text(),
                "sd": self.f_sd.text(),
                "snapshot": self.f_snapshot.isChecked(),
                "boot": self.f_boot.currentText(),

                "net_type": self.f_net_type.currentText(),
                "net_device": self.f_net_device.currentText(),
                "nic": self.f_nic.text(),
                "hostfwd": self.f_hostfwd.text(),
                "hostname": self.f_hostname.text(),
                "redir": self.f_redir.text(),

                "display": self.f_display.currentText(),
                "vga": self.f_vga.currentText(),
                "vnc": self.f_vnc.text(),
                "fullscreen": self.f_fullscreen.isChecked(),

                "usb": self.f_usb.isChecked(),
                "usb_device": self.f_usb_device.currentText(),
                "usbdevice": self.f_usbdevice.text(),
                "kbd_layout": self.f_kbd_layout.text(),

                "kernel": self.f_kernel.text(),
                "initrd": self.f_initrd.text(),
                "append": self.f_append.text(),
                "dtb": self.f_dtb.text(),
                "bios": self.f_bios.text(),
                "L": self.f_L.text(),

                "audio_drv": self.f_audio_drv.currentText(),
                "audiodev": self.f_audiodev.text(),
                "soundhw": self.f_soundhw.currentText(),

                "debug_item": self.f_debug_item.text(),
                "debug_log": self.f_debug_log.text(),
                "gdb": self.f_gdb.text(),
                "trace": self.f_trace.text(),
                "trace_file": self.f_trace_file.text(),

                "object": self.f_object.text(),
                "global": self.f_global.text(),
                "add_fd": self.f_add_fd.text(),
                "device_extra": self.f_device_extra.text(),

                "qemu_path": self.f_qemu_path.text(),
                "extra": self.f_extra.toPlainText()
            }
            with open(p / "config.json", "w", encoding='utf-8') as f:
                json.dump(data, f, indent=4)
            self.refresh_list()
            QMessageBox.information(self, d["success"], d["saved_ok"])
        except (OSError, FileNotFoundError) as exc:
            QMessageBox.critical(self, d["err"], f"Failed to save: {exc}")

    def load_vm(self, name):
        p = self.base_path / name / "config.json"
        if not p.exists():
            return
        try:
            with open(p, "r", encoding='utf-8') as f:
                d = json.load(f)
                self.f_lang.setCurrentIndex(d.get("lang_idx", 0))
                self.f_intuitive.setChecked(d.get("intuitive", False))
                self.retranslate_ui()
                self.f_mode.setCurrentIndex(d.get("mode", 0))
                self.on_mode_changed()
                self.f_name.setText(d.get("name", name))
                self.f_arch.setCurrentText(d.get("arch", "x86_64"))
                self.f_machine.setCurrentText(d.get("machine", "q35"))
                self.f_cpu.setCurrentText(d.get("cpu", "host"))
                self.f_accel.setCurrentText(d.get("accel", "kvm"))
                self.f_ram.setValue(d.get("ram", 2048))
                self.f_smp.setValue(d.get("smp", 2))
                self.f_uuid.setText(d.get("uuid", ""))
                self.f_pidfile.setText(d.get("pidfile", ""))
                self.f_mem_path.setText(d.get("mem_path", ""))
                self.f_numa.setText(d.get("numa", ""))
                self.f_nodefaults.setChecked(d.get("nodefaults", False))
                self.f_no_user_config.setChecked(d.get("no_user_config", False))
                self.f_S.setChecked(d.get("S", False))
                self.f_no_acpi.setChecked(d.get("no_acpi", False))
                self.f_no_hpet.setChecked(d.get("no_hpet", False))
                self.f_no_shutdown.setChecked(d.get("no_shutdown", False))
                self.f_no_reboot.setChecked(d.get("no_reboot", False))
                self.f_daemonize.setChecked(d.get("daemonize", False))
                self.f_mem_prealloc.setChecked(d.get("mem_prealloc", False))

                self.f_hda.setText(d.get("hda", ""))
                self.f_hdb.setText(d.get("hdb", ""))
                self.f_hdc.setText(d.get("hdc", ""))
                self.f_hdd.setText(d.get("hdd", ""))
                self.f_cdrom.setText(d.get("cdrom", ""))
                self.f_fda.setText(d.get("fda", ""))
                self.f_fdb.setText(d.get("fdb", ""))
                self.f_mtdblock.setText(d.get("mtdblock", ""))
                self.f_pflash.setText(d.get("pflash", ""))
                self.f_sd.setText(d.get("sd", ""))
                self.f_snapshot.setChecked(d.get("snapshot", False))
                self.f_boot.setCurrentText(d.get("boot", ""))

                self.f_net_type.setCurrentText(d.get("net_type", "user"))
                self.f_net_device.setCurrentText(d.get("net_device", "virtio-net-pci"))
                self.f_nic.setText(d.get("nic", ""))
                self.f_hostfwd.setText(d.get("hostfwd", ""))
                self.f_hostname.setText(d.get("hostname", ""))
                self.f_redir.setText(d.get("redir", ""))

                self.f_display.setCurrentText(d.get("display", "gtk"))
                self.f_vga.setCurrentText(d.get("vga", "virtio"))
                self.f_vnc.setText(d.get("vnc", ""))
                self.f_fullscreen.setChecked(d.get("fullscreen", False))

                self.f_usb.setChecked(d.get("usb", False))
                self.f_usb_device.setCurrentText(d.get("usb_device", ""))
                self.f_usbdevice.setText(d.get("usbdevice", ""))
                self.f_kbd_layout.setText(d.get("kbd_layout", ""))

                self.f_kernel.setText(d.get("kernel", ""))
                self.f_initrd.setText(d.get("initrd", ""))
                self.f_append.setText(d.get("append", ""))
                self.f_dtb.setText(d.get("dtb", ""))
                self.f_bios.setText(d.get("bios", ""))
                self.f_L.setText(d.get("L", ""))

                self.f_audio_drv.setCurrentText(d.get("audio_drv", "none"))
                self.f_audiodev.setText(d.get("audiodev", ""))
                self.f_soundhw.setCurrentText(d.get("soundhw", "none"))

                self.f_debug_item.setText(d.get("debug_item", ""))
                self.f_debug_log.setText(d.get("debug_log", ""))
                self.f_gdb.setText(d.get("gdb", ""))
                self.f_trace.setText(d.get("trace", ""))
                self.f_trace_file.setText(d.get("trace_file", ""))

                self.f_object.setText(d.get("object", ""))
                self.f_global.setText(d.get("global", ""))
                self.f_add_fd.setText(d.get("add_fd", ""))
                self.f_device_extra.setText(d.get("device_extra", ""))

                self.f_qemu_path.setText(d.get("qemu_path", ""))
                self.f_extra.setPlainText(d.get("extra", ""))
        except (OSError, JSONDecodeError) as exc:
            print(f"Load error: {exc}")
        self.update_preview()

    def refresh_list(self):
        self.vm_list.clear()
        if self.base_path.exists():
            for d in sorted(self.base_path.iterdir()):
                if d.is_dir() and (d / "config.json").exists():
                    self.vm_list.addItem(d.name)

    def select_file(self, line_edit):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select File")
        if file_path:
            line_edit.setText(file_path.replace("\\", "/"))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MguiQemu()
    window.show()
    sys.exit(app.exec())