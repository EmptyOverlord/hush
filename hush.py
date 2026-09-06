# -*- coding: utf-8 -*-
"""
HUSH — окно для auto-editor.
Вырезает паузы из видео. Работает на macOS и Windows.

Запуск:  python3 tishina.py [файлы...]
"""

import json
import math
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import tkinter as tk
import webbrowser
from tkinter import filedialog
from queue import Queue, Empty

IS_WIN = platform.system() == "Windows"
IS_MAC = platform.system() == "Darwin"
HERE = os.path.dirname(os.path.abspath(__file__))
FISH_URL = "https://EmptyOverlord.com"

ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
VIDEO_EXT = (".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v", ".wmv", ".flv",
             ".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg")


# ──────────────────────────────────────────────────────────── языки

STRINGS = {
    "ru": {
        "app": "HUSH",
        "tagline": "вырезает паузы из видео",
        "title": "HUSH — вырезает паузы из видео",
        "update": "Обновить движок",
        "engine": "движок {v} · {where}",
        "bundled": "встроенный",
        "updated": "обновлённый",
        "no_engine": "движок не найден",

        "files": "файлы",
        "settings": "настройки",
        "defaults": "По умолчанию",
        "add": "Добавить файлы",
        "remove": "Убрать",
        "clear": "Очистить",
        "drop_hint": "Перетащи сюда файлы или нажми «Добавить файлы»",
        "no_dnd": "Нажми «Добавить файлы» — перетаскивание недоступно",

        "smooth": "Сглаживание",
        "smooth_hint": "склеивает микро-резы, чтобы речь не дёргалась",
        "smooth_off": "выключено",
        "speed": "Скорость речи",
        "speed_hint": "ускоряет саму речь, а не паузы",
        "speed_normal": "как есть",
        "motion_sens": "Чувствительность движения",
        "motion_hint": "меньше — замечает мелкие шевеления",
        "tab_subs": "Субтитры",
        "model": "Модель распознавания",
        "model_hint": "для русского бери от turbo-q5",
        "model_missing": "не скачана",
        "model_ready": "готова",
        "dl_model": "Скачать модель",
        "subs_lang": "Язык речи",
        "lang_auto": "Определить",
        "lang_ru": "Русский",
        "lang_en": "Английский",
        "subs_fmt": "Формат",
        "fmt_srt": "SRT (субтитры)",
        "fmt_text": "Просто текст",
        "subs_words": "По одному слову — для Shorts",
        "words_hint": "каждое слово отдельной строкой со своим таймингом",
        "subs_tr": "Перевести на английский",
        "tr_hint": "говоришь по-русски — субтитры выходят английскими",
        "subs_btn": "Сделать субтитры",
        "subs_note": "Отдельное действие. Субтитры берутся из исходника, "
                     "не из обработанного файла.",
        "head_subs": "── Распознаю речь ──",
        "subs_need_model": "Сначала скачай модель на вкладке «Субтитры».",
        "subs_done": "     готово → {name}",
        "subs_dl": "  Качаю модель {m}, {mb}. Один раз, потом лежит на диске.",
        "subs_dl_ok": "  Модель готова.",
        "subs_slow": "  Распознавание идёт примерно со скоростью видео. Наберись терпения.",
        "tab_cut": "Резка",
        "tab_fine": "Точнее",
        "tab_out": "Вывод",
        "detect": "По чему резать",
        "det_audio": "По звуку",
        "det_both": "Звук и движение",
        "det_motion": "По движению",
        "det_hint_audio": "оставляем там, где говорят",
        "det_hint_both": "оставляем, где говорят или что-то движется — для записей экрана",
        "det_hint_motion": "оставляем, где картинка меняется; звук не учитывается",
        "black": "Убирать чёрные кадры",
        "black_hint": "выкидывает затемнения и совсем тёмные куски: заставки, "
                      "склейки, закрытый объектив",
        "trans": "Плавные переходы",
        "trans_hint": "растворение на месте резов вместо жёсткой склейки",
        "trans_len": "Длина перехода",
        "trans_fail": "     Переход длиннее, чем куски между резами. Уменьши длину перехода.",
        "soft": "Мягко",
        "normal": "Обычно",
        "tight": "Плотно",
        "margin": "Воздух по краям",
        "margin_hint": "сколько тишины оставить вокруг слов",
        "unit_sec": "сек",
        "thresh": "Порог тишины",
        "thresh_hint": "тише этого — считается молчанием",
        "silence": "Что делать с тишиной",
        "cut": "Вырезать",
        "speed2": "Ускорить ×2",
        "speed4": "Ускорить ×4",
        "output": "Что на выходе",
        "video": "Готовое видео",
        "out_video": "Готовый файл. Быстро, но правки уже не внести.",
        "out_timeline": "Проект {ext} для {name}. "
                        "Таймлайн с нарезкой, без перекодирования.",
        "norm": "Выровнять громкость",
        "norm_hint": "приводит звук к ровному уровню по стандарту вещания — "
                     "тихие места подтягивает, громкие придерживает",
        "norm_off": "Выровнять громкость — только для готового видео",

        "save_to": "Сохранять в:",
        "beside": "папку Hush рядом с оригиналом",
        "choose": "Выбрать папку",
        "reset": "Сброс",
        "run": "Обработать",
        "preview": "Посчитать без рендера",
        "stop": "Стоп",

        "ready": "Готов к работе. Движок внутри — интернет не нужен.",
        "engine_missing": "Не нашёл движок ({name}).",
        "engine_where": "Он должен лежать в папке bin рядом с программой, "
                        "либо нажми «Обновить движок» при интернете.",
        "added": "Добавлено файлов: {n}",
        "need_files": "Сначала добавь файлы.",
        "no_engine_log": "Движок не установлен.",
        "head_preview": "── Считаю, ничего не рендерю ──",
        "head_run": "── Обработка ──",
        "head_update": "── Проверяю обновления ──",
        "was_becomes": "     было {a}  →  станет {b}"
                       "   (вырежется {p}%, резов {c})",
        "cant_count": "  {name} — не смог посчитать",
        "err": "  {name} — ошибка: {e}",
        "cant_start": "     не запустилось: {e}",
        "done_file": "     готово → {name}  ({size})",
        "fail_file": "     не получилось (код {code})",
        "done_all": "Готово: {ok} из {total}.",
        "stopped": "Остановлено.",
        "settings_reset": "Настройки сброшены к обычным.",

        "no_net": "  Интернета нет. Работаем на встроенном движке — "
                  "он полностью рабочий.",
        "fresh": "  Уже свежий: {v}. Обновлять нечего.",
        "new_ver": "  Есть новая версия: {a} → {b}. Качаю…",
        "dl_fail": "  Не скачалось: {e}",
        "dl_fail2": "  Не страшно — встроенный движок продолжает работать.",
        "updated_to": "  Обновлено до {v}.",
        "lies_at": "  Лежит тут: {p}",

        "st_counting": "считаю {i} из {n}",
        "st_github": "смотрю GitHub",
        "st_dl": "качаю {p}%",
        "st_analyze": "анализ звука",
        "st_render": "рендер",
        "st_line": "{stage} · {i} из {n} · {p}%",

        "sec": "{n} сек",
        "min": "{m}:{s:02d} мин",
        "mb": "{n} МБ",
        "kb": "{n} КБ",
        "sfx_cut": "_без_пауз",
        "sfx_speed": "_ускорено",
        "sfx_timeline": "_таймлайн",
        "dlg_files": "Выбери видео",
        "dlg_folder": "Куда сохранять результат",
        "ft_media": "Видео и звук",
        "ft_all": "Все файлы",
    },
    "en": {
        "app": "HUSH",
        "tagline": "cuts the pauses out of your video",
        "title": "HUSH — cuts the pauses out of your video",
        "update": "Update engine",
        "engine": "engine {v} · {where}",
        "bundled": "bundled",
        "updated": "updated",
        "no_engine": "engine not found",

        "files": "files",
        "settings": "settings",
        "defaults": "Defaults",
        "add": "Add files",
        "remove": "Remove",
        "clear": "Clear",
        "drop_hint": "Drop files here, or click “Add files”",
        "no_dnd": "Click “Add files” — drag and drop is unavailable",

        "smooth": "Smoothing",
        "smooth_hint": "merges micro-cuts so speech doesn't stutter",
        "smooth_off": "off",
        "speed": "Speech speed",
        "speed_hint": "speeds up the talking itself, not the pauses",
        "speed_normal": "as recorded",
        "motion_sens": "Motion sensitivity",
        "motion_hint": "lower notices smaller movement",
        "tab_subs": "Subtitles",
        "model": "Recognition model",
        "model_hint": "for anything but English take turbo-q5 or bigger",
        "model_missing": "not downloaded",
        "model_ready": "ready",
        "dl_model": "Download model",
        "subs_lang": "Spoken language",
        "lang_auto": "Detect",
        "lang_ru": "Russian",
        "lang_en": "English",
        "subs_fmt": "Format",
        "fmt_srt": "SRT (subtitles)",
        "fmt_text": "Plain text",
        "subs_words": "One word per line — for Shorts",
        "words_hint": "every word gets its own line and timing",
        "subs_tr": "Translate into English",
        "tr_hint": "speak any language, get English subtitles out",
        "subs_btn": "Make subtitles",
        "subs_note": "A separate job. Subtitles come from the source, "
                     "not from the cut file.",
        "head_subs": "── Transcribing ──",
        "subs_need_model": "Download a model on the Subtitles tab first.",
        "subs_done": "     done → {name}",
        "subs_dl": "  Downloading the {m} model, {mb}. Once, then it stays on disk.",
        "subs_dl_ok": "  Model ready.",
        "subs_slow": "  Transcribing runs at roughly video speed. Be patient.",
        "tab_cut": "Cutting",
        "tab_fine": "Fine-tune",
        "tab_out": "Output",
        "detect": "What counts as content",
        "det_audio": "Sound",
        "det_both": "Sound or motion",
        "det_motion": "Motion",
        "det_hint_audio": "keep the parts where someone is talking",
        "det_hint_both": "keep talking or moving picture — good for screen recordings",
        "det_hint_motion": "keep where the picture changes; audio is ignored",
        "black": "Drop black frames",
        "black_hint": "throws away fades and near-black stretches: title cards, "
                      "dead joins, a covered lens",
        "trans": "Smooth transitions",
        "trans_hint": "dissolve across each cut instead of a hard join",
        "trans_len": "Transition length",
        "trans_fail": "     The transition is longer than the clips between cuts. Shorten it.",
        "soft": "Soft",
        "normal": "Normal",
        "tight": "Tight",
        "margin": "Padding around speech",
        "margin_hint": "how much silence to keep around words",
        "unit_sec": "sec",
        "thresh": "Silence threshold",
        "thresh_hint": "anything quieter counts as silence",
        "silence": "What to do with silence",
        "cut": "Cut out",
        "speed2": "Speed ×2",
        "speed4": "Speed ×4",
        "output": "Output",
        "video": "Finished video",
        "out_video": "A finished file. Fast, but no edits afterwards.",
        "out_timeline": "A {ext} project for {name}. "
                        "Cut timeline, nothing re-encoded.",
        "norm": "Normalize loudness",
        "norm_hint": "levels the audio to the broadcast standard — quiet parts "
                     "come up, loud ones are held back",
        "norm_off": "Normalize loudness — video output only",

        "save_to": "Save to:",
        "beside": "a Hush folder next to the original",
        "choose": "Choose folder",
        "reset": "Reset",
        "run": "Process",
        "preview": "Count without rendering",
        "stop": "Stop",

        "ready": "Ready. The engine is bundled — no internet needed.",
        "engine_missing": "Engine not found ({name}).",
        "engine_where": "It belongs in the bin folder next to the app, "
                        "or press “Update engine” while online.",
        "added": "Files added: {n}",
        "need_files": "Add some files first.",
        "no_engine_log": "Engine is not installed.",
        "head_preview": "── Counting, rendering nothing ──",
        "head_run": "── Processing ──",
        "head_update": "── Checking for updates ──",
        "was_becomes": "     was {a}  →  becomes {b}"
                       "   ({p}% removed, {c} cuts)",
        "cant_count": "  {name} — could not count",
        "err": "  {name} — error: {e}",
        "cant_start": "     failed to start: {e}",
        "done_file": "     done → {name}  ({size})",
        "fail_file": "     failed (code {code})",
        "done_all": "Done: {ok} of {total}.",
        "stopped": "Stopped.",
        "settings_reset": "Settings reset to normal.",

        "no_net": "  No internet. Running on the bundled engine — "
                  "it works fine.",
        "fresh": "  Already current: {v}. Nothing to update.",
        "new_ver": "  New version available: {a} → {b}. Downloading…",
        "dl_fail": "  Download failed: {e}",
        "dl_fail2": "  No problem — the bundled engine keeps working.",
        "updated_to": "  Updated to {v}.",
        "lies_at": "  Stored at: {p}",

        "st_counting": "counting {i} of {n}",
        "st_github": "checking GitHub",
        "st_dl": "downloading {p}%",
        "st_analyze": "analyzing audio",
        "st_render": "rendering",
        "st_line": "{stage} · {i} of {n} · {p}%",

        "sec": "{n} sec",
        "min": "{m}:{s:02d} min",
        "mb": "{n} MB",
        "kb": "{n} KB",
        "sfx_cut": "_no_pauses",
        "sfx_speed": "_sped_up",
        "sfx_timeline": "_timeline",
        "dlg_files": "Choose video",
        "dlg_folder": "Where to save the result",
        "ft_media": "Video and audio",
        "ft_all": "All files",
    },
}

