"""
ctk_scrollable_frame_ext.py
────────────────────────────
Extended CTkScrollableFrame with support for:
  - orientation = "vertical" | "horizontal" | "both"
  - content_anchor = "nw" | "n" | "ne" | "w" | "center" | "e" | "sw" | "s" | "se"
  - Dynamic theme changes (suporta mudanças de tema em tempo real)

Usage:
    from ctk_scrollable_frame_ext import CTkScrollableFrameExt

    frame = CTkScrollableFrameExt(
        master,
        orientation="both",
        content_anchor="center",
    )
    frame.pack(fill="both", expand=True)

    # Add widgets directly to the frame:
    ctk.CTkLabel(frame, text="Hello").pack()

    # Change anchor at runtime:
    frame.configure(content_anchor="se")
    
    # Mudar tema em tempo real (agora funciona):
    ctk.set_appearance_mode("dark")  # a cor do canvas será atualizada automaticamente
"""

from typing import Union, Tuple, Optional, Literal, Any
import tkinter
import sys
import customtkinter as ctk


# ── Anchor → relative position (x, y) in 0.0–1.0 ─────────────────────────────
_ANCHOR_POSITION: dict[str, tuple[float, float]] = {
    "nw":     (0.0, 0.0),
    "n":      (0.5, 0.0),
    "ne":     (1.0, 0.0),
    "w":      (0.0, 0.5),
    "center": (0.5, 0.5),
    "e":      (1.0, 0.5),
    "sw":     (0.0, 1.0),
    "s":      (0.5, 1.0),
    "se":     (1.0, 1.0),
}

_VALID_ANCHORS = list(_ANCHOR_POSITION.keys())
_VALID_ORIENTATIONS = ("vertical", "horizontal", "both")


