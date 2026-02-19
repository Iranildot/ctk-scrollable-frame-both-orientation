"""
usage_example.py
──────────────
Demonstration of CTkScrollableFrameExt with interactive controls
to test orientation and content_anchor in real-time.
"""

import customtkinter as ctk
from ctk_scrollable_frame_ext import CTkScrollableFrameExt

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("CTkScrollableFrameExt — Demo")
app.geometry("780x540")
app.grid_columnconfigure(0, weight=1)
app.grid_rowconfigure(1, weight=1)

# ── Control Panel ─────────────────────────────────────────────────────────────
controls_frame = ctk.CTkFrame(app, fg_color="transparent")
controls_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 0))

ctk.CTkLabel(controls_frame, text="content_anchor:").pack(side="left", padx=(0, 4))
anchor_var = ctk.StringVar(value="nw")
ctk.CTkOptionMenu(
    controls_frame,
    variable=anchor_var,
    values=["nw", "n", "ne", "w", "center", "e", "sw", "s", "se"],
    width=100,
).pack(side="left", padx=(0, 16))

ctk.CTkLabel(controls_frame, text="orientation:").pack(side="left", padx=(0, 4))
orient_var = ctk.StringVar(value="both")
ctk.CTkOptionMenu(
    controls_frame,
    variable=orient_var,
    values=["vertical", "horizontal", "both"],
    width=120,
).pack(side="left", padx=(0, 16))

ctk.CTkLabel(controls_frame, text="Rows:").pack(side="left", padx=(0, 4))
rows_var = ctk.IntVar(value=12)
ctk.CTkSlider(controls_frame, from_=3, to=40, number_of_steps=37,
              variable=rows_var, width=100).pack(side="left", padx=(0, 16))

ctk.CTkLabel(controls_frame, text="Cols:").pack(side="left", padx=(0, 4))
cols_var = ctk.IntVar(value=8)
ctk.CTkSlider(controls_frame, from_=2, to=20, number_of_steps=18,
              variable=cols_var, width=100).pack(side="left", padx=(0, 16))

# ── ScrollableFrame ───────────────────────────────────────────────────────────
scroll_frame = CTkScrollableFrameExt(
    app,
    width=740,
    height=400,
    orientation="both",
    content_anchor="nw",
    label_text="📜 CTkScrollableFrameExt",
    fg_color="#1e1e2e",
    scrollbar_button_color="#6c63ff",
    scrollbar_button_hover_color="#9f97ff",
)
scroll_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)

ctk.CTkLabel(
    app,
    text="🖱  Scroll = vertical   │   Shift + Scroll = horizontal",
    font=ctk.CTkFont(size=11),
    text_color="gray",
).grid(row=2, column=0, pady=(0, 6))

# ── Cache ─────────────────────────────────────────────────────────────────────
HEADER_FONT = ctk.CTkFont(weight="bold")
PALETTE = ("#2a2a3e", "#252538")

_headers = []
_cells = []

def populate():
    rows = rows_var.get()
    cols = cols_var.get()

    for c in range(cols):
        if c < len(_headers):
            lbl = _headers[c]
        else:
            lbl = ctk.CTkLabel(
                scroll_frame,
                width=90,
                fg_color="#3b3b5c",
                corner_radius=4,
                font=HEADER_FONT
            )
            _headers.append(lbl)

        lbl.configure(text=f"Col {c + 1}")
        lbl.grid(row=0, column=c, padx=3, pady=3, sticky="nsew")

    for i in range(cols, len(_headers)):
        _headers[i].grid_forget()

    idx = 0
    for r in range(1, rows + 1):
        for c in range(cols):
            if idx < len(_cells):
                lbl = _cells[idx]
            else:
                lbl = ctk.CTkLabel(scroll_frame, width=90, corner_radius=3)
                _cells.append(lbl)

            lbl.configure(text=f"{r * (c + 1):>6}", fg_color=PALETTE[(r + c) & 1])
            lbl.grid(row=r, column=c, padx=3, pady=2, sticky="nsew")
            idx += 1

    for i in range(idx, len(_cells)):
        _cells[i].grid_forget()

_last_orient = orient_var.get()
_last_anchor = anchor_var.get()

def apply_changes():
    global scroll_frame, _last_orient, _last_anchor

    orient = orient_var.get()
    anchor = anchor_var.get()

    if orient != _last_orient or anchor != _last_anchor:
        scroll_frame.destroy()

        scroll_frame = CTkScrollableFrameExt(
            app,
            width=740,
            height=400,
            orientation=orient,
            content_anchor=anchor,
            label_text="📜 CTkScrollableFrameExt",
            fg_color="#1e1e2e",
            scrollbar_button_color="#6c63ff",
            scrollbar_button_hover_color="#9f97ff",
        )
        scroll_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)

        # 🔥 RESET DO POOL (widgets antigos foram destruídos)
        _headers.clear()
        _cells.clear()

        _last_orient = orient
        _last_anchor = anchor

    populate()

ctk.CTkButton(controls_frame, text="▶ Apply", command=apply_changes, width=90).pack(side="left")

populate()
app.mainloop()
