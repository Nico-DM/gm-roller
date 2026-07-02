from __future__ import annotations

import sys
import tkinter as tk
from tkinter import messagebox

import customtkinter as ctk

from gm_roller.combat import RollSettings, collect_option_choices, format_roll_outcome, roll_character_attack
from gm_roller.dice.engine import DiceEngine
from gm_roller.gui.widgets import format_character_summary
from gm_roller.models.character import Character
from gm_roller.storage import CharacterNotFoundError, CharacterStore


class GmRollerApp(ctk.CTk):
    def __init__(self, store: CharacterStore) -> None:
        super().__init__()
        self._store = store
        self._engine = DiceEngine()
        self._characters: list[Character] = []
        self._selected_character: Character | None = None
        self._character_var = tk.StringVar(value="")
        self._attack_var = tk.StringVar(value="")
        self._advantage_var = tk.BooleanVar(value=False)
        self._disadvantage_var = tk.BooleanVar(value=False)
        self._crit_var = tk.BooleanVar(value=False)
        self._damage_only_var = tk.BooleanVar(value=False)
        self._option_vars: dict[str, tk.BooleanVar] = {}

        self.title("gm-roller")
        self.geometry("900x600")
        self.minsize(720, 480)

        self._build_layout()
        self._load_characters()

    def _build_layout(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ctk.CTkLabel(self, text="gm-roller", font=ctk.CTkFont(size=20, weight="bold"))
        header.grid(row=0, column=0, padx=16, pady=(12, 8), sticky="w")

        body = ctk.CTkFrame(self)
        body.grid(row=1, column=0, padx=16, pady=8, sticky="nsew")
        body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(0, weight=1)

        left = ctk.CTkFrame(body)
        left.grid(row=0, column=0, padx=(12, 6), pady=12, sticky="nsew")
        left.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(left, text="Characters", font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, padx=12, pady=(12, 6), sticky="w"
        )
        self._character_list = ctk.CTkScrollableFrame(left, width=220)
        self._character_list.grid(row=1, column=0, padx=12, pady=(0, 12), sticky="nsew")

        right = ctk.CTkFrame(body)
        right.grid(row=0, column=1, padx=(6, 12), pady=12, sticky="nsew")
        right.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(right, text="Attack", font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, padx=12, pady=(12, 4), sticky="w"
        )
        self._character_summary = ctk.CTkLabel(right, text="Select a character", anchor="w")
        self._character_summary.grid(row=1, column=0, padx=12, pady=(0, 8), sticky="ew")

        ctk.CTkLabel(right, text="Attack").grid(row=2, column=0, padx=12, pady=(4, 0), sticky="w")
        self._attack_menu = ctk.CTkOptionMenu(
            right,
            variable=self._attack_var,
            values=[""],
            command=self._on_attack_selected,
        )
        self._attack_menu.grid(row=3, column=0, padx=12, pady=(0, 8), sticky="ew")

        toggles = ctk.CTkFrame(right, fg_color="transparent")
        toggles.grid(row=4, column=0, padx=12, pady=4, sticky="ew")
        ctk.CTkCheckBox(toggles, text="Advantage", variable=self._advantage_var).grid(
            row=0, column=0, padx=(0, 12), pady=4, sticky="w"
        )
        ctk.CTkCheckBox(toggles, text="Disadvantage", variable=self._disadvantage_var).grid(
            row=0, column=1, padx=(0, 12), pady=4, sticky="w"
        )
        ctk.CTkCheckBox(toggles, text="Force crit", variable=self._crit_var).grid(
            row=1, column=0, padx=(0, 12), pady=4, sticky="w"
        )
        ctk.CTkCheckBox(toggles, text="Damage only", variable=self._damage_only_var).grid(
            row=1, column=1, padx=(0, 12), pady=4, sticky="w"
        )

        ctk.CTkLabel(right, text="Options").grid(row=5, column=0, padx=12, pady=(8, 0), sticky="w")
        self._options_frame = ctk.CTkFrame(right, fg_color="transparent")
        self._options_frame.grid(row=6, column=0, padx=12, pady=4, sticky="ew")

        self._roll_button = ctk.CTkButton(right, text="Roll Attack", command=self._on_roll)
        self._roll_button.grid(row=7, column=0, padx=12, pady=(12, 12), sticky="ew")

        ctk.CTkLabel(self, text="Results", font=ctk.CTkFont(weight="bold")).grid(
            row=2, column=0, padx=16, pady=(0, 4), sticky="w"
        )
        self._results = ctk.CTkTextbox(self, height=180)
        self._results.grid(row=3, column=0, padx=16, pady=(0, 16), sticky="nsew")
        self._results.configure(state="disabled")
        self.grid_rowconfigure(3, weight=1)

    def _load_characters(self) -> None:
        self._characters = self._store.list()
        for widget in self._character_list.winfo_children():
            widget.destroy()

        if not self._characters:
            ctk.CTkLabel(self._character_list, text="No characters found.").pack(anchor="w", padx=4, pady=4)
            return

        for character in self._characters:
            ctk.CTkRadioButton(
                self._character_list,
                text=character.name,
                variable=self._character_var,
                value=character.id,
                command=self._on_character_selected,
            ).pack(anchor="w", padx=4, pady=4)

        first = self._characters[0]
        self._character_var.set(first.id)
        self._on_character_selected()

    def _on_character_selected(self) -> None:
        character_id = self._character_var.get()
        if not character_id:
            return
        try:
            character = self._store.get(character_id)
        except CharacterNotFoundError:
            return

        self._selected_character = character
        self._character_summary.configure(text=format_character_summary(character))

        attack_ids = [attack.id for attack in character.attacks]
        if not attack_ids:
            self._attack_menu.configure(values=[""])
            self._attack_var.set("")
            self._rebuild_option_checkboxes()
            return

        self._attack_menu.configure(values=attack_ids)
        if self._attack_var.get() not in attack_ids:
            self._attack_var.set(attack_ids[0])
        self._on_attack_selected(self._attack_var.get())

    def _on_attack_selected(self, _value: str | None = None) -> None:
        self._rebuild_option_checkboxes()

    def _rebuild_option_checkboxes(self) -> None:
        for widget in self._options_frame.winfo_children():
            widget.destroy()
        self._option_vars.clear()

        character = self._selected_character
        attack_id = self._attack_var.get()
        if character is None or not attack_id:
            ctk.CTkLabel(self._options_frame, text="(none)").grid(row=0, column=0, sticky="w")
            return

        try:
            attack = character.get_attack(attack_id)
        except KeyError:
            ctk.CTkLabel(self._options_frame, text="(none)").grid(row=0, column=0, sticky="w")
            return

        choices = collect_option_choices(character, attack)
        if not choices:
            ctk.CTkLabel(self._options_frame, text="(none)").grid(row=0, column=0, sticky="w")
            return

        for index, (option_id, label) in enumerate(choices):
            var = tk.BooleanVar(value=False)
            self._option_vars[option_id] = var
            ctk.CTkCheckBox(self._options_frame, text=label, variable=var).grid(
                row=index // 2,
                column=index % 2,
                padx=(0, 12),
                pady=2,
                sticky="w",
            )

    def _append_result(self, text: str) -> None:
        self._results.configure(state="normal")
        if self._results.get("1.0", "end").strip():
            self._results.insert("end", "\n\n")
        self._results.insert("end", text)
        self._results.see("end")
        self._results.configure(state="disabled")

    def _on_roll(self) -> None:
        character = self._selected_character
        attack_id = self._attack_var.get()
        if character is None:
            self._append_result("Error: select a character.")
            return
        if not attack_id:
            self._append_result("Error: select an attack.")
            return

        try:
            attack = character.get_attack(attack_id)
        except KeyError:
            self._append_result(f"Error: attack not found: {attack_id!r}.")
            return

        enabled = {option_id for option_id, var in self._option_vars.items() if var.get()}
        settings = RollSettings(
            options=frozenset(enabled),
            advantage=self._advantage_var.get(),
            disadvantage=self._disadvantage_var.get(),
            force_crit=self._crit_var.get(),
            damage_only=self._damage_only_var.get(),
        )

        try:
            outcome = roll_character_attack(character, attack, self._engine, settings)
        except ValueError as exc:
            self._append_result(f"Error: {exc}")
            return

        header = f"— {character.name} / {attack.id} —"
        self._append_result(f"{header}\n{format_roll_outcome(outcome)}")


def main(argv: list[str] | None = None) -> int:
    _ = argv
    ctk.set_appearance_mode("system")
    ctk.set_default_color_theme("blue")

    store = CharacterStore()
    try:
        store.load_all()
    except Exception as exc:
        print(f"Failed to load characters: {exc}", file=sys.stderr)
        return 1

    app = GmRollerApp(store)
    try:
        app.mainloop()
    except tk.TclError as exc:
        messagebox.showerror("gm-roller", f"Display error: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
