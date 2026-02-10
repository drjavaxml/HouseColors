import streamlit as st

st.set_page_config(page_title="HouseColors", page_icon="\U0001f3e0", layout="wide")

st.markdown("""<style>
    .block-container { max-width: 1000px; }
    @media (max-width: 640px) {
        .block-container { padding: 1rem; }
    }
</style>""", unsafe_allow_html=True)

st.title("\U0001f3e0 HouseColors")
st.markdown("Your all-in-one tool for house color visualization, palette building, and paint tracking.")

st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    st.subheader("\U0001f3a8 Color Visualizer")
    st.write("Apply colors to a house template or your own photo and download the result.")

    st.subheader("\U0001f4cb Paint Tracker")
    st.write("Track which paints you've used in each room of your house.")

with col2:
    st.subheader("\U0001f308 Palette Builder")
    st.write("Browse paint brand colors, build custom palettes, and get color suggestions.")

    st.subheader("\U0001f50d Color Matching")
    st.write("Upload a photo and find the closest matching paint colors.")

st.markdown("---")
st.caption("Use the sidebar to navigate between pages.")
