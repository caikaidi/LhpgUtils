import streamlit as st
import pandas as pd
import numpy as np
import zstd
import struct
import os
import cv2
import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from PIL import Image


def bin_filename_to_datetime(filename):
    # convert filename to datetime
    # filename format: LHPG-1730122064.bin
    filename = filename.split(".")[0]
    ts = int(filename.split("-")[1])
    dt = pd.to_datetime(ts, unit="s")
    return dt


def file_list_to_df(file_list) -> pd.DataFrame:
    # make a dataframe that have filename and datetime columns
    df_list = []
    for f in file_list:
        dt = bin_filename_to_datetime(f)
        df_list.append({"filename": f, "datetime": dt})
    df = pd.DataFrame(df_list, columns=["filename", "datetime"])
    return df


def _read_frames(file_bytes) -> list:
    frames = []
    while True:
        try:
            frame_len_bytes = file_bytes.read(4)
            if len(frame_len_bytes) < 4:
                break
            frame_len = int.from_bytes(frame_len_bytes, "little")
            if frame_len == 0:
                break
            frame_bytes = file_bytes.read(frame_len)
            if len(frame_bytes) < frame_len:
                break
            frames.append(frame_len_bytes + frame_bytes)
        except ValueError as e:
            print(f"读取文件 {file_bytes.name} 出错：{e}")
            break
    return frames


def _process_frame(frame_bytes: bytearray) -> tuple | None:
    len_size = 4
    frame_bytes = frame_bytes[len_size:]
    try:
        frame_bytes = zstd.decompress(frame_bytes)
    except zstd.ZstdError as e:
        st.error(f"解压文件出错：{e}")

    if len(frame_bytes) <= 0:
        return None

    try:
        data_offset = 24
        frame_header = struct.unpack("I4H2If", frame_bytes[:data_offset])
        frame_length = frame_header[0]
        height, width, channels = frame_header[2], frame_header[3], frame_header[4]
        ts = (frame_header[5] << 32) + frame_header[6]
        if channels == 1:
            data = np.ndarray(
                (height, width),
                "B",
                frame_bytes[:frame_length],
                data_offset,
                (width, 1),
            )
        else:  # untested
            data = np.ndarray(
                (height, width, channels),
                "B",
                frame_bytes[:frame_length],
                data_offset,
                (height * width, width, 1),
            )
        return ts, data
    except Exception as e:
        print(f"解析文件出错：{e}")
        return None


def _read_bin_file(file_path) -> list[np.ndarray]:
    frame_ts_and_ndarrays = []
    with open(file_path, "rb") as file:
        header_size = 32
        file.seek(header_size)
        frames = _read_frames(file)

    with ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(_process_frame, frame_bytes) for frame_bytes in frames
        ]
        for future in as_completed(futures):
            frame_ndarray = future.result()
            if frame_ndarray is not None:
                frame_ts_and_ndarrays.append(frame_ndarray)
    return frame_ts_and_ndarrays


def _save_image(ts, data, file_path):
    image_name = f"{ts}.jpg"
    image_path = os.path.join(file_path, image_name)
    if os.path.exists(image_path):
        st.write(f"文件 {image_path} 已存在，跳过")
        return
    else:
        image = Image.fromarray(data)
        image.save(image_path)


def convert_to_images(file_list):
    if not file_list:
        st.warning("没有选择文件，请先选择文件。")
        return

    # 在folder_path文件夹中创建photo文件夹
    photo_folder = os.path.join(folder_path, "photo")
    os.makedirs(photo_folder, exist_ok=True)

    process_bar = st.progress(0, text="正在处理第 0 个文件")
    for i, file_name in enumerate(file_list):
        process_bar.progress((i + 1) / len(file_list), text=f"正在处理第 {i+1} 个文件")
        frame_ts_and_ndarrays = _read_bin_file(os.path.join(folder_path, file_name))

        with ThreadPoolExecutor() as executor:
            for ts, data in frame_ts_and_ndarrays:
                executor.submit(_save_image, ts, data, photo_folder)


def _convert_bin_to_video(file_list, video_path):
    all_frames = []
    process_bar = st.progress(0, text="正在读取第 0 个文件")
    for i, file_name in enumerate(file_list):
        process_bar.progress((i + 1) / len(file_list), text=f"正在读取第 {i+1} 个文件")
        frame_ts_and_ndarrays = _read_bin_file(os.path.join(folder_path, file_name))
        all_frames.extend([(ts, data) for ts, data in frame_ts_and_ndarrays])

    if not all_frames:
        st.error("没有找到有效的帧数据，请检查输入文件是否正确。")
        return
    
    all_frames.sort(key=lambda x: x[0])  # 按时间戳排序

    height, width = all_frames[0][1].shape
    video_writer = cv2.VideoWriter(
        video_path, cv2.VideoWriter_fourcc(*"mp4v"), 30, (width, height)
    )  # encoder fourcc: mp4v, fps: 30

    process_bar.progress(0, text="正在处理第 0 帧")
    for i, ts_frame in enumerate(all_frames):
        ts, frame = ts_frame
        process_bar.progress((i + 1) / len(all_frames), text=f"正在处理第 {i+1} 帧")
        if len(frame.shape) == 2:  # 灰度图
            frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
        video_writer.write(frame)

    video_writer.release()


def convert_to_video(file_list):
    if not file_list:
        st.warning("没有选择文件，请先选择文件。")
        return
    video_folder = os.path.join(folder_path, "video")
    os.makedirs(video_folder, exist_ok=True)

    base_name = os.path.splitext(os.path.basename(file_list[0]))[0]
    ts_str = base_name.split("-")[-1]
    ts = int(ts_str)
    formatted_time = datetime.datetime.fromtimestamp(ts).strftime("%Y%m%d-%H点%M分")
    video_path = os.path.join(video_folder, f"{formatted_time}.mp4")

    _convert_bin_to_video(file_list, video_path)


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
                    convert_to_images(selected_files)
                    st.success("图片转换成功！")

            with col2:
                if st.button("转为视频 🎥"):
                    # 调用转换为视频的函数，传递选择的文件
                    convert_to_video(selected_files)
                    st.success("视频转换成功！")
