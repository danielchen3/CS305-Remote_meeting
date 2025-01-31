'''
Simple util implementation for video conference
Including data capture, image compression and image overlap
Note that you can use your own implementation as well :)
'''
from io import BytesIO
import pyaudio
import cv2
import pyautogui
import numpy as np
from PIL import Image, ImageGrab
from config import *
import base64
import re
import json
# audio setting
FORMAT = pyaudio.paInt16
audio = pyaudio.PyAudio()
streamin = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
streamout = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, output=True, frames_per_buffer=CHUNK)

# print warning if no available camera
# cap = cv2.VideoCapture(0)
# if cap.isOpened():
#     can_capture_camera = True
#     cap.set(cv2.CAP_PROP_FRAME_WIDTH, camera_width)
#     cap.set(cv2.CAP_PROP_FRAME_HEIGHT, camera_height)
# else:
#     can_capture_camera = False

my_screen_size = pyautogui.size()
def parse_multiple_json_objects(data):
    # 使用正则表达式查找所有JSON对象
    json_objects = re.findall(r"\{.*?\}", data.decode(), re.DOTALL)

    # 解析每个JSON对象，丢弃不完整或无效的JSON对象
    parsed_objects = []
    for obj in json_objects:
        try:
            parsed_objects.append(json.loads(obj))
        except json.JSONDecodeError:
            # 如果解析失败，直接跳过这个对象
            continue
    return parsed_objects

def resize_image_to_fit_screen(image, my_screen_size):
    screen_width, screen_height = my_screen_size

    original_width, original_height = image.size

    aspect_ratio = original_width / original_height

    if screen_width / screen_height > aspect_ratio:
        # resize according to height
        new_height = screen_height
        new_width = int(new_height * aspect_ratio)
    else:
        # resize according to width
        new_width = screen_width
        new_height = int(new_width / aspect_ratio)

    # resize the image
    resized_image = image.resize((new_width, new_height), Image.LANCZOS)

    return resized_image


def overlay_camera_images(screen_image, camera_images):
    """
    screen_image: PIL.Image
    camera_images: list[PIL.Image]
    """
    if screen_image is None and camera_images is None:
        print('[Warn]: cannot display when screen and camera are both None')
        return None
    if screen_image is not None:
        screen_image = resize_image_to_fit_screen(screen_image, my_screen_size)

    if camera_images is not None:
        # make sure same camera images
        if not all(img.size == camera_images[0].size for img in camera_images):
            raise ValueError("All camera images must have the same size")

        screen_width, screen_height = my_screen_size if screen_image is None else screen_image.size
        camera_width, camera_height = camera_images[0].size

        # calculate num_cameras_per_row
        num_cameras_per_row = screen_width // camera_width

        # adjust camera_imgs
        if len(camera_images) > num_cameras_per_row:
            adjusted_camera_width = screen_width // len(camera_images)
            adjusted_camera_height = (adjusted_camera_width * camera_height) // camera_width
            camera_images = [img.resize((adjusted_camera_width, adjusted_camera_height), Image.LANCZOS) for img in
                             camera_images]
            camera_width, camera_height = adjusted_camera_width, adjusted_camera_height
            num_cameras_per_row = len(camera_images)

        # if no screen_img, create a container
        if screen_image is None:
            display_image = Image.fromarray(np.zeros((camera_width, my_screen_size[1], 3), dtype=np.uint8))
        else:
            display_image = screen_image
        # cover screen_img using camera_images
        for i, camera_image in enumerate(camera_images):
            row = i // num_cameras_per_row
            col = i % num_cameras_per_row
            x = col * camera_width
            y = row * camera_height
            display_image.paste(camera_image, (x, y))

        return display_image
    else:
        return screen_image


def capture_screen():
    # capture screen with the resolution of display
    # img = pyautogui.screenshot()
    img = ImageGrab.grab()
    return img

def capture_camera(cap):
    # capture frame of camera

    # cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    if not ret:
        raise Exception('Fail to capture frame from camera')
    # return Image.fromarray(frame)
    
    if ret:
        # 将BGR转换为RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # 转换为PIL Image
        image = Image.fromarray(frame_rgb)
        return image


def capture_voice():
    # 打开麦克风流
    stream = pyaudio.PyAudio().open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)

    # 捕获音频数据
    audio_data = stream.read(CHUNK)
    return audio_data


def compress_image(image, format='JPEG', quality=85):
    """
    compress image and output Bytes

    :param image: PIL.Image, input image
    :param format: str, output format ('JPEG', 'PNG', 'WEBP', ...)
    :param quality: int, compress quality (0-100), 85 default
    :return: bytes, compressed image data
    """
    
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    img_byte_arr = BytesIO()
    image.save(img_byte_arr, format=format, quality=quality)
    img_byte_arr = img_byte_arr.getvalue()

    return img_byte_arr


def decompress_image(image_bytes):
    """
    解压缩字节数据为PIL.Image对象
    :param image_bytes: bytes, 压缩的图像数据
    :return: PIL.Image 或 None (如果解压失败)
    """
    try:
        if not image_bytes:
            return None
            
        # 解码Base64字符串
        compressed_bytes = base64.b64decode(image_bytes)
        img_byte_arr = BytesIO(compressed_bytes)
        
        # 打开并验证图像
        image = Image.open(img_byte_arr)
        image.verify()  # 验证图像完整性
        
        # 重新打开图像(verify后需要重新打开)
        img_byte_arr.seek(0)
        image = Image.open(img_byte_arr)
        
        # 统一转换为RGB模式
        if image.mode != 'RGB':
            image = image.convert('RGB')
            
        return image
        
    except (base64.binascii.Error, IOError, OSError) as e:
        print(f"图像解压错误: {e}")
        return None


black_image = Image.new("RGB", (200, 150), (255, 255, 255))
black_image = compress_image(black_image)
black_image = base64.b64encode(black_image).decode("utf-8")