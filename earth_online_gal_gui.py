# THESIS: A quiet reply desk for private chat, not a terminal transplanted into a window.
# OWN-WORLD: graphite surfaces, restrained sea-glass accents, warm error signals, and precise Windows controls.
# STORY: The user sees what was read, chooses a relation, generates a suggestion, and copies only a reply they approve.
# FIRST VIEWPORT: a compact desktop panel leads with current state and latest incoming text; the main action sits at center.
# FORM: Operate-mode desktop assistant, direction seed 950e2746, constrained by the user's explicit non-terminal brief.

from __future__ import annotations

import os
import sys
import threading
import tkinter as tk
from pathlib import Path
from typing import Any, Callable, Mapping

import deepseek_wechat_fallback as core


APP_NAME = "地球online gal工具包"
ICON_PATH = Path(__file__).with_name("earth_online_icon.png")
RELATION_LABELS = {
    "ambiguous": "暧昧",
    "colleague": "同事",
    "family": "家人",
    "client": "客户",
    "friend": "好友",
}


def enable_dpi_awareness() -> None:
    if sys.platform != "win32":
        return
    try:
        import ctypes

        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass


class ApiKeyDialog(tk.Toplevel):
    def __init__(self, parent: tk.Tk) -> None:
        super().__init__(parent)
        self.value = ""
        self.configure(bg="#151b20")
        self.title("输入 DeepSeek API Key")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        body = tk.Frame(self, bg="#151b20", padx=24, pady=22)
        body.pack(fill="both", expand=True)
        tk.Label(
            body,
            text="输入 DeepSeek API Key",
            bg="#151b20",
            fg="#eef7f5",
            font=("Microsoft YaHei UI", 13, "bold"),
        ).pack(anchor="w")
        tk.Label(
            body,
            text="仅保留在本次运行的内存中，不会写入文件。",
            bg="#151b20",
            fg="#a6b8b5",
            font=("Microsoft YaHei UI", 9),
        ).pack(anchor="w", pady=(6, 16))
        self.entry = tk.Entry(
            body,
            show="*",
            width=40,
            bg="#0f1418",
            fg="#eef7f5",
            insertbackground="#45d7c1",
            relief="flat",
            highlightthickness=1,
            highlightbackground="#37514f",
            highlightcolor="#45d7c1",
            font=("Cascadia Mono", 10),
        )
        self.entry.pack(fill="x", ipady=8)
        actions = tk.Frame(body, bg="#151b20")
        actions.pack(fill="x", pady=(18, 0))
        tk.Button(
            actions,
            text="取消",
            command=self.cancel,
            bg="#222d32",
            fg="#d8e6e3",
            activebackground="#2a383e",
            activeforeground="#ffffff",
            relief="flat",
            padx=16,
            pady=8,
            cursor="hand2",
        ).pack(side="right")
        tk.Button(
            actions,
            text="继续",
            command=self.confirm,
            bg="#2ba994",
            fg="#071412",
            activebackground="#45d7c1",
            activeforeground="#071412",
            relief="flat",
            padx=16,
            pady=8,
            cursor="hand2",
        ).pack(side="right", padx=(0, 8))
        self.protocol("WM_DELETE_WINDOW", self.cancel)
        self.bind("<Return>", lambda _: self.confirm())
        self.bind("<Escape>", lambda _: self.cancel())
        self.entry.focus_set()

    def confirm(self) -> None:
        self.value = self.entry.get().strip()
        self.destroy()

    def cancel(self) -> None:
        self.value = ""
        self.destroy()


