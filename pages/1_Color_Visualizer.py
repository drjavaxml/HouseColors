import streamlit as st
from PIL import Image, ImageDraw
import numpy as np
import io
import base64
from streamlit_image_coordinates import streamlit_image_coordinates
from lib.persistence import load_json, save_json
from lib.paint_db import load_all_brands

st.set_page_config(page_title="Color Visualizer", page_icon="\U0001f3a8", layout="wide")
st.title("\U0001f3a8 Color Visualizer")

brands = load_all_brands()

# Session state defaults
if "photo_fills" not in st.session_state:
    st.session_state.photo_fills = []
if "photo_points" not in st.session_state:
    st.session_state.photo_points = []
if "photo_pending" not in st.session_state:
    st.session_state.photo_pending = []
if "photo_last_click" not in st.session_state:
    st.session_state.photo_last_click = None
if "photo_sampled_color" not in st.session_state:
    st.session_state.photo_sampled_color = None
if "photo_base_img" not in st.session_state:
    st.session_state.photo_base_img = None  # cached PIL Image

# Load session option — available even without an image
saved_work = load_json("photo_work.json", default={"sessions": {}})
session_names = list(saved_work["sessions"].keys())
if session_names and st.session_state.photo_base_img is None:
    st.markdown("**Load a previous session:**")
    load_cols = st.columns([2, 1])
    with load_cols[0]:
        quick_load_sel = st.selectbox("Session", session_names,
                                      key="photo_quick_load")
    with load_cols[1]:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Load Session", key="quick_load_btn"):
            data = saved_work["sessions"][quick_load_sel]
            if "image_b64" in data:
                img_bytes = base64.b64decode(data["image_b64"])
                st.session_state.photo_base_img = Image.open(
                    io.BytesIO(img_bytes)).convert("RGBA")
            st.session_state.photo_fills = data.get("fills", [])
            st.session_state.photo_pending = [
                [tuple(p) for p in poly]
                for poly in data.get("pending", [])
            ]
            st.session_state.photo_points = data.get("points", [])
            st.session_state.photo_last_click = None
            st.rerun()
    st.markdown("---")

uploaded = st.file_uploader("Upload a house photo", type=["png", "jpg", "jpeg"])
if uploaded:
    new_img = Image.open(uploaded).convert("RGBA")
    MAX_W = 800
    w, h = new_img.size
    if w > MAX_W:
        ratio = MAX_W / w
        new_img = new_img.resize((MAX_W, int(h * ratio)), Image.LANCZOS)
    st.session_state.photo_base_img = new_img

