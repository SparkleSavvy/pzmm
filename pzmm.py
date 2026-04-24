import sys
import os
import json
import subprocess
import shutil
from PyQt6.QtCore import QUrl, QThread, pyqtSignal, Qt
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QWidget, QPushButton, QLineEdit, QTextEdit, QLabel,
                             QListWidget, QProgressBar, QDialog, QFileDialog, QSplitter, 
                             QMessageBox, QCheckBox, QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile

SETTINGS_FILE = "settings.json"
PZ_APP_ID = "108600"

# --- Темная тема (QSS) ---
DARK_STYLESHEET = """
QMainWindow, QDialog, QWidget { background-color: #1e1e2e; color: #cdd6f4; font-family: 'Segoe UI', Arial; }
QLineEdit { background-color: #313244; color: #cdd6f4; border: 1px solid #45475a; padding: 5px; border-radius: 4px; }
QPushButton { background-color: #45475a; color: #cdd6f4; border: none; padding: 8px 15px; border-radius: 4px; font-weight: bold; }
QPushButton:hover { background-color: #585b70; }
QPushButton#NavBtn { padding: 5px 10px; font-size: 16px; background-color: #313244; border: 1px solid #45475a; }
QPushButton#NavBtn:hover { background-color: #585b70; }
QPushButton#ActionBtn { background-color: #89b4fa; color: #11111b; }
QPushButton#ActionBtn:hover { background-color: #b4befe; }
QPushButton#SuccessBtn { background-color: #a6e3a1; color: #11111b; }
QPushButton#SuccessBtn:hover { background-color: #94e2d5; }
QPushButton#WarnBtn { background-color: #f9e2af; color: #11111b; }
QPushButton#WarnBtn:hover { background-color: #f5e0dc; }
QPushButton#DangerBtn { background-color: #f38ba8; color: #11111b; }
QPushButton#DangerBtn:hover { background-color: #eba0ac; }
QListWidget, QTableWidget { background-color: #313244; border: 1px solid #45475a; border-radius: 4px; }
QHeaderView::section { background-color: #1e1e2e; border: 1px solid #45475a; padding: 4px; }
QTabWidget::pane { border: 1px solid #45475a; border-radius: 4px; }
QTabBar::tab { background-color: #313244; padding: 8px 20px; margin-right: 2px; border-top-left-radius: 4px; border-top-right-radius: 4px; }
QTabBar::tab:selected { background-color: #45475a; font-weight: bold; border-bottom: 2px solid #89b4fa; }
QProgressBar { border: 1px solid #45475a; border-radius: 4px; text-align: center; }
QProgressBar::chunk { background-color: #a6e3a1; }
"""

# ================= ФИКС ОШИБОК JS В КОНСОЛИ =================
class SilentWebEnginePage(QWebEnginePage):
    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):
        pass # Игнорируем спам об ошибках CSP от Steam

def load_settings():
    default_game_mods = os.path.expanduser(r"~\Zomboid\mods")
    default_settings = {
        "steamcmd_path": "", "workshop_path": "", "game_mods_path": default_game_mods, "auto_install": True
    }
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r') as f:
            default_settings.update(json.load(f))
    return default_settings

def save_settings(settings):
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f, indent=4)

def parse_mod_info(filepath):
    mod_data = {"id": "", "name": "Неизвестный мод", "require": []}
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if line.startswith("id="): mod_data["id"] = line[3:].strip()
                elif line.startswith("name="): mod_data["name"] = line[5:].strip()
                elif line.startswith("require="):
                    reqs = line[8:].strip()
                    if reqs: mod_data["require"] = [r.strip() for r in reqs.split(',')]
    except Exception: pass
    return mod_data

