import streamlit as st
import pandas as pd
from matplotlib import pyplot as plt

# 设置页面标题
st.title("Pandas DataFrame Visualizer")


@st.cache_data
def load_data(file) -> pd.DataFrame:
    if file is not None:
        return pd.read_pickle(file)
    return pd.DataFrame()


# 上传 .pkl 文件
uploaded_file = st.file_uploader("Upload a .pkl file", type="pkl")

if uploaded_file is not None:
    df: pd.DataFrame = load_data(uploaded_file)

    # 仅显示最多10行的数据
    st.write("Data from the .pkl file (showing up to 10 rows):")
    if len(df) > 10:
        st.dataframe(df.head(10))
    else:
        st.dataframe(df)

    # 获取列名列表
    columns: list[str] = df.columns.tolist()

    # 选择需要绘制的列
    st.write("Select columns for visualization:")
    x_axis: str = st.selectbox("Select X-axis", columns)
    y_axis: str = st.selectbox("Select Y-axis", columns)

    if st.button("Plot"):
        # 绘图并显示
        plt.rcParams["font.family"] = "Times New Roman"
        plt.rcParams["mathtext.fontset"] = "stix"
        plt.rcParams["font.size"] = 30
        plt.rcParams['xtick.direction'] = 'in'
        plt.rcParams['ytick.direction'] = 'in'
        fig, ax = plt.subplots()
        ax.plot(df[x_axis], df[y_axis])
        ax.set_xlabel(x_axis)
        ax.set_ylabel(y_axis)
        st.pyplot(fig)
