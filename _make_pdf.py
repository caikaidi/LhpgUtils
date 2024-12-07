import os

import pandas as pd
import streamlit as st
from PIL import Image

# 新建 PDF 制作页面
st.markdown("#### PDF 制作工具")
st.write("选择一个文件夹来加载图片文件。")

# 输入文件夹路径
folder_path = st.text_input("请输入文件夹路径：")

# 查找文件夹中的所有图片文件
image_files = []
if folder_path:
    if not os.path.isdir(folder_path):
        st.write("输入的文件夹路径无效，请重新输入。")
    else:
        image_files = [
            f
            for f in os.listdir(folder_path)
            if f.lower().endswith((".png", ".jpg", ".jpeg", ".gif"))
        ]

        if not image_files:
            st.write("该文件夹中没有找到图片文件。")
        else:
            st.write("找到以下图片文件：")
            # 将文件列表转换为 DataFrame 并展示
            df_files = pd.DataFrame(
                {
                    "filename": image_files,
                    "create_time": [
                        pd.to_datetime(
                            os.path.getctime(os.path.join(folder_path, f)), unit="s"
                        )
                        for f in image_files
                    ],
                }
            )
            event = st.dataframe(
                df_files, on_select="rerun", selection_mode="multi-row"
            )

            selected_indices = event.selection["rows"]
            selected_files = (
                df_files.iloc[selected_indices]["filename"].to_list()
                if selected_indices
                else []
            )

            # 设置输出文件名
            output_filename = st.text_input("设置输出 PDF 文件名", value="output.pdf")

            if st.button("生成 PDF"):
                if selected_files:
                    with st.spinner("正在生成 PDF..."):
                        pdf_path = os.path.join(folder_path, output_filename)
                        images = []

                        for file in selected_files:
                            img_path = os.path.join(folder_path, file)
                            image = Image.open(img_path)
                            images.append(image.convert("RGB"))  # 转换为 RGB

                        # 保存为 PDF
                        if images:
                            images[0].save(
                                pdf_path, save_all=True, append_images=images[1:]
                            )
                            st.success(f"PDF 文件已生成: {pdf_path}")
                        else:
                            st.error("未能生成 PDF，检查选择的文件是否有效。")
                else:
                    st.error("请至少选择一个文件。")
