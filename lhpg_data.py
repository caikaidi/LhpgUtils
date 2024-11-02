import streamlit as st
camera_page = st.Page("lhpg_camera_data.py", title="相机数据处理", icon="📸")
motor_page = st.Page("lhpg_motor_data.py", title="电机数据处理", icon="⚙️")
spectra_page = st.Page("lhpg_spectra_data.py", title="光谱数据处理", icon="🌈")

pg = st.navigation([camera_page, motor_page, spectra_page])
st.set_page_config(page_title="实验数据处理工具", layout="wide")
st.markdown("*← 请从侧边栏选择一个模块开始。*")

pg.run()