LANG = "ru"


def L(key, **kw):
    """Строка на текущем языке."""
    s = STRINGS.get(LANG, STRINGS["ru"]).get(key) or STRINGS["ru"].get(key, key)
    return s.format(**kw) if kw else s


# ─────────────────────────────────────────────────────────── тема

class T:
    bg      = "#0E0F11"   # фон окна
    panel   = "#16181B"   # карточка
    panel2  = "#1D2024"   # кнопка, поле
    line    = "#23262B"   # рамка
    text    = "#E6E8EB"   # основной текст
    dim     = "#8A9099"   # тусклый текст
    faint   = "#5A6069"   # совсем тусклый
    accent  = "#7A5CFF"   # акцент
    accent2 = "#9C86FF"   # акцент при наведении
    good    = "#3DD68C"   # успех
    bad     = "#FF6B5C"   # ошибка

    @staticmethod
    def font(size=13, bold=False):
        if IS_MAC:
            fam = "SF Pro Text"
        elif IS_WIN:
            fam = "Segoe UI"
        else:
            fam = "DejaVu Sans"
        return (fam, size, "bold" if bold else "normal")

    @staticmethod
    def mono(size=12):
        fam = "Menlo" if IS_MAC else ("Consolas" if IS_WIN else "monospace")
        return (fam, size)


# ─────────────────────────────────────────────────── свои виджеты

class Btn(tk.Frame):
    """Кнопка. tk.Button на macOS не красится, поэтому рисуем сами."""

    def __init__(self, parent, text, command, kind="ghost", pad=(16, 9)):
        self.kind = kind
        bg = T.accent if kind == "primary" else T.panel2
        super().__init__(parent, bg=bg, cursor="hand2",
                         highlightthickness=0 if kind == "primary" else 1,
                         highlightbackground=T.line, highlightcolor=T.line)
        self.command = command
        self._enabled = True

        fg = "#FFFFFF" if kind == "primary" else T.text
        self.label = tk.Label(self, text=text, bg=bg, fg=fg,
                              font=T.font(13, kind == "primary"),
                              padx=pad[0], pady=pad[1])
        self.label.pack()

        for w in (self, self.label):
            w.bind("<Button-1>", self._click)
            w.bind("<Enter>", self._enter)
            w.bind("<Leave>", self._leave)

    def _colors(self, hover=False):
        if not self._enabled:
            return (T.panel2, T.faint)
        if self.kind == "primary":
            return (T.accent2 if hover else T.accent, "#FFFFFF")
        return (T.line if hover else T.panel2, T.text)

    def _paint(self, hover=False):
        bg, fg = self._colors(hover)
        self.config(bg=bg)
        self.label.config(bg=bg, fg=fg)

    def _click(self, _=None):
        if self._enabled:
            self.command()

    def _enter(self, _=None):
        self._paint(True)

    def _leave(self, _=None):
        self._paint(False)

    def set_text(self, text):
        self.label.config(text=text)

    def enable(self, on=True):
        self._enabled = on
        self.config(cursor="hand2" if on else "arrow")
        self._paint(False)

    def set_kind(self, kind):
        """Сделать кнопку главной или обычной."""
        if kind == self.kind:
            return
        self.kind = kind
        self.config(highlightthickness=0 if kind == "primary" else 1)
        self.label.config(font=T.font(13, kind == "primary"))
        self._paint(False)


class Slider(tk.Canvas):
    """Горизонтальный ползунок. Рисуем сами — одинаково на всех ОС."""

    H = 34

    def __init__(self, parent, lo, hi, value, step, fmt, on_change=None,
                 width=280):
        super().__init__(parent, height=self.H, width=width, bg=T.panel,
                         highlightthickness=0, cursor="hand2")
        self.lo, self.hi, self.step = lo, hi, step
        self.value = value
        self.fmt = fmt
        self.on_change = on_change
        self.w = width
        self.bind("<Configure>", self._resize)
        self.bind("<Button-1>", self._drag)
        self.bind("<B1-Motion>", self._drag)
        self._draw()

    def _resize(self, e):
        self.w = e.width
        self._draw()

    def _draw(self):
        self.delete("all")
        y = 14
        self.create_line(12, y, self.w - 12, y, fill=T.line, width=4,
                         capstyle="round")
        frac = (self.value - self.lo) / (self.hi - self.lo)
        x = 12 + frac * (self.w - 24)
        self.create_line(12, y, x, y, fill=T.accent, width=4, capstyle="round")
        self.create_oval(x - 8, y - 8, x + 8, y + 8, fill=T.text, outline="")
        self.create_text(self.w - 2, self.H - 7, text=self.fmt(self.value),
                         anchor="se", fill=T.dim, font=T.font(11))

    def _drag(self, e):
        frac = min(1.0, max(0.0, (e.x - 12) / max(1, self.w - 24)))
        raw = self.lo + frac * (self.hi - self.lo)
        self.value = round(round(raw / self.step) * self.step, 4)
        self._draw()
        if self.on_change:
            self.on_change(self.value)

    def set(self, value):
        self.value = value
        self._draw()


