import streamlit as st
import os
from _tool_functions import file_list_to_df, convert_to_images, convert_to_video


st.markdown("#### → 📸相机数据处理模块")
st.text("选择一个文件夹来加载相机文件。")

# 选择文件夹路径
folder_path = st.text_input("请输入文件夹路径：")

# 初始化文件列表
bin_files = []

if folder_path:
    # 检查文件夹是否存在
    if not os.path.isdir(folder_path):
        st.write("输入的文件夹路径无效，请重新输入。")
    else:
        # 获取所有 .bin 文件
        bin_files = [f for f in os.listdir(folder_path) if f.endswith(".bin")]

        if not bin_files:
            st.write("该文件夹中没有找到 .bin 文件。")
        else:
            st.write("找到以下 .bin 文件：")
            st.session_state.df = file_list_to_df(bin_files)
            event = st.dataframe(
                st.session_state.df, on_select="rerun", selection_mode="multi-row"
            )

            # 获取选择的文件索引
            selected_indices = event.selection["rows"]  # 获取用户选择的索引
            selected_files = (
                st.session_state.df.iloc[selected_indices]["filename"].tolist()
                if selected_indices
                else []
            )

            if selected_files:
                st.write(f"您选择了 {len(selected_files)} 个文件")

            # 添加转图片和转视频按钮
            col1, col2 = st.columns(2)

            with col1:
                if st.button("转为图片 📸"):
                    # 调用转换为图片的函数，传递选择的文件
                    convert_to_images(selected_files, folder_path)
                    st.success("图片转换成功！")

            with col2:
                if st.button("转为视频 🎥"):
                    # 调用转换为视频的函数，传递选择的文件
                    convert_to_video(selected_files, folder_path)
                    st.success("视频转换成功！")
