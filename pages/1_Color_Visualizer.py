import streamlit as st
from PIL import Image, ImageDraw
import io
from streamlit_image_coordinates import streamlit_image_coordinates
from lib.house_svg import house_svg, SECTIONS, DEFAULT_COLORS
from lib.persistence import load_json, save_json
from lib.paint_db import load_all_brands

st.set_page_config(page_title="Color Visualizer", page_icon="\U0001f3a8", layout="wide")
st.title("\U0001f3a8 Color Visualizer")

# Load saved state or defaults
saved = load_json("visualizer_state.json", default=None)
if saved is None:
    saved = dict(DEFAULT_COLORS)

# Initialize per-section session state keys
for section in SECTIONS:
    key = f"cp_{section}"
    if key not in st.session_state:
        st.session_state[key] = saved.get(section, DEFAULT_COLORS[section])

brands = load_all_brands()


def _get_colors() -> dict:
    """Read current colors from session state keys."""
    return {s: st.session_state.get(f"cp_{s}", DEFAULT_COLORS[s]) for s in SECTIONS}


# ── Mode selector ──
mode = st.radio("Mode", ["House Template", "Upload Photo"], horizontal=True)

if mode == "House Template":
    col_controls, col_preview = st.columns([1, 2])

    with col_controls:
        st.subheader("Pick Colors")
        for section in SECTIONS:
            label = section.replace("_", " ").title()
            st.color_picker(label, key=f"cp_{section}")

        if st.button("Reset to Defaults"):
            for section in SECTIONS:
                st.session_state[f"cp_{section}"] = DEFAULT_COLORS[section]
            st.rerun()

        if st.button("Save State"):
            save_json("visualizer_state.json", _get_colors())
            st.success("Saved!")

    with col_preview:
        st.subheader("Preview")
        svg_str = house_svg(**_get_colors())
        st.markdown(svg_str, unsafe_allow_html=True)

        # Download as SVG
        st.download_button(
            label="Download SVG",
            data=svg_str,
            file_name="house_colors.svg",
            mime="image/svg+xml",
        )

    # ── Quick-apply from brand colors ──
    st.markdown("---")
    st.subheader("Apply Brand Color to a Section")
    qcol1, qcol2, qcol3 = st.columns(3)
    with qcol1:
        target_section = st.selectbox("Section", SECTIONS, key="qa_section")
    with qcol2:
        brand_names = [b["brand"] for b in brands]
        sel_brand = st.selectbox("Brand", brand_names, key="qa_brand")
        brand_data = next(b for b in brands if b["brand"] == sel_brand)
    with qcol3:
        color_opts = {f'{c["name"]} ({c["code"]})': c for c in brand_data["colors"]}
        sel_label = st.selectbox("Color", list(color_opts.keys()), key="qa_color")

    if st.button("Apply to Section"):
        st.session_state[f"cp_{target_section}"] = color_opts[sel_label]["hex"]
        st.rerun()

else:
    # ── Upload photo mode ──
    st.subheader("Upload a House Photo")
    uploaded = st.file_uploader("Drag & drop or browse", type=["png", "jpg", "jpeg"])
    if uploaded:
        # Load and resize image to fit canvas
        base_img = Image.open(uploaded).convert("RGBA")
        MAX_W = 800
        w, h = base_img.size
        if w > MAX_W:
            ratio = MAX_W / w
            base_img = base_img.resize((MAX_W, int(h * ratio)), Image.LANCZOS)

        # Session state
        if "photo_fills" not in st.session_state:
            st.session_state.photo_fills = []      # applied fills
        if "photo_points" not in st.session_state:
            st.session_state.photo_points = []      # current polygon vertices
        if "photo_pending" not in st.session_state:
            st.session_state.photo_pending = []     # closed but unfilled polygons
        if "photo_last_click" not in st.session_state:
            st.session_state.photo_last_click = None  # track processed clicks

        # Build composited image from applied fills
        def _composite(img):
            result = img.copy()
            overlay = Image.new("RGBA", result.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay)
            for fill in st.session_state.photo_fills:
                draw.polygon(fill["pts"], fill=tuple(fill["rgba"]))
            return Image.alpha_composite(result, overlay)

        # Draw pending polygons and current points as markers
        def _draw_guides(img):
            display = img.copy()
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

        composited = _composite(base_img)
        display_img = _draw_guides(composited)
        display_rgb = display_img.convert("RGB")

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

            n_pts = len(st.session_state.photo_points)
            n_pending = len(st.session_state.photo_pending)
            st.caption(f"Current points: {n_pts} | Pending polygons: {n_pending}")

            close_poly_btn = st.button("Close Polygon", disabled=(n_pts < 3))
            fill_btn = st.button("Fill All Polygons", disabled=(n_pending == 0))
            st.markdown("---")
            clear_pts_btn = st.button("Clear Current Points")
            clear_pending_btn = st.button("Clear Pending Polygons",
                                          disabled=(n_pending == 0))
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
            saved_work = load_json("photo_work.json", default={"sessions": {}})
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

        # Clickable image
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
                st.session_state.photo_points.append(list(click_key))
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

        # Undo last applied fill — restore its polygons back to pending
        if undo_btn and st.session_state.photo_fills:
            last_fill = st.session_state.photo_fills.pop()
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

        # Save current work
        if save_work_btn and session_name:
            saved_work["sessions"][session_name] = {
                "fills": st.session_state.photo_fills,
                "pending": [
                    [list(p) for p in poly]
                    for poly in st.session_state.photo_pending
                ],
                "points": st.session_state.photo_points,
            }
            save_json("photo_work.json", saved_work)
            st.success(f"Saved '{session_name}'!")
        elif save_work_btn and not session_name:
            st.warning("Enter a name for the session.")

        # Load saved work
        if load_work_btn:
            data = saved_work["sessions"][load_sel]
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
        st.info("Upload a photo of your house to view it here.")