class Seg(tk.Frame):
    """Переключатель из нескольких кнопок. Активна одна."""

    def __init__(self, parent, options, value, on_change=None, columns=None,
                 pady=7):
        super().__init__(parent, bg=T.panel)
        self.value = value
        self.on_change = on_change
        self.cells = {}
        self.marked = set()      # ключи, которые уже есть на диске
        self.labels = dict(options)

        cols = columns or len(options)
        for i, (key, label) in enumerate(options):
            cell = tk.Label(self, text=label, bg=T.panel2, fg=T.dim,
                            font=T.font(12), padx=12, pady=pady,
                            cursor="hand2")
            cell.grid(row=i // cols, column=i % cols, sticky="ew",
                      padx=(0, 4), pady=(0, 4))
            cell.bind("<Button-1>", lambda _e, k=key: self.set(k))
            self.cells[key] = cell
        for c in range(cols):
            self.grid_columnconfigure(c, weight=1)
        self._paint()

    def _paint(self):
        for key, cell in self.cells.items():
            on = key == self.value
            have = key in self.marked
            if on:
                bg, fg = T.accent, "#FFFFFF"
            elif have:
                bg, fg = T.line, T.text        # скачана — светлее и ярче
            else:
                bg, fg = T.panel2, T.dim
            text = self.labels.get(key, "")
            if have and not on:
                text += "  ✓"
            cell.config(bg=bg, fg=fg, font=T.font(12, on), text=text)

    def set(self, key):
        self.value = key
        self._paint()
        if self.on_change:
            self.on_change(key)

    def set_marks(self, keys):
        """Отметить ячейки, которые уже загружены."""
        self.marked = set(keys)
        self._paint()


class Tabs(tk.Frame):
    """Полоска вкладок. Показывает одну страницу из нескольких."""

    def __init__(self, parent, names, on_change=None):
        super().__init__(parent, bg=T.panel)
        self.on_change = on_change
        self.value = names[0][0]
        self.heads = {}
        self.pages = {}

        bar = tk.Frame(self, bg=T.panel)
        bar.pack(fill="x")
        self.marks = {}
        for key, label in names:
            cell = tk.Frame(bar, bg=T.panel, cursor="hand2")
            cell.pack(side="left", padx=(0, 6))
            lab = tk.Label(cell, text=label, bg=T.panel, fg=T.dim,
                           font=T.font(14, True), padx=14, pady=8,
                           cursor="hand2")
            lab.pack()
            mark = tk.Frame(cell, bg=T.panel, height=3)   # подчёркивание
            mark.pack(fill="x")
            for w in (cell, lab):
                w.bind("<Button-1>", lambda _e, k=key: self.show(k))
                w.bind("<Enter>", lambda _e, k=key: self._hover(k, True))
                w.bind("<Leave>", lambda _e, k=key: self._hover(k, False))
            self.heads[key] = lab
            self.marks[key] = mark

        # линия под всей полосой — видно, что это переключатель
        tk.Frame(self, bg=T.line, height=1).pack(fill="x", pady=(0, 12))

        # тело вкладок прокручивается — иначе длинная вкладка обрежется
        wrap = tk.Frame(self, bg=T.panel)
        wrap.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(wrap, bg=T.panel, highlightthickness=0)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.rail = tk.Canvas(wrap, bg=T.panel, width=4,
                              highlightthickness=0)
        self.rail.pack(side="right", fill="y")
        self.body = tk.Frame(self.canvas, bg=T.panel)
        self._win = self.canvas.create_window((0, 0), window=self.body,
                                              anchor="nw")

        def fit(_=None):
            self.canvas.itemconfig(self._win, width=self.canvas.winfo_width())
            self.canvas.config(scrollregion=self.canvas.bbox("all"))
            self._rail()
        self.canvas.bind("<Configure>", fit)
        self.body.bind("<Configure>", fit)
        self.canvas.config(yscrollcommand=lambda *_a: self._rail())

        def wheel(e):
            if self.body.winfo_reqheight() > self.canvas.winfo_height():
                self.canvas.yview_scroll(-1 if e.delta > 0 else 1, "units")
        self.canvas.bind("<Enter>",
                         lambda _e: self.canvas.bind_all("<MouseWheel>", wheel))
        self.canvas.bind("<Leave>",
                         lambda _e: self.canvas.unbind_all("<MouseWheel>"))

        for key, _ in names:
            self.pages[key] = tk.Frame(self.body, bg=T.panel)
        self._paint()

    def _hover(self, key, on):
        if key != self.value:
            self.heads[key].config(fg=T.text if on else T.dim)

    def _rail(self):
        """Полоска справа — только когда содержимое длиннее окна."""
        self.rail.delete("all")
        h = self.canvas.winfo_height()
        full = self.body.winfo_reqheight()
        if full <= h or h < 10:
            return
        top, bot = self.canvas.yview()
        self.rail.create_rectangle(1, 0, 4, h, fill=T.panel2, outline="")
        self.rail.create_rectangle(1, top * h, 4, bot * h,
                                   fill=T.line, outline="")

    def page(self, key):
        return self.pages[key]

    def _paint(self):
        for key, h in self.heads.items():
            on = key == self.value
            h.config(fg=T.text if on else T.dim, font=T.font(14, True),
                     bg=T.panel2 if on else T.panel)
            h.master.config(bg=T.panel2 if on else T.panel)
            self.marks[key].config(bg=T.accent if on else T.panel)
        for key, pg in self.pages.items():
            pg.pack_forget()
        self.pages[self.value].pack(fill="both", expand=True)

    def show(self, key):
        self.value = key
        self._paint()
        self.canvas.yview_moveto(0)
        self.after(30, self._rail)
        if self.on_change:
            self.on_change(key)


class Check(tk.Frame):
    """Галочка."""

    def __init__(self, parent, text, value=False, on_change=None):
        super().__init__(parent, bg=T.panel, cursor="hand2")
        self.value = value
        self.on_change = on_change
        self._enabled = True
        self.box = tk.Label(self, text="", bg=T.panel2, fg="#FFFFFF",
                            font=T.font(11, True), width=2, height=1)
        self.box.pack(side="left")
        self.lbl = tk.Label(self, text=text, bg=T.panel, fg=T.dim,
                            font=T.font(12), padx=8)
        self.lbl.pack(side="left")
        for w in (self, self.box, self.lbl):
            w.bind("<Button-1>", self._toggle)
        self._paint()

    def _paint(self):
        on = self.value and self._enabled
        self.box.config(text="✓" if on else "",
                        bg=T.accent if on else T.panel2)
        self.lbl.config(fg=T.text if on
                        else (T.dim if self._enabled else T.faint))

    def _toggle(self, _=None):
        if not self._enabled:
            return
        self.value = not self.value
        self._paint()
        if self.on_change:
            self.on_change(self.value)

    def set(self, value):
        self.value = value
        self._paint()

    def enable(self, on=True, text=None):
        self._enabled = on
        self.config(cursor="hand2" if on else "arrow")
        if text is not None:
            self.lbl.config(text=text)
        self._paint()


class Progress(tk.Canvas):
    """Полоса прогресса."""

    def __init__(self, parent, height=6):
        super().__init__(parent, height=height, bg=T.line, highlightthickness=0)
        self.frac = 0.0
        self.h = height
        self.bind("<Configure>", lambda _e: self._draw())

    def _draw(self):
        self.delete("all")
        w = self.winfo_width()
        if self.frac > 0:
            self.create_rectangle(0, 0, w * self.frac, self.h,
                                  fill=T.accent, outline="")

    def set(self, frac):
        self.frac = min(1.0, max(0.0, frac))
        self._draw()


class Fish(tk.Canvas):
    """Плавает туда-сюда. Клик — открывает сайт."""

    H = 26

    def __init__(self, parent, url):
        super().__init__(parent, height=self.H, bg=T.bg, highlightthickness=0)
        self.url = url
        self.x = 60.0
        self.dir = 1
        self.t = 0.0
        self.item = self.create_text(self.x, self.H / 2, text="><>",
                                     fill=T.faint, font=T.mono(14), anchor="c")
        self.tag_bind(self.item, "<Button-1>", self.open)
        self.tag_bind(self.item, "<Enter>", self.enter)
        self.tag_bind(self.item, "<Leave>", self.leave)
        self.swim()

    def enter(self, _=None):
        self.config(cursor="hand2")
        self.itemconfig(self.item, fill=T.accent)

    def leave(self, _=None):
        self.config(cursor="")
        self.itemconfig(self.item, fill=T.faint)

    def open(self, _=None):
        try:
            webbrowser.open(self.url)
        except Exception:
            pass

    def swim(self):
        w = self.winfo_width() or 400
        self.x += 1.1 * self.dir
        if self.x > w - 30:
            self.dir, self.x = -1, w - 30
            self.itemconfig(self.item, text="<><")
        elif self.x < 30:
            self.dir, self.x = 1, 30
            self.itemconfig(self.item, text="><>")
        self.t += 0.14
        self.coords(self.item, self.x, self.H / 2 + math.sin(self.t) * 2.5)
        self.after(45, self.swim)


def hint(parent, text, bg=None, fg=None):
    """Мелкая подпись. Перенос строк подстраивается под ширину панели."""
    bg = bg or T.panel
    lab = tk.Label(parent, text=text, bg=bg, fg=fg or T.faint,
                   font=T.font(10), anchor="w", justify="left")
    lab.bind("<Configure>",
             lambda e, w=lab: w.winfo_width() > 20
             and w.config(wraplength=w.winfo_width() - 4))
    return lab


