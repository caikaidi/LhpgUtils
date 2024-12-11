import os

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from _tool_functions import auto_fft, downsample_data

# 设置页面标题
st.markdown("#### → ⚙️电机数据处理模块")
st.text("选择一个文件夹来加载电机文件。")


@st.cache_data
def load_data(file_path) -> pd.DataFrame:
    if file_path:
        return pd.read_pickle(file_path)
    return pd.DataFrame()


# 输入文件夹路径
folder_path = st.text_input("请输入文件夹路径：").strip("\"'")

# 查找文件夹下的所有 .pkl 文件
pkl_files = []

if folder_path:
    # 检查文件夹是否存在
    if not os.path.isdir(folder_path):
        st.write("输入的文件夹路径无效，请重新输入。")
    else:
        # 获取所有 .pkl 文件
        # .pkl结尾并且包含motor
        pkl_files = [
            f for f in os.listdir(folder_path) if f.endswith(".pkl") and "motor" in f
        ]

        if not pkl_files:
            st.write("该文件夹中没有找到 .pkl 文件。")
        else:
            st.write("找到以下 .pkl 文件：")
            # 将文件列表转换为 DataFrame 并展示
            df_list = []
            for f in pkl_files:
                # 获取文件创建时间
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

                # 显示前10行数据
                st.write(f"文件 `{selected_file}` 中的数据")
                st.dataframe(df.head(10))

                # 获取列名列表
                columns = df.columns.tolist()
                pull_speed = df["motor1"].mode()[0]

                # 默认绘图
                if "time_axis" in df.columns and "fiber diameter" in df.columns:
                    df_sampled = downsample_data(df)
                    fig = px.line(
                        df_sampled,
                        x="time_axis",
                        y="fiber diameter",
                        labels={"x": "Time (min)", "y": "Fiber Diameter (μm)"},
                        title=f"{selected_file} - 默认绘图",
                    )
                    st.plotly_chart(fig)

                    # 频谱图
                    x_sec = df["time_axis"] * 60
                    df_fft = auto_fft(x_sec, df["fiber diameter"], cut_off=1, downsample_length=50000)
                    fig_fft = px.line(
                        df_fft,
                        x="x_fft",
                        y="y_fft",
                        title=f"{selected_file} - 频谱图",
                    )

                    st.plotly_chart(fig_fft)
                else:
                    st.write(
                        "数据中缺少 `time_axis` 或 `fiber diameter` 列，无法绘制默认图表。"
                    )

                # 手动选择列并更新绘图
                st.markdown(
                    f"本次拉制速度：***{pull_speed:.2f} mm/min***, 选择需要的列："
                )
                columns = df.columns.tolist()
                x_axis = st.selectbox(
                    "选择 X 轴",
                    columns,
                    index=columns.index("time_axis") if "time_axis" in columns else 0,
                )
                y_axis = st.selectbox(
                    "选择 Y 轴",
                    columns,
                    index=columns.index("fiber diameter")
                    if "fiber diameter" in columns
                    else 0,
                )

                if st.button("更新图表"):
                    df_sampled = downsample_data(df)
                    fig = px.line(
                        df_sampled,
                        x=x_axis,
                        y=y_axis,
                        title=f"{selected_file}",
                    )
                    st.plotly_chart(fig)
