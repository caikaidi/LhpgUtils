import streamlit as st
import pandas as pd
import plotly.figure_factory as ff
import plotly.express as px

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
        # 缓存绘图并显示
        # fig = ff.create_distplot(x=x_axis, y=y_axis)
        fig = px.line(df, x=x_axis, y=y_axis)
        st.plotly_chart(fig)
