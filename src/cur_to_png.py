# Copyright (c) 2025, CIF3
# SPDX-License-Identifier: BSD-3-Clause
import struct
import io
from PIL import Image

def convert_cur_to_png(input_file, output_file):
    with open(input_file, 'rb') as f:
        header = f.read(6)
        if len(header) < 6: return
        _, res_type, count = struct.unpack('<HHH', header)
        
        if res_type != 2:
            print(f"错误: {input_file} 不是标准 CUR 文件。")
            return

        entry = f.read(16)
        width, height, _, _, _, _, size, offset = struct.unpack('<BBBBHHII', entry)
        
        real_w = width if width != 0 else 256
        real_h = height if height != 0 else 256
        f.seek(offset)
        dib_data = f.read(size)

        dib_list = list(dib_data)
        
        # 偏移 8-12 字节是 Height (int32)
        new_h_bytes = struct.pack('<i', real_h)
        dib_list[8:12] = new_h_bytes
        
        final_dib = bytes(dib_list)

        try:
            image = Image.open(io.BytesIO(final_dib))
            image.save(output_file, 'PNG')
            print(f"成功: {input_file} -> {output_file} ({real_w}x{real_h})")
        except Exception as e:
            print(f"转换图像数据时出错: {e}")

def get_cur_image(input_file):
    """解析 CUR 文件并返回 PIL Image 对象"""
    try:
        with open(input_file, 'rb') as f:
            header = f.read(6)
            if len(header) < 6: return None
            _, res_type, count = struct.unpack('<HHH', header)
            if res_type != 2: return None

            entry = f.read(16)
            width, height, _, _, _, _, size, offset = struct.unpack('<BBBBHHII', entry)
            real_h = height if height != 0 else 256

            f.seek(offset)
            dib_data = f.read(size)
            dib_list = list(dib_data)
            new_h_bytes = struct.pack('<i', real_h)
            dib_list[8:12] = new_h_bytes
            
            return Image.open(io.BytesIO(bytes(dib_list))).convert("RGBA")
    except Exception:
        return None

# 调用示例
if __name__ == "__main__":
    convert_cur_to_png(r"C:\Users\woshi\Desktop\MouseEngine\src\mouses\蓝色科技\Hand.cur", 'mouse_pointer.png')