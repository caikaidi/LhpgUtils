import pyvisa
import plotly.graph_objs as go
import streamlit as st
import time
from collections import deque

st.title("功率计数据读取")

st.header("选择设备")
rm = pyvisa.ResourceManager()
available_devices = rm.list_resources()

# 创建一个字典，将设备地址映射到识别信息
device_info = {}
for addr in available_devices:
    try:
        idn = rm.open_resource(addr).query("*IDN?").strip()
        device_info[idn] = addr
    except Exception as e:
        st.warning(f"无法获取设备 {addr} 的识别信息: {e}")

# 使用设备识别信息在 selectbox 中展示
device_name = st.selectbox("选择功率计设备", list(device_info.keys()))

# 选定设备的地址
device_addr = device_info.get(device_name)

# 读取功率数据
if device_addr:
    power_meter = rm.open_resource(device_addr)
    st.success(f"已连接到设备：{device_name}")

    # 功能1：改变测量波长
    st.header("设置测量波长")
    default_wavelength = power_meter.query("correction:wavelength?").strip()
    st.write(f"当前测量波长：{default_wavelength} nm")
    wavelength = st.number_input(
        "输入波长 (nm)",
        min_value=200.0,
        max_value=12000.0,
        step=1.0,
        value=float(default_wavelength),
    )
    if st.button("设置波长"):
        try:
            power_meter.write(f"correction:wavelength {wavelength}")
            st.success(f"波长已设置为 {wavelength} nm")
        except Exception as e:
            st.error(f"设置波长时出错: {e}")

    # 功能2：读取功率
    st.header("读取功率")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("读取功率"):
            try:
                power_value = power_meter.query("measure:power?")
                st.session_state["power_value"] = power_value.strip()
            except Exception as e:
                st.error(f"读取功率时出错: {e}")
    with col2:
        if "power_value" in st.session_state:
            st.write(f"功率值：{st.session_state['power_value']} W")
    # 功能3：实时功率曲线
    st.header("功率曲线")
    if st.button("开始读取"):
        st.session_state["power_stream"] = True
        st.session_state["time_list"] = deque(maxlen=100)
        st.session_state["power_list"] = deque(maxlen=100)
        st.session_state["temperature_list"] = deque(maxlen=100)
    if st.button("停止读取"):
        st.session_state["power_stream"] = False

    # 初始化图表，只执行一次
    if "fig" not in st.session_state:
        st.session_state["fig"] = go.FigureWidget()
        st.session_state["fig"].add_trace(
            go.Scatter(x=[], y=[], mode="lines+markers", name="功率 (W)")
        )
        st.session_state["fig"].update_layout(
            title="实时功率曲线",
            xaxis_title="时间 (秒)",
            yaxis_title="功率 (W)",
        )
    if "fig_temp" not in st.session_state:
        st.session_state["fig_temp"] = go.FigureWidget()
        st.session_state["fig_temp"].add_trace(
            go.Scatter(x=[], y=[], mode="lines+markers", name="温度 (°C)")
        )
        st.session_state["fig_temp"].update_layout(
            title="实时温度曲线",
            xaxis_title="时间 (秒)",
            yaxis_title="温度 (°C)",
        )


    # 动态读取数据并更新图表
    power_chart_placeholder = st.empty()
    temperature_chart_placeholder = st.empty()
    while st.session_state.get("power_stream", False):
        try:
            power_value = power_meter.query("measure:power?").strip()
            temperature_value = power_meter.query("measure:temperature?").strip()
            current_time = time.time()
            st.session_state["time_list"].append(current_time)
            st.session_state["power_list"].append(float(power_value))
            st.session_state["temperature_list"].append(float(temperature_value))

            # 更新图表的 trace 数据
            with st.session_state["fig"].batch_update():
                st.session_state["fig"].data[0].x = [t - current_time for t in st.session_state["time_list"]]
                st.session_state["fig"].data[0].y = list(st.session_state["power_list"])
            with st.session_state["fig_temp"].batch_update():
                st.session_state["fig_temp"].data[0].x = [t - current_time for t in st.session_state["time_list"]]
                st.session_state["fig_temp"].data[0].y = list(st.session_state["temperature_list"])

            # 渲染图表
            power_chart_placeholder.plotly_chart(
                st.session_state["fig"], use_container_width=True
            )
            temperature_chart_placeholder.plotly_chart(
                st.session_state["fig_temp"], use_container_width=True
            )
            time.sleep(0.1)  # 控制读取频率

        except Exception as e:
            st.error(f"读取功率时出错: {e}")
            break

    # 关闭设备连接
    power_meter.close()
else:
    st.warning("未找到任何功率计设备，请检查连接")
