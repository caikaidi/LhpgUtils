import os
import streamlit as st
import pandas as pd
from PIL import Image
import cv2

# 设置页面标题
st.title("GIF 制作模块")
st.write("选择一个文件夹来加载图片/视频文件。")


@st.cache_data
def load_files(folder_path):
    """加载文件夹中的所有图片和视频文件"""
    files = [
        f
        for f in os.listdir(folder_path)
        if f.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".mp4", ".avi"))
    ]
    df_list = []
    for f in files:
        create_time = os.path.getctime(os.path.join(folder_path, f))
        formatted_time = pd.to_datetime(create_time, unit="s")
        df_list.append({"filename": f, "create_time": formatted_time})
    return pd.DataFrame(df_list)


# 输入文件夹路径
folder_path = st.text_input("请输入文件夹路径：")

if folder_path:
    if not os.path.isdir(folder_path):
        st.write("输入的文件夹路径无效，请重新输入。")
    else:
        df_files = load_files(folder_path)
        if df_files.empty:
            st.write("该文件夹中没有找到图片或视频文件。")
        else:
            st.write("找到以下文件：")
            event = st.dataframe(
                df_files, on_select="rerun", selection_mode="multi-row"
            )

            selected_indices = event.selection["rows"]
            selected_files = (
                df_files.iloc[selected_indices]["filename"].to_list()
                if selected_indices
                else []
            )

            if selected_files:
                # 检查文件类型
                file_types = {file.split(".")[-1] for file in selected_files}
                if len(file_types) > 1:
                    st.error("选择的文件包含不同类型，不能混合使用图片和视频。")
                else:
                    st.write(f"您选择了 {len(selected_files)} 个文件。")

                    # GIF 参数输入
                    compression_choice = st.selectbox("压缩级别", [32, 64, 128, "无损"])
                    fps = st.number_input("帧率 (FPS)", min_value=1, value=25)
                    output_filename = st.text_input(
                        "输出 GIF 文件名", value="output.gif"
                    )
                    if st.button("生成 GIF"):
                        images = []
                        read_process_bar = st.progress(
                            0, text="正在读取第 0 个文件"
                        )  # 初始化进度条
                        total_files = len(selected_files)

                        for i, file in enumerate(selected_files):
                            file_path = os.path.join(folder_path, file)
                            if file.lower().endswith((".mp4", ".avi")):
                                # 读取视频文件并提取帧
                                cap = cv2.VideoCapture(file_path)
                                while cap.isOpened():
                                    ret, frame = cap.read()
                                    if not ret:
                                        break
                                    images.append(
                                        Image.fromarray(
                                            cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                                        )
                                    )
                                cap.release()
                            else:
                                # 读取图片文件
                                img = Image.open(file_path)
                                images.append(img)

                            # 更新进度条
                            read_process_bar.progress(
                                (i + 1) / total_files, text=f"正在读取第 {i + 1} 个文件"
                            )
                        read_process_bar.empty()

                        # 创建 GIF
                        gif_path = os.path.join(folder_path, output_filename)
                        if images:
                            if compression_choice == "无损":
                                compressed_images = images  # 无损处理，直接使用原图
                            else:
                                with st.spinner("正在压缩图片..."):
                                    color_reduction = int(
                                        compression_choice
                                    )  # 将选择的压缩比转为整数
                                    compressed_images = [
                                        img.convert(
                                            "P",
                                            palette=Image.ADAPTIVE,
                                            colors=color_reduction,
                                        )
                                        for img in images
                                    ]
                            duration = 1000 // fps  # 转换为毫秒
                            with st.spinner("正在生成 GIF..."):
                                compressed_images[0].save(
                                    gif_path,
                                    save_all=True,
                                    append_images=compressed_images[1:],
                                    duration=duration,
                                    loop=0,
                                )
                            st.success(f"GIF 文件已生成: {gif_path}")
                        else:
                            st.error("未能生成 GIF，检查选择的文件是否有效。")
