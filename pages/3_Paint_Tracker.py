import streamlit as st
from lib.persistence import load_json, save_json
from lib.color_utils import color_swatch_html
from lib.paint_db import load_all_brands

st.set_page_config(page_title="Paint Tracker", page_icon="\U0001f4cb", layout="wide")
st.title("\U0001f4cb Paint Tracker")
st.markdown("Track which paints you've used in each room.")

rooms_data: dict = load_json("rooms.json", default={"rooms": []})
brands = load_all_brands()

# ── Add a room ──
st.subheader("Add a Room")
new_room = st.text_input("Room name")
if st.button("Add Room") and new_room:
    rooms_data["rooms"].append({"name": new_room, "paints": []})
    save_json("rooms.json", rooms_data)
    st.rerun()

if not rooms_data["rooms"]:
    st.info("No rooms yet. Add one above to get started.")
    st.stop()

# ── Room selector ──
st.markdown("---")
room_names = [r["name"] for r in rooms_data["rooms"]]
selected_room_name = st.selectbox("Select a room", room_names)
room_idx = room_names.index(selected_room_name)
room = rooms_data["rooms"][room_idx]

# ── Add paint to room ──
st.subheader(f"Add Paint to {room['name']}")
col1, col2 = st.columns(2)
with col1:
    surface = st.selectbox("Surface", ["Walls", "Trim", "Ceiling", "Accent", "Door", "Other"])
with col2:
    finish = st.selectbox("Finish", ["Flat", "Matte", "Eggshell", "Satin", "Semi-Gloss", "Gloss"])

# Pick paint from brands or enter custom
method = st.radio("Color source", ["Pick from brand", "Custom"], horizontal=True)

paint_name = ""
paint_hex = ""
paint_brand = ""
paint_code = ""

if method == "Pick from brand":
    brand_names = [b["brand"] for b in brands]
    sel_brand = st.selectbox("Brand", brand_names, key="tracker_brand")
    brand_data = next(b for b in brands if b["brand"] == sel_brand)
    color_options = {f'{c["name"]} ({c["code"]})': c for c in brand_data["colors"]}
    sel_color_label = st.selectbox("Color", list(color_options.keys()))
    sel_color = color_options[sel_color_label]
    paint_name = sel_color["name"]
    paint_hex = sel_color["hex"]
    paint_brand = sel_brand
    paint_code = sel_color["code"]
    st.markdown(f'{color_swatch_html(paint_hex, 35)} `{paint_hex}`', unsafe_allow_html=True)
else:
    paint_name = st.text_input("Color name", key="custom_name")
    paint_hex = st.color_picker("Pick color", "#ffffff", key="custom_color")
    paint_brand = st.text_input("Brand (optional)", key="custom_brand")
    paint_code = st.text_input("Code (optional)", key="custom_code")

notes = st.text_input("Notes (optional)")

if st.button("Add Paint Entry"):
    if paint_name:
        room["paints"].append({
            "name": paint_name,
            "hex": paint_hex,
            "brand": paint_brand,
            "code": paint_code,
            "surface": surface,
            "finish": finish,
            "notes": notes,
        })
        save_json("rooms.json", rooms_data)
        st.success(f"Added {paint_name} to {room['name']}!")
        st.rerun()
    else:
        st.warning("Please provide a color name.")

# ── Display room paints ──
st.markdown("---")
st.subheader(f"Paints in {room['name']}")

if not room["paints"]:
    st.info("No paints recorded for this room yet.")
else:
    for i, p in enumerate(room["paints"]):
        col1, col2, col3 = st.columns([3, 5, 1])
        with col1:
            st.markdown(
                f'{color_swatch_html(p["hex"], 30)} **{p["name"]}**',
                unsafe_allow_html=True,
            )
        with col2:
            parts = [p["surface"], p["finish"]]
            if p.get("brand"):
                parts.insert(0, p["brand"])
            if p.get("code"):
                parts.append(p["code"])
            st.write(" | ".join(parts))
            if p.get("notes"):
                st.caption(p["notes"])
        with col3:
            if st.button("\U0001f5d1", key=f"del_paint_{i}"):
                room["paints"].pop(i)
                save_json("rooms.json", rooms_data)
                st.rerun()

# ── Delete room ──
st.markdown("---")
if st.button(f"Delete room '{room['name']}'", type="secondary"):
    rooms_data["rooms"].pop(room_idx)
    save_json("rooms.json", rooms_data)
    st.rerun()
