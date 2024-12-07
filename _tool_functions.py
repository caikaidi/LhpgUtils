import datetime
import os
import struct
from concurrent.futures import ThreadPoolExecutor, as_completed

import cv2
import numpy as np
import pandas as pd
import streamlit as st
import zstd
from PIL import Image
from scipy.signal import savgol_filter
from scipy.optimize import curve_fit


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


def convert_to_images(file_list, folder_path):
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


def _convert_bin_to_video(file_list, video_path, file_folder_path):
    process_bar = st.progress(0, text="正在转换第 0 个文件")
    video_writer = None

    for i, file_name in enumerate(file_list):
        process_bar.progress((i + 1) / len(file_list), text=f"正在读取第 {i+1} 个文件")
        frame_ts_and_ndarrays = _read_bin_file(os.path.join(file_folder_path, file_name))

        # 初始化 video_writer 在第一次处理时设置视频宽高
        if video_writer is None and frame_ts_and_ndarrays:
            height, width = frame_ts_and_ndarrays[0][1].shape
            video_writer = cv2.VideoWriter(
                video_path, cv2.VideoWriter_fourcc(*"mp4v"), 30, (width, height)
            )

        # 按时间戳排序并逐帧写入视频
        for ts, frame in sorted(frame_ts_and_ndarrays, key=lambda x: x[0]):
            if len(frame.shape) == 2:  # 灰度图
                frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
            video_writer.write(frame)

    if video_writer is None:
        st.error("没有找到有效的帧数据，请检查输入文件是否正确。")
        return

    video_writer.release()
    process_bar.progress(1, text="视频转换完成")


def convert_to_video(file_list, output_folder_path, file_folder_path=None):
    # 如果没有指定文件路径，则使用输出文件夹路径
    if file_folder_path is None:
        file_folder_path = output_folder_path
    if not file_list:
        st.warning("没有选择文件，请先选择文件。")
        return
    video_folder = os.path.join(output_folder_path, "video")
    os.makedirs(video_folder, exist_ok=True)

    base_name = os.path.splitext(os.path.basename(file_list[0]))[0]
    ts_str = base_name.split("-")[-1]
    ts = int(ts_str)
    formatted_time = datetime.datetime.fromtimestamp(ts).strftime("%Y%m%d-%H点%M分")
    video_path = os.path.join(video_folder, f"{formatted_time}.mp4")

    _convert_bin_to_video(file_list, video_path, file_folder_path)


def downsample_data(df: pd.DataFrame, max_points: int = 20000) -> pd.DataFrame:
    """对数据进行下采样，确保数据点数量不超过 max_points"""
    if len(df) > max_points:
        df = df.iloc[:: len(df) // max_points]
    return df


def get_intensity_by_wavelength(df, wavelength, smooth=False, to_db=False):
    """根据指定波长获取各条数据的强度值，支持平滑和dB转换"""
    # 获取指定波长的索引
    wavelength_index = np.argmin(np.abs(df["wavelengths"].iloc[0] - wavelength))

    # 提取所有条目中该波长的强度
    intensity = np.array(
        [intensity_row[wavelength_index] for intensity_row in df["intensitys"]]
    )

    # 平滑处理
    if smooth:
        window_size = max(3, len(intensity) // 50)  # 自适应窗口大小
        intensity = savgol_filter(intensity, window_size, polyorder=2)

    # 转换为 dB
    if to_db:
        reference = intensity[0]  # 使用第一个强度值作为参考
        intensity = -10 * np.log10(intensity / reference)

    return intensity

def linear_curve_fit(x, y):
    def fun(x, a, b):
        return a * x + b

    (a, b), _ = curve_fit(fun, x, y)
    return a, b