class EarthOnlineApp:
    BG = "#0d1216"
    SURFACE = "#151d22"
    SURFACE_RAISED = "#202a30"
    SURFACE_ACTIVE = "#2a373d"
    TEXT = "#eef7f5"
    MUTED = "#a6b8b5"
    ACCENT = "#45d7c1"
    ACCENT_DARK = "#2ba994"
    ERROR = "#f18377"
    WARNING = "#f0bf72"

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title(APP_NAME)
        self.root.geometry("780x626")
        self.root.minsize(740, 600)
        self.root.configure(bg=self.BG)
        if ICON_PATH.exists():
            self.window_icon = tk.PhotoImage(file=ICON_PATH)
            self.root.iconphoto(True, self.window_icon)

        self.api_key = self._read_api_key()
        self.region = core.load_region()
        self.relation = "ambiguous"
        self.busy = False
        self.calibrating = False
        self.generation_id = 0
        self.calibration_id = 0
        self.request_timeout_handle: str | None = None
        self.operation_kind = "idle"
        self.capture_hidden = False
        self.hotkeys: list[object] = []
        self.replies: list[str] = []
        self.analysis: dict[str, Any] | None = None
        self.analysis_note = ""
        self.reply_buttons: list[tk.Button] = []
        self.relation_buttons: dict[str, tk.Button] = {}
        self.status_var = tk.StringVar(value="已就绪" if self.region else "需要先校准聊天区域")
        self.message_var = tk.StringVar(value="尚未识别消息")
        self.shortcut_var = tk.StringVar(value="快捷键  Ctrl+Alt+J")

        self._build()
        self._set_relation(self.relation, announce=False)
        if not self.region:
            self.generate_button.configure(state="disabled")
        self._register_hotkeys()
        self.root.protocol("WM_DELETE_WINDOW", self.close)

    def _build(self) -> None:
        shell = tk.Frame(self.root, bg=self.BG, padx=22, pady=16)
        shell.pack(fill="both", expand=True)

        header = tk.Frame(shell, bg=self.BG)
        header.pack(fill="x")
        title_wrap = tk.Frame(header, bg=self.BG)
        title_wrap.pack(side="left")
        tk.Label(
            title_wrap,
            text="地球online",
            bg=self.BG,
            fg=self.TEXT,
            font=("Microsoft YaHei UI", 16, "bold"),
        ).pack(anchor="w")
        tk.Label(
            title_wrap,
            text="gal工具包",
            bg=self.BG,
            fg=self.ACCENT,
            font=("Microsoft YaHei UI", 10, "bold"),
        ).pack(anchor="w", pady=(1, 0))

        status = tk.Frame(header, bg=self.BG)
        status.pack(side="right", anchor="n", pady=(7, 0))
        self.status_dot = tk.Canvas(status, width=10, height=10, bg=self.BG, highlightthickness=0)
        self.status_dot.pack(side="left", padx=(0, 6))
        self.status_dot.create_oval(1, 1, 9, 9, fill=self.ACCENT, outline="")
        self.status_label = tk.Label(
            status,
            textvariable=self.status_var,
            bg=self.BG,
            fg=self.MUTED,
            font=("Microsoft YaHei UI", 9),
        )
        self.status_label.pack(side="left")

        self._divider(shell, pady=(14, 12))

        tk.Label(
            shell,
            text="对方最后一句",
            bg=self.BG,
            fg=self.TEXT,
            font=("Microsoft YaHei UI", 11, "bold"),
        ).pack(anchor="w")
        self.message_label = tk.Label(
            shell,
            textvariable=self.message_var,
            justify="left",
            anchor="nw",
            wraplength=700,
            bg=self.SURFACE,
            fg="#dce9e7",
            padx=14,
            pady=9,
            height=2,
            font=("Microsoft YaHei UI", 11),
        )
        self.message_label.pack(fill="x", pady=(8, 14))

        tk.Label(
            shell,
            text="关系语气",
            bg=self.BG,
            fg=self.TEXT,
            font=("Microsoft YaHei UI", 11, "bold"),
        ).pack(anchor="w")
        relation_bar = tk.Frame(shell, bg=self.BG)
        relation_bar.pack(fill="x", pady=(8, 14))
        for relation, label in RELATION_LABELS.items():
            button = tk.Button(
                relation_bar,
                text=label,
                command=lambda value=relation: self._set_relation(value),
                bg=self.SURFACE_RAISED,
                fg=self.MUTED,
                activebackground=self.SURFACE_ACTIVE,
                activeforeground=self.TEXT,
                relief="flat",
                bd=0,
                padx=11,
                pady=6,
                cursor="hand2",
                takefocus=True,
            )
            button.pack(side="left", expand=True, fill="x", padx=(0, 4) if relation != "friend" else 0)
            self.relation_buttons[relation] = button

        controls = tk.Frame(shell, bg=self.BG)
        controls.pack(fill="x", pady=(0, 14))
        self.generate_button = tk.Button(
            controls,
            text="生成回复",
            command=self.generate,
            bg=self.ACCENT_DARK,
            fg="#071412",
            activebackground=self.ACCENT,
            activeforeground="#071412",
            disabledforeground="#5a736f",
            relief="flat",
            bd=0,
            pady=9,
            cursor="hand2",
            font=("Microsoft YaHei UI", 11, "bold"),
        )
        self.generate_button.pack(side="left", fill="x", expand=True)
        self.cancel_button = tk.Button(
            controls,
            text="取消",
            command=self.cancel_current_operation,
            state="disabled",
            bg=self.SURFACE_RAISED,
            fg=self.TEXT,
            activebackground=self.SURFACE_ACTIVE,
            activeforeground=self.TEXT,
            disabledforeground="#76908c",
            relief="flat",
            bd=0,
            padx=12,
            pady=9,
            cursor="hand2",
        )
        self.cancel_button.pack(side="left", padx=(8, 0))
        self.connection_button = tk.Button(
            controls,
            text="检查连接",
            command=self.check_connection,
            bg=self.SURFACE_RAISED,
            fg=self.TEXT,
            activebackground=self.SURFACE_ACTIVE,
            activeforeground=self.TEXT,
            relief="flat",
            bd=0,
            padx=12,
            pady=9,
            cursor="hand2",
        )
        self.connection_button.pack(side="left", padx=(8, 0))
        self.calibrate_button = tk.Button(
            controls,
            text="校准区域",
            command=self.calibrate,
            bg=self.SURFACE_RAISED,
            fg=self.TEXT,
            activebackground=self.SURFACE_ACTIVE,
            activeforeground=self.TEXT,
            relief="flat",
            bd=0,
            padx=18,
            pady=9,
            cursor="hand2",
        )
        self.calibrate_button.pack(side="left", padx=(8, 0))

        results = tk.Frame(shell, bg=self.BG)
        results.pack(fill="x", pady=(0, 2))
        results.columnconfigure(0, weight=3, minsize=400)
        results.columnconfigure(1, weight=2, minsize=270)

        reply_column = tk.Frame(results, bg=self.BG)
        reply_column.grid(row=0, column=0, sticky="nsew")
        tk.Label(
            reply_column,
            text="候选回复",
            bg=self.BG,
            fg=self.TEXT,
            font=("Microsoft YaHei UI", 11, "bold"),
        ).pack(anchor="w")
        replies = tk.Frame(reply_column, bg=self.BG)
        replies.pack(fill="x", pady=(8, 0))
        for index in range(3):
            button = tk.Button(
                replies,
                text=f"{index + 1}   等待生成",
                command=lambda value=index: self.copy_reply(value),
                state="disabled",
                anchor="w",
                justify="left",
                wraplength=370,
                bg=self.SURFACE,
                fg="#76908c",
                activebackground=self.SURFACE_ACTIVE,
                activeforeground=self.TEXT,
                disabledforeground="#76908c",
                relief="flat",
                bd=0,
                padx=14,
                pady=8,
                cursor="hand2",
                font=("Microsoft YaHei UI", 10),
            )
            button.pack(fill="x", pady=(0, 5))
            self.reply_buttons.append(button)

        analysis_column = tk.Frame(results, bg=self.BG)
        analysis_column.grid(row=0, column=1, sticky="nsew", padx=(14, 0))
        analysis_header = tk.Frame(analysis_column, bg=self.BG)
        analysis_header.pack(fill="x")
        tk.Label(
            analysis_header,
            text="具体判断",
            bg=self.BG,
            fg=self.TEXT,
            font=("Microsoft YaHei UI", 11, "bold"),
        ).pack(side="left")
        self.analysis_source_var = tk.StringVar(value="等待生成")
        tk.Label(
            analysis_header,
            textvariable=self.analysis_source_var,
            bg=self.BG,
            fg=self.MUTED,
            font=("Microsoft YaHei UI", 9),
        ).pack(side="right", pady=(3, 0))

        analysis_card = tk.Frame(analysis_column, bg=self.SURFACE, padx=12, pady=10)
        analysis_card.pack(fill="x", pady=(8, 0))
        self.analysis_question_var = tk.StringVar(value="生成后显示本次模型判断")
        tk.Label(
            analysis_card,
            textvariable=self.analysis_question_var,
            bg=self.SURFACE,
            fg=self.TEXT,
            anchor="w",
            justify="left",
            wraplength=250,
            font=("Microsoft YaHei UI", 10, "bold"),
        ).pack(fill="x")

        answer_row = tk.Frame(analysis_card, bg=self.SURFACE_RAISED, padx=10, pady=7)
        answer_row.pack(fill="x", pady=(8, 10))
        self.analysis_yes_var = tk.StringVar(value="Yes  --")
        self.analysis_yes_label = tk.Label(
            answer_row,
            textvariable=self.analysis_yes_var,
            bg=self.SURFACE_RAISED,
            fg=self.MUTED,
            font=("Microsoft YaHei UI", 10, "bold"),
        )
        self.analysis_yes_label.pack(side="left")
        self.analysis_no_var = tk.StringVar(value="No  --")
        self.analysis_no_label = tk.Label(
            answer_row,
            textvariable=self.analysis_no_var,
            bg=self.SURFACE_RAISED,
            fg=self.MUTED,
            font=("Microsoft YaHei UI", 10, "bold"),
        )
        self.analysis_no_label.pack(side="right")

        tk.Label(
            analysis_card,
            text="最佳动作",
            bg=self.SURFACE,
            fg=self.MUTED,
            font=("Microsoft YaHei UI", 9, "bold"),
        ).pack(anchor="w")
        self.analysis_best_action_var = tk.StringVar(value="等待生成")
        self.analysis_best_action_label = tk.Label(
            analysis_card,
            textvariable=self.analysis_best_action_var,
            bg=self.SURFACE,
            fg=self.MUTED,
            anchor="w",
            justify="left",
            wraplength=250,
            font=("Microsoft YaHei UI", 10, "bold"),
        )
        self.analysis_best_action_label.pack(fill="x", pady=(3, 5))

        self.analysis_action_vars = [tk.StringVar(value=f"{index + 1}. 等待行动建议") for index in range(3)]
        for variable in self.analysis_action_vars:
            tk.Label(
                analysis_card,
                textvariable=variable,
                bg=self.SURFACE,
                fg="#c7d7d4",
                anchor="w",
                justify="left",
                wraplength=250,
                font=("Microsoft YaHei UI", 9),
            ).pack(fill="x", pady=1)

        risk_row = tk.Frame(analysis_card, bg=self.SURFACE_RAISED, padx=10, pady=6)
        risk_row.pack(fill="x", pady=(8, 0))
        tk.Label(
            risk_row,
            text="措辞风险",
            bg=self.SURFACE_RAISED,
            fg=self.TEXT,
            font=("Microsoft YaHei UI", 9, "bold"),
        ).pack(side="left")
        self.analysis_risk_var = tk.StringVar(value="-- / 10")
        self.analysis_risk_label = tk.Label(
            risk_row,
            textvariable=self.analysis_risk_var,
            bg=self.SURFACE_RAISED,
            fg=self.MUTED,
            font=("Cascadia Mono", 10, "bold"),
        )
        self.analysis_risk_label.pack(side="right")

        self.analysis_note_var = tk.StringVar(value="生成完成后显示是否应回复、推荐动作与措辞风险。")
        tk.Label(
            analysis_column,
            textvariable=self.analysis_note_var,
            bg=self.BG,
            fg=self.MUTED,
            anchor="w",
            justify="left",
            wraplength=260,
            font=("Microsoft YaHei UI", 9),
        ).pack(fill="x", pady=(7, 0))

        footer = tk.Frame(shell, bg=self.BG)
        footer.pack(side="bottom", fill="x", pady=(10, 0))
        self.topmost_var = tk.BooleanVar(value=False)
        tk.Checkbutton(
            footer,
            text="窗口置顶",
            variable=self.topmost_var,
            command=self._toggle_topmost,
            bg=self.BG,
            fg=self.MUTED,
            activebackground=self.BG,
            activeforeground=self.TEXT,
            selectcolor=self.SURFACE_RAISED,
            highlightthickness=0,
            font=("Microsoft YaHei UI", 9),
        ).pack(side="left")
        tk.Label(
            footer,
            textvariable=self.shortcut_var,
            bg=self.BG,
            fg=self.MUTED,
            font=("Cascadia Mono", 9),
        ).pack(side="right")

    def _divider(self, parent: tk.Widget, pady: tuple[int, int]) -> None:
        tk.Frame(parent, bg="#2a363b", height=1).pack(fill="x", pady=pady)

    def _read_api_key(self) -> str:
        value = os.environ.get("DEEPSEEK_API_KEY", "").strip()
        return value or core.load_dotenv_api_key()

    def _request_api_key(self) -> bool:
        dialog = ApiKeyDialog(self.root)
        self.root.wait_window(dialog)
        if dialog.value:
            self.api_key = dialog.value
            return True
        self._set_status("需要 API Key 才能生成回复", self.WARNING)
        return False

    def _set_status(self, text: str, color: str | None = None) -> None:
        self.status_var.set(text)
        self.status_dot.itemconfig(1, fill=color or self.ACCENT)

    def _set_relation(self, relation: str, announce: bool = True) -> None:
        if self.busy and relation != self.relation:
            self._set_status("正在生成，本次结束后再切换语气", self.WARNING)
            return
        relation_changed = relation != self.relation
        self.relation = relation
        for key, button in self.relation_buttons.items():
            selected = key == relation
            button.configure(
                bg=self.ACCENT_DARK if selected else self.SURFACE_RAISED,
                fg="#071412" if selected else self.MUTED,
                activebackground=self.ACCENT if selected else self.SURFACE_ACTIVE,
            )
        if not announce:
            return
        if relation_changed:
            self._clear_results("关系已切换")
        if not self.region:
            self._set_status("需要先校准聊天区域", self.WARNING)
            return
        self._set_status(f"当前语气：{RELATION_LABELS[relation]}")

    def _toggle_topmost(self) -> None:
        self.root.attributes("-topmost", self.topmost_var.get())

    def _register_hotkeys(self) -> None:
        try:
            import keyboard

            self.hotkeys.append(keyboard.add_hotkey("ctrl+alt+j", lambda: self.root.after(0, self.generate)))
            for number, relation in core.RELATION_KEYS.items():
                self.hotkeys.append(
                    keyboard.add_hotkey(
                        f"ctrl+alt+{number}",
                        lambda value=relation: self.root.after(0, lambda: self._set_relation(value)),
                    )
                )
        except Exception as error:
            self.shortcut_var.set("快捷键注册失败")
            self._set_status(f"快捷键不可用：{error}", self.WARNING)

    def calibrate(self) -> None:
        if self.calibrating or self.busy:
            return
        self.calibrating = True
        self.calibration_id += 1
        self.calibrate_button.configure(state="disabled")
        self.connection_button.configure(state="disabled")
        self.cancel_button.configure(state="normal")
        self._countdown(self.calibration_id, "左上角", 3, self._capture_top_left)

    def _countdown(self, calibration_id: int, label: str, seconds: int, callback: Callable[[int], None]) -> None:
        if calibration_id != self.calibration_id or not self.calibrating:
            return
        if seconds:
            self._set_status(f"{seconds} 秒后记录聊天区{label}，请移动鼠标", self.WARNING)
            self.root.after(1000, lambda: self._countdown(calibration_id, label, seconds - 1, callback))
            return
        callback(calibration_id)

    def _capture_top_left(self, calibration_id: int) -> None:
        if calibration_id != self.calibration_id or not self.calibrating:
            return
        try:
            import pyautogui

            self.calibration_start = pyautogui.position()
            self._countdown(calibration_id, "右下角", 3, self._capture_bottom_right)
        except Exception as error:
            self._finish_calibration_error(calibration_id, error)

    def _capture_bottom_right(self, calibration_id: int) -> None:
        if calibration_id != self.calibration_id or not self.calibrating:
            return
        try:
            import pyautogui

            end = pyautogui.position()
            self.region = core.save_region(
                (self.calibration_start.x, self.calibration_start.y, end.x - self.calibration_start.x, end.y - self.calibration_start.y)
            )
            self.generate_button.configure(state="normal")
            self._set_status(f"聊天区域已保存：{self.region[2]} x {self.region[3]}")
        except Exception as error:
            self._finish_calibration_error(calibration_id, error)
            return
        self.calibrating = False
        self.calibrate_button.configure(state="normal")
        self.connection_button.configure(state="normal")
        self.cancel_button.configure(state="disabled")

    def _finish_calibration_error(self, calibration_id: int, error: Exception) -> None:
        if calibration_id != self.calibration_id:
            return
        self.calibrating = False
        self.calibrate_button.configure(state="normal")
        self.connection_button.configure(state="normal")
        self.cancel_button.configure(state="disabled")
        self._set_status(f"校准失败：{error}", self.ERROR)

    def generate(self) -> None:
        if self.busy or self.calibrating:
            return
        if not self.region:
            self._set_status("请先校准聊天区域", self.WARNING)
            return
        if not self.api_key and not self._request_api_key():
            return
        self.busy = True
        self.operation_kind = "generation"
        self.generation_id += 1
        generation_id = self.generation_id
        self._clear_results("正在生成")
        self.generate_button.configure(state="disabled", text="正在识别和生成...")
        self.connection_button.configure(state="disabled")
        self.cancel_button.configure(state="normal")
        self._set_status("正在读取聊天内容")
        self._hide_for_capture()
        self.root.after(
            250,
            lambda: self._start_generation_worker(generation_id, self.api_key, self.region, self.relation),
        )

    def _hide_for_capture(self) -> None:
        self.root.withdraw()
        self.capture_hidden = True

    def _restore_after_capture(self) -> None:
        if not self.capture_hidden:
            return
        self.root.deiconify()
        self.root.lift()
        self.capture_hidden = False

    def _start_generation_worker(
        self,
        generation_id: int,
        api_key: str,
        region: tuple[int, int, int, int] | None,
        relation: str,
    ) -> None:
        if generation_id != self.generation_id or not self.busy:
            return
        threading.Thread(
            target=self._generate_worker,
            args=(generation_id, api_key, region, relation),
            daemon=True,
        ).start()

    def check_connection(self) -> None:
        if self.busy or self.calibrating:
            return
        if not self.api_key and not self._request_api_key():
            return
        self.busy = True
        self.operation_kind = "connection"
        self.generation_id += 1
        generation_id = self.generation_id
        self.generate_button.configure(state="disabled")
        self.connection_button.configure(state="disabled", text="正在检查...")
        self.cancel_button.configure(state="normal")
        self._set_status("正在测试 DeepSeek 推理，不发送聊天内容")
        self._start_request_timeout(generation_id)
        threading.Thread(target=self._connection_worker, args=(generation_id, self.api_key), daemon=True).start()

    def _connection_worker(self, generation_id: int, api_key: str) -> None:
        try:
            core.test_deepseek_connection(api_key)
            self.root.after(0, lambda: self._show_connection_result(generation_id, "DeepSeek 推理正常，可以生成回复", None))
        except core.ToolkitError as error:
            self.root.after(0, lambda: self._show_connection_result(generation_id, str(error), self.ERROR))
        except Exception as error:
            self.root.after(0, lambda: self._show_connection_result(generation_id, f"连接检查失败：{error}", self.ERROR))

    def _show_connection_result(self, generation_id: int, message: str, color: str | None) -> None:
        if generation_id != self.generation_id or not self.busy:
            return
        self._finish_generation(generation_id, message, color)

    def _generate_worker(
        self,
        generation_id: int,
        api_key: str,
        region: tuple[int, int, int, int] | None,
        relation: str,
    ) -> None:
        if not region:
            return
        try:
            context = core.capture_chat_context(region)
            self.root.after(0, lambda: self._show_recognized_context(generation_id, context))
            suggestion = core.analyze_chat(api_key, "deepseek-chat", relation, context)
            self.root.after(0, lambda: self._show_suggestion(generation_id, context, suggestion))
        except core.ToolkitError as error:
            self.root.after(0, lambda: self._finish_generation_error(generation_id, str(error)))
        except Exception as error:
            self.root.after(0, lambda: self._finish_generation_error(generation_id, f"未预期错误：{error}"))

    def _show_recognized_context(self, generation_id: int, context: core.ChatContext) -> None:
        if generation_id != self.generation_id or not self.busy:
            return
        self._restore_after_capture()
        self.message_var.set(context.latest_incoming)
        self.generate_button.configure(text="正在请求 DeepSeek...")
        self._set_status(f"已识别消息，正在请求 DeepSeek（最多 {int(core.REQUEST_TIMEOUT_SECONDS)} 秒）")
        self._start_request_timeout(generation_id)

    def _start_request_timeout(self, generation_id: int) -> None:
        self._cancel_request_timeout()
        milliseconds = int(core.REQUEST_TIMEOUT_SECONDS * 1000)
        self.request_timeout_handle = self.root.after(milliseconds, lambda: self._handle_request_timeout(generation_id))

    def _cancel_request_timeout(self) -> None:
        if not self.request_timeout_handle:
            return
        try:
            self.root.after_cancel(self.request_timeout_handle)
        except tk.TclError:
            pass
        self.request_timeout_handle = None

    def _handle_request_timeout(self, generation_id: int) -> None:
        self.request_timeout_handle = None
        if generation_id != self.generation_id or not self.busy:
            return
        self._restore_after_capture()
        operation_kind = self.operation_kind
        self.busy = False
        self.generation_id += 1
        if operation_kind != "connection":
            self._clear_results("请求超时")
        self.generate_button.configure(state="normal", text="生成回复")
        self.connection_button.configure(state="normal", text="检查连接")
        self.cancel_button.configure(state="disabled")
        self.operation_kind = "idle"
        if operation_kind == "connection":
            self._set_status("推理测试未响应，请检查网络后重试", self.ERROR)
        else:
            self._set_status("DeepSeek 45 秒未响应，请检查 Key 或网络后重试", self.ERROR)

    def _show_suggestion(self, generation_id: int, context: core.ChatContext, suggestion: dict[str, object]) -> None:
        if generation_id != self.generation_id or not self.busy:
            return
        self.message_var.set(context.latest_incoming)
        analysis = suggestion.get("analysis")
        if isinstance(analysis, Mapping):
            self.analysis = dict(analysis)
            self.analysis_note = str(suggestion.get("note", "")).strip()
            self._render_analysis_panel()
        else:
            self._reset_analysis_panel()
        replies = suggestion.get("replies", [])
        should_reply = suggestion.get("should_reply") is True
        if not should_reply or not isinstance(replies, list) or not replies:
            self._reset_reply_buttons("建议先不回")
            self._finish_generation(generation_id, "模型建议先不回复；判断已显示在右侧", self.WARNING)
            return
        self.replies = [reply if isinstance(reply, str) else "" for reply in replies[:3]]
        for index, button in enumerate(self.reply_buttons):
            reply = self.replies[index] if index < len(self.replies) else ""
            if isinstance(reply, str) and reply:
                button.configure(text=f"{index + 1}   {reply}   点击复制", state="normal", fg=self.TEXT)
            else:
                button.configure(text=f"{index + 1}   暂无候选", state="disabled", fg="#76908c")
        note = suggestion.get("note", "")
        note_text = str(note).strip() if note else ""
        self._finish_generation(generation_id, note_text or "已生成候选回复和具体判断")

    def _finish_generation(self, generation_id: int, status: str, color: str | None = None) -> None:
        if generation_id != self.generation_id:
            return
        self._cancel_request_timeout()
        self.busy = False
        self.operation_kind = "idle"
        self.generate_button.configure(state="normal", text="生成回复")
        self.connection_button.configure(state="normal", text="检查连接")
        self.cancel_button.configure(state="disabled")
        self._set_status(status, color)

    def _finish_generation_error(self, generation_id: int, message: str) -> None:
        if generation_id != self.generation_id:
            return
        self._restore_after_capture()
        self._clear_results("本次未生成")
        self._finish_generation(generation_id, message, self.ERROR)

    def cancel_current_operation(self) -> None:
        if self.calibrating:
            self.calibrating = False
            self.calibration_id += 1
            self.calibrate_button.configure(state="normal")
            self.connection_button.configure(state="normal")
            self.cancel_button.configure(state="disabled")
            self._set_status("已取消区域校准", self.WARNING)
            return
        if self.busy:
            operation_kind = self.operation_kind
            self.busy = False
            self.generation_id += 1
            self._cancel_request_timeout()
            self._restore_after_capture()
            if operation_kind != "connection":
                self._clear_results("已取消")
            self.generate_button.configure(state="normal", text="生成回复")
            self.connection_button.configure(state="normal", text="检查连接")
            self.cancel_button.configure(state="disabled")
            self.operation_kind = "idle"
            self._set_status("已取消本轮操作，后台返回会自动丢弃", self.WARNING)

    def _clear_results(self, reply_text: str) -> None:
        self._reset_reply_buttons(reply_text)
        self.analysis = None
        self.analysis_note = ""
        self._reset_analysis_panel()

    def _reset_analysis_panel(self) -> None:
        self.analysis_source_var.set("等待生成")
        self.analysis_question_var.set("生成后显示本次模型判断")
        self.analysis_yes_var.set("Yes  --")
        self.analysis_no_var.set("No  --")
        self.analysis_yes_label.configure(fg=self.MUTED)
        self.analysis_no_label.configure(fg=self.MUTED)
        self.analysis_best_action_var.set("等待生成")
        self.analysis_best_action_label.configure(fg=self.MUTED)
        for index, variable in enumerate(self.analysis_action_vars):
            variable.set(f"{index + 1}. 等待行动建议")
        self.analysis_risk_var.set("-- / 10")
        self.analysis_risk_label.configure(fg=self.MUTED)
        self.analysis_note_var.set("生成完成后显示是否应回复、推荐动作与措辞风险。")

    def _render_analysis_panel(self) -> None:
        if not self.analysis:
            self._reset_analysis_panel()
            return

        analysis = self.analysis
        source = "基础判断" if analysis.get("is_estimate") else "模型倾向"
        self.analysis_source_var.set(source)
        question = str(analysis.get("question", "是否应该立刻回答具体内容？")).strip()
        self.analysis_question_var.set(question or "是否应该立刻回答具体内容？")
        self.analysis_yes_var.set(f"Yes  {analysis.get('yes', 0)}%")
        self.analysis_no_var.set(f"No  {analysis.get('no', 0)}%")
        self.analysis_yes_label.configure(fg=self.ACCENT)
        self.analysis_no_label.configure(fg=self.WARNING)
        best_action = str(analysis.get("best_action", "")).strip()
        self.analysis_best_action_var.set(best_action or "暂未给出最佳动作")
        self.analysis_best_action_label.configure(fg=self.ACCENT)

        actions = analysis.get("actions", [])
        for index, variable in enumerate(self.analysis_action_vars):
            action = actions[index] if isinstance(actions, list) and index < len(actions) else None
            if isinstance(action, Mapping):
                label = str(action.get("label", "暂未给出行动")).strip() or "暂未给出行动"
                probability = action.get("probability", 0)
                variable.set(f"{index + 1}. {label}  {probability}%")
            else:
                variable.set(f"{index + 1}. 暂未给出行动")

        try:
            risk = max(0, min(10, int(analysis.get("risk_level", 0))))
        except (TypeError, ValueError):
            risk = 0
        self.analysis_risk_var.set(f"{risk} / 10")
        self.analysis_risk_label.configure(fg=self.WARNING if risk >= 6 else self.ACCENT)
        self.analysis_note_var.set(self.analysis_note or "模型判断基于当前识别内容，仅供参考。")

    def _reset_reply_buttons(self, text: str) -> None:
        self.replies = []
        for index, button in enumerate(self.reply_buttons):
            button.configure(text=f"{index + 1}   {text}", state="disabled", fg="#76908c")

    def copy_reply(self, index: int) -> None:
        reply = self.replies[index] if index < len(self.replies) else ""
        if not reply:
            return
        try:
            import pyperclip

            pyperclip.copy(reply)
            self._set_status(f"已复制第 {index + 1} 条，确认后手动发送")
        except Exception as error:
            self._set_status(f"复制失败：{error}", self.ERROR)

    def close(self) -> None:
        self._cancel_request_timeout()
        try:
            import keyboard

            for handle in self.hotkeys:
                keyboard.remove_hotkey(handle)
        except Exception:
            pass
        self.root.destroy()


def main() -> None:
    enable_dpi_awareness()
    root = tk.Tk()
    EarthOnlineApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