def card(parent, title=None):
    """Карточка с тонкой рамкой."""
    outer = tk.Frame(parent, bg=T.line, padx=1, pady=1)
    inner = tk.Frame(outer, bg=T.panel, padx=18, pady=13)
    inner.pack(fill="both", expand=True)
    if title:
        tk.Label(inner, text=title.upper(), bg=T.panel, fg=T.faint,
                 font=T.font(10, True), anchor="w").pack(fill="x", pady=(0, 9))
    outer.inner = inner
    return outer


# ─────────────────────────────────────────────── запуск auto-editor

EXPORTS = ["default", "resolve", "premiere", "final-cut-pro",
           "shotcut", "kdenlive"]
EXPORT_INFO = {
    "default":       (None,               ".mp4"),
    "resolve":       ("DaVinci Resolve",  ".fcpxml"),
    "premiere":      ("Premiere Pro",     ".xml"),
    "final-cut-pro": ("Final Cut Pro",    ".fcpxml"),
    "shotcut":       ("Shotcut",          ".mlt"),
    "kdenlive":      ("Kdenlive",         ".kdenlive"),
}

# имя файла на HuggingFace: (размер в МБ, короткая подпись на кнопке)
MODELS = {
    "tiny":                (74,   "tiny"),
    "base":                (141,  "base"),
    "small-q5_1":          (181,  "small-q5"),
    "small":               (465,  "small"),
    "medium-q5_0":         (514,  "medium-q5"),
    "large-v3-turbo-q5_0": (547,  "turbo-q5"),
    "large-v3-turbo":      (1549, "turbo"),
    "large-v3":            (2951, "large-v3"),
}


def model_size(name):
    """74 МБ / 2.9 ГБ"""
    mb = MODELS[name][0]
    if mb < 1024:
        return f"{mb} " + ("МБ" if LANG == "ru" else "MB")
    return f"{mb / 1024:.1f} " + ("ГБ" if LANG == "ru" else "GB")
MODEL_URL = ("https://huggingface.co/ggerganov/whisper.cpp/resolve/main/"
             "ggml-{}.bin")


def models_dir():
    return os.path.join(os.path.dirname(update_dir()), "models")


def model_path(name):
    return os.path.join(models_dir(), f"ggml-{name}.bin")


def model_ready(name):
    p = model_path(name)
    return os.path.isfile(p) and os.path.getsize(p) > 1_000_000


def download_model(name, on_progress=None):
    """Качаем модель распознавания с HuggingFace."""
    import urllib.request
    os.makedirs(models_dir(), exist_ok=True)
    dst = model_path(name)
    tmp = dst + ".part"
    req = urllib.request.Request(MODEL_URL.format(name),
                                 headers={"User-Agent": "hush"})
    with urllib.request.urlopen(req, timeout=60) as r, open(tmp, "wb") as f:
        total = int(r.headers.get("Content-Length") or 0)
        done = 0
        while True:
            chunk = r.read(1 << 19)
            if not chunk:
                break
            f.write(chunk)
            done += len(chunk)
            if on_progress and total:
                on_progress(done / total)
    os.replace(tmp, dst)
    return dst


def subs_path(src, s):
    """Куда положить субтитры."""
    folder = s["outdir"] or os.path.join(os.path.dirname(src), OUT_FOLDER)
    os.makedirs(folder, exist_ok=True)
    stem = os.path.splitext(os.path.basename(src))[0]
    ext = ".srt" if s["subs_fmt"] == "srt" else ".txt"
    path = os.path.join(folder, stem + ext)
    n = 2
    while os.path.exists(path):
        path = os.path.join(folder, f"{stem} ({n}){ext}")
        n += 1
    return path


PRESETS = {
    "soft":   {"margin": 0.50, "db": -35},
    "normal": {"margin": 0.30, "db": -30},
    "tight":  {"margin": 0.15, "db": -25},
}

DEFAULTS = {
    "lang": "ru",
    "detect": "audio",
    "black": False,
    "trans": False,
    "trans_len": 0.25,
    "smooth": 0.20,
    "speed": 1.0,
    "motion_sens": 0.02,
    "model": "base",
    "subs_lang": "auto",
    "subs_fmt": "srt",
    "subs_words": False,
    "subs_tr": False,
    "preset": "normal",
    "margin": 0.30,
    "db": -30,
    "silent": "cut",
    "export": "default",
    "normalize": False,
    "outdir": "",
}


def resource_dir():
    """Папка с ресурсами: внутри собранного .app или рядом со скриптом."""
    if getattr(sys, "frozen", False):
        return getattr(sys, "_MEIPASS", HERE)
    return HERE


def update_dir():
    """Куда класть обновлённый бинарник (внутрь .app писать нельзя)."""
    if IS_WIN:
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
    elif IS_MAC:
        base = os.path.expanduser("~/Library/Application Support")
    else:
        base = os.path.expanduser("~/.local/share")
    return os.path.join(base, "Hush", "bin")


def config_path():
    """Файл настроек. В собранном приложении — в пользовательской папке."""
    if getattr(sys, "frozen", False):
        folder = os.path.dirname(update_dir())
        os.makedirs(folder, exist_ok=True)
        return os.path.join(folder, "settings.json")
    return os.path.join(HERE, "settings.json")


def no_window():
    """На Windows не показывать чёрное окно консоли."""
    if IS_WIN:
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        return {"startupinfo": si,
                "creationflags": subprocess.CREATE_NO_WINDOW}
    return {}


def binary_names():
    """Имена бинарника под эту систему, свежее имя первым.

    В 31.x файлы переименовали: windows-amd64 -> windows-x86_64.
    Держим оба, чтобы работать и со старым движком, и с новым."""
    arm = platform.machine().lower() in ("arm64", "aarch64")
    if IS_WIN:
        return (["auto-editor-windows-aarch64.exe"] if arm
                else ["auto-editor-windows-x86_64.exe",
                      "auto-editor-windows-amd64.exe"])
    if IS_MAC:
        return ["auto-editor-macos-arm64"] if arm \
            else ["auto-editor-macos-x86_64"]
    return (["auto-editor-linux-aarch64"] if arm
            else ["auto-editor-linux-x86_64"])


def binary_name():
    """Основное имя — им подписываем сообщения об ошибке."""
    return binary_names()[0]


def find_auto_editor():
    """Ищем бинарник: обновлённый → вшитый в приложение → системный."""
    for folder, name in ((f, n)
                         for f in (update_dir(),
                                   os.path.join(resource_dir(), "bin"))
                         for n in binary_names()):
        path = os.path.join(folder, name)
        if os.path.isfile(path):
            if not IS_WIN and not os.access(path, os.X_OK):
                try:
                    os.chmod(path, 0o755)
                except Exception:
                    pass
            return [path]
    exe = shutil.which("auto-editor")
    return [exe] if exe else None


_TEMP_DIR_OK = {}


def supports_temp_dir(cmd):
    """--temp-dir выпилили в auto-editor 31.1.0. Спрашиваем движок сами."""
    key = cmd[0]
    if key not in _TEMP_DIR_OK:
        try:
            r = subprocess.run(cmd + ["--help"], capture_output=True,
                               text=True, timeout=20, encoding="utf-8",
                               errors="replace", **no_window())
            _TEMP_DIR_OK[key] = "--temp-dir" in (r.stdout or "") + (r.stderr or "")
        except Exception:
            _TEMP_DIR_OK[key] = False
    return _TEMP_DIR_OK[key]


def binary_version(cmd):
    try:
        r = subprocess.run(cmd + ["--version"], capture_output=True, text=True,
                           timeout=20, encoding="utf-8", errors="replace",
                           **no_window())
        return ANSI.sub("", (r.stdout or r.stderr)).strip().split()[-1]
    except Exception:
        return "?"


def latest_release():
    """Последняя версия на GitHub. None — если интернета нет."""
    import urllib.request
    try:
        req = urllib.request.Request(
            "https://api.github.com/repos/WyattBlue/auto-editor/releases/latest",
            headers={"User-Agent": "hush"})
        with urllib.request.urlopen(req, timeout=12) as r:
            return json.load(r).get("tag_name", "").lstrip("v") or None
    except Exception:
        return None


def download_binary(version, on_progress=None):
    """Качаем бинарник нужной версии. Имена файлов менялись — пробуем все."""
    import urllib.request
    folder = update_dir()
    os.makedirs(folder, exist_ok=True)
    base = "https://github.com/WyattBlue/auto-editor/releases/download"

    last = None
    for name in binary_names():
        try:
            req = urllib.request.Request(f"{base}/{version}/{name}",
                                         headers={"User-Agent": "hush"})
            urllib.request.urlopen(req, timeout=20).close()
            break
        except Exception as e:
            last = e
    else:
        raise last or RuntimeError("no binary for this platform")

    tmp = os.path.join(folder, name + ".part")
    dst = os.path.join(folder, name)
    req = urllib.request.Request(f"{base}/{version}/{name}",
                                 headers={"User-Agent": "hush"})
    with urllib.request.urlopen(req, timeout=60) as r, open(tmp, "wb") as f:
        total = int(r.headers.get("Content-Length") or 0)
        done = 0
        while True:
            chunk = r.read(262144)
            if not chunk:
                break
            f.write(chunk)
            done += len(chunk)
            if on_progress and total:
                on_progress(done / total)
    os.replace(tmp, dst)
    if not IS_WIN:
        os.chmod(dst, 0o755)
    return dst


