import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os

# 设置页面标题
st.markdown("#### → 🔋️功率数据处理模块")
st.text("选择一个文件夹来加载功率文件。")

DEFAULT_SAMPLING_INTERVAL = 1  # 默认采样间隔（秒）


@st.cache_data
def load_power_data(file_path) -> pd.DataFrame:
    """加载功率数据并处理为标准格式"""
    if file_path:
        # 读取 .txt 文件
        df = pd.read_csv(file_path, sep="\t", skiprows=1, header=None)
        # 保留第二列和第四列并重命名
        df = df.iloc[:, [1, 3]]
        df.columns = ["voltage", "power"]
        return df
    return pd.DataFrame()


def downsample_data(df: pd.DataFrame, max_points: int = 10000) -> pd.DataFrame:
    """对数据进行下采样，确保数据点数量不超过 max_points"""
    if len(df) > max_points:
        df = df.iloc[:: len(df) // max_points]
    return df


def add_time_axis(df: pd.DataFrame, interval: float) -> pd.DataFrame:
    """根据采样间隔添加时间轴"""
    df["time"] = df.index * interval / 60  # 转换为分钟
    return df


# 输入文件夹路径
folder_path = st.text_input("请输入文件夹路径：")

# 查找文件夹下的所有 .txt 文件
txt_files = []

if folder_path:
    # 检查文件夹是否存在
    if not os.path.isdir(folder_path):
        st.write("输入的文件夹路径无效，请重新输入。")
    else:
        # 获取所有 .txt 文件
        txt_files = [f for f in os.listdir(folder_path) if f.endswith(".txt")]

        if not txt_files:
            st.write("该文件夹中没有找到 .txt 文件。")
        else:
            st.write("找到以下 .txt 文件：")
            # 将文件列表转换为 DataFrame 并展示
            df_list = []
            for f in txt_files:
                # 获取文件创建时间
                create_time = os.path.getctime(os.path.join(folder_path, f))
                formatted_time = pd.to_datetime(create_time, unit="s")
                df_list.append({"filename": f, "create_time": formatted_time})
            df_files = pd.DataFrame(df_list)
            selected_file = st.selectbox("请选择文件：", df_files["filename"].tolist())

            if selected_file:
                file_path = os.path.join(folder_path, selected_file)
                df = load_power_data(file_path)

                # 添加时间轴
                df = add_time_axis(df, DEFAULT_SAMPLING_INTERVAL)

                # 显示前10行数据
                st.write(f"文件 `{selected_file}` 中的数据")
                st.dataframe(df.head(10))

                # 默认绘图
                df_sampled = downsample_data(df)
                fig = go.Figure()
                fig.add_trace(
                    go.Scatter(
                        x=df_sampled["time"],
                        y=df_sampled["power"],
                        mode="lines",
                        name="Power",
                    )
                )
                fig.update_layout(
                    title=f"{selected_file} - 功率曲线",
                    xaxis_title="Time (min)",
                    yaxis_title="Power (W)",
                )
                # 绘制图表
                fig = go.Figure()
                fig.add_trace(
                    go.Scatter(
                        x=df_sampled["time"],
                        y=df_sampled["power"],
                        mode="lines",
                        name="Power",
                    )
                )
                fig.update_layout(
                    title=f"{selected_file} - 功率曲线",
                    xaxis_title="Time (min)",
                    yaxis_title="Power (W)",
                )

                plot = st.plotly_chart(fig, use_container_width=True, config={"editable": True})
