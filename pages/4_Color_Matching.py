import streamlit as st
import numpy as np
from PIL import Image
from sklearn.cluster import KMeans
from lib.color_utils import rgb_to_hex, color_swatch_html
from lib.paint_db import load_all_brands, find_closest

st.set_page_config(page_title="Color Matching", page_icon="\U0001f50d", layout="wide")
st.title("\U0001f50d Color Matching")
st.markdown("Upload a photo to extract its dominant colors and find matching paints.")

brands = load_all_brands()

uploaded = st.file_uploader("Upload a photo", type=["png", "jpg", "jpeg"])

if uploaded:
    image = Image.open(uploaded).convert("RGB")
    st.image(image, caption="Uploaded image", use_container_width=True)

    n_colors = st.slider("Number of colors to extract", 3, 10, 5)

    if st.button("Extract Colors"):
        with st.spinner("Analyzing image..."):
            # Resize for speed
            img_small = image.copy()
            img_small.thumbnail((200, 200))
            pixels = np.array(img_small).reshape(-1, 3)

            kmeans = KMeans(n_clusters=n_colors, n_init=10, random_state=42)
            kmeans.fit(pixels)

            # Sort clusters by frequency
            labels, counts = np.unique(kmeans.labels_, return_counts=True)
            sorted_idx = np.argsort(-counts)
            centers = kmeans.cluster_centers_[sorted_idx].astype(int)
            sorted_counts = counts[sorted_idx]
            total = sorted_counts.sum()

        st.subheader("Extracted Colors")
        cols = st.columns(n_colors)
        extracted = []
        for i, center in enumerate(centers):
            r, g, b = int(center[0]), int(center[1]), int(center[2])
            hex_val = rgb_to_hex(r, g, b)
            pct = sorted_counts[i] / total * 100
            extracted.append(hex_val)
            with cols[i]:
                st.markdown(
                    f'{color_swatch_html(hex_val, 50)}<br>`{hex_val}`<br>{pct:.1f}%',
                    unsafe_allow_html=True,
                )

        # Match each extracted color to paints
        st.markdown("---")
        st.subheader("Closest Paint Matches")
        for hex_val in extracted:
            st.markdown(f"#### {color_swatch_html(hex_val, 25)} `{hex_val}`", unsafe_allow_html=True)
            matches = find_closest(hex_val, n=3, brands=brands)
            mcols = st.columns(3)
            for j, m in enumerate(matches):
                with mcols[j]:
                    st.markdown(
                        f'{color_swatch_html(m["hex"], 30)} **{m["name"]}**<br>'
                        f'{m["brand"]} ({m["code"]})<br>'
                        f'`{m["hex"]}` — distance {m["distance"]}',
                        unsafe_allow_html=True,
                    )
else:
    st.info("Drag & drop or click to upload a photo of a room, wall, or inspiration image.")