def cmp_version(a, b):
    """a новее b?"""
    def parts(v):
        return [int(x) for x in re.findall(r"\d+", v)] or [0]
    pa, pb = parts(a), parts(b)
    pa += [0] * (len(pb) - len(pa))
    pb += [0] * (len(pa) - len(pb))
    return pa > pb


def edit_expr(s):
    """Выражение для --edit. Синтаксис у движка лисповый."""
    audio = f"audio:{int(s['db'])}dB"
    motion = f"motion:{s.get('motion_sens', 0.02):.3f}"
    base = {"audio": audio,
            "both": f"(or {audio} {motion})",
            "motion": motion}[s.get("detect", "audio")]
    if s.get("black"):
        base = f"(and {base} (not blackdetect))"
    return base


def build_args(s):
    """Общие флаги из настроек."""
    args = ["--margin", f"{s['margin']}s",
            "--edit", edit_expr(s),
            "--no-open"]
    if s.get("trans"):
        args += ["--transition", f"dissolve:{s['trans_len']}sec"]
    sm = s.get("smooth", 0.2)
    args += ["--smooth", "0" if sm <= 0 else f"{sm}s,{sm / 2:.2f}s"]
    if s.get("speed", 1.0) > 1.001:
        args += ["--when-active", f"speed:{s['speed']:.2f}"]
    if s["silent"] != "cut":
        args += ["--when-silent", f"speed:{s['silent']}"]
    if s["normalize"] and s["export"] == "default":
        args += ["--audio-normalize", "ebu"]
    return args


OUT_FOLDER = "Hush"


def out_path(src, s):
    """Куда положить результат. Оригинал не трогаем никогда."""
    if s["outdir"]:
        folder = s["outdir"]
    else:
        # своя папка рядом с оригиналом — перепутать невозможно
        folder = os.path.join(os.path.dirname(src), OUT_FOLDER)
    os.makedirs(folder, exist_ok=True)
    stem = os.path.splitext(os.path.basename(src))[0]
    if s["export"] == "default":
        ext = os.path.splitext(src)[1] or ".mp4"
        suffix = L("sfx_cut") if s["silent"] == "cut" else L("sfx_speed")
    else:
        ext = EXPORT_INFO[s["export"]][1]
        suffix = L("sfx_timeline")
    path = os.path.join(folder, stem + suffix + ext)
    n = 2
    # никогда не писать поверх исходника и поверх готового файла
    while (os.path.exists(path)
           or os.path.abspath(path) == os.path.abspath(src)):
        path = os.path.join(folder, f"{stem}{suffix} ({n}){ext}")
        n += 1
    return path


def parse_preview(text):
    """Достаём цифры из вывода --preview."""
    text = ANSI.sub("", text)
    got = {}
    for key, name in (("input", "a"), ("output", "b")):
        m = re.search(rf"{key}:\s+(\d+:\d+:[\d.]+)", text)
        if m:
            got[name] = m.group(1)
    m = re.search(r"output:\s+\S+\s+\(\d+\)\s+([\d.]+)%", text)
    if m:
        got["percent"] = float(m.group(1))
    m = re.search(r"cuts:\s*\n\s*-\s*amount:\s+(\d+)", text)
    if m:
        got["cuts"] = int(m.group(1))
    return got


