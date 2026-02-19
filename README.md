# CTkScrollableFrame / CTkScrollableFrameExt

This document describes the usage and structure of the following files:

-   `ctk_scrollable_frame.py`
-   `ctk_scrollable_frame_ext.py`
-   `example1.py`

------------------------------------------------------------------------

## 📦 Overview

`CTkScrollableFrameExt` is an extension of `CTkScrollableFrame` that
adds support for:

-   Vertical, horizontal, or both scroll directions\
-   Content alignment (`content_anchor`)\
-   Optional top label\
-   Appearance integrated with CustomTkinter\
-   Horizontal scrolling using **Shift + Mouse Scroll**

------------------------------------------------------------------------

## 📁 File Structure

    ctk_scrollable_frame.py      # Base ScrollableFrame implementation
    ctk_scrollable_frame_ext.py  # Extension with content_anchor and improvements
    example1.py                  # Interactive usage example

------------------------------------------------------------------------

## 🧠 Important Parameters

### orientation

Defines the scroll type:

-   "vertical"\
-   "horizontal"\
-   "both"

### content_anchor

Defines how the content is aligned when it is smaller than the frame:

  Value    Position
  -------- ---------------
  nw       Top left
  n        Top center
  ne       Top right
  w        Center left
  center   Center
  e        Center right
  sw       Bottom left
  s        Bottom center
  se       Bottom right

------------------------------------------------------------------------

## 🧪 Usage Example

``` python
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
```

------------------------------------------------------------------------

## 🖱 Scroll Controls

-   Mouse scroll → vertical\
-   Shift + Scroll → horizontal\
-   Works on Windows, macOS, and Linux

------------------------------------------------------------------------

## ⚠️ Notes

-   When changing `orientation` or `content_anchor`, the frame is
    recreated.\
-   Internal widgets must be recreated after `destroy()`\
-   Alignment only affects layout when the content is smaller than the
    canvas

------------------------------------------------------------------------

## ✅ Conclusion

This component allows you to create grids, tables, and large layouts
with excellent layout and UX control in CustomTkinter.

------------------------------------------------------------------------

## Exemple 1

https://github.com/user-attachments/assets/68f056be-01b6-472c-8af3-f196ca4a28bb
