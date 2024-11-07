import streamlit as st
from streamlit_extras.colored_header import colored_header
from streamlit_extras.add_vertical_space import add_vertical_space

st.set_page_config(page_title="Diego 工具箱", layout="centered")

camera_page = st.Page("lhpg_camera_data.py", title="相机数据处理", icon="📸")
motor_page = st.Page("lhpg_motor_data.py", title="电机数据处理", icon="⚙️")
spectra_page = st.Page("lhpg_spectra_data.py", title="光谱数据处理", icon="🌈")
gif_page = st.Page("make_gif.py", title="制作GIF", icon="🎞️")
pdf_page = st.Page("make_pdf.py", title="制作PDF", icon="📃")
pg = st.navigation([camera_page, motor_page, spectra_page, gif_page, pdf_page])


with st.sidebar:
    st.title("Diego Utilities")
    add_vertical_space(10)
    st.image("diego studio logo.png")
    st.text("copyright © 2024 Diego")

colored_header(label="Diego 工具箱", description="请从侧边栏选择一个模块开始。")
add_vertical_space(2)

pg.run()