def human(hms):
    """0:00:50.28 → 50 сек / 2:05 мин"""
    try:
        h, m, s = hms.split(":")
        total = int(h) * 3600 + int(m) * 60 + float(s)
    except Exception:
        return hms
    if total < 60:
        return L("sec", n=f"{total:.0f}")
    return L("min", m=int(total // 60), s=int(total % 60))


def reveal(path):
    """Показать файл в проводнике/финдере."""
    try:
        if IS_MAC:
            subprocess.run(["open", "-R", path])
        elif IS_WIN:
            subprocess.run(["explorer", "/select,", os.path.normpath(path)])
        else:
            subprocess.run(["xdg-open", os.path.dirname(path)])
    except Exception:
        pass


# ─────────────────────────────────────────────────────── приложение

class App:
    def __init__(self, root, start_files=()):
        global LANG
        self.root = root
        self.files = []
        self.busy = False
        self.proc = None
        self.stop_flag = False
        self.queue = Queue()
        self.bin = find_auto_editor()
        self.dnd_ok = False

        self.s = dict(DEFAULTS)
        self.load_settings()
        LANG = self.s.get("lang", "ru")

        root.configure(bg=T.bg)
        root.geometry("1020x880")
        root.minsize(940, 780)

        self.build()
        self.pending = list(start_files)
        root.after(60, self.pump)
        root.after(120, self.first_run)

    def first_run(self):
        if self.pending:
            self.push_files(self.pending)
            self.pending = []
        self.show_version()
        if self.bin:
            self.log(L("ready"), "dim")
        else:
            self.log(L("engine_missing", name=binary_name()), "bad")
            self.log(L("engine_where"), "dim")

    # ── интерфейс ────────────────────────────────────────────────

    def build(self):
        root = self.root
        root.title(L("title"))

        head = tk.Frame(root, bg=T.bg, padx=24, pady=20)
        head.pack(fill="x")
        tk.Label(head, text=L("app"), bg=T.bg, fg=T.text,
                 font=T.font(22, True)).pack(side="left")
        tk.Label(head, text="  " + L("tagline"), bg=T.bg, fg=T.faint,
                 font=T.font(13)).pack(side="left", pady=(6, 0))

        self.btn_update = Btn(head, L("update"), self.start_update,
                              pad=(14, 7))
        self.btn_update.pack(side="right", pady=(4, 0))
        self.btn_lang = Btn(head, self.lang_label(), self.switch_lang,
                            pad=(13, 7))
        self.btn_lang.pack(side="right", padx=(0, 8), pady=(4, 0))
        self.lbl_ver = tk.Label(head, text="", bg=T.bg, fg=T.faint,
                                font=T.font(11))
        self.lbl_ver.pack(side="right", padx=(0, 12), pady=(6, 0))

        # низ пакуем первым — так его никогда не срежет
        self.build_actions(root)
        self.build_log(root)

        body = tk.Frame(root, bg=T.bg, padx=24)
        body.pack(fill="both", expand=True, side="top")
        body.grid_columnconfigure(0, weight=3, uniform="c")
        body.grid_columnconfigure(1, weight=2, uniform="c")
        body.grid_rowconfigure(0, weight=1)

        self.build_files(body)
        self.build_settings(body)
        self.refresh_labels()
        self.setup_dnd()

    def on_tab(self, key):
        """На вкладке субтитров главной становится своя кнопка."""
        subs = key == "subs"
        self.btn_subs.set_kind("primary" if subs else "ghost")
        self.btn_run.set_kind("ghost" if subs else "primary")

    def lang_label(self):
        return "🌐  " + ("RU" if LANG == "ru" else "EN")

    def build_files(self, parent):
        c = card(parent, L("files"))
        c.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        box = c.inner

        wrap = tk.Frame(box, bg=T.line, padx=1, pady=1)
        wrap.pack(fill="both", expand=True)
        self.listbox = tk.Listbox(
            wrap, bg=T.panel2, fg=T.text, font=T.font(12),
            selectbackground=T.accent, selectforeground="#FFFFFF",
            highlightthickness=0, borderwidth=0, activestyle="none")
        self.listbox.pack(fill="both", expand=True)
        self.listbox.bind("<Double-Button-1>", self.open_selected)

        self.hint = tk.Label(box, text="", bg=T.panel, fg=T.faint,
                             font=T.font(11))
        self.hint.pack(pady=(10, 0))

        row = tk.Frame(box, bg=T.panel)
        row.pack(fill="x", pady=(12, 0))
        Btn(row, L("add"), self.add_files, "primary").pack(side="left")
        Btn(row, L("remove"), self.remove_selected).pack(side="left",
                                                        padx=(8, 0))
        Btn(row, L("clear"), self.clear_files).pack(side="left", padx=(8, 0))

    def build_settings(self, parent):
        c = card(parent, L("settings"))
        c.grid(row=0, column=1, sticky="nsew")
        box = c.inner

        head = tk.Frame(box, bg=T.panel)
        head.place(relx=1.0, y=-4, anchor="ne")
        Btn(head, L("defaults"), self.reset_all, pad=(10, 3)).pack()

        self.tabs = Tabs(box, [("cut", L("tab_cut")), ("fine", L("tab_fine")),
                               ("out", L("tab_out")), ("subs", L("tab_subs"))],
                         self.on_tab)
        self.tabs.pack(fill="both", expand=True)
        cut = self.tabs.page("cut")
        fine = self.tabs.page("fine")
        out = self.tabs.page("out")
        subs = self.tabs.page("subs")

        self.seg_preset = Seg(
            cut, [(k, L(k)) for k in ("soft", "normal", "tight")],
            self.s["preset"], self.apply_preset)
        self.seg_preset.pack(fill="x", pady=(0, 12))

        box = cut          # дальше всё кладём на вкладку «Резка»
        tk.Label(box, text=L("margin"), bg=T.panel, fg=T.text,
                 font=T.font(12), anchor="w").pack(fill="x")
        hint(box, L("margin_hint")).pack(fill="x")
        self.sl_margin = Slider(
            box, 0.0, 1.0, self.s["margin"], 0.05,
            lambda v: f"{v:.2f} {L('unit_sec')}", self.on_margin)
        self.sl_margin.pack(fill="x", pady=(2, 10))

        tk.Label(box, text=L("thresh"), bg=T.panel, fg=T.text,
                 font=T.font(12), anchor="w").pack(fill="x")
        hint(box, L("thresh_hint")).pack(fill="x")
        self.sl_db = Slider(box, -50, -10, self.s["db"], 1,
                            lambda v: f"{int(v)} dB", self.on_db)
        self.sl_db.pack(fill="x", pady=(2, 12))

        tk.Label(box, text=L("silence"), bg=T.panel, fg=T.text,
                 font=T.font(12), anchor="w").pack(fill="x", pady=(0, 4))
        self.seg_silent = Seg(
            box, [("cut", L("cut")), ("2", L("speed2")), ("4", L("speed4"))],
            self.s["silent"], self.on_silent)
        self.seg_silent.pack(fill="x", pady=(0, 12))

        # ── вкладка «Точнее»
        box = fine
        tk.Label(box, text=L("detect"), bg=T.panel, fg=T.text,
                 font=T.font(12), anchor="w").pack(fill="x", pady=(0, 4))
        self.seg_detect = Seg(
            box, [("audio", L("det_audio")), ("both", L("det_both")),
                  ("motion", L("det_motion"))],
            self.s["detect"], self.on_detect)
        self.seg_detect.pack(fill="x", pady=(0, 2))
        self.lbl_detect = tk.Label(
            box, text="", bg=T.panel, fg=T.dim, font=T.font(10),
            anchor="nw", justify="left", height=2)
        self.lbl_detect.bind("<Configure>",
                         lambda e, w=self.lbl_detect: w.winfo_width() > 20
                         and w.config(wraplength=w.winfo_width() - 4))
        self.lbl_detect.pack(fill="x", pady=(0, 8))

        self.sl_motion = Slider(box, 0.005, 0.100, self.s["motion_sens"],
                                0.005, lambda v: f"{v * 100:.1f} %",
                                self.on_motion_sens)

        self.chk_black = Check(box, L("black"), self.s["black"],
                               self.on_black)
        self.chk_black.pack(fill="x")
        hint(box, L("black_hint")).pack(fill="x", pady=(0, 10))

        tk.Label(box, text=L("smooth"), bg=T.panel, fg=T.text,
                 font=T.font(12), anchor="w").pack(fill="x")
        hint(box, L("smooth_hint")).pack(fill="x")
        self.sl_smooth = Slider(
            box, 0.0, 0.60, self.s["smooth"], 0.05,
            lambda v: L("smooth_off") if v <= 0 else f"{v:.2f} {L('unit_sec')}",
            self.on_smooth)
        self.sl_smooth.pack(fill="x", pady=(2, 10))

        tk.Label(box, text=L("speed"), bg=T.panel, fg=T.text,
                 font=T.font(12), anchor="w").pack(fill="x")
        hint(box, L("speed_hint")).pack(fill="x")
        self.sl_speed = Slider(
            box, 1.0, 2.0, self.s["speed"], 0.05,
            lambda v: L("speed_normal") if v <= 1.001 else f"×{v:.2f}",
            self.on_speed)
        self.sl_speed.pack(fill="x", pady=(2, 4))

        # ── вкладка «Вывод»
        tk.Label(out, text=L("output"), bg=T.panel, fg=T.text,
                 font=T.font(12), anchor="w").pack(fill="x", pady=(0, 6))
        self.seg_export = Seg(
            out, [(k, L("video") if k == "default" else EXPORT_INFO[k][0])
                  for k in EXPORTS],
            self.s["export"], self.on_export, columns=2)
        self.seg_export.pack(fill="x", pady=(0, 4))
        self.lbl_export = tk.Label(
            out, text="", bg=T.panel, fg=T.dim, font=T.font(10),
            anchor="nw", justify="left", height=2)
        self.lbl_export.bind("<Configure>",
                         lambda e, w=self.lbl_export: w.winfo_width() > 20
                         and w.config(wraplength=w.winfo_width() - 4))
        self.lbl_export.pack(fill="x", pady=(0, 10))

        self.chk_trans = Check(out, L("trans"), self.s["trans"],
                               self.on_trans)
        self.chk_trans.pack(fill="x")
        hint(out, L("trans_hint")).pack(fill="x", pady=(0, 2))
        self.sl_trans = Slider(out, 0.10, 0.50, self.s["trans_len"], 0.05,
                               lambda v: f"{v:.2f} {L('unit_sec')}",
                               self.on_trans_len)
        self.sl_trans.pack(fill="x", pady=(0, 10))

        self.chk_norm = Check(out, L("norm"), self.s["normalize"],
                              self.on_norm)
        self.chk_norm.pack(fill="x")
        hint(out, L("norm_hint")).pack(fill="x", pady=(0, 4))

        # ── вкладка «Субтитры»
        note = tk.Frame(subs, bg=T.panel2, padx=10, pady=7)
        note.pack(fill="x", pady=(0, 8))
        nl = tk.Label(note, text=L("subs_note"), bg=T.panel2, fg=T.dim,
                      font=T.font(11), anchor="w", justify="left")
        nl.bind("<Configure>", lambda e, w=nl: w.winfo_width() > 20
                and w.config(wraplength=w.winfo_width() - 4))
        nl.pack(fill="x")

        tk.Label(subs, text=L("model"), bg=T.panel, fg=T.text,
                 font=T.font(12), anchor="w").pack(fill="x")
        hint(subs, L("model_hint")).pack(fill="x", pady=(0, 4))
        self.seg_model = Seg(
            subs, [(m, f"{MODELS[m][1]}  ·  {model_size(m)}") for m in MODELS],
            self.s["model"], self.on_model, columns=2, pady=5)
        self.seg_model.pack(fill="x", pady=(0, 4))

        row = tk.Frame(subs, bg=T.panel)
        row.pack(fill="x", pady=(0, 10))
        self.lbl_model = tk.Label(row, text="", bg=T.panel, fg=T.dim,
                                  font=T.font(11), anchor="w")
        self.lbl_model.pack(side="left")
        self.btn_model = Btn(row, L("dl_model"), self.start_model,
                             pad=(12, 5))
        self.btn_model.pack(side="right")

        tk.Label(subs, text=L("subs_lang"), bg=T.panel, fg=T.text,
                 font=T.font(12), anchor="w").pack(fill="x", pady=(0, 4))
        self.seg_slang = Seg(
            subs, [("auto", L("lang_auto")), ("ru", L("lang_ru")),
                   ("en", L("lang_en"))],
            self.s["subs_lang"], self.on_slang)
        self.seg_slang.pack(fill="x", pady=(0, 10))

        tk.Label(subs, text=L("subs_fmt"), bg=T.panel, fg=T.text,
                 font=T.font(12), anchor="w").pack(fill="x", pady=(0, 4))
        self.seg_sfmt = Seg(
            subs, [("srt", L("fmt_srt")), ("text", L("fmt_text"))],
            self.s["subs_fmt"], self.on_sfmt)
        self.seg_sfmt.pack(fill="x", pady=(0, 10))

        self.chk_words = Check(subs, L("subs_words"), self.s["subs_words"],
                               self.on_words)
        self.chk_words.pack(fill="x")
        hint(subs, L("words_hint")).pack(fill="x", pady=(0, 8))
        self.chk_tr = Check(subs, L("subs_tr"), self.s["subs_tr"],
                            self.on_tr)
        self.chk_tr.pack(fill="x")
        hint(subs, L("tr_hint")).pack(fill="x")

    def build_actions(self, parent):
        wrap = tk.Frame(parent, bg=T.bg, padx=24, pady=10)
        wrap.pack(fill="x", side="bottom")

        dirrow = tk.Frame(wrap, bg=T.bg)
        dirrow.pack(fill="x", pady=(0, 8))
        tk.Label(dirrow, text=L("save_to"), bg=T.bg, fg=T.dim,
                 font=T.font(12)).pack(side="left")
        self.lbl_dir = tk.Label(dirrow, text="", bg=T.bg, fg=T.text,
                                font=T.font(12), anchor="w")
        self.lbl_dir.pack(side="left", padx=(8, 0))
        Btn(dirrow, L("reset"), self.reset_dir,
            pad=(14, 7)).pack(side="right")
        Btn(dirrow, L("choose"), self.pick_dir,
            pad=(14, 7)).pack(side="right", padx=(0, 8))
        self.fish = Fish(dirrow, FISH_URL)
        self.fish.pack(side="right", fill="x", expand=True, padx=16)

        row = tk.Frame(wrap, bg=T.bg)
        row.pack(fill="x")
        self.btn_run = Btn(row, L("run"), self.start_run, "primary",
                           pad=(28, 12))
        self.btn_run.pack(side="left")
        self.btn_preview = Btn(row, L("preview"), self.start_preview,
                               pad=(20, 12))
        self.btn_preview.pack(side="left", padx=(10, 0))
        self.btn_subs = Btn(row, L("subs_btn"), self.start_subs,
                            pad=(20, 12))
        self.btn_subs.pack(side="left", padx=(10, 0))
        self.btn_stop = Btn(row, L("stop"), self.stop_run, pad=(20, 12))
        self.btn_stop.pack(side="left", padx=(10, 0))
        self.btn_stop.enable(False)

        self.status = tk.Label(row, text="", bg=T.bg, fg=T.dim,
                               font=T.font(12), anchor="e")
        self.status.pack(side="right")

        self.progress = Progress(wrap)
        self.progress.pack(fill="x", pady=(10, 0))

    def build_log(self, parent):
        wrap = tk.Frame(parent, bg=T.bg, padx=24)
        wrap.pack(fill="x", side="bottom", pady=(0, 16))
        frame = tk.Frame(wrap, bg=T.line, padx=1, pady=1)
        frame.pack(fill="x")
        self.text = tk.Text(frame, bg=T.panel, fg=T.dim, font=T.mono(12),
                            highlightthickness=0, borderwidth=0, height=3,
                            padx=14, pady=12, wrap="word", state="disabled")
        self.text.pack(fill="x")
        for name, color in (("ok", T.good), ("bad", T.bad),
                            ("acc", T.accent2), ("dim", T.faint),
                            ("txt", T.text)):
            self.text.tag_config(name, foreground=color)

    def setup_dnd(self):
        """Перетаскивание файлов — если доступен tkinterdnd2."""
        self.dnd_ok = False
        for widget in (self.root, self.listbox):
            try:
                widget.drop_target_register("DND_Files")
                widget.dnd_bind("<<Drop>>", self.on_drop)
                self.dnd_ok = True
            except Exception:
                pass
        self.hint.config(text=L("drop_hint") if self.dnd_ok else L("no_dnd"))

    # ── язык ─────────────────────────────────────────────────────

    def switch_lang(self):
        global LANG
        if self.busy:
            return
        LANG = "en" if LANG == "ru" else "ru"
        self.s["lang"] = LANG
        self.save_settings()
        self.rebuild()

    def rebuild(self):
        """Пересобрать окно на другом языке, сохранив список файлов."""
        tab = self.tabs.value if hasattr(self, "tabs") else "cut"
        for w in self.root.winfo_children():
            w.destroy()
        self.build()
        self.tabs.show(tab)          # остаёмся на той же вкладке
        for p in self.files:
            self.listbox.insert("end", "  " + os.path.basename(p))
        self.show_version()

    # ── настройки ────────────────────────────────────────────────

    def load_settings(self):
        try:
            with open(config_path(), encoding="utf-8") as f:
                self.s.update(json.load(f))
        except Exception:
            pass

    def save_settings(self):
        try:
            with open(config_path(), "w", encoding="utf-8") as f:
                json.dump(self.s, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def refresh_labels(self):
        folder = self.s["outdir"] or L("beside")
        if len(folder) > 52:
            folder = "…" + folder[-51:]
        self.lbl_dir.config(text=folder)

        if self.s["export"] == "default":
            self.lbl_export.config(text=L("out_video"))
        else:
            name, ext = EXPORT_INFO[self.s["export"]]
            self.lbl_export.config(text=L("out_timeline", ext=ext, name=name))

        video = self.s["export"] == "default"
        self.chk_norm.enable(video, L("norm") if video else L("norm_off"))
        self.lbl_detect.config(text=L("det_hint_" + self.s["detect"]))
        self.seg_model.set_marks(m for m in MODELS if model_ready(m))
        ready = model_ready(self.s["model"])
        self.lbl_model.config(
            text=L("model_ready") if ready else L("model_missing"),
            fg=T.good if ready else T.dim)
        self.btn_model.enable(not ready)
        if self.s["detect"] in ("both", "motion"):
            self.sl_motion.pack(fill="x", pady=(0, 8),
                                before=self.chk_black)
        else:
            self.sl_motion.pack_forget()

    def apply_preset(self, key):
        if not key:
            return
        self.s["preset"] = key
        self.s["margin"] = PRESETS[key]["margin"]
        self.s["db"] = PRESETS[key]["db"]
        self.sl_margin.set(self.s["margin"])
        self.sl_db.set(self.s["db"])
        self.save_settings()

    def on_margin(self, v):
        self.s["margin"] = v
        self.s["preset"] = ""
        self.seg_preset.set("")
        self.save_settings()

    def on_db(self, v):
        self.s["db"] = v
        self.s["preset"] = ""
        self.seg_preset.set("")
        self.save_settings()

    def on_silent(self, key):
        self.s["silent"] = key
        self.save_settings()

    def on_export(self, key):
        self.s["export"] = key
        self.refresh_labels()
        self.save_settings()

    def on_detect(self, key):
        self.s["detect"] = key
        self.refresh_labels()
        self.save_settings()

    def on_model(self, key):
        self.s["model"] = key
        self.refresh_labels()
        self.save_settings()

    def on_slang(self, key):
        self.s["subs_lang"] = key
        self.save_settings()

    def on_sfmt(self, key):
        self.s["subs_fmt"] = key
        self.save_settings()

    def on_words(self, v):
        self.s["subs_words"] = v
        self.save_settings()

    def on_tr(self, v):
        self.s["subs_tr"] = v
        self.save_settings()

    def on_motion_sens(self, v):
        self.s["motion_sens"] = v
        self.save_settings()

    def on_smooth(self, v):
        self.s["smooth"] = v
        self.save_settings()

    def on_speed(self, v):
        self.s["speed"] = v
        self.save_settings()

    def on_black(self, v):
        self.s["black"] = v
        self.save_settings()

    def on_trans(self, v):
        self.s["trans"] = v
        self.save_settings()

    def on_trans_len(self, v):
        self.s["trans_len"] = v
        self.save_settings()

    def on_norm(self, v):
        self.s["normalize"] = v
        self.refresh_labels()
        self.save_settings()

    def reset_all(self):
        keep = self.s["lang"]
        self.s.update(DEFAULTS)
        self.s["lang"] = keep
        self.sl_margin.set(self.s["margin"])
        self.sl_db.set(self.s["db"])
        self.seg_preset.set(self.s["preset"])
        self.seg_silent.set(self.s["silent"])
        self.seg_export.set(self.s["export"])
        self.seg_detect.set(self.s["detect"])
        self.chk_black.set(self.s["black"])
        self.chk_trans.set(self.s["trans"])
        self.sl_trans.set(self.s["trans_len"])
        self.sl_smooth.set(self.s["smooth"])
        self.sl_speed.set(self.s["speed"])
        self.sl_motion.set(self.s["motion_sens"])
        self.seg_model.set(self.s["model"])
        self.seg_slang.set(self.s["subs_lang"])
        self.seg_sfmt.set(self.s["subs_fmt"])
        self.chk_words.set(self.s["subs_words"])
        self.chk_tr.set(self.s["subs_tr"])
        self.chk_norm.set(self.s["normalize"])
        self.refresh_labels()
        self.save_settings()
        self.log(L("settings_reset"), "dim")

    def pick_dir(self):
        d = filedialog.askdirectory(title=L("dlg_folder"))
        if d:
            self.s["outdir"] = d
            self.refresh_labels()
            self.save_settings()

    def reset_dir(self):
        self.s["outdir"] = ""
        self.refresh_labels()
        self.save_settings()

    # ── файлы ────────────────────────────────────────────────────

    def add_files(self):
        paths = filedialog.askopenfilenames(
            title=L("dlg_files"),
            filetypes=[(L("ft_media"), " ".join("*" + e for e in VIDEO_EXT)),
                       (L("ft_all"), "*.*")])
        self.push_files(paths)

    def on_drop(self, event):
        """Файлы приходят строкой; пути с пробелами — в фигурных скобках."""
        raw = event.data
        paths = re.findall(r"\{([^}]*)\}", raw)
        rest = re.sub(r"\{[^}]*\}", " ", raw).split()
        self.push_files(paths + rest)

    def push_files(self, paths):
        added = 0
        for p in paths:
            p = p.strip()
            if not p or not os.path.isfile(p) or p in self.files:
                continue
            self.files.append(p)
            self.listbox.insert("end", "  " + os.path.basename(p))
            added += 1
        if added:
            self.log(L("added", n=added), "dim")

    def remove_selected(self):
        for i in sorted(self.listbox.curselection(), reverse=True):
            self.listbox.delete(i)
            del self.files[i]

    def clear_files(self):
        self.listbox.delete(0, "end")
        self.files.clear()

    def open_selected(self, _=None):
        sel = self.listbox.curselection()
        if sel:
            reveal(self.files[sel[0]])

    # ── лог ──────────────────────────────────────────────────────

    def log(self, msg, tag="dim"):
        self.text.config(state="normal")
        self.text.insert("end", msg + "\n", tag)
        self.text.see("end")
        self.text.config(state="disabled")

    def say(self, msg, tag="dim"):
        self.queue.put(("log", (msg, tag)))

    def pump(self):
        try:
            while True:
                kind, payload = self.queue.get_nowait()
                if kind == "log":
                    self.log(*payload)
                elif kind == "status":
                    self.status.config(text=payload)
                elif kind == "progress":
                    self.progress.set(payload)
                elif kind == "labels":
                    self.refresh_labels()
                elif kind == "version":
                    self.lbl_ver.config(text=payload)
                elif kind == "update_done":
                    self.finish()
                    self.btn_update.enable(True)
                    self.show_version()
                elif kind == "done":
                    self.finish()
        except Empty:
            pass
        self.root.after(60, self.pump)

    # ── движок и обновление ──────────────────────────────────────

    def show_version(self):
        def job():
            if not self.bin:
                self.queue.put(("version", L("no_engine")))
                return
            v = binary_version(self.bin)
            where = (L("updated") if self.bin[0].startswith(update_dir())
                     else L("bundled"))
            self.queue.put(("version", L("engine", v=v, where=where)))
        threading.Thread(target=job, daemon=True).start()

    def start_update(self):
        if self.busy:
            return
        self.lock(True)
        self.btn_update.enable(False)
        threading.Thread(target=self.work_update, daemon=True).start()

    def work_update(self):
        self.say("", "dim")
        self.say(L("head_update"), "acc")
        have = binary_version(self.bin) if self.bin else "0"
        self.queue.put(("status", L("st_github")))

        latest = latest_release()
        if latest is None:
            self.say(L("no_net"), "dim")
            self.queue.put(("update_done", None))
            return
        if not cmp_version(latest, have):
            self.say(L("fresh", v=have), "ok")
            self.queue.put(("update_done", None))
            return

        self.say(L("new_ver", a=have, b=latest), "txt")
        try:
            path = download_binary(
                latest,
                lambda f: (self.queue.put(("progress", f)),
                           self.queue.put(("status",
                                           L("st_dl", p=f"{f * 100:.0f}")))))
        except Exception as e:
            self.say(L("dl_fail", e=e), "bad")
            self.say(L("dl_fail2"), "dim")
            self.queue.put(("update_done", None))
            return

        self.bin = [path]
        self.say(L("updated_to", v=latest), "ok")
        self.say(L("lies_at", p=path), "dim")
        self.queue.put(("update_done", None))

    # ── запуск ───────────────────────────────────────────────────

    def guard(self):
        if self.busy:
            return False
        if not self.bin:
            self.log(L("no_engine_log"), "bad")
            return False
        if not self.files:
            self.log(L("need_files"), "bad")
            return False
        return True

    def lock(self, on):
        self.busy = on
        self.btn_run.enable(not on)
        self.btn_preview.enable(not on)
        self.btn_subs.enable(not on)
        self.btn_lang.enable(not on)
        self.btn_stop.enable(on)

    def finish(self):
        self.lock(False)
        self.progress.set(0)
        self.status.config(text="")
        self.proc = None

    def start_model(self):
        if self.busy or model_ready(self.s["model"]):
            return
        self.lock(True)
        self.stop_flag = False
        threading.Thread(target=self.work_model, daemon=True).start()

    def work_model(self):
        name = self.s["model"]
        self.say("", "dim")
        self.say(L("subs_dl", m=name, mb=model_size(name)), "acc")
        try:
            download_model(
                name,
                lambda f: (self.queue.put(("progress", f)),
                           self.queue.put(("status",
                                           L("st_dl", p=f"{f * 100:.0f}")))))
            self.say(L("subs_dl_ok"), "ok")
        except Exception as e:
            self.say(L("dl_fail", e=e), "bad")
        self.queue.put(("labels", None))
        self.queue.put(("done", None))

    def start_subs(self):
        if not self.guard():
            return
        if not model_ready(self.s["model"]):
            self.log(L("subs_need_model"), "bad")
            return
        self.lock(True)
        self.stop_flag = False
        threading.Thread(target=self.work_subs, daemon=True).start()

    def work_subs(self):
        self.say("", "dim")
        self.say(L("head_subs"), "acc")
        self.say(L("subs_slow"), "dim")
        total = len(self.files)
        made = []

        for i, src in enumerate(self.files):
            if self.stop_flag:
                break
            name = os.path.basename(src)
            dst = subs_path(src, self.s)
            self.say(f"  {name}", "txt")
            self.queue.put(("status", L("st_counting", i=i + 1, n=total)))
            self.queue.put(("progress", (i + 0.5) / total))

            cmd = (self.bin + ["whisper", src, model_path(self.s["model"]),
                               "--format", self.s["subs_fmt"], "-o", dst])
            if self.s["subs_lang"] != "auto":
                cmd += ["--language", self.s["subs_lang"]]
            if self.s["subs_words"]:
                cmd += ["--split-words"]
            if self.s["subs_tr"]:
                cmd += ["--translate"]

            try:
                self.proc = subprocess.Popen(
                    cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    text=True, encoding="utf-8", errors="replace",
                    bufsize=1, **no_window())
                tail = []
                for line in self.proc.stdout:
                    if self.stop_flag:
                        break
                    line = ANSI.sub("", line).strip()
                    if line:
                        tail.append(line)
                        tail = tail[-6:]
                code = self.proc.wait()
            except Exception as e:
                self.say(L("cant_start", e=e), "bad")
                continue

            if self.stop_flag:
                break
            if code == 0 and os.path.exists(dst):
                self.say(L("subs_done", name=os.path.basename(dst)), "ok")
                made.append(dst)
            else:
                self.say(L("fail_file", code=code), "bad")
                for t in tail:
                    if "rror" in t:
                        self.say(f"     {t}", "bad")

        if made:
            self.say(L("done_all", ok=len(made), total=total), "acc")
            reveal(made[0])
        self.queue.put(("done", None))

    def start_preview(self):
        if not self.guard():
            return
        self.lock(True)
        self.stop_flag = False
        threading.Thread(target=self.work_preview, daemon=True).start()

    def start_run(self):
        if not self.guard():
            return
        self.lock(True)
        self.stop_flag = False
        threading.Thread(target=self.work_run, daemon=True).start()

    def stop_run(self):
        self.stop_flag = True
        if self.proc and self.proc.poll() is None:
            try:
                self.proc.kill()
            except Exception:
                pass
        self.say(L("stopped"), "bad")

    def work_preview(self):
        self.say("", "dim")
        self.say(L("head_preview"), "acc")
        for i, src in enumerate(self.files):
            if self.stop_flag:
                break
            self.queue.put(("status",
                            L("st_counting", i=i + 1, n=len(self.files))))
            self.queue.put(("progress", (i + 0.5) / len(self.files)))
            cmd = self.bin + [src] + build_args(self.s) + ["--preview"]
            name = os.path.basename(src)
            try:
                r = subprocess.run(cmd, capture_output=True, text=True,
                                   encoding="utf-8", errors="replace",
                                   **no_window())
                got = parse_preview(r.stdout + r.stderr)
            except Exception as e:
                self.say(L("err", name=name, e=e), "bad")
                continue

            if "a" in got and "b" in got:
                cut = 100 - got.get("percent", 100)
                self.say(f"  {name}", "txt")
                self.say(L("was_becomes", a=human(got["a"]),
                           b=human(got["b"]), p=f"{cut:.0f}",
                           c=got.get("cuts", "?")), "ok")
            else:
                self.say(L("cant_count", name=name), "bad")
        self.queue.put(("done", None))

    def work_run(self):
        self.say("", "dim")
        self.say(L("head_run"), "acc")
        total = len(self.files)
        ok_files = []

        for i, src in enumerate(self.files):
            if self.stop_flag:
                break
            name = os.path.basename(src)
            dst = out_path(src, self.s)
            self.say(f"  {name}", "txt")

            tmp = (tempfile.mkdtemp(prefix="hush-")
                   if supports_temp_dir(self.bin) else None)
            cmd = (self.bin + [src] + build_args(self.s)
                   + ["--export", self.s["export"], "-o", dst,
                      "--progress", "machine"])
            if tmp:
                cmd += ["--temp-dir", os.path.join(tmp, "work")]
            try:
                self.proc = subprocess.Popen(
                    cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    text=True, encoding="utf-8", errors="replace",
                    bufsize=1, **no_window())
            except Exception as e:
                self.say(L("cant_start", e=e), "bad")
                continue

            tail = []
            for line in self.proc.stdout:
                if self.stop_flag:
                    break
                line = ANSI.sub("", line).strip()
                if not line:
                    continue
                if "~" in line:
                    parts = line.split("~")
                    if len(parts) >= 3:
                        try:
                            cur, tot = float(parts[1]), float(parts[2])
                        except ValueError:
                            continue
                        stage = (L("st_analyze") if "Analyz" in parts[0]
                                 else L("st_render"))
                        self.queue.put(
                            ("progress",
                             (i + (cur / tot if tot else 0)) / total))
                        self.queue.put((
                            "status",
                            L("st_line", stage=stage, i=i + 1, n=total,
                              p=f"{cur / tot * 100:.0f}" if tot else "0")))
                else:
                    tail.append(line)
                    tail = tail[-6:]

            code = self.proc.wait()
            if tmp:
                shutil.rmtree(tmp, ignore_errors=True)
            if self.stop_flag:
                break
            if code == 0 and os.path.exists(dst):
                kb = os.path.getsize(dst) / 1024
                size = (L("mb", n=f"{kb / 1024:.1f}") if kb >= 1024
                        else L("kb", n=f"{kb:.0f}"))
                self.say(L("done_file", name=os.path.basename(dst),
                           size=size), "ok")
                ok_files.append(dst)
            else:
                self.say(L("fail_file", code=code), "bad")
                joined = " ".join(tail)
                if "Transitions must have" in joined:
                    self.say(L("trans_fail"), "bad")
                else:
                    for t in tail:
                        if "rror" in t:
                            self.say(f"     {t}", "bad")

        if ok_files:
            self.say(L("done_all", ok=len(ok_files), total=total), "acc")
            reveal(ok_files[0])
        self.queue.put(("done", None))


def main():
    files = [a for a in sys.argv[1:] if os.path.isfile(a)]
    try:
        from tkinterdnd2 import TkinterDnD
        root = TkinterDnD.Tk()
    except Exception:
        root = tk.Tk()
    App(root, files)
    root.mainloop()


if __name__ == "__main__":
    main()