# ================= ОКНО НАСТРОЕК =================
class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⚙️ Настройки")
        self.resize(600, 250)
        self.settings = load_settings()
        layout = QVBoxLayout(self)

        def add_row(label, key, browse_func):
            row = QHBoxLayout()
            inp = QLineEdit(self.settings.get(key, ""))
            btn = QPushButton("📂")
            btn.setFixedWidth(40)
            btn.clicked.connect(lambda: browse_func(inp))
            row.addWidget(QLabel(label))
            row.addWidget(inp)
            row.addWidget(btn)
            layout.addLayout(row)
            return inp

        self.steam_input = add_row("steamcmd.exe:", "steamcmd_path", self.browse_file)
        self.ws_input = add_row("Папка Workshop (108600):", "workshop_path", self.browse_dir)
        self.game_input = add_row("Папка Zomboid/mods:", "game_mods_path", self.browse_dir)

        self.auto_cb = QCheckBox("Авто-установка в игру после скачивания")
        self.auto_cb.setChecked(self.settings.get("auto_install", True))
        layout.addWidget(self.auto_cb)

        save_btn = QPushButton("💾 Сохранить")
        save_btn.setObjectName("SuccessBtn")
        save_btn.clicked.connect(self.save_and_close)
        layout.addWidget(save_btn, alignment=Qt.AlignmentFlag.AlignRight)

    def browse_file(self, inp):
        path, _ = QFileDialog.getOpenFileName(self, "Выбор файла", "", "Exe (*.exe)")
        if path: inp.setText(path)

    def browse_dir(self, inp):
        path = QFileDialog.getExistingDirectory(self, "Выбор папки")
        if path: inp.setText(path)

    def save_and_close(self):
        self.settings.update({
            "steamcmd_path": self.steam_input.text(),
            "workshop_path": self.ws_input.text(),
            "game_mods_path": self.game_input.text(),
            "auto_install": self.auto_cb.isChecked()
        })
        save_settings(self.settings)
        self.accept()

# ================= КОНСОЛЬ =================
class ConsoleWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Выполнение задач")
        self.resize(700, 450)
        layout = QVBoxLayout(self)
        self.progress_label = QLabel("Ожидание...")
        self.progress_bar = QProgressBar()
        self.log_console = QTextEdit()
        self.log_console.setReadOnly(True)
        self.log_console.setStyleSheet("background-color: #11111b; color: #a6e3a1; font-family: Consolas;")
        layout.addWidget(self.progress_label)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.log_console)

    def update_progress(self, current, total):
        self.progress_label.setText(f"Прогресс: {current} / {total}")
        self.progress_bar.setValue(int((current / total) * 100) if total > 0 else 0)

    def append_log(self, text):
        self.log_console.append(text)
        sb = self.log_console.verticalScrollBar()
        sb.setValue(sb.maximum())

# ================= РАБОЧИЙ ПОТОК =================
class DownloadWorker(QThread):
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int, int)
    finished_signal = pyqtSignal()

    def __init__(self, mod_ids, settings, install_only=False):
        super().__init__()
        self.mod_ids = mod_ids
        self.settings = settings
        self.install_only = install_only

    def run(self):
        steamcmd = self.settings.get("steamcmd_path")
        ws_path = self.settings.get("workshop_path")
        game_path = self.settings.get("game_mods_path")
        auto_inst = self.settings.get("auto_install", True)
        total = len(self.mod_ids)
        self.progress_signal.emit(0, total)

        for i, mod_id in enumerate(self.mod_ids):
            self.log_signal.emit(f"\n--- [{i+1}/{total}] ID: {mod_id} ---")
            if not self.install_only:
                try:
                    cmd = [steamcmd, "+login", "anonymous", "+workshop_download_item", PZ_APP_ID, mod_id, "+quit"]
                    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
                    for line in process.stdout: self.log_signal.emit(line.strip())
                    process.wait()
                except Exception as e:
                    self.log_signal.emit(f"Ошибка SteamCMD: {e}")

            if auto_inst or self.install_only:
                self.install_mod(mod_id, ws_path, game_path)
            self.progress_signal.emit(i + 1, total)

        self.log_signal.emit("\n=== ГОТОВО ===")
        self.finished_signal.emit()

    def install_mod(self, mod_id, ws_path, game_path):
        ws_mods_dir = os.path.join(ws_path, mod_id, "mods")
        if not os.path.exists(ws_mods_dir): return
        os.makedirs(game_path, exist_ok=True)
        for sub_mod in os.listdir(ws_mods_dir):
            src, dst = os.path.join(ws_mods_dir, sub_mod), os.path.join(game_path, sub_mod)
            if os.path.isdir(src):
                try:
                    shutil.copytree(src, dst, dirs_exist_ok=True)
                    self.log_signal.emit(f"✅ Установлен: {sub_mod}")
                except Exception as e: self.log_signal.emit(f"❌ Ошибка копирования {sub_mod}: {e}")

