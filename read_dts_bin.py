import streamlit as st
import os
import numpy as np
import plotly.express as px
import tempfile
from RSRTxReadBin import RTxReadBin

C = 299792458
N = 1.774

st.title("Read DTS Binary File")
uploaded_files = st.file_uploader(
    "Upload your .bin file and .Wfm.bin file", type=["bin"], accept_multiple_files=True
)

if uploaded_files:
    if len(uploaded_files) != 2:
        st.error("Please upload two files: one.bin file and one.Wfm.bin file")
    else:
        file_paths = {}
        with tempfile.TemporaryDirectory() as temp_dir:
            for uploaded_file in uploaded_files:
                if uploaded_file.name.endswith(
                    ".bin"
                ) and not uploaded_file.name.endswith(".Wfm.bin"):
                    file_type = "header"
                elif uploaded_file.name.endswith(".Wfm.bin"):
                    file_type = "samples"
                else:
                    st.error(f"Unexpected file type: {uploaded_file.name}")
                    continue

                # 保存文件到临时目录
                temp_path = os.path.join(temp_dir, uploaded_file.name)
                with open(temp_path, "wb") as f:
                    f.write(uploaded_file.read())
                file_paths[file_type] = temp_path

            # 确保两种文件都存在
            if "header" not in file_paths or "samples" not in file_paths:
                st.error(
                    "Both .bin (header) and .Wfm.bin (samples) files are required."
                )
            else:
                # read file
                try:
                    data_voltage, data_time, header = RTxReadBin(file_paths["header"])
                except ValueError:
                    st.warning("可能是多帧数据，请指定读取范围")
                    try:
                        # input read range
                        col1, col2 = st.columns(2)
                        with col1:
                            start_trace = st.number_input("Start trace", value=0)
                        with col2:
                            end_trace = st.number_input("End trace", value=100)
                        data_voltage, data_time, header = RTxReadBin(
                            file_paths["header"], [start_trace, end_trace]
                        )
                    except Exception as e:
                        st.error(f"Error reading file: {e}")

                x_length, seq_length, channel_num = data_voltage.shape
                st.success(f"Successfully read {x_length} samples from {seq_length} sequences, {channel_num} channels.")
                # choose a channel
                if channel_num > 1:
                    channel_idx = st.selectbox("Select a channel", range(channel_num))
                else:
                    channel_idx = 0

                # t -> offset -> distance
                start_position = header.get("XStart")
                resolution = header.get("Resolution")
                t_offset = start_position * resolution
                time_axis = data_time - t_offset
                x_axis = C / N * (time_axis / 2)

                # # v -> average -> denoise -> mV
                choosed_channel = data_voltage[:, :, channel_idx]
                y_axis = choosed_channel.mean(axis=1).reshape(-1) * 1000
                noise = np.mean(y_axis[0:100])
                y_axis = y_axis - noise

                fig = px.line(
                    x=x_axis,
                    y=y_axis,
                    labels={"x": "Distance (m)", "y": "Amplitude (mV)"},
                )
                st.plotly_chart(fig)
