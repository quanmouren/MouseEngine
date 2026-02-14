# Copyright (c) 2025, CIF3
# SPDX-License-Identifier: BSD-3-Clause
import struct
import io
from PIL import Image

def generate_cur_from_image(img_obj, hotspot_x=0, hotspot_y=0):
    """
    将 PIL Image 对象转换为 CUR 字节数据
    :param img_obj: PIL.Image 实例 (RGBA)
    :param hotspot_x: 热点 X 坐标
    :param hotspot_y: 热点 Y 坐标
    :return: bytes 类型的 CUR 文件数据
    """
    img = img_obj.convert('RGBA')
    width, height = img.size
    

    reg_w = width if width < 256 else 0
    reg_h = height if height < 256 else 0


    with io.BytesIO() as bmp_io:
        img.save(bmp_io, format='BMP')
        bmp_data = bmp_io.getvalue()
        dib_data = bytearray(bmp_data[14:])


    new_h_bytes = struct.pack('<i', height * 2)
    dib_data[8:12] = new_h_bytes
    final_dib = bytes(dib_data)

    header = struct.pack('<HHH', 0, 2, 1)

    entry = struct.pack('<BBBBHHII', 
                        reg_w, reg_h, 0, 0, 
                        int(hotspot_x), int(hotspot_y), 
                        len(final_dib), 22)

    return header + entry + final_dib

# 测试调用
if __name__ == "__main__":
    test_img = Image.new('RGBA', (64, 64), color=(0, 122, 204, 255))
    cur_data = generate_cur_from_image(test_img, 32, 32)
    
    # 测试
    with open("output_test.cur", "wb") as f:
        f.write(cur_data)
    
    print(f"CUR 字节对象生成成功，大小: {len(cur_data)} 字节")