# ================= ГЛАВНОЕ ОКНО =================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PZ Mod Manager")
        self.resize(1200, 750)
        self.setStyleSheet(DARK_STYLESHEET)
        self.console = ConsoleWindow(self)

        # --- Настройка постоянного профиля браузера ---
        # Это сохраняет кэш и логины стима (чтобы не логиниться каждый раз)
        self.browser_profile = QWebEngineProfile.defaultProfile()
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.browser_profile.setPersistentStoragePath(os.path.join(base_dir, "browser_data"))
        self.browser_profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        header_layout = QHBoxLayout()
        title = QLabel("🧟 Project Zomboid Mod Manager")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #89b4fa;")
        settings_btn = QPushButton("⚙️ Настройки")
        settings_btn.setFixedWidth(120)
        settings_btn.clicked.connect(self.open_settings)
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(settings_btn)
        main_layout.addLayout(header_layout)

        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        self.init_workshop_tab()
        self.init_local_mods_tab()

    def init_workshop_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # --- ПАНЕЛЬ НАВИГАЦИИ ---
        url_layout = QHBoxLayout()
        
        btn_back = QPushButton("◀")
        btn_back.setObjectName("NavBtn")
        btn_back.clicked.connect(lambda: self.browser.back())
        
        btn_forward = QPushButton("▶")
        btn_forward.setObjectName("NavBtn")
        btn_forward.clicked.connect(lambda: self.browser.forward())
        
        btn_reload = QPushButton("🔄")
        btn_reload.setObjectName("NavBtn")
        btn_reload.clicked.connect(lambda: self.browser.reload())

        self.url_bar = QLineEdit("https://steamcommunity.com/app/108600/workshop/")
        nav_btn = QPushButton("Перейти")
        nav_btn.clicked.connect(lambda: self.browser.setUrl(QUrl(self.url_bar.text())))
        
        url_layout.addWidget(btn_back)
        url_layout.addWidget(btn_forward)
        url_layout.addWidget(btn_reload)
        url_layout.addWidget(self.url_bar)
        url_layout.addWidget(nav_btn)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # --- БРАУЗЕР ---
        self.browser = QWebEngineView()
        self.browser.setPage(SilentWebEnginePage(self.browser_profile, self.browser)) # Применяем профиль
        self.browser.setUrl(QUrl(self.url_bar.text()))
        self.browser.urlChanged.connect(lambda q: self.url_bar.setText(q.toString()))
        # Подключаем инжектор JS для скрытия табличек Cookie
        self.browser.loadFinished.connect(self.inject_cookie_remover)
        
        splitter.addWidget(self.browser)

        # --- ПРАВАЯ ПАНЕЛЬ ---
        right_panel = QWidget()
        r_layout = QVBoxLayout(right_panel)
        r_layout.setContentsMargins(0,0,0,0)

        add_btn = QPushButton("➕ В очередь")
        add_btn.setObjectName("ActionBtn")
        add_btn.clicked.connect(self.add_to_queue)
        self.queue_list = QListWidget()
        del_btn = QPushButton("Убрать из очереди")
        del_btn.clicked.connect(lambda: [self.queue_list.takeItem(self.queue_list.row(i)) for i in self.queue_list.selectedItems()])
        
        dl_btn = QPushButton("🚀 Скачать очередь")
        dl_btn.setObjectName("SuccessBtn")
        dl_btn.clicked.connect(self.start_download)

        upd_btn = QPushButton("🔄 Обновить скачанные")
        upd_btn.setObjectName("WarnBtn")
        upd_btn.clicked.connect(self.update_all)

        r_layout.addWidget(add_btn)
        r_layout.addWidget(QLabel("Очередь (Workshop IDs):"))
        r_layout.addWidget(self.queue_list)
        r_layout.addWidget(del_btn)
        r_layout.addWidget(dl_btn)
        r_layout.addWidget(QLabel("База:"))
        r_layout.addWidget(upd_btn)
        
        splitter.addWidget(right_panel)
        splitter.setSizes([850, 300])
        layout.addLayout(url_layout)
        layout.addWidget(splitter)
        self.tabs.addTab(tab, "🌐 Мастерская")

    # --- ИНЖЕКТОР СКРИПТОВ (Магия решения проблемы с куки) ---
    def inject_cookie_remover(self, ok):
        if ok:
            js = """
            // Ищем и скрываем темный фон и саму табличку с куки от Steam
            var bg = document.getElementById('cookie_prefs_popup_background');
            var popup = document.getElementById('cookie_prefs_popup');
            if(bg) bg.style.display = 'none';
            if(popup) popup.style.display = 'none';
            
            // Если Steam блокирует прокрутку колесиком при появлении таблички - возвращаем ее
            document.body.style.overflow = 'auto';
            """
            self.browser.page().runJavaScript(js)

    def init_local_mods_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        top_layout = QHBoxLayout()
        refresh_btn = QPushButton("🔄 Обновить список")
        refresh_btn.setObjectName("ActionBtn")
        refresh_btn.clicked.connect(self.load_local_mods)

        open_folder_btn = QPushButton("📂 Открыть папку")
        open_folder_btn.clicked.connect(self.open_mods_folder)

        del_selected_btn = QPushButton("🗑️ Удалить выбранные")
        del_selected_btn.setObjectName("WarnBtn")
        del_selected_btn.clicked.connect(self.delete_selected_mods)

        del_all_btn = QPushButton("⚠️ Удалить ВСЕ")
        del_all_btn.setObjectName("DangerBtn")
        del_all_btn.clicked.connect(self.delete_all_mods)

        top_layout.addWidget(refresh_btn)
        top_layout.addWidget(open_folder_btn)
        top_layout.addStretch()
        top_layout.addWidget(del_selected_btn)
        top_layout.addWidget(del_all_btn)

        self.mods_table = QTableWidget()
        self.mods_table.setColumnCount(4)
        self.mods_table.setHorizontalHeaderLabels(["Название мода", "Внутренний ID", "Требуемые моды", "Статус зависимостей"])
        self.mods_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.mods_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.mods_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.mods_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.mods_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.mods_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        layout.addLayout(top_layout)
        layout.addWidget(self.mods_table)
        self.tabs.addTab(tab, "📦 Установленные моды (В игре)")
        
        self.load_local_mods()

    def load_local_mods(self):
        settings = load_settings()
        game_path = settings.get("game_mods_path")
        if not game_path or not os.path.exists(game_path):
            self.mods_table.setRowCount(0)
            return

        mods_info = []
        installed_ids = set()

        for folder in os.listdir(game_path):
            folder_path = os.path.join(game_path, folder)
            info_path = os.path.join(folder_path, "mod.info")
            if os.path.exists(info_path):
                data = parse_mod_info(info_path)
                if data["id"]:
                    data["folder_path"] = folder_path 
                    mods_info.append(data)
                    installed_ids.add(data["id"])

        self.mods_table.setRowCount(len(mods_info))
        for row, mod in enumerate(mods_info):
            name_item = QTableWidgetItem(mod["name"])
            name_item.setData(Qt.ItemDataRole.UserRole, mod["folder_path"]) 
            self.mods_table.setItem(row, 0, name_item)
            
            self.mods_table.setItem(row, 1, QTableWidgetItem(mod["id"]))
            req_str = ", ".join(mod["require"]) if mod["require"] else "Нет"
            self.mods_table.setItem(row, 2, QTableWidgetItem(req_str))

            if not mod["require"]:
                status_item = QTableWidgetItem("✅ Ок")
                status_item.setForeground(Qt.GlobalColor.green)
            else:
                missing = [r for r in mod["require"] if r not in installed_ids]
                if not missing:
                    status_item = QTableWidgetItem("✅ Все установлены")
                    status_item.setForeground(Qt.GlobalColor.green)
                else:
                    status_item = QTableWidgetItem(f"❌ Нет: {', '.join(missing)}")
                    status_item.setForeground(Qt.GlobalColor.red)
            
            self.mods_table.setItem(row, 3, status_item)

    def open_mods_folder(self):
        game_path = load_settings().get("game_mods_path")
        if game_path and os.path.exists(game_path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(game_path))
        else:
            QMessageBox.warning(self, "Ошибка", "Папка модов не найдена. Проверьте настройки.")

    def delete_selected_mods(self):
        selected_rows = set(item.row() for item in self.mods_table.selectedItems())
        if not selected_rows: return

        reply = QMessageBox.question(self, "Подтверждение", f"Удалить {len(selected_rows)} выбранных модов?", 
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            for row in selected_rows:
                folder_path = self.mods_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
                if folder_path and os.path.exists(folder_path):
                    try: shutil.rmtree(folder_path)
                    except Exception as e: print(f"Ошибка удаления {folder_path}: {e}")
            self.load_local_mods()

    def delete_all_mods(self):
        game_path = load_settings().get("game_mods_path")
        if not game_path or not os.path.exists(game_path): return

        reply = QMessageBox.warning(self, "ВНИМАНИЕ", 
            "Вы уверены, что хотите УДАЛИТЬ ВСЕ МОДЫ из папки игры?\nЭто действие нельзя отменить!", 
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            for folder in os.listdir(game_path):
                folder_path = os.path.join(game_path, folder)
                if os.path.isdir(folder_path):
                    try: shutil.rmtree(folder_path)
                    except Exception as e: print(f"Ошибка удаления {folder_path}: {e}")
            self.load_local_mods()

    def open_settings(self):
        if SettingsDialog(self).exec():
            self.load_local_mods()

    def add_to_queue(self):
        import re
        match = re.search(r'id=(\d+)', self.url_bar.text())
        if match:
            mid = match.group(1)
            if not self.queue_list.findItems(mid, Qt.MatchFlag.MatchExactly):
                self.queue_list.addItem(mid)
        else: QMessageBox.warning(self, "Ошибка", "Не найден ID мода в URL.")

    def start_download(self):
        if self.queue_list.count() == 0: return
        ids = [self.queue_list.item(i).text() for i in range(self.queue_list.count())]
        self.queue_list.clear()
        self.run_task(ids, False)

    def update_all(self):
        ws_path = load_settings().get("workshop_path")
        if not ws_path or not os.path.exists(ws_path): return
        ids = [d for d in os.listdir(ws_path) if os.path.isdir(os.path.join(ws_path, d)) and d.isdigit()]
        if ids: self.run_task(ids, False)

    def run_task(self, ids, install_only):
        self.console.show()
        self.console.log_console.clear()
        self.worker = DownloadWorker(ids, load_settings(), install_only)
        self.worker.log_signal.connect(self.console.append_log)
        self.worker.progress_signal.connect(self.console.update_progress)
        self.worker.finished_signal.connect(self.on_task_finished)
        self.worker.start()

    def on_task_finished(self):
        QMessageBox.information(self, "Готово", "Все задачи выполнены!")
        self.load_local_mods()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())