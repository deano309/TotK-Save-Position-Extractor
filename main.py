import struct
import os
import sys
import customtkinter as ctk
from tkinter import filedialog, messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD

SAVE_POS_HASH = 0xC884818D
SAVE_POS_RADY_HASH = 0x1EA93BD8
HASH_TABLE_START = 0x28
HASH_TABLE_END = 0x03C800


def get_player_position(filename):
    with open(filename, "rb") as f:
        data = f.read()

    x = y = z = rad_y = None

    for offset in range(HASH_TABLE_START, HASH_TABLE_END, 8):
        hash_value = struct.unpack_from("<I", data, offset)[0]
        ptr = struct.unpack_from("<I", data, offset + 4)[0]

        if hash_value == SAVE_POS_HASH:
            if ptr + 12 > len(data):
                raise ValueError("Invalid SavePos pointer found in save.")

            x = struct.unpack_from("<f", data, ptr)[0]
            y = struct.unpack_from("<f", data, ptr + 4)[0]
            z = struct.unpack_from("<f", data, ptr + 8)[0]

        elif hash_value == SAVE_POS_RADY_HASH:
            # SavePosRadY is stored directly in the hash table entry
            rad_y = struct.unpack_from("<f", data, offset + 4)[0]

    if x is None:
        raise ValueError("PlayerStatus.SavePos not found.")

    return x, y, z, rad_y


class App(TkinterDnD.DnDWrapper, ctk.CTk):
    def __init__(self):
        super().__init__()

        # Initialize tkdnd
        TkinterDnD._require(self)

        if getattr(sys, "frozen", False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))

        icon_path = os.path.join(base_path, "icon.ico")

        if os.path.exists(icon_path):
            self.iconbitmap(icon_path)

        self.title("TotK Position Extractor")
        self.geometry("420x170")

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.grid_columnconfigure(0, weight=1)

        self.select_button = ctk.CTkButton(
            self,
            width=130,
            text="Select progress.sav",
            command=self.select_file
        )
        self.select_button.grid(
            row=0,
            column=0,
            padx=20,
            pady=(20, 10),
            sticky=""
        )

        self.output_box = ctk.CTkTextbox(
            self,
            height=51,
            wrap="none",
            font=("Consolas", 14)
        )
        self.output_box.grid(
            row=1,
            column=0,
            padx=20,
            pady=10,
            sticky="ew"
        )

        self.copy_button = ctk.CTkButton(
            self,
            width=90,
            text="Copy Output",
            command=self.copy_output
        )
        self.copy_button.grid(
            row=2,
            column=0,
            padx=20,
            pady=(0, 20),
            sticky=""
        )

        self.drop_target_register(DND_FILES)
        self.dnd_bind("<<Drop>>", self.on_drop)


    def process_file(self, filename):
        try:
            x, y, z, rad_y = get_player_position(filename)

            output = f"Translate: [{x:.5f},{y:.5f},{z:.5f}]\nRotate: [0.0,{rad_y:.5f},0.0]"

            self.output_box.delete("1.0", "end")
            self.output_box.insert("1.0", output)

        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Failed to read save:\n\n{e}"
            )

    def on_drop(self, event):
        filename = event.data.strip().strip("{}")
        if filename:
            self.process_file(filename)

    def select_file(self):
        filename = filedialog.askopenfilename(
            title="Select progress.sav",
            filetypes=[("Save files", "*.sav"), ("All files", "*.*")]
        )

        if not filename:
            return

        self.process_file(filename)

    def copy_output(self):
        text = self.output_box.get("1.0", "end").strip()

        if not text:
            return

        self.clipboard_clear()
        self.clipboard_append(text)

        messagebox.showinfo(
            "Copied",
            "Output copied to clipboard."
        )


if __name__ == "__main__":
    app = App()
    app.mainloop()
