"""Tkinter user interface for the lightweight Windows desktop app."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from .engine import proofread_text
from .profiles import DEFAULT_PROFILES, profile_description, profile_names

WINDOW_TITLE = "Proofread App"


class ProofreadApp(tk.Tk):
    """Main desktop window with a single-screen proofreading workflow."""

    def __init__(self) -> None:
        super().__init__()
        self.title(WINDOW_TITLE)
        self.minsize(760, 560)
        self.geometry("900x660")
        self.configure(background="#f3f4f6")

        self.profile_var = tk.StringVar(value=DEFAULT_PROFILES[0].name)
        self.status_var = tk.StringVar(value="Ready")
        self.description_var = tk.StringVar(value=profile_description(self.profile_var.get()))

        self._configure_style()
        self._build_layout()

    def _configure_style(self) -> None:
        self.style = ttk.Style(self)
        if "vista" in self.style.theme_names():
            self.style.theme_use("vista")
        self.option_add("*Font", ("Segoe UI", 10))
        self.style.configure("App.TFrame", background="#f3f4f6")
        self.style.configure("Card.TFrame", background="#ffffff", relief="flat")
        self.style.configure("Title.TLabel", background="#f3f4f6", font=("Segoe UI Semibold", 18))
        self.style.configure("Hint.TLabel", background="#ffffff", foreground="#4b5563")
        self.style.configure("Status.TLabel", background="#f3f4f6", foreground="#4b5563")
        self.style.configure("Primary.TButton", font=("Segoe UI Semibold", 10), padding=(18, 8))
        self.style.configure("Secondary.TButton", padding=(14, 7))

    def _build_layout(self) -> None:
        shell = ttk.Frame(self, padding=20, style="App.TFrame")
        shell.grid(row=0, column=0, sticky="nsew")
        shell.columnconfigure(0, weight=1)
        shell.rowconfigure(2, weight=1)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        ttk.Label(shell, text="Proofread App", style="Title.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            shell,
            text="Paste text, choose a profile, and proofread without accounts or web views.",
            style="Status.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(4, 16))

        content = ttk.Frame(shell, style="App.TFrame")
        content.grid(row=2, column=0, sticky="nsew")
        content.columnconfigure(0, weight=1)
        content.columnconfigure(1, weight=1)
        content.rowconfigure(0, weight=1)

        input_card = self._build_input_card(content)
        input_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        output_card = self._build_output_card(content)
        output_card.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        footer = ttk.Frame(shell, style="App.TFrame")
        footer.grid(row=3, column=0, sticky="ew", pady=(16, 0))
        footer.columnconfigure(0, weight=1)
        ttk.Label(footer, textvariable=self.status_var, style="Status.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Button(footer, text="Copy Result", command=self.copy_result, style="Secondary.TButton").grid(
            row=0, column=1, padx=(8, 0)
        )
        ttk.Button(footer, text="Clear", command=self.clear_text, style="Secondary.TButton").grid(
            row=0, column=2, padx=(8, 0)
        )
        ttk.Button(footer, text="Edit Profiles", command=self.show_profiles, style="Secondary.TButton").grid(
            row=0, column=3, padx=(8, 0)
        )

    def _build_input_card(self, parent: ttk.Frame) -> ttk.Frame:
        card = ttk.Frame(parent, padding=16, style="Card.TFrame")
        card.columnconfigure(0, weight=1)
        card.rowconfigure(3, weight=1)

        ttk.Label(card, text="Input", background="#ffffff", font=("Segoe UI Semibold", 12)).grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(card, text="Type or paste the text to correct.", style="Hint.TLabel").grid(
            row=1, column=0, sticky="w", pady=(2, 12)
        )

        controls = ttk.Frame(card, style="Card.TFrame")
        controls.grid(row=2, column=0, sticky="ew", pady=(0, 12))
        controls.columnconfigure(1, weight=1)
        ttk.Label(controls, text="Profile", background="#ffffff").grid(row=0, column=0, sticky="w", padx=(0, 8))
        profile_menu = ttk.Combobox(
            controls,
            textvariable=self.profile_var,
            values=profile_names(),
            state="readonly",
            width=18,
        )
        profile_menu.grid(row=0, column=1, sticky="w")
        profile_menu.bind("<<ComboboxSelected>>", self._update_profile_description)
        ttk.Button(controls, text="Proofread", command=self.run_proofread, style="Primary.TButton").grid(
            row=0, column=2, sticky="e"
        )

        ttk.Label(card, textvariable=self.description_var, style="Hint.TLabel", wraplength=360).grid(
            row=3, column=0, sticky="new", pady=(0, 8)
        )

        text_frame = ttk.Frame(card, style="Card.TFrame")
        text_frame.grid(row=4, column=0, sticky="nsew")
        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(0, weight=1)
        card.rowconfigure(4, weight=1)

        self.input_text = tk.Text(
            text_frame,
            wrap="word",
            undo=True,
            borderwidth=1,
            relief="solid",
            padx=10,
            pady=10,
            font=("Segoe UI", 10),
        )
        self.input_text.grid(row=0, column=0, sticky="nsew")
        input_scroll = ttk.Scrollbar(text_frame, command=self.input_text.yview)
        input_scroll.grid(row=0, column=1, sticky="ns")
        self.input_text.configure(yscrollcommand=input_scroll.set)
        return card

    def _build_output_card(self, parent: ttk.Frame) -> ttk.Frame:
        card = ttk.Frame(parent, padding=16, style="Card.TFrame")
        card.columnconfigure(0, weight=1)
        card.rowconfigure(2, weight=1)

        ttk.Label(card, text="Corrected version", background="#ffffff", font=("Segoe UI Semibold", 12)).grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(card, text="Review the result, then copy it when ready.", style="Hint.TLabel").grid(
            row=1, column=0, sticky="w", pady=(2, 12)
        )

        text_frame = ttk.Frame(card, style="Card.TFrame")
        text_frame.grid(row=2, column=0, sticky="nsew")
        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(0, weight=1)

        self.output_text = tk.Text(
            text_frame,
            wrap="word",
            borderwidth=1,
            relief="solid",
            padx=10,
            pady=10,
            font=("Segoe UI", 10),
            background="#fbfdff",
        )
        self.output_text.grid(row=0, column=0, sticky="nsew")
        output_scroll = ttk.Scrollbar(text_frame, command=self.output_text.yview)
        output_scroll.grid(row=0, column=1, sticky="ns")
        self.output_text.configure(yscrollcommand=output_scroll.set)
        return card

    def _update_profile_description(self, _event: tk.Event | None = None) -> None:
        self.description_var.set(profile_description(self.profile_var.get()))

    def run_proofread(self) -> None:
        source = self.input_text.get("1.0", "end-1c")
        if not source.strip():
            self.status_var.set("Add text before proofreading.")
            self.input_text.focus_set()
            return

        result = proofread_text(source, self.profile_var.get())
        self.output_text.delete("1.0", "end")
        self.output_text.insert("1.0", result)
        self.status_var.set(f"Proofread with {self.profile_var.get()} profile.")

    def copy_result(self) -> None:
        result = self.output_text.get("1.0", "end-1c")
        if not result.strip():
            self.status_var.set("There is no result to copy.")
            return
        self.clipboard_clear()
        self.clipboard_append(result)
        self.status_var.set("Result copied to clipboard.")

    def clear_text(self) -> None:
        self.input_text.delete("1.0", "end")
        self.output_text.delete("1.0", "end")
        self.status_var.set("Cleared input and output.")
        self.input_text.focus_set()

    def show_profiles(self) -> None:
        details = "\n\n".join(f"{profile.name}: {profile.description}" for profile in DEFAULT_PROFILES)
        messagebox.showinfo("Edit Profiles", f"Profile editing placeholder for the first UI.\n\n{details}")


def main() -> None:
    app = ProofreadApp()
    app.mainloop()
