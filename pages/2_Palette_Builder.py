import streamlit as st
from lib.paint_db import load_all_brands, search_by_name, find_closest
from lib.color_utils import hex_to_rgb, rgb_to_hex, complementary, triadic, color_swatch_html
from lib.persistence import load_json, save_json

st.set_page_config(page_title="Palette Builder", page_icon="\U0001f308", layout="wide")
st.title("\U0001f308 Palette Builder")

# --- Load data ---
brands = load_all_brands()
palettes: dict = load_json("palettes.json", default={"palettes": []})

# ── Sidebar: saved palettes ──
st.sidebar.header("Saved Palettes")
for i, pal in enumerate(palettes["palettes"]):
    with st.sidebar.expander(pal["name"]):
        for c in pal["colors"]:
            st.markdown(
                f'{color_swatch_html(c["hex"])} **{c["name"]}** ({c["hex"]})',
                unsafe_allow_html=True,
            )
        if st.button("Delete", key=f"del_pal_{i}"):
            palettes["palettes"].pop(i)
            save_json("palettes.json", palettes)
            st.rerun()

# ── Browse brand colors ──
st.subheader("Browse Brand Colors")
brand_names = [b["brand"] for b in brands]
selected_brand = st.selectbox("Select brand", brand_names)
brand_data = next(b for b in brands if b["brand"] == selected_brand)

search_q = st.text_input("Filter by name")
colors_list = brand_data["colors"]
if search_q:
    colors_list = [c for c in colors_list if search_q.lower() in c["name"].lower()]

# Display as a grid
cols = st.columns(5)
for idx, color in enumerate(colors_list):
    with cols[idx % 5]:
        st.markdown(
            f'{color_swatch_html(color["hex"], 40)}<br>'
            f'**{color["name"]}**<br>'
            f'{color.get("code", "")} &nbsp; `{color["hex"]}`',
            unsafe_allow_html=True,
        )
        if st.button("Add", key=f"add_{selected_brand}_{idx}"):
            if "current_palette" not in st.session_state:
                st.session_state.current_palette = []
            st.session_state.current_palette.append(
                {"name": color["name"], "hex": color["hex"], "brand": selected_brand}
            )

# ── Search across all brands ──
st.subheader("Search All Brands")
global_q = st.text_input("Search by color name", key="global_search")
if global_q:
    results = search_by_name(global_q, brands)
    if results:
        for r in results[:20]:
            st.markdown(
                f'{color_swatch_html(r["hex"])} **{r["name"]}** — {r["brand"]} ({r["hex"]})',
                unsafe_allow_html=True,
            )
    else:
        st.info("No matches found.")

# ── Find closest paint to a custom color ──
st.subheader("Match a Custom Color")
picked = st.color_picker("Pick a color", "#7a9e7e")
if picked:
    matches = find_closest(picked, n=8, brands=brands)
    st.write(f"Closest paints to `{picked}`:")
    for m in matches:
        st.markdown(
            f'{color_swatch_html(m["hex"])} **{m["name"]}** — {m["brand"]} '
            f'(`{m["hex"]}`, distance {m["distance"]})',
            unsafe_allow_html=True,
        )

# ── Current palette ──
st.markdown("---")
st.subheader("Current Palette")
current = st.session_state.get("current_palette", [])
if not current:
    st.info("Add colors from above to start building a palette.")
else:
    cols = st.columns(len(current))
    for i, c in enumerate(current):
        with cols[i]:
            st.markdown(
                f'{color_swatch_html(c["hex"], 50)}<br>**{c["name"]}**',
                unsafe_allow_html=True,
            )
            if st.button("\u2716", key=f"rm_{i}"):
                current.pop(i)
                st.session_state.current_palette = current
                st.rerun()

    # Color suggestions
    if current:
        st.markdown("**Suggestions based on your first color:**")
        base = current[0]["hex"]
        comp = complementary(base)
        tri = triadic(base)
        suggestions = [("Complementary", comp)] + [(f"Triadic {j+1}", t) for j, t in enumerate(tri)]
        scols = st.columns(len(suggestions))
        for j, (label, shex) in enumerate(suggestions):
            with scols[j]:
                st.markdown(
                    f'{color_swatch_html(shex, 35)}<br>{label}<br>`{shex}`',
                    unsafe_allow_html=True,
                )

    # Save palette
    st.markdown("---")
    pal_name = st.text_input("Palette name")
    if st.button("Save Palette") and pal_name and current:
        palettes["palettes"].append({"name": pal_name, "colors": current})
        save_json("palettes.json", palettes)
        st.session_state.current_palette = []
        st.success(f"Saved palette '{pal_name}'!")
        st.rerun()
