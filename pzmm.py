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
                             QMessageBox, QCheckBox, QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView, QComboBox)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile

# --- НАСТРОЙКИ ---
def get_base_dir():
    if getattr(sys, 'frozen', False): return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

SETTINGS_FILE = os.path.join(get_base_dir(), "settings.json")
LOCALES_DIR = os.path.join(get_base_dir(), "locales")
PZ_APP_ID = "108600"

# --- Темная тема (QSS) ---
DARK_STYLESHEET = """
QMainWindow, QDialog, QWidget { background-color: #1e1e2e; color: #cdd6f4; font-family: 'Segoe UI', Arial; }
QLineEdit, QComboBox { background-color: #313244; color: #cdd6f4; border: 1px solid #45475a; padding: 5px; border-radius: 4px; }
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

# ================= ЛОКАЛИЗАЦИЯ =================
DEFAULT_LANG = {
    "app_title": "🌸 Project Zomboid Mod Manager",
    "btn_settings": "⚙️ Настройки",
    "tab_workshop": "🌐 Мастерская",
    "tab_mods": "📦 Установленные моды",
    "tab_trouble": "🛠️ Траблшутинг",
    "btn_nav_go": "Перейти",
    "btn_add_queue": "➕ В очередь",
    "btn_rem_queue": "Убрать из очереди",
    "btn_dl_queue": "🚀 Скачать очередь",
    "btn_update_all": "🔄 Обновить скачанные",
    "lbl_queue": "Очередь (Workshop IDs):",
    "lbl_db": "База:",
    "btn_refresh": "🔄 Обновить список",
    "btn_open_folder": "📂 Открыть папку",
    "btn_del_sel": "🗑️ Удалить выбранные",
    "btn_del_all": "⚠️ Удалить ВСЕ",
    "tbl_name": "Название мода",
    "tbl_id": "Внутренний ID",
    "tbl_req": "Требуемые моды",
    "tbl_status": "Статус зависимостей",
    "stat_ok": "✅ Ок",
    "stat_all_inst": "✅ Все установлены",
    "stat_miss": "❌ Нет: {miss}",
    "txt_none": "Нет",
    "msg_done": "Готово",
    "msg_all_done": "Все задачи выполнены!",
    "msg_err": "Ошибка",
    "msg_err_id": "Не найден ID мода в URL.",
    "msg_err_folder": "Папка модов не найдена. Проверьте настройки.",
    "msg_conf": "Подтверждение",
    "msg_conf_del": "Удалить {count} выбранных модов?",
    "msg_warn": "ВНИМАНИЕ",
    "msg_warn_del_all": "Вы уверены, что хотите УДАЛИТЬ ВСЕ МОДЫ из папки игры?\nЭто действие нельзя отменить!",
    "set_title": "⚙️ Настройки",
    "set_steamcmd": "steamcmd.exe:",
    "set_ws": "Папка Workshop (108600):",
    "set_game": "Папка Zomboid/mods:",
    "set_auto": "Авто-установка в игру",
    "set_lang": "Язык интерфейса:",
    "set_save": "💾 Сохранить",
    "cons_title": "Выполнение задач",
    "cons_wait": "Ожидание...",
    "cons_prog": "Прогресс: {cur} / {tot}",
    "log_start": "\n--- [{cur}/{tot}] ID: {mod_id} ---",
    "log_err_st": "Ошибка SteamCMD: {e}",
    "log_ok_inst": "✅ Установлен: {sub}",
    "log_err_inst": "❌ Ошибка копирования {sub}: {e}",
    "log_done": "\n=== ГОТОВО ===",
    "trb_analyze": "🔍 Анализ console.txt",
    "trb_clear_lua": "🧹 Очистить кэш Lua (Фикс UI)",
    "trb_clear_logs": "🗑️ Удалить старые логи",
    "trb_log_title": "Анализ логов игры (Ошибки и конфликты):",
    "trb_no_log": "Файл console.txt не найден. Запустите игру хотя бы один раз.",
    "trb_no_errors": "✅ Ошибок Lua или крашей в последней сессии не найдено! Игра работает стабильно.",
    "trb_found_errors": "⚠️ НАЙДЕНЫ ОШИБКИ ({count} шт.):\nВозможно конфликтуют моды.\n\n",
    "trb_lua_ok": "Папка Lua кэша успешно удалена. При следующем запуске игры интерфейс пересоберется с нуля.",
    "trb_logs_ok": "Старые логи игры успешно удалены. Освобождено место на диске."
}

LANG_DICT = {}

def tr(key, **kwargs):
    text = LANG_DICT.get(key, DEFAULT_LANG.get(key, key))
    try: return text.format(**kwargs)
    except Exception: return text

def load_language(lang_code="ru"):
    os.makedirs(LOCALES_DIR, exist_ok=True)
    ru_path = os.path.join(LOCALES_DIR, "ru.json")
    if not os.path.exists(ru_path):
        with open(ru_path, 'w', encoding='utf-8') as f:
            json.dump(DEFAULT_LANG, f, indent=4, ensure_ascii=False)
            
    lang_path = os.path.join(LOCALES_DIR, f"{lang_code}.json")
    if os.path.exists(lang_path):
        with open(lang_path, 'r', encoding='utf-8') as f:
            global LANG_DICT
            LANG_DICT = json.load(f)
    else: LANG_DICT = DEFAULT_LANG

def get_available_languages():
    if not os.path.exists(LOCALES_DIR): return ["ru"]
    return [f.replace(".json", "") for f in os.listdir(LOCALES_DIR) if f.endswith(".json")]

# ================= НАСТРОЙКИ =================
def load_settings():
    def_mods = os.path.expanduser(r"~\Zomboid\mods")
    s = {"steamcmd_path": "", "workshop_path": "", "game_mods_path": def_mods, "auto_install": True, "language": "ru"}
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r') as f: s.update(json.load(f))
    return s

def save_settings(s):
    with open(SETTINGS_FILE, 'w') as f: json.dump(s, f, indent=4)

load_language(load_settings().get("language", "ru"))

class SilentWebEnginePage(QWebEnginePage):
    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID): pass

def parse_mod_info(filepath):
    data = {"id": "", "name": "Unknown Mod", "require": []}
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if line.startswith("id="): data["id"] = line[3:].strip()
                elif line.startswith("name="): data["name"] = line[5:].strip()
                elif line.startswith("require="):
                    r = line[8:].strip()
                    if r: data["require"] = [x.strip() for x in r.split(',')]
    except: pass
    return data

# ================= ОКНО НАСТРОЕК =================
class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("set_title"))
        self.resize(600, 300)
        self.settings = load_settings()
        layout = QVBoxLayout(self)

        def add_row(lbl, key, browse):
            row = QHBoxLayout()
            inp = QLineEdit(self.settings.get(key, ""))
            btn = QPushButton("📂")
            btn.setFixedWidth(40)
            btn.clicked.connect(lambda: browse(inp))
            row.addWidget(QLabel(lbl))
            row.addWidget(inp)
            row.addWidget(btn)
            layout.addLayout(row)
            return inp

        self.st_inp = add_row(tr("set_steamcmd"), "steamcmd_path", self.br_f)
        self.ws_inp = add_row(tr("set_ws"), "workshop_path", self.br_d)
        self.gm_inp = add_row(tr("set_game"), "game_mods_path", self.br_d)

        self.auto_cb = QCheckBox(tr("set_auto"))
        self.auto_cb.setChecked(self.settings.get("auto_install", True))
        layout.addWidget(self.auto_cb)

        lang_lay = QHBoxLayout()
        self.lang_cb = QComboBox()
        self.lang_cb.addItems(get_available_languages())
        self.lang_cb.setCurrentText(self.settings.get("language", "ru"))
        lang_lay.addWidget(QLabel(tr("set_lang")))
        lang_lay.addWidget(self.lang_cb)
        layout.addLayout(lang_lay)

        sv_btn = QPushButton(tr("set_save"))
        sv_btn.setObjectName("SuccessBtn")
        sv_btn.clicked.connect(self.save_close)
        layout.addWidget(sv_btn, alignment=Qt.AlignmentFlag.AlignRight)

    def br_f(self, i): 
        p, _ = QFileDialog.getOpenFileName(self, "", "", "Exe (*.exe)")
        if p: i.setText(p)
    def br_d(self, i): 
        p = QFileDialog.getExistingDirectory(self, "")
        if p: i.setText(p)

    def save_close(self):
        self.settings.update({
            "steamcmd_path": self.st_inp.text(),
            "workshop_path": self.ws_inp.text(),
            "game_mods_path": self.gm_inp.text(),
            "auto_install": self.auto_cb.isChecked(),
            "language": self.lang_cb.currentText()
        })
        save_settings(self.settings)
        QMessageBox.information(self, tr("msg_done"), tr("msg_done") + "\nПерезапустите программу для смены языка.")
        self.accept()

# ================= КОНСОЛЬ =================
class ConsoleWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("cons_title"))
        self.resize(700, 450)
        lay = QVBoxLayout(self)
        self.lbl = QLabel(tr("cons_wait"))
        self.bar = QProgressBar()
        self.txt = QTextEdit()
        self.txt.setReadOnly(True)
        self.txt.setStyleSheet("background-color: #11111b; color: #a6e3a1; font-family: Consolas;")
        lay.addWidget(self.lbl)
        lay.addWidget(self.bar)
        lay.addWidget(self.txt)

    def update_prog(self, c, t):
        self.lbl.setText(tr("cons_prog", cur=c, tot=t))
        self.bar.setValue(int((c/t)*100) if t>0 else 0)

    def add_log(self, t):
        self.txt.append(t)
        sb = self.txt.verticalScrollBar()
        sb.setValue(sb.maximum())

# ================= ВОРКЕР =================
class DownloadWorker(QThread):
    log_sig = pyqtSignal(str)
    prog_sig = pyqtSignal(int, int)
    fin_sig = pyqtSignal()

    def __init__(self, ids, s, only_inst=False):
        super().__init__()
        self.ids = ids
        self.s = s
        self.only_inst = only_inst

    def run(self):
        st = self.s.get("steamcmd_path")
        ws = self.s.get("workshop_path")
        gm = self.s.get("game_mods_path")
        auto = self.s.get("auto_install", True)
        tot = len(self.ids)
        self.prog_sig.emit(0, tot)

        for i, mid in enumerate(self.ids):
            self.log_sig.emit(tr("log_start", cur=i+1, tot=tot, mod_id=mid))
            if not self.only_inst:
                try:
                    c = [st, "+login", "anonymous", "+workshop_download_item", PZ_APP_ID, mid, "+quit"]
                    p = subprocess.Popen(c, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
                    for l in p.stdout: self.log_sig.emit(l.strip())
                    p.wait()
                except Exception as e: self.log_sig.emit(tr("log_err_st", e=e))

            if auto or self.only_inst: self.install(mid, ws, gm)
            self.prog_sig.emit(i+1, tot)
        self.log_sig.emit(tr("log_done"))
        self.fin_sig.emit()

    def install(self, mid, ws, gm):
        ws_m = os.path.join(ws, mid, "mods")
        if not os.path.exists(ws_m): return
        os.makedirs(gm, exist_ok=True)
        for sub in os.listdir(ws_m):
            src, dst = os.path.join(ws_m, sub), os.path.join(gm, sub)
            if os.path.isdir(src):
                try:
                    shutil.copytree(src, dst, dirs_exist_ok=True)
                    self.log_sig.emit(tr("log_ok_inst", sub=sub))
                except Exception as e: self.log_sig.emit(tr("log_err_inst", sub=sub, e=e))

# ================= ГЛАВНОЕ ОКНО =================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(tr("PZMM"))
        self.resize(1200, 750)
        self.setStyleSheet(DARK_STYLESHEET)
        self.cons = ConsoleWindow(self)

        self.prof = QWebEngineProfile.defaultProfile()
        self.prof.setPersistentStoragePath(os.path.join(get_base_dir(), "browser_data"))
        self.prof.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies)

        cen = QWidget()
        self.setCentralWidget(cen)
        lay = QVBoxLayout(cen)

        head = QHBoxLayout()
        ttl = QLabel(tr("app_title"))
        ttl.setStyleSheet("font-size: 18px; font-weight: bold; color: #89b4fa;")
        set_btn = QPushButton(tr("btn_settings"))
        set_btn.clicked.connect(self.op_set)
        head.addWidget(ttl); head.addStretch(); head.addWidget(set_btn)
        lay.addLayout(head)

        self.tabs = QTabWidget()
        lay.addWidget(self.tabs)
        
        self.init_ws_tab()
        self.init_mod_tab()
        self.init_trouble_tab() # НОВАЯ ВКЛАДКА

    # --- Вкладка 1: Мастерская ---
    def init_ws_tab(self):
        t = QWidget()
        lay = QVBoxLayout(t)
        u_lay = QHBoxLayout()
        for b_txt, f in [("◀", lambda: self.bw.back()), ("▶", lambda: self.bw.forward()), ("🔄", lambda: self.bw.reload())]:
            b = QPushButton(b_txt); b.setObjectName("NavBtn"); b.clicked.connect(f); u_lay.addWidget(b)

        self.url = QLineEdit("https://steamcommunity.com/app/108600/workshop/")
        n_btn = QPushButton(tr("btn_nav_go"))
        n_btn.clicked.connect(lambda: self.bw.setUrl(QUrl(self.url.text())))
        u_lay.addWidget(self.url); u_lay.addWidget(n_btn)

        spl = QSplitter(Qt.Orientation.Horizontal)
        self.bw = QWebEngineView()
        self.bw.setPage(SilentWebEnginePage(self.prof, self.bw))
        self.bw.setUrl(QUrl(self.url.text()))
        self.bw.urlChanged.connect(lambda q: self.url.setText(q.toString()))
        self.bw.loadFinished.connect(self.inj_js)
        spl.addWidget(self.bw)

        rp = QWidget(); r_lay = QVBoxLayout(rp); r_lay.setContentsMargins(0,0,0,0)
        ad = QPushButton(tr("btn_add_queue")); ad.setObjectName("ActionBtn"); ad.clicked.connect(self.add_q)
        self.q_list = QListWidget()
        rm = QPushButton(tr("btn_rem_queue")); rm.clicked.connect(lambda: [self.q_list.takeItem(self.q_list.row(i)) for i in self.q_list.selectedItems()])
        dl = QPushButton(tr("btn_dl_queue")); dl.setObjectName("SuccessBtn"); dl.clicked.connect(self.dl_q)
        up = QPushButton(tr("btn_update_all")); up.setObjectName("WarnBtn"); up.clicked.connect(self.up_all)
        
        for w in [ad, QLabel(tr("lbl_queue")), self.q_list, rm, dl, QLabel(tr("lbl_db")), up]: r_lay.addWidget(w)
        spl.addWidget(rp); spl.setSizes([850, 300])
        lay.addLayout(u_lay); lay.addWidget(spl)
        self.tabs.addTab(t, tr("tab_workshop"))

    def inj_js(self, ok):
        if ok: self.bw.page().runJavaScript("var b=document.getElementById('cookie_prefs_popup_background'),p=document.getElementById('cookie_prefs_popup');if(b)b.style.display='none';if(p)p.style.display='none';document.body.style.overflow='auto';")

    # --- Вкладка 2: Моды ---
    def init_mod_tab(self):
        t = QWidget(); lay = QVBoxLayout(t)
        top = QHBoxLayout()
        rf = QPushButton(tr("btn_refresh")); rf.setObjectName("ActionBtn"); rf.clicked.connect(self.ld_mods)
        op = QPushButton(tr("btn_open_folder")); op.clicked.connect(self.op_fld)
        ds = QPushButton(tr("btn_del_sel")); ds.setObjectName("WarnBtn"); ds.clicked.connect(self.del_s)
        da = QPushButton(tr("btn_del_all")); da.setObjectName("DangerBtn"); da.clicked.connect(self.del_a)
        top.addWidget(rf); top.addWidget(op); top.addStretch(); top.addWidget(ds); top.addWidget(da)

        self.tb = QTableWidget()
        self.tb.setColumnCount(4)
        self.tb.setHorizontalHeaderLabels([tr("tbl_name"), tr("tbl_id"), tr("tbl_req"), tr("tbl_status")])
        self.tb.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.tb.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.tb.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.tb.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.tb.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tb.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        lay.addLayout(top); lay.addWidget(self.tb)
        self.tabs.addTab(t, tr("tab_mods"))
        self.ld_mods()

    # --- Вкладка 3: Траблшутинг (НОВАЯ) ---
    def init_trouble_tab(self):
        t = QWidget()
        lay = QVBoxLayout(t)
        
        # Кнопки быстрых действий
        actions_lay = QHBoxLayout()
        
        btn_analyze = QPushButton(tr("trb_analyze"))
        btn_analyze.setObjectName("ActionBtn")
        btn_analyze.clicked.connect(self.analyze_logs)
        
        btn_clear_lua = QPushButton(tr("trb_clear_lua"))
        btn_clear_lua.setObjectName("WarnBtn")
        btn_clear_lua.clicked.connect(self.clear_lua_cache)
        
        btn_clear_logs = QPushButton(tr("trb_clear_logs"))
        btn_clear_logs.setObjectName("DangerBtn")
        btn_clear_logs.clicked.connect(self.clear_game_logs)
        
        actions_lay.addWidget(btn_analyze)
        actions_lay.addWidget(btn_clear_lua)
        actions_lay.addWidget(btn_clear_logs)
        actions_lay.addStretch()
        
        # Окно вывода логов
        self.trouble_console = QTextEdit()
        self.trouble_console.setReadOnly(True)
        self.trouble_console.setStyleSheet("background-color: #11111b; color: #cdd6f4; font-family: Consolas; font-size: 13px;")
        
        lay.addLayout(actions_lay)
        lay.addWidget(QLabel(tr("trb_log_title")))
        lay.addWidget(self.trouble_console)
        
        self.tabs.addTab(t, tr("tab_trouble"))

    # --- Логика Траблшутинга ---
    def analyze_logs(self):
        self.trouble_console.clear()
        zomboid_dir = os.path.expanduser(r"~\Zomboid")
        console_path = os.path.join(zomboid_dir, "console.txt")
        
        if not os.path.exists(console_path):
            self.trouble_console.append(f"<span style='color: yellow;'>{tr('trb_no_log')}</span>")
            return
            
        errors_found = []
        try:
            # Читаем только последние 10000 строк, чтобы не повесить UI
            with open(console_path, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.readlines()[-10000:]
                
            for line in lines:
                # Ищем критические маркеры ошибок PZ
                if "ERROR:" in line or "Exception" in line or "STACK TRACE" in line or "failed to load" in line:
                    errors_found.append(line.strip())
                    
            if not errors_found:
                self.trouble_console.append(f"<span style='color: #a6e3a1;'>{tr('trb_no_errors')}</span>")
            else:
                self.trouble_console.append(f"<span style='color: #f38ba8; font-weight: bold;'>{tr('trb_found_errors', count=len(errors_found))}</span>")
                # Выводим уникальные ошибки (чтобы не спамить одинаковыми)
                unique_errors = list(dict.fromkeys(errors_found))[:50] # Показываем макс 50
                for err in unique_errors:
                    self.trouble_console.append(f"<span style='color: #eba0ac;'>- {err}</span>")
                    
        except Exception as e:
            self.trouble_console.append(f"<span style='color: red;'>Ошибка чтения логов: {e}</span>")

    def clear_lua_cache(self):
        lua_dir = os.path.expanduser(r"~\Zomboid\Lua")
        if os.path.exists(lua_dir):
            try:
                shutil.rmtree(lua_dir, ignore_errors=True)
                QMessageBox.information(self, tr("msg_done"), tr("trb_lua_ok"))
            except Exception as e:
                QMessageBox.critical(self, tr("msg_err"), str(e))
        else:
            QMessageBox.information(self, "Info", "Кэш Lua уже чист.")

    def clear_game_logs(self):
        logs_dir = os.path.expanduser(r"~\Zomboid\Logs")
        console_txt = os.path.expanduser(r"~\Zomboid\console.txt")
        
        cleared = False
        if os.path.exists(logs_dir):
            shutil.rmtree(logs_dir, ignore_errors=True)
            cleared = True
        if os.path.exists(console_txt):
            try: os.remove(console_txt); cleared = True
            except: pass
            
        if cleared:
            QMessageBox.information(self, tr("msg_done"), tr("trb_logs_ok"))
        else:
            QMessageBox.information(self, "Info", "Папка с логами уже пуста.")

    # --- Функции Вкладки 2 ---
    def ld_mods(self):
        p = load_settings().get("game_mods_path")
        if not p or not os.path.exists(p): self.tb.setRowCount(0); return
        mi, ids = [], set()
        for f in os.listdir(p):
            fp = os.path.join(p, f)
            inf = os.path.join(fp, "mod.info")
            if os.path.exists(inf):
                d = parse_mod_info(inf)
                if d["id"]: d["fp"] = fp; mi.append(d); ids.add(d["id"])
        
        self.tb.setRowCount(len(mi))
        for r, m in enumerate(mi):
            n = QTableWidgetItem(m["name"]); n.setData(Qt.ItemDataRole.UserRole, m["fp"])
            self.tb.setItem(r, 0, n)
            self.tb.setItem(r, 1, QTableWidgetItem(m["id"]))
            self.tb.setItem(r, 2, QTableWidgetItem(", ".join(m["require"]) if m["require"] else tr("txt_none")))

            if not m["require"]: st = QTableWidgetItem(tr("stat_ok")); st.setForeground(Qt.GlobalColor.green)
            else:
                ms = [x for x in m["require"] if x not in ids]
                if not ms: st = QTableWidgetItem(tr("stat_all_inst")); st.setForeground(Qt.GlobalColor.green)
                else: st = QTableWidgetItem(tr("stat_miss", miss=", ".join(ms))); st.setForeground(Qt.GlobalColor.red)
            self.tb.setItem(r, 3, st)

    def op_fld(self):
        p = load_settings().get("game_mods_path")
        if p and os.path.exists(p): QDesktopServices.openUrl(QUrl.fromLocalFile(p))
        else: QMessageBox.warning(self, tr("msg_err"), tr("msg_err_folder"))

    def del_s(self):
        sr = set(i.row() for i in self.tb.selectedItems())
        if not sr: return
        if QMessageBox.question(self, tr("msg_conf"), tr("msg_conf_del", count=len(sr))) == QMessageBox.StandardButton.Yes:
            for r in sr:
                p = self.tb.item(r, 0).data(Qt.ItemDataRole.UserRole)
                if p and os.path.exists(p): shutil.rmtree(p, ignore_errors=True)
            self.ld_mods()

    def del_a(self):
        p = load_settings().get("game_mods_path")
        if not p or not os.path.exists(p): return
        if QMessageBox.warning(self, tr("msg_warn"), tr("msg_warn_del_all"), QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            for f in os.listdir(p):
                fp = os.path.join(p, f)
                if os.path.isdir(fp): shutil.rmtree(fp, ignore_errors=True)
            self.ld_mods()

    # --- Функции Вкладки 1 ---
    def op_set(self):
        if SettingsDialog(self).exec(): self.ld_mods()

    def add_q(self):
        import re
        m = re.search(r'id=(\d+)', self.url.text())
        if m:
            if not self.q_list.findItems(m.group(1), Qt.MatchFlag.MatchExactly): self.q_list.addItem(m.group(1))
        else: QMessageBox.warning(self, tr("msg_err"), tr("msg_err_id"))

    def dl_q(self):
        if self.q_list.count() == 0: return
        ids = [self.q_list.item(i).text() for i in range(self.q_list.count())]; self.q_list.clear(); self.rn(ids, False)

    def up_all(self):
        p = load_settings().get("workshop_path")
        if p and os.path.exists(p):
            ids = [d for d in os.listdir(p) if os.path.isdir(os.path.join(p, d)) and d.isdigit()]
            if ids: self.rn(ids, False)

    def rn(self, ids, oi):
        self.cons.show(); self.cons.txt.clear()
        self.w = DownloadWorker(ids, load_settings(), oi)
        self.w.log_sig.connect(self.cons.add_log); self.w.prog_sig.connect(self.cons.update_prog); self.w.fin_sig.connect(self.fin)
        self.w.start()

    def fin(self):
        QMessageBox.information(self, tr("msg_done"), tr("msg_all_done")); self.ld_mods()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    w = MainWindow(); w.show()
    sys.exit(app.exec())