base_img = st.session_state.photo_base_img
if base_img is not None:

    # Build composited image from applied fills
    def _composite(img):
        result = img.copy()
        overlay = Image.new("RGBA", result.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        base_arr = np.array(img)[:, :, :3].astype(np.float64)
        overlay_arr = np.array(overlay)
        for fill in st.session_state.photo_fills:
            if fill.get("type") == "color_replace":
                sampled = np.array(fill["sampled_rgb"], dtype=np.float64)
                diff = base_arr - sampled
                dist = np.sqrt(np.sum(diff ** 2, axis=2))
                mask = dist <= fill["tolerance"]
                r, g, b, a = fill["rgba"]
                overlay_arr[mask] = [r, g, b, a]
            else:
                draw.polygon(fill["pts"], fill=tuple(fill["rgba"]))
        overlay = Image.fromarray(overlay_arr, "RGBA")
        return Image.alpha_composite(result, overlay)

    # Draw pending polygons and current points as markers
    def _draw_guides(img):
        display = img.copy()
        draw = ImageDraw.Draw(display)

        tool = st.session_state.get("photo_tool", "Polygon")

        # Color replace preview highlight
        if (tool == "Color Replace"
                and st.session_state.photo_sampled_color is not None):
            tol = st.session_state.get("photo_tolerance", 30)
            sampled = np.array(st.session_state.photo_sampled_color,
                               dtype=np.float64)
            base_arr = np.array(base_img)[:, :, :3].astype(np.float64)
            diff = base_arr - sampled
            dist = np.sqrt(np.sum(diff ** 2, axis=2))
            mask = dist <= tol
            # Semi-transparent highlight overlay
            highlight = Image.new("RGBA", display.size, (0, 0, 0, 0))
            h_arr = np.array(highlight)
            if fill_color:
                r_h = int(fill_color[1:3], 16)
                g_h = int(fill_color[3:5], 16)
                b_h = int(fill_color[5:7], 16)
            else:
                r_h, g_h, b_h = 255, 0, 255
            h_arr[mask] = [r_h, g_h, b_h, 100]
            highlight = Image.fromarray(h_arr, "RGBA")
            display = Image.alpha_composite(display, highlight)
            draw = ImageDraw.Draw(display)

        # Draw closed pending polygons as outlines
        for poly in st.session_state.photo_pending:
            pts = [tuple(p) for p in poly]
            draw.polygon(pts, outline="yellow")
            for x, y in pts:
                draw.ellipse([x - 3, y - 3, x + 3, y + 3],
                             fill="yellow", outline="white")
        # Draw current in-progress points
        for i, pt in enumerate(st.session_state.photo_points):
            x, y = pt
            draw.ellipse([x - 4, y - 4, x + 4, y + 4],
                         fill="red", outline="white")
            if i > 0:
                draw.line([tuple(st.session_state.photo_points[i - 1]),
                           (x, y)], fill="red", width=2)
        return display

    # Load saved palettes from Palette Builder
    saved_palettes = load_json("palettes.json", default={"palettes": []})

    # Initialize working palette
    if "photo_palette" not in st.session_state:
        st.session_state.photo_palette = []

    # Sidebar controls
    with st.sidebar:
        # Load from saved palettes
        st.subheader("Saved Palettes")
        if saved_palettes["palettes"]:
            pal_names = [p["name"] for p in saved_palettes["palettes"]]
            sel_pal = st.selectbox("Load a palette", pal_names,
                                   key="photo_load_pal")
            if st.button("Load Palette"):
                pal_data = next(p for p in saved_palettes["palettes"]
                                if p["name"] == sel_pal)
                st.session_state.photo_palette = [
                    {"hex": c["hex"], "name": c.get("name", c["hex"])}
                    for c in pal_data["colors"]
                ]
                st.rerun()
        else:
            st.caption("No saved palettes yet. Build one in Palette Builder.")

        st.markdown("---")
        st.subheader("Fill Color")

        # Display working palette as selectable swatches
        palette = st.session_state.photo_palette
        if palette:
            palette_labels = [
                f'{c["name"]} ({c["hex"]})' for c in palette
            ]
            active_idx = st.radio(
                "Pick from palette",
                range(len(palette)),
                format_func=lambda i: palette_labels[i],
                key="palette_active",
                horizontal=False,
            )
            # Show color swatches
            swatches_html = ""
            for i, c in enumerate(palette):
                border = "3px solid white" if i == active_idx else "1px solid #555"
                swatches_html += (
                    f'<span style="display:inline-block;width:28px;height:28px;'
                    f'background:{c["hex"]};border:{border};border-radius:4px;'
                    f'margin:2px;" title="{c["name"]}"></span>'
                )
            st.markdown(swatches_html, unsafe_allow_html=True)
            fill_color = palette[active_idx]["hex"]
        else:
            st.caption("Load a palette above, or pick a custom color below.")
            fill_color = None

        # Custom color picker as fallback / addition
        st.markdown("---")
        custom_color = st.color_picker("Custom color", "#4488CC",
                                       key="photo_custom_color")
        use_custom = st.checkbox("Use custom color instead", value=(not palette))
        if use_custom:
            fill_color = custom_color

        st.markdown("---")
        opacity = st.slider("Opacity", 0, 255, 120, key="photo_opacity")

        st.markdown("---")
        st.subheader("Tool")
        st.radio("Tool", ["Polygon", "Color Replace"],
                 key="photo_tool", horizontal=True)

        tool = st.session_state.get("photo_tool", "Polygon")

        n_pts = len(st.session_state.photo_points)
        n_pending = len(st.session_state.photo_pending)

        if tool == "Polygon":
            st.caption(f"Current points: {n_pts} | Pending polygons: {n_pending}")

            close_poly_btn = st.button("Close Polygon", disabled=(n_pts < 3))
            fill_btn = st.button("Fill All Polygons",
                                 disabled=(n_pending == 0))
            st.markdown("---")
            clear_pts_btn = st.button("Clear Current Points")
            clear_pending_btn = st.button("Clear Pending Polygons",
                                          disabled=(n_pending == 0))
        else:
            close_poly_btn = False
            fill_btn = False
            clear_pts_btn = False
            clear_pending_btn = False

            st.slider("Tolerance", 0, 100, 30, key="photo_tolerance")
            sampled = st.session_state.photo_sampled_color
            if sampled is not None:
                r_s, g_s, b_s = sampled
                hex_s = f"#{r_s:02x}{g_s:02x}{b_s:02x}"
                st.markdown(
                    f'Sampled: <span style="display:inline-block;width:20px;'
                    f'height:20px;background:{hex_s};border:1px solid #ccc;'
                    f'vertical-align:middle;border-radius:3px;"></span> '
                    f'`{hex_s}`',
                    unsafe_allow_html=True,
                )
            else:
                st.caption("Click on the image to sample a color.")

            apply_cr_btn = st.button("Apply Color Replace",
                                     disabled=(sampled is None))
            clear_sample_btn = st.button("Clear Sample")

        undo_btn = st.button("Undo Last Fill")

        # Save / Load polygon sets
        st.markdown("---")
        st.subheader("Save / Load Polygons")
        saved_polys = load_json("saved_polygons.json", default={"sets": {}})
        poly_set_name = st.text_input("Polygon set name", key="poly_set_name")
        save_poly_btn = st.button("Save Polygons",
                                   disabled=(n_pending == 0 and n_pts < 3))
        poly_set_names = list(saved_polys["sets"].keys())
        if poly_set_names:
            load_poly_sel = st.selectbox("Load polygon set", poly_set_names,
                                          key="poly_load_sel")
            load_poly_btn = st.button("Load Polygons")
            delete_poly_btn = st.button("Delete Polygon Set")
        else:
            st.caption("No saved polygon sets yet.")
            load_poly_btn = False
            delete_poly_btn = False

        # Save / Load work
        st.markdown("---")
        st.subheader("Save / Load Work")
        session_name = st.text_input("Session name", key="photo_session_name")
        save_work_btn = st.button("Save Current Work")

        session_names = list(saved_work["sessions"].keys())
        if session_names:
            load_sel = st.selectbox("Load session", session_names,
                                    key="photo_load_session")
            load_work_btn = st.button("Load Session")
            delete_work_btn = st.button("Delete Session")
        else:
            st.caption("No saved sessions yet.")
            load_work_btn = False
            delete_work_btn = False

    composited = _composite(base_img)
    display_img = _draw_guides(composited)
    display_rgb = display_img.convert("RGB")

    # Clickable image
    if tool == "Color Replace":
        st.info(
            "Click on the image to sample a color. Adjust tolerance to "
            "expand/shrink the match area, then click 'Apply Color Replace'."
        )
    else:
        st.info(
            "Click to place vertices. 'Close Polygon' to finish a shape "
            "(shown in yellow). Draw more polygons, then 'Fill All Polygons' "
            "to apply the color."
        )
    coords = streamlit_image_coordinates(display_rgb, key="photo_click")

    # Handle new click — only process if it's genuinely new
    if coords is not None:
        click_key = (coords["x"], coords["y"])
        if click_key != st.session_state.photo_last_click:
            st.session_state.photo_last_click = click_key
            if tool == "Color Replace":
                # Sample pixel color from base image
                px = base_img.getpixel((coords["x"], coords["y"]))
                st.session_state.photo_sampled_color = (px[0], px[1], px[2])
            else:
                st.session_state.photo_points.append(list(click_key))
            st.rerun()

    # Apply Color Replace
    if tool == "Color Replace":
        if apply_cr_btn and st.session_state.photo_sampled_color is not None:
            r_c = int(fill_color[1:3], 16) if fill_color else 0
            g_c = int(fill_color[3:5], 16) if fill_color else 0
            b_c = int(fill_color[5:7], 16) if fill_color else 0
            st.session_state.photo_fills.append({
                "type": "color_replace",
                "sampled_rgb": list(st.session_state.photo_sampled_color),
                "tolerance": st.session_state.get("photo_tolerance", 30),
                "rgba": [r_c, g_c, b_c, opacity],
            })
            st.session_state.photo_sampled_color = None
            st.rerun()
        if clear_sample_btn:
            st.session_state.photo_sampled_color = None
            st.rerun()

    # Close current polygon → move to pending, keep last_click to prevent ghost point
    if close_poly_btn and len(st.session_state.photo_points) >= 3:
        st.session_state.photo_pending.append(
            [tuple(p) for p in st.session_state.photo_points]
        )
        st.session_state.photo_points = []
        st.rerun()

    # Fill all pending polygons with chosen color
    if fill_btn and st.session_state.photo_pending:
        r_c = int(fill_color[1:3], 16)
        g_c = int(fill_color[3:5], 16)
        b_c = int(fill_color[5:7], 16)
        rgba = [r_c, g_c, b_c, opacity]
        for poly in st.session_state.photo_pending:
            st.session_state.photo_fills.append({"pts": poly, "rgba": rgba})
        st.session_state.photo_pending = []
        st.rerun()

    # Clear current points
    if clear_pts_btn:
        st.session_state.photo_points = []
        st.session_state.photo_last_click = None
        st.rerun()

    # Clear pending polygons
    if clear_pending_btn:
        st.session_state.photo_pending = []
        st.session_state.photo_last_click = None
        st.rerun()

    # Undo last applied fill — restore polygons back to pending (or just remove color_replace)
    if undo_btn and st.session_state.photo_fills:
        last_fill = st.session_state.photo_fills.pop()
        if last_fill.get("type") != "color_replace":
            st.session_state.photo_pending.append(last_fill["pts"])
        st.rerun()

    # Save polygon set
    if save_poly_btn and poly_set_name:
        # Include current in-progress points as a polygon if 3+
        polys_to_save = [
            [list(p) for p in poly]
            for poly in st.session_state.photo_pending
        ]
        if len(st.session_state.photo_points) >= 3:
            polys_to_save.append(
                [list(p) for p in st.session_state.photo_points]
            )
        saved_polys["sets"][poly_set_name] = polys_to_save
        save_json("saved_polygons.json", saved_polys)
        st.success(f"Saved polygon set '{poly_set_name}'!")
    elif save_poly_btn and not poly_set_name:
        st.warning("Enter a name for the polygon set.")

    # Load polygon set
    if load_poly_btn:
        loaded_polys = saved_polys["sets"][load_poly_sel]
        st.session_state.photo_pending = [
            [tuple(p) for p in poly] for poly in loaded_polys
        ]
        st.session_state.photo_points = []
        st.rerun()

    # Delete polygon set
    if delete_poly_btn:
        del saved_polys["sets"][load_poly_sel]
        save_json("saved_polygons.json", saved_polys)
        st.rerun()

    # Save current work (including image)
    if save_work_btn and session_name:
        img_buf = io.BytesIO()
        base_img.save(img_buf, format="PNG")
        img_b64 = base64.b64encode(img_buf.getvalue()).decode("ascii")
        saved_work["sessions"][session_name] = {
            "fills": st.session_state.photo_fills,
            "pending": [
                [list(p) for p in poly]
                for poly in st.session_state.photo_pending
            ],
            "points": st.session_state.photo_points,
            "image_b64": img_b64,
        }
        save_json("photo_work.json", saved_work)
        st.success(f"Saved '{session_name}'!")
    elif save_work_btn and not session_name:
        st.warning("Enter a name for the session.")

    # Load saved work
    if load_work_btn:
        data = saved_work["sessions"][load_sel]
        if "image_b64" in data:
            img_bytes = base64.b64decode(data["image_b64"])
            st.session_state.photo_base_img = Image.open(
                io.BytesIO(img_bytes)).convert("RGBA")
        st.session_state.photo_fills = data.get("fills", [])
        st.session_state.photo_pending = [
            [tuple(p) for p in poly]
            for poly in data.get("pending", [])
        ]
        st.session_state.photo_points = data.get("points", [])
        st.session_state.photo_last_click = None
        st.rerun()

    # Delete saved session
    if delete_work_btn:
        del saved_work["sessions"][load_sel]
        save_json("photo_work.json", saved_work)
        st.rerun()

    # Download composited result
    final = _composite(base_img).convert("RGB")
    buf = io.BytesIO()
    final.save(buf, format="PNG")
    st.download_button("Download PNG", buf.getvalue(), "house_colored.png", "image/png")
else:
    st.info("Upload a photo of your house to get started, or load a saved session above.")
