import os

import pandas as pd
import plotly.express as px
import streamlit as st

from _tool_functions import downsample_data, get_intensity_by_wavelength

# 设置页面标题
st.markdown("#### → 🌈光谱数据处理模块")
st.text("选择一个文件夹来加载光谱数据文件。")


@st.cache_data
def load_data(file_path) -> pd.DataFrame:
    if file_path:
        return pd.read_pickle(file_path)
    return pd.DataFrame()


# 输入文件夹路径
folder_path = st.text_input("请输入文件夹路径：").strip("\"'")

# 查找文件夹下的所有包含 "spectra" 的 .pkl 文件
spectra_files = []

if folder_path:
    # 检查文件夹是否存在
    if not os.path.isdir(folder_path):
        st.write("输入的文件夹路径无效，请重新输入。")
    else:
        # 获取所有包含“spectra”的 .pkl 文件
        spectra_files = [
            f for f in os.listdir(folder_path) if f.endswith(".pkl") and "spectra" in f
        ]

        if not spectra_files:
            st.write("该文件夹中没有找到包含 'spectra' 的 .pkl 文件。")
        else:
            st.write("找到以下 .pkl 文件：")
            # 将文件列表转换为 DataFrame 并展示
            df_list = []
            for f in spectra_files:
                create_time = os.path.getctime(os.path.join(folder_path, f))
                formatted_time = pd.to_datetime(create_time, unit="s")
                df_list.append({"filename": f, "create_time": formatted_time})
            df_files = pd.DataFrame(df_list)
            event = st.dataframe(
                df_files, on_select="rerun", selection_mode="single-row"
            )

            selected_index = event.selection["rows"]
            selected_file = (
                df_files.iloc[selected_index]["filename"].to_list()
                if selected_index
                else []
            )

            if len(selected_file) > 0:
                selected_file = selected_file[0]
                file_path = os.path.join(folder_path, selected_file)
                df = load_data(file_path)

                # 显示数据统计
                total_rows = len(df)
                last_time = df["time_axis"].iloc[-1] if total_rows > 0 else "N/A"
                st.markdown(
                    f"文件共有 `{total_rows}` 行数据，时间长度为 `{last_time:.0f}` min。"
                )

                # 检查是否包含光谱所需的列
                if {"time_axis", "wavelengths", "intensitys"}.issubset(df.columns):
                    # 选择要绘制的行数
                    row_to_plot = st.number_input(
                        "选择要绘制的行数",
                        min_value=0,
                        max_value=total_rows - 1,
                        value=0,
                        step=1,
                    )

                    # 获取指定行的光谱数据
                    wavelengths = df["wavelengths"].iloc[row_to_plot]
                    intensitys = df["intensitys"].iloc[row_to_plot]

                    # 绘制光谱图
                    fig = px.line(
                        x=wavelengths,
                        y=intensitys,
                        labels={"x": "Wavelength (nm)", "y": "Intensity"},
                        title=f"{selected_file} - 第{row_to_plot+1}行光谱数据",
                    )
                    st.plotly_chart(fig)
                else:
                    st.write(
                        "数据中缺少 `time_axis`、`wavelengths` 或 `intensitys` 列，无法绘制光谱图。"
                    )

                # 输入查询的波长值
                wavelength = st.number_input(
                    "输入要查询的波长（nm）",
                    min_value=0.0,
                    max_value=4000.0,
                    value=1550.0,
                )

                # 是否平滑和转换为 dB
                smooth = st.checkbox("平滑数据")
                to_db = st.checkbox("将强度转换为 dB")

                # 获取指定波长的强度值
                intensity = get_intensity_by_wavelength(
                    df, wavelength, smooth=smooth, to_db=to_db
                )

                # 绘制强度值的时间序列图
                fig = px.line(
                    x=downsample_data(df["time_axis"].to_numpy()),
                    y=downsample_data(intensity),
                    labels={
                        "x": "Time (minutes)",
                        "y": "Intensity (dB)" if to_db else "Intensity",
                    },
                    title=f"{selected_file} - {wavelength} nm 处的光谱强度",
                )
                st.plotly_chart(fig)
