import os
import shutil
import plotly.express as px
import tempfile
import zipfile
from concurrent.futures import ThreadPoolExecutor
from diegoplot import diegoplot

import pandas as pd
import streamlit as st

from _tool_functions import (
    convert_to_video,
    downsample_data,
    get_intensity_by_wavelength,
    linear_curve_fit,
)

st.markdown("#### → 🧰LHPG summary 处理模块")
st.text("选择一个文件夹来加载相机文件。")

# 选择文件夹路径
folder_path = st.text_input("请输入文件夹路径：")

# 初始化文件列表
st.session_state["camera_file"] = None
st.session_state["motor_file"] = None
st.session_state["spectra_file"] = None

if folder_path:
    # 检查文件夹是否存在
    if not os.path.isdir(folder_path):
        st.write("输入的文件夹路径无效，请重新输入。")
    else:
        # 遍历文件夹，获取文件列表
        st.session_state["folder_path"] = folder_path
        for file in os.listdir(folder_path):
            if file.endswith(".zip"):
                st.session_state["camera_file"] = os.path.join(folder_path, file)
            elif file.endswith(".pkl") and "motor" in file:
                st.session_state["motor_file"] = os.path.join(folder_path, file)
            elif file.endswith(".pkl") and "spectra" in file:
                st.session_state["spectra_file"] = os.path.join(folder_path, file)
        if (
            st.session_state["camera_file"]
            and st.session_state["motor_file"]
            and st.session_state["spectra_file"]
        ):
            st.success("文件加载成功！")

# 相机处理
if st.session_state["camera_file"]:
    st.markdown("##### 📸1. 相机文件转视频")
    if st.button("开始处理"):
        # 解压缩
        try:
            temp_dir = tempfile.mkdtemp()
            with st.spinner("正在解压缩文件..."):
                with zipfile.ZipFile(st.session_state["camera_file"], "r") as zip_file:
                    camera_file_list = zip_file.namelist()

                    def extract_file(file_name):
                        zip_file.extract(file_name, temp_dir)

                    with ThreadPoolExecutor(max_workers=6) as executor:
                        executor.map(extract_file, camera_file_list)

            # 转视频
            camera_file_list = os.listdir(temp_dir)
            convert_to_video(
                camera_file_list,
                st.session_state["folder_path"],
                file_folder_path=temp_dir,
            )
            st.success("视频生成完成！")
        finally:
            shutil.rmtree(temp_dir)

# 电机处理
if st.session_state["motor_file"]:
    st.markdown("##### ⚙️2. 电机数据处理")
    motor_df = pd.read_pickle(st.session_state["motor_file"])
    pull_speed = motor_df["motor1"].mode()[0]
    st.markdown(f"本次拉制速度：***{pull_speed} mm/min***, 选择需要的列：")
    column_name = st.selectbox(
        "选择需要的列", motor_df.columns, index=1, label_visibility="collapsed"
    )

    motor_df_resampled = downsample_data(motor_df)
    fig = px.line(
        motor_df_resampled,
        x=motor_df_resampled.index,
        y=column_name,
        labels={"x": "Time (min)", "y": "Fiber Diameter (μm)"},
        title="电机数据预览",
    )
    st.plotly_chart(fig)
    st.markdown("**设置绘图参数**")
    motor_fig_set_1, motor_fig_set_2 = st.columns(2)
    with motor_fig_set_1:
        x_start = st.number_input(
            "起始index", value=0, min_value=0, max_value=len(motor_df) - 1
        )
        x_end = st.number_input(
            "终止index",
            value=len(motor_df) - 1,
            min_value=0,
            max_value=len(motor_df) - 1,
        )
        start_at_zero = st.checkbox("横轴从零开始", value=True)
    with motor_fig_set_2:
        x_label = st.text_input("X轴标签", value="Length (mm)")
        y_label = st.text_input("Y轴标签", value="Fiber Diameter (μm)")
        use_length = st.checkbox("横轴使用长度", value=True)
    if st.button("生成图表"):
        dp_motor = diegoplot.DiegoPlot()
        x_data = motor_df["time_axis"].iloc[x_start:x_end]
        if use_length:
            x_data = x_data * pull_speed
        if start_at_zero:
            x_data -= x_data.iloc[0]
        dp_motor.ax.plot(x_data, motor_df[column_name].iloc[x_start:x_end])
        dp_motor.plot_label([x_label, y_label])
        dp_motor.fig.tight_layout()
        st.pyplot(dp_motor.fig)

# 光谱处理
if st.session_state["spectra_file"]:
    st.markdown("##### 🌈3. 光谱数据处理")
    spectra_df = pd.read_pickle(st.session_state["spectra_file"])
    spectra_df_resampled = downsample_data(spectra_df)

    wavelength = st.number_input(
        "选择波长", value=1550.0, min_value=0.0, max_value=4000.0
    )
    smooth = st.checkbox("平滑光谱", value=False)
    intensity = get_intensity_by_wavelength(
        spectra_df_resampled, wavelength, smooth, to_db=False
    )
    fig = px.line(
        spectra_df_resampled,
        x=spectra_df_resampled.index,
        y=intensity,
        labels={"x": "Time (min)", "y": "Intensity (a.u.)"},
        title="光谱数据预览",
    )
    st.plotly_chart(fig)
    st.markdown("**设置绘图参数**")
    spectra_fig_set_1, spectra_fig_set_2 = st.columns(2)
    with spectra_fig_set_1:
        x_start = st.number_input(
            "起始index", value=0, min_value=0, max_value=len(spectra_df) - 1
        )
        x_end = st.number_input(
            "终止index",
            value=len(spectra_df) - 1,
            min_value=0,
            max_value=len(spectra_df) - 1,
        )

    with spectra_fig_set_2:
        output_smooth = st.checkbox("平滑光谱", value=True)
        to_db = st.checkbox("转换为dB", value=True)
        fit = st.checkbox("拟合损耗", value=False)

    if st.button("生成损耗图"):
        dp_spectra = diegoplot.DiegoPlot()
        x_data = spectra_df["time_axis"].iloc[x_start:x_end] * pull_speed
        y_data = get_intensity_by_wavelength(
            spectra_df.iloc[x_start:x_end], wavelength, output_smooth, to_db
        )
        y_label = "Loss (dB)" if to_db else "Intensity (a.u.)"
        dp_spectra.ax.plot(x_data, y_data)
        dp_spectra.plot_label(["Length (mm)", "Intensity (a.u.)"])

        if fit:
            a, b = linear_curve_fit(x_data, y_data)
            dp_spectra.ax.plot(x_data, a * x_data + b, "r--", label="fit")
            dp_spectra.ax.set_title(
                f"Fitted Loss: {a*1000:.3f} dB/m @ {wavelength:.1f} nm",
                fontdict={"fontsize": 18},
            )
        dp_spectra.fig.tight_layout()
        st.pyplot(dp_spectra.fig)