class CTkScrollableFrameExt(tkinter.Frame):
    """
    Replacement for CTkScrollableFrame with dual scrolling and content anchoring support.

    Extra parameters compared to the original
    ──────────────────────────────────────────
    orientation : "vertical" | "horizontal" | "both"
        Defines which scrollbars are created.
        In "both" mode, Shift + mouse wheel activates horizontal scrolling.

    content_anchor : "nw" | "n" | "ne" | "w" | "center" | "e" | "sw" | "s" | "se"
        Content position when it is SMALLER than the visible area.
        When the content overflows, scrolling behaves normally.
        Default: "nw" (original customtkinter behavior).
    """

    def __init__(
        self,
        master: Any,
        width: int = 200,
        height: int = 200,
        corner_radius: Optional[Union[int, str]] = None,
        border_width: Optional[Union[int, str]] = None,
        bg_color: Union[str, Tuple[str, str]] = "transparent",
        fg_color: Optional[Union[str, Tuple[str, str]]] = None,
        border_color: Optional[Union[str, Tuple[str, str]]] = None,
        scrollbar_fg_color: Optional[Union[str, Tuple[str, str]]] = None,
        scrollbar_button_color: Optional[Union[str, Tuple[str, str]]] = None,
        scrollbar_button_hover_color: Optional[Union[str, Tuple[str, str]]] = None,
        label_fg_color: Optional[Union[str, Tuple[str, str]]] = None,
        label_text_color: Optional[Union[str, Tuple[str, str]]] = None,
        label_text: str = "",
        label_font: Optional[Union[tuple, ctk.CTkFont]] = None,
        label_anchor: str = "center",
        orientation: Literal["vertical", "horizontal", "both"] = "vertical",
        content_anchor: Literal["nw", "n", "ne", "w", "center", "e", "sw", "s", "se"] = "nw",
    ):
        # ── Validations ───────────────────────────────────────────────────────
        if orientation not in _VALID_ORIENTATIONS:
            raise ValueError(f"Invalid orientation: '{orientation}'. Use: {_VALID_ORIENTATIONS}")

        anchor = content_anchor.lower()
        if anchor not in _ANCHOR_POSITION:
            raise ValueError(f"Invalid content_anchor: '{content_anchor}'. Use: {_VALID_ANCHORS}")

        self._orientation = orientation
        self._content_anchor = anchor
        self._desired_width = width
        self._desired_height = height
        self._shift_pressed = False
        self._label_text = label_text
        self._destroying = False  # anti-recursion flag for destroy
        self._theme_update_scheduled = False  # Evita múltiplas atualizações de tema

        # ── Outer frame (border + background color) ───────────────────────────
        self._parent_frame = ctk.CTkFrame(
            master=master, width=0, height=0,
            corner_radius=corner_radius, border_width=border_width,
            bg_color=bg_color, fg_color=fg_color, border_color=border_color,
        )

        # ── Canvas ───────────────────────────────────────────────────────────
        self._parent_canvas = tkinter.Canvas(
            master=self._parent_frame, highlightthickness=0
        )
        self._set_scroll_increments()

        # ── Scrollbar(s) ─────────────────────────────────────────────────────
        self._scrollbar: Optional[ctk.CTkScrollbar] = None
        self._scrollbar_x: Optional[ctk.CTkScrollbar] = None

        sb_kw = dict(
            fg_color=scrollbar_fg_color,
            button_color=scrollbar_button_color,
            button_hover_color=scrollbar_button_hover_color,
        )

        if orientation == "horizontal":
            self._scrollbar = ctk.CTkScrollbar(
                master=self._parent_frame, orientation="horizontal",
                command=self._parent_canvas.xview, **sb_kw,
            )
            self._parent_canvas.configure(xscrollcommand=self._scrollbar.set)

        elif orientation == "vertical":
            self._scrollbar = ctk.CTkScrollbar(
                master=self._parent_frame, orientation="vertical",
                command=self._parent_canvas.yview, **sb_kw,
            )
            self._parent_canvas.configure(yscrollcommand=self._scrollbar.set)

        elif orientation == "both":
            self._scrollbar = ctk.CTkScrollbar(
                master=self._parent_frame, orientation="vertical",
                command=self._parent_canvas.yview, **sb_kw,
            )
            self._scrollbar_x = ctk.CTkScrollbar(
                master=self._parent_frame, orientation="horizontal",
                command=self._parent_canvas.xview, **sb_kw,
            )
            self._parent_canvas.configure(
                yscrollcommand=self._scrollbar.set,
                xscrollcommand=self._scrollbar_x.set,
            )

        # ── Optional top label ───────────────────────────────────────────────
        self._label = ctk.CTkLabel(
            self._parent_frame, text=label_text, anchor=label_anchor,
            font=label_font,
            corner_radius=self._parent_frame.cget("corner_radius"),
            text_color=label_text_color,
            fg_color=(
                ctk.ThemeManager.theme["CTkScrollableFrame"]["label_fg_color"]
                if label_fg_color is None else label_fg_color
            ),
        )

        # ── Inner frame (where the user adds widgets) ─────────────────────────
        # master=_parent_canvas creates the hierarchy: _parent_frame → canvas → self
        # destroy() needs to be aware of this to avoid infinite recursion.
        tkinter.Frame.__init__(self, master=self._parent_canvas, highlightthickness=0)
        self._sync_bg()

        # ── Layout ───────────────────────────────────────────────────────────
        self._create_grid()
        self._parent_canvas.configure(width=width, height=height)

        # ── Canvas window ────────────────────────────────────────────────────
        self._create_window_id = self._parent_canvas.create_window(
            0, 0, window=self, anchor="nw"
        )

        # ── Event bindings ───────────────────────────────────────────────────
        self.bind("<Configure>", self._on_frame_configure)
        self._parent_canvas.bind("<Configure>", self._on_canvas_configure)

        self.bind_all("<MouseWheel>",         self._mouse_wheel_all,            add="+")
        self.bind_all("<Button-4>",           self._mouse_wheel_all,            add="+")
        self.bind_all("<Button-5>",           self._mouse_wheel_all,            add="+")
        self.bind_all("<KeyPress-Shift_L>",   self._keyboard_shift_press_all,   add="+")
        self.bind_all("<KeyPress-Shift_R>",   self._keyboard_shift_press_all,   add="+")
        self.bind_all("<KeyRelease-Shift_L>", self._keyboard_shift_release_all, add="+")
        self.bind_all("<KeyRelease-Shift_R>", self._keyboard_shift_release_all, add="+")

        # ── Monitorar mudanças de tema ───────────────────────────────────────
        # Verifica a cada 100ms se o tema mudou (método utilizado pelo CustomTkinter)
        self._schedule_theme_check()

    # ══════════════════════════════════════════════════════════════════════════
    # Theme monitoring (NEW)
    # ══════════════════════════════════════════════════════════════════════════

    def _schedule_theme_check(self):
        """Agenda uma verificação de mudança de tema."""
        if not self._destroying:
            try:
                self._check_theme_changed()
                self.after(100, self._schedule_theme_check)
            except tkinter.TclError:
                pass  # Widget foi destruído

    def _check_theme_changed(self):
        """Verifica se o tema mudou e sincroniza as cores se necessário."""
        # Pega a cor atual do CTkFrame (que responde a mudanças de tema)
        current_fg = self._parent_frame.cget("fg_color")
        
        # Compara com a cor armazenada no canvas
        canvas_color = self._parent_canvas.cget("bg")
        
        # Converte a cor do CTkFrame para o formato esperado
        expected_color = self._parent_frame.cget("bg_color")
        if expected_color == "transparent":
            expected_color = current_fg
        
        if isinstance(expected_color, (list, tuple)):
            mode = ctk.get_appearance_mode()
            expected_color = expected_color[0] if mode == "Light" else expected_color[1]
        
        # Se as cores não correspondem, sincroniza
        if canvas_color != expected_color:
            self._sync_bg()

    # ══════════════════════════════════════════════════════════════════════════
    # Destroy without recursion
    # ══════════════════════════════════════════════════════════════════════════

    def destroy(self):
        """
        Correct destruction order:
          1. Set the flag to block re-entrance.
          2. Destroy the inner frame (self) directly via tkinter.
          3. Destroy the outer frame (which contains canvas + scrollbars + label).

        Without the flag, tkinter walks the _parent_frame children tree,
        finds the canvas, which contains the inner frame, which calls destroy()
        again — causing infinite recursion.
        """
        if self._destroying:
            return
        self._destroying = True

        # Destroy the inner frame (tkinter.Frame base) without calling our destroy
        try:
            tkinter.Frame.destroy(self)
        except tkinter.TclError:
            pass  # already destroyed by tkinter during parent cleanup

        # Destroy the outer frame (CTkFrame with canvas, scrollbars, label)
        try:
            self._parent_frame.destroy()
        except tkinter.TclError:
            pass

    # ══════════════════════════════════════════════════════════════════════════
    # Internals
    # ══════════════════════════════════════════════════════════════════════════

    def _sync_bg(self):
        """Synchronize the inner frame and canvas background with the parent CTkFrame."""
        fg = self._parent_frame.cget("fg_color")
        color = self._parent_frame.cget("bg_color") if fg == "transparent" else fg

        if isinstance(color, (list, tuple)):
            mode = ctk.get_appearance_mode()
            color = color[0] if mode == "Light" else color[1]

        tkinter.Frame.configure(self, bg=color)
        self._parent_canvas.configure(bg=color)

    def _create_grid(self):
        cr = self._parent_frame.cget("corner_radius") or 0
        bw = self._parent_frame.cget("border_width") or 0
        sp = int(cr + bw)

        if self._orientation == "horizontal":
            self._parent_frame.grid_columnconfigure(0, weight=1)
            self._parent_frame.grid_rowconfigure(1, weight=1)
            self._parent_canvas.grid(row=1, column=0, sticky="nsew",
                                     padx=sp, pady=(sp, 0))
            self._scrollbar.grid(row=2, column=0, sticky="ew", padx=sp)
            if self._label_text:
                self._label.grid(row=0, column=0, sticky="ew", padx=sp, pady=sp)
            else:
                self._label.grid_forget()

        elif self._orientation == "vertical":
            self._parent_frame.grid_columnconfigure(0, weight=1)
            self._parent_frame.grid_rowconfigure(1, weight=1)
            self._parent_canvas.grid(row=1, column=0, sticky="nsew",
                                     padx=(sp, 0), pady=sp)
            self._scrollbar.grid(row=1, column=1, sticky="ns", pady=sp)
            if self._label_text:
                self._label.grid(row=0, column=0, columnspan=2,
                                 sticky="ew", padx=sp, pady=sp)
            else:
                self._label.grid_forget()

        elif self._orientation == "both":
            self._parent_frame.grid_columnconfigure(0, weight=1)
            self._parent_frame.grid_columnconfigure(1, weight=0)
            self._parent_frame.grid_rowconfigure(1, weight=1)
            self._parent_canvas.grid(row=1, column=0, sticky="nsew",
                                     padx=(sp, 0), pady=(sp, 0))
            self._scrollbar.grid(row=1, column=1, sticky="ns", pady=(sp, 0))
            self._scrollbar_x.grid(row=2, column=0, sticky="ew", padx=(sp, 0))
            if self._label_text:
                self._label.grid(row=0, column=0, columnspan=2,
                                 sticky="ew", padx=sp, pady=sp)
            else:
                self._label.grid_forget()

    # ── Anchor ───────────────────────────────────────────────────────────────

    def _apply_content_anchor(self):
        """Reposition the inner frame according to content_anchor."""
        cw = self._parent_canvas.winfo_width()
        ch = self._parent_canvas.winfo_height()
        fw = self.winfo_width()
        fh = self.winfo_height()

        rx, ry = _ANCHOR_POSITION[self._content_anchor]
        x = max(0, int((cw - fw) * rx))
        y = max(0, int((ch - fh) * ry))

        self._parent_canvas.coords(self._create_window_id, x, y)

        sr_w = max(fw + x, cw)
        sr_h = max(fh + y, ch)
        self._parent_canvas.configure(scrollregion=(0, 0, sr_w, sr_h))

    def _on_frame_configure(self, event=None):
        self._apply_content_anchor()

    def _on_canvas_configure(self, event):
        if self._orientation == "horizontal":
            self._parent_canvas.itemconfigure(
                self._create_window_id, height=event.height)
        elif self._orientation == "vertical":
            self._parent_canvas.itemconfigure(
                self._create_window_id, width=event.width)
        self._apply_content_anchor()

    # ── Scrolling ────────────────────────────────────────────────────────────

    def _set_scroll_increments(self):
        if sys.platform.startswith("win"):
            self._parent_canvas.configure(xscrollincrement=1, yscrollincrement=1)
        elif sys.platform == "darwin":
            self._parent_canvas.configure(xscrollincrement=4, yscrollincrement=8)

    def _mouse_wheel_all(self, event):
        if not self._is_child_of_canvas(event.widget):
            return

        if sys.platform.startswith("win"):
            delta = -int(event.delta / 6)
        elif sys.platform == "darwin":
            delta = -event.delta
        else:
            delta = -2 if event.num == 4 else 2

        if self._orientation == "both":
            if self._shift_pressed:
                if self._parent_canvas.xview() != (0.0, 1.0):
                    self._parent_canvas.xview("scroll", delta, "units")
            else:
                if self._parent_canvas.yview() != (0.0, 1.0):
                    self._parent_canvas.yview("scroll", delta, "units")
        elif self._orientation == "vertical":
            if self._parent_canvas.yview() != (0.0, 1.0):
                self._parent_canvas.yview("scroll", delta, "units")
        elif self._orientation == "horizontal":
            if self._parent_canvas.xview() != (0.0, 1.0):
                self._parent_canvas.xview("scroll", delta, "units")

    def _keyboard_shift_press_all(self, event):
        self._shift_pressed = True

    def _keyboard_shift_release_all(self, event):
        self._shift_pressed = False

    def _is_child_of_canvas(self, widget):
        if widget == self._parent_canvas:
            return True
        try:
            return self._is_child_of_canvas(widget.master)
        except AttributeError:
            return False

    # ══════════════════════════════════════════════════════════════════════════
    # Public API
    # ══════════════════════════════════════════════════════════════════════════

    def configure(self, **kwargs):
        if "content_anchor" in kwargs:
            anchor = kwargs.pop("content_anchor").lower()
            if anchor not in _ANCHOR_POSITION:
                raise ValueError(f"Invalid content_anchor: '{anchor}'. Use: {_VALID_ANCHORS}")
            self._content_anchor = anchor
            self._apply_content_anchor()

        if "width" in kwargs:
            self._desired_width = kwargs.pop("width")
            self._parent_canvas.configure(width=self._desired_width)

        if "height" in kwargs:
            self._desired_height = kwargs.pop("height")
            self._parent_canvas.configure(height=self._desired_height)

        if "corner_radius" in kwargs:
            self._parent_frame.configure(corner_radius=kwargs.pop("corner_radius"))
            self._create_grid()

        if "border_width" in kwargs:
            self._parent_frame.configure(border_width=kwargs.pop("border_width"))
            self._create_grid()

        if "fg_color" in kwargs:
            self._parent_frame.configure(fg_color=kwargs.pop("fg_color"))
            self._sync_bg()
            for child in self.winfo_children():
                if isinstance(child, ctk.CTkBaseClass):
                    child.configure(bg_color=self._parent_frame.cget("fg_color"))

        if "scrollbar_fg_color" in kwargs:
            v = kwargs.pop("scrollbar_fg_color")
            self._scrollbar.configure(fg_color=v)
            if self._scrollbar_x:
                self._scrollbar_x.configure(fg_color=v)

        if "scrollbar_button_color" in kwargs:
            v = kwargs.pop("scrollbar_button_color")
            self._scrollbar.configure(button_color=v)
            if self._scrollbar_x:
                self._scrollbar_x.configure(button_color=v)

        if "scrollbar_button_hover_color" in kwargs:
            v = kwargs.pop("scrollbar_button_hover_color")
            self._scrollbar.configure(button_hover_color=v)
            if self._scrollbar_x:
                self._scrollbar_x.configure(button_hover_color=v)

        if "label_text" in kwargs:
            self._label_text = kwargs.pop("label_text")
            self._label.configure(text=self._label_text)
            self._create_grid()

        if "label_font" in kwargs:
            self._label.configure(font=kwargs.pop("label_font"))

        if "label_text_color" in kwargs:
            self._label.configure(text_color=kwargs.pop("label_text_color"))

        if "label_fg_color" in kwargs:
            self._label.configure(fg_color=kwargs.pop("label_fg_color"))

        if "label_anchor" in kwargs:
            self._label.configure(anchor=kwargs.pop("label_anchor"))

        if kwargs:
            self._parent_frame.configure(**kwargs)

    def cget(self, attribute_name: str):
        match attribute_name:
            case "width":                        return self._desired_width
            case "height":                       return self._desired_height
            case "content_anchor":               return self._content_anchor
            case "orientation":                  return self._orientation
            case "label_text":                   return self._label_text
            case "label_font":                   return self._label.cget("font")
            case "label_text_color":             return self._label.cget("text_color")
            case "label_fg_color":               return self._label.cget("fg_color")
            case "label_anchor":                 return self._label.cget("anchor")
            case "scrollbar_fg_color":           return self._scrollbar.cget("fg_color")
            case "scrollbar_button_color":       return self._scrollbar.cget("button_color")
            case "scrollbar_button_hover_color": return self._scrollbar.cget("button_hover_color")
            case _:                              return self._parent_frame.cget(attribute_name)

    # ── Geometry proxies (delegated to the outer frame) ───────────────────────

    def pack(self, **kwargs):        self._parent_frame.pack(**kwargs)
    def place(self, **kwargs):       self._parent_frame.place(**kwargs)
    def grid(self, **kwargs):        self._parent_frame.grid(**kwargs)
    def pack_forget(self):           self._parent_frame.pack_forget()
    def place_forget(self):          self._parent_frame.place_forget()
    def grid_forget(self):           self._parent_frame.grid_forget()
    def grid_remove(self):           self._parent_frame.grid_remove()
    def grid_propagate(self, **kw):  self._parent_frame.grid_propagate(**kw)
    def grid_info(self):             return self._parent_frame.grid_info()
    def lift(self, above=None):      self._parent_frame.lift(above)
    def lower(self, below=None):     self._parent_frame.lower(below)