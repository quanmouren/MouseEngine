import struct
import io
from PIL import Image

def convert_ani_to_gif(ani_path, output_gif_path, duration=100):
    """
    ani_path: .ani 文件路径
    output_gif_path: 输出 .gif 路径
    """
    with open(ani_path, 'rb') as f:
        header = f.read(12)
        if header[:4] != b'RIFF' or header[8:12] != b'ACON':
            print("不是有效的 ANI 文件")
            return

        frames = []
        while True:
            chunk_header = f.read(8)
            if len(chunk_header) < 8:
                break
            
            chunk_id, chunk_size = struct.unpack('<4sI', chunk_header)
            
            if chunk_id == b'LIST':
                list_type = f.read(4)
                if list_type == b'fram':
                    remaining_list = chunk_size - 4
                    while remaining_list > 0:
                        icon_header = f.read(8)
                        if len(icon_header) < 8: break
                        
                        icon_id, icon_size = struct.unpack('<4sI', icon_header)
                        if icon_id == b'icon':
                            icon_data = f.read(icon_size)
                            try:
                                img = Image.open(io.BytesIO(icon_data)).convert("RGBA")
                                frames.append(img)
                            except:
                                pass
                        else:
                            f.seek(icon_size, 1)
                        
                        remaining_list -= (8 + icon_size)
                        if icon_size % 2 != 0:
                            f.read(1)
                            remaining_list -= 1
                else:
                    f.seek(chunk_size - 4, 1)
            else:
                f.seek(chunk_size, 1)
            
            if chunk_size % 2 != 0:
                f.seek(1, 1)

        if frames:
            frames[0].save(
                output_gif_path,
                save_all=True,
                append_images=frames[1:],
                duration=duration,
                loop=0,
                disposal=2
            )
            print(f"转换成功！共 {len(frames)} 帧 -> {output_gif_path}")
        else:
            print("未能提取到有效帧")



def get_ani_frames(ani_path):
    """
    解析 .ani 文件并返回 PIL Image 对象列表
    """
    with open(ani_path, 'rb') as f:
        header = f.read(12)
        if header[:4] != b'RIFF' or header[8:12] != b'ACON':
            return None

        frames = []
        while True:
            chunk_header = f.read(8)
            if len(chunk_header) < 8: break
            chunk_id, chunk_size = struct.unpack('<4sI', chunk_header)
            
            if chunk_id == b'LIST':
                list_type = f.read(4)
                if list_type == b'fram':
                    remaining_list = chunk_size - 4
                    while remaining_list > 0:
                        icon_header = f.read(8)
                        if len(icon_header) < 8: break
                        icon_id, icon_size = struct.unpack('<4sI', icon_header)
                        if icon_id == b'icon':
                            icon_data = f.read(icon_size)
                            try:
                                img = Image.open(io.BytesIO(icon_data)).convert("RGBA")
                                frames.append(img)
                            except: pass
                        else:
                            f.seek(icon_size, 1)
                        remaining_list -= (8 + icon_size)
                        if icon_size % 2 != 0:
                            f.read(1)
                            remaining_list -= 1
                else:
                    f.seek(chunk_size - 4, 1)
            else:
                f.seek(chunk_size, 1)
            if chunk_size % 2 != 0: f.seek(1, 1)
        
        return frames if frames else None

if __name__ == "__main__":
    convert_ani_to_gif(r'C:\Users\woshi\Desktop\MouseEngine\src\mouses\初音未来\Busy.ani', 'rainbow_cursor.gif')
