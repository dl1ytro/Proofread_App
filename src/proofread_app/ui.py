"""Tkinter user interface for the lightweight Windows desktop app."""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from .engine import LOCAL_LLM_UNAVAILABLE_MESSAGE, LocalLLMConfigurationError, LocalLLMUnavailable, proofread_text
from .profiles import (
    ProfileError,
    ProofreadingProfile,
    delete_profile,
    duplicate_profile,
    export_profile,
    import_profile,
    load_profiles,
    profile_description,
    profile_names,
    save_profile,
)
from .settings import SettingsError, load_settings, parse_settings, save_settings

WINDOW_TITLE = "Proofread App"


class ProofreadApp(tk.Tk):
    """Main desktop window with a single-screen proofreading workflow."""

    def __init__(self) -> None:
        super().__init__()
        self.title(WINDOW_TITLE)
        self.minsize(760, 560)
        self.geometry("900x660")
        self.configure(background="#f3f4f6")

        self.profiles = load_profiles()
        self.profile_var = tk.StringVar(value=self.profiles[0].name)
        self.status_var = tk.StringVar(value="Ready")
        self.description_var = tk.StringVar(value=profile_description(self.profile_var.get(), self.profiles))
        self.settings = load_settings()

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
            text="Paste text, choose a profile, and proofread with your local Ollama model.",
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
        ttk.Button(footer, text="Settings", command=self.show_settings, style="Secondary.TButton").grid(
            row=0, column=3, padx=(8, 0)
        )
        ttk.Button(footer, text="Edit Profiles", command=self.show_profiles, style="Secondary.TButton").grid(
            row=0, column=4, padx=(8, 0)
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
        self.profile_menu = ttk.Combobox(
            controls,
            textvariable=self.profile_var,
            values=profile_names(self.profiles),
            state="readonly",
            width=18,
        )
        self.profile_menu.grid(row=0, column=1, sticky="w")
        self.profile_menu.bind("<<ComboboxSelected>>", self._update_profile_description)
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
        self.description_var.set(profile_description(self.profile_var.get(), self.profiles))


    def _selected_profile(self) -> ProofreadingProfile:
        for profile in self.profiles:
            if profile.name == self.profile_var.get():
                return profile
        return self.profiles[0]

    def _refresh_profile_menu(self) -> None:
        names = profile_names(self.profiles)
        self.profile_menu.configure(values=names)
        if self.profile_var.get() not in names:
            self.profile_var.set(names[0])
        self._update_profile_description()

    def run_proofread(self) -> None:
        source = self.input_text.get("1.0", "end-1c")
        if not source.strip():
            self.status_var.set("Add text before proofreading.")
            self.input_text.focus_set()
            return

        self.status_var.set("Sending request to local Ollama...")
        self.update_idletasks()

        try:
            result = proofread_text(source, self._selected_profile(), self.settings)
        except LocalLLMUnavailable as exc:
            message = str(exc) or LOCAL_LLM_UNAVAILABLE_MESSAGE
            self.status_var.set(message)
            messagebox.showwarning("Local LLM unavailable", message)
            return
        except LocalLLMConfigurationError as exc:
            self.status_var.set(str(exc))
            messagebox.showerror("Settings error", str(exc))
            return

        self.output_text.delete("1.0", "end")
        self.output_text.insert("1.0", result)
        self.status_var.set(f"Proofread offline with {self.settings.ollama_model} using {self.profile_var.get()} profile.")

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

    def show_settings(self) -> None:
        """Open a settings dialog for the local Ollama backend."""

        dialog = tk.Toplevel(self)
        dialog.title("Settings")
        dialog.transient(self)
        dialog.grab_set()
        dialog.configure(background="#ffffff")
        dialog.resizable(False, False)

        endpoint_var = tk.StringVar(value=self.settings.ollama_endpoint)
        model_var = tk.StringVar(value=self.settings.ollama_model)
        timeout_var = tk.StringVar(value=str(self.settings.ollama_timeout))

        frame = ttk.Frame(dialog, padding=16, style="Card.TFrame")
        frame.grid(row=0, column=0, sticky="nsew")
        frame.columnconfigure(1, weight=1)

        ttk.Label(frame, text="Local LLM settings", background="#ffffff", font=("Segoe UI Semibold", 12)).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 8)
        )
        ttk.Label(
            frame,
            text="Proofreading requests are sent only to the local Ollama endpoint below.",
            style="Hint.TLabel",
            wraplength=360,
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 12))

        ttk.Label(frame, text="Ollama endpoint", background="#ffffff").grid(row=2, column=0, sticky="w", pady=(0, 6))
        ttk.Entry(frame, textvariable=endpoint_var, width=38).grid(row=2, column=1, sticky="ew", pady=(0, 6))

        ttk.Label(frame, text="Model name", background="#ffffff").grid(row=3, column=0, sticky="w", pady=(0, 6))
        ttk.Entry(frame, textvariable=model_var, width=38).grid(row=3, column=1, sticky="ew", pady=(0, 6))

        ttk.Label(frame, text="Timeout (seconds)", background="#ffffff").grid(row=4, column=0, sticky="w", pady=(0, 12))
        ttk.Entry(frame, textvariable=timeout_var, width=38).grid(row=4, column=1, sticky="ew", pady=(0, 12))

        buttons = ttk.Frame(frame, style="Card.TFrame")
        buttons.grid(row=5, column=0, columnspan=2, sticky="e")

        def save() -> None:
            try:
                parsed = parse_settings(endpoint_var.get(), model_var.get(), timeout_var.get())
                self.settings = save_settings(parsed)
            except SettingsError as exc:
                messagebox.showerror("Settings error", str(exc), parent=dialog)
                return
            self.status_var.set("Settings saved for local Ollama.")
            dialog.destroy()

        ttk.Button(buttons, text="Cancel", command=dialog.destroy, style="Secondary.TButton").grid(
            row=0, column=0, padx=(0, 8)
        )
        ttk.Button(buttons, text="Save", command=save, style="Primary.TButton").grid(row=0, column=1)
        dialog.wait_window()

    def show_profiles(self) -> None:
        """Open a profile manager for portable JSON proofreading profiles."""

        dialog = tk.Toplevel(self)
        dialog.title("Profiles")
        dialog.transient(self)
        dialog.grab_set()
        dialog.configure(background="#ffffff")
        dialog.minsize(780, 520)

        selected_index = tk.IntVar(value=0)
        name_var = tk.StringVar()
        temperature_var = tk.StringVar()
        explain_var = tk.BooleanVar(value=False)
        preserve_var = tk.BooleanVar(value=True)

        frame = ttk.Frame(dialog, padding=16, style="Card.TFrame")
        frame.grid(row=0, column=0, sticky="nsew")
        dialog.columnconfigure(0, weight=1)
        dialog.rowconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(2, weight=1)

        ttk.Label(frame, text="Proofreading profiles", background="#ffffff", font=("Segoe UI Semibold", 12)).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 4)
        )
        ttk.Label(
            frame,
            text="Profiles are portable JSON files that can be exported, imported, or copied to another Windows machine.",
            style="Hint.TLabel",
            wraplength=720,
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 12))

        list_frame = ttk.Frame(frame, style="Card.TFrame")
        list_frame.grid(row=2, column=0, sticky="nsw", padx=(0, 14))
        list_frame.rowconfigure(0, weight=1)
        profile_list = tk.Listbox(list_frame, width=24, exportselection=False)
        profile_list.grid(row=0, column=0, sticky="ns")
        list_scroll = ttk.Scrollbar(list_frame, command=profile_list.yview)
        list_scroll.grid(row=0, column=1, sticky="ns")
        profile_list.configure(yscrollcommand=list_scroll.set)

        editor = ttk.Frame(frame, style="Card.TFrame")
        editor.grid(row=2, column=1, sticky="nsew")
        editor.columnconfigure(1, weight=1)
        editor.rowconfigure(2, weight=1)

        ttk.Label(editor, text="Name", background="#ffffff").grid(row=0, column=0, sticky="w", pady=(0, 6))
        ttk.Entry(editor, textvariable=name_var).grid(row=0, column=1, sticky="ew", pady=(0, 6))

        ttk.Label(editor, text="Description", background="#ffffff").grid(row=1, column=0, sticky="nw", pady=(0, 6))
        description_text = tk.Text(editor, height=3, wrap="word", borderwidth=1, relief="solid", padx=8, pady=6)
        description_text.grid(row=1, column=1, sticky="ew", pady=(0, 6))

        ttk.Label(editor, text="System message", background="#ffffff").grid(row=2, column=0, sticky="nw", pady=(0, 6))
        system_text = tk.Text(editor, height=8, wrap="word", borderwidth=1, relief="solid", padx=8, pady=6)
        system_text.grid(row=2, column=1, sticky="nsew", pady=(0, 6))

        ttk.Label(editor, text="Temperature", background="#ffffff").grid(row=3, column=0, sticky="w", pady=(0, 6))
        ttk.Entry(editor, textvariable=temperature_var, width=12).grid(row=3, column=1, sticky="w", pady=(0, 6))

        ttk.Checkbutton(editor, text="Explain changes", variable=explain_var).grid(
            row=4, column=1, sticky="w", pady=(0, 4)
        )
        ttk.Checkbutton(editor, text="Preserve tone", variable=preserve_var).grid(row=5, column=1, sticky="w")

        action_bar = ttk.Frame(frame, style="Card.TFrame")
        action_bar.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(14, 0))
        action_bar.columnconfigure(7, weight=1)

        def refresh_list(select_name: str | None = None) -> None:
            self.profiles = load_profiles()
            profile_list.delete(0, "end")
            for profile in self.profiles:
                profile_list.insert("end", profile.name)
            index = 0
            if select_name:
                for candidate_index, profile in enumerate(self.profiles):
                    if profile.name == select_name:
                        index = candidate_index
                        break
            profile_list.selection_clear(0, "end")
            profile_list.selection_set(index)
            profile_list.activate(index)
            selected_index.set(index)
            load_selected_fields()
            self._refresh_profile_menu()

        def selected_profile() -> ProofreadingProfile:
            index = selected_index.get()
            if index < 0 or index >= len(self.profiles):
                return self.profiles[0]
            return self.profiles[index]

        def load_selected_fields() -> None:
            if not self.profiles:
                return
            profile = selected_profile()
            name_var.set(profile.name)
            description_text.delete("1.0", "end")
            description_text.insert("1.0", profile.description)
            system_text.delete("1.0", "end")
            system_text.insert("1.0", profile.system_message)
            temperature_var.set("" if profile.temperature is None else str(profile.temperature))
            explain_var.set(profile.explain_changes)
            preserve_var.set(profile.preserve_tone)

        def on_select(_event: tk.Event | None = None) -> None:
            selection = profile_list.curselection()
            if not selection:
                return
            selected_index.set(selection[0])
            load_selected_fields()

        def profile_from_fields() -> ProofreadingProfile:
            temperature_text = temperature_var.get().strip()
            return ProofreadingProfile(
                name=name_var.get(),
                description=description_text.get("1.0", "end-1c"),
                system_message=system_text.get("1.0", "end-1c"),
                temperature=None if not temperature_text else float(temperature_text),
                explain_changes=explain_var.get(),
                preserve_tone=preserve_var.get(),
            ).normalized()

        def new_profile() -> None:
            name_var.set("New Profile")
            description_text.delete("1.0", "end")
            description_text.insert("1.0", "Describe when to use this proofreading profile.")
            system_text.delete("1.0", "end")
            system_text.insert("1.0", "You proofread the user's text according to this profile's task.")
            temperature_var.set("0.1")
            explain_var.set(False)
            preserve_var.set(True)
            profile_list.selection_clear(0, "end")
            selected_index.set(-1)

        def save_current() -> None:
            old_name = selected_profile().name if selected_index.get() >= 0 and self.profiles else None
            try:
                profile = profile_from_fields()
                if old_name and old_name != profile.name:
                    delete_profile(old_name)
                saved = save_profile(profile)
            except (ProfileError, ValueError) as exc:
                messagebox.showerror("Profile error", str(exc), parent=dialog)
                return
            self.status_var.set(f"Saved {saved.name} profile.")
            refresh_list(saved.name)

        def delete_current() -> None:
            profile = selected_profile()
            if len(self.profiles) <= 1:
                messagebox.showwarning("Profile required", "At least one profile must remain.", parent=dialog)
                return
            if not messagebox.askyesno("Delete profile", f"Delete {profile.name}?", parent=dialog):
                return
            delete_profile(profile.name)
            self.status_var.set(f"Deleted {profile.name} profile.")
            refresh_list()

        def duplicate_current() -> None:
            try:
                copied = duplicate_profile(selected_profile())
            except ProfileError as exc:
                messagebox.showerror("Profile error", str(exc), parent=dialog)
                return
            self.status_var.set(f"Duplicated {copied.name} profile.")
            refresh_list(copied.name)

        def export_current() -> None:
            profile = selected_profile()
            destination = filedialog.asksaveasfilename(
                parent=dialog,
                title="Export profile",
                defaultextension=".json",
                initialfile=f"{profile.name.lower().replace(' ', '_')}.json",
                filetypes=[("JSON profile", "*.json"), ("All files", "*.*")],
            )
            if not destination:
                return
            export_profile(profile, Path(destination))
            self.status_var.set(f"Exported {profile.name} profile.")

        def import_new() -> None:
            source = filedialog.askopenfilename(
                parent=dialog,
                title="Import profile",
                filetypes=[("JSON profile", "*.json"), ("All files", "*.*")],
            )
            if not source:
                return
            try:
                imported = import_profile(Path(source))
            except (OSError, ProfileError, ValueError) as exc:
                messagebox.showerror("Profile error", str(exc), parent=dialog)
                return
            self.status_var.set(f"Imported {imported.name} profile.")
            refresh_list(imported.name)

        profile_list.bind("<<ListboxSelect>>", on_select)
        ttk.Button(action_bar, text="New", command=new_profile, style="Secondary.TButton").grid(row=0, column=0, padx=(0, 8))
        ttk.Button(action_bar, text="Save", command=save_current, style="Primary.TButton").grid(row=0, column=1, padx=(0, 8))
        ttk.Button(action_bar, text="Delete", command=delete_current, style="Secondary.TButton").grid(
            row=0, column=2, padx=(0, 8)
        )
        ttk.Button(action_bar, text="Duplicate", command=duplicate_current, style="Secondary.TButton").grid(
            row=0, column=3, padx=(0, 8)
        )
        ttk.Button(action_bar, text="Export", command=export_current, style="Secondary.TButton").grid(
            row=0, column=4, padx=(0, 8)
        )
        ttk.Button(action_bar, text="Import", command=import_new, style="Secondary.TButton").grid(
            row=0, column=5, padx=(0, 8)
        )
        ttk.Button(action_bar, text="Close", command=dialog.destroy, style="Secondary.TButton").grid(row=0, column=8)

        refresh_list(self.profile_var.get())
        dialog.wait_window()


def main() -> None:
    app = ProofreadApp()
    app.mainloop()
