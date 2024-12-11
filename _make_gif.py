import os

import cv2
import pandas as pd
import streamlit as st
from PIL import Image

# 设置页面标题
st.markdown("#### GIF 制作工具")
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
folder_path = st.text_input("请输入文件夹路径：").strip("\"'")

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
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        compression_choice = st.selectbox(
                            "压缩级别",
                            ["无损", "256", "128", "64", "32"],
                            help="如选择32，则输出GIF中将只有32种颜色。",
                        )
                    with col2:
                        fps = st.number_input("帧率 (FPS)", min_value=1, value=25)
                    with col3:
                        speed_multiplier = st.number_input(
                            "倍速", min_value=0.1, value=1.0, step=0.1
                        )
                    with col4:
                        output_filename = st.text_input(
                            "输出文件名", value="output.gif"
                        )

                    # 添加裁剪功能
                    if selected_files[0].lower().endswith((".mp4", ".avi")):
                        file_path = os.path.join(folder_path, selected_files[0])
                        cap = cv2.VideoCapture(file_path)
                        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                        video_fps = cap.get(cv2.CAP_PROP_FPS)
                        video_duration = total_frames / video_fps

                        start_time, end_time = st.slider(
                            "选择裁剪时间范围 (秒)",
                            min_value=0.0,
                            max_value=video_duration,
                            value=(0.0, video_duration),
                            step=0.1,
                        )

                        # 显示起止位置的帧图像
                        col1, col2 = st.columns(2)

                        with col1:
                            frame_position_start = int(start_time * video_fps)
                            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_position_start)
                            ret, frame_start = cap.read()
                            if ret:
                                st.image(
                                    cv2.cvtColor(frame_start, cv2.COLOR_BGR2RGB),
                                    caption=f"起始帧 (时间: {start_time:.1f} 秒)",
                                )

                        with col2:
                            frame_position_end = int(end_time * video_fps)
                            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_position_end)
                            ret, frame_end = cap.read()
                            if ret:
                                st.image(
                                    cv2.cvtColor(frame_end, cv2.COLOR_BGR2RGB),
                                    caption=f"结束帧 (时间: {end_time:.1f} 秒)",
                                )

                        cap.release()

                        # 计算帧数信息
                        total_extracted_frames = int(
                            (end_time - start_time) * video_fps
                        )
                        total_output_frames = int(
                            total_extracted_frames / speed_multiplier
                        )  # * (fps / video_fps))
                        st.markdown(
                            f"*当前截取范围包含 {total_extracted_frames} 帧，输出 GIF 约 {total_output_frames} 帧，持续时间 {total_output_frames / fps:.1f} 秒。*"
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
                                frame_start = int(start_time * video_fps)
                                frame_end = int(end_time * video_fps)
                                frame_step = int(speed_multiplier)

                                current_frame = frame_start
                                while current_frame <= frame_end:
                                    cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame)
                                    ret, frame = cap.read()
                                    if not ret:
                                        break
                                    images.append(
                                        Image.fromarray(
                                            cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                                        )
                                    )
                                    current_frame += frame_step
                                cap.release()
                                st.write(
                                    f"视频文件 {file} 已提取 {len(images)} 张图片。"
                                )
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
