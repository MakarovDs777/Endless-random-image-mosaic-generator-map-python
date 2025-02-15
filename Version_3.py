import numpy as np
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import filedialog
import random
import os
import cv2  # Импортируем OpenCV
import threading
import time

# Параметры
canvas_width = 640
canvas_height = 480
image_data = []
current_flat_mosaic = None
update_interval = 100
is_running = False
canvas = None 
canvas_window = None

x, y, z = 0, 0, 0
seed = 42
auto_random_running = False
auto_random_thread = None
auto_random_delay = 1
used_blocks = []
mosaic_storage = {}

def load_images():
    global image_data
    file_paths = filedialog.askopenfilenames(filetypes=[("Image files", "*.jpg;*.png;*.jpeg;*.mp4;*.avi")])
    if file_paths:
        for fp in file_paths:
            if fp.endswith(('.jpg', '.png', '.jpeg')):
                img = np.array(Image.open(fp).resize((canvas_width, canvas_height)).convert("RGB"))
                image_data.append(img)
                image_listbox.insert(tk.END, os.path.basename(fp))  # Добавляем изображение в Listbox
            elif fp.endswith(('.mp4', '.avi')):
                # Извлечение случайных кадров из видео
                video_frames = extract_random_frames(fp)
                image_data.extend(video_frames)
                image_listbox.insert(tk.END, os.path.basename(fp))  # Добавляем видео в Listbox

def extract_random_frames(video_path, num_frames=10):
    frames = []
    cap = cv2.VideoCapture(video_path)

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frame_indices = random.sample(range(total_frames), min(num_frames, total_frames))  # Случайные индексы кадров

    for idx in frame_indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)  # Установка на индекс кадра
        ret, frame = cap.read()
        if ret:
            frame = cv2.resize(frame, (canvas_width, canvas_height))  # Изменение размера кадра
            frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))  # Конвертация цвета до RGB
    cap.release()
    return frames

def split_image(image, min_size=20):
    height, width, _ = image.shape
    blocks = []
    
    while height >= min_size and width >= min_size:
        block_width = random.randint(min_size, min(width, 100))
        block_height = random.randint(min_size, min(height, 100))

        start_x = random.randint(0, width - block_width)
        start_y = random.randint(0, height - block_height)

        block = image[start_y:start_y + block_height, start_x:start_x + block_width]
        blocks.append(block)

        if len(blocks) >= 50:
            break

    return blocks

def generate_random_mosaic(images):
    global used_blocks
    used_blocks = []

    if len(images) == 0:
        return np.zeros((canvas_height, canvas_width, 3), dtype=np.uint8)

    flat_mosaic = np.zeros((canvas_height, canvas_width, 3), dtype=np.uint8)

    while len(used_blocks) < len(images) * 50:
        img = random.choice(images)
        blocks = split_image(img)

        for block in blocks:
            if block.tobytes() not in used_blocks:
                used_blocks.append(block.tobytes())
                block_height, block_width, _ = block.shape

                x_pos = random.randint(0, canvas_width - block_width)
                y_pos = random.randint(0, canvas_height - block_height)

                flat_mosaic[y_pos:y_pos + block_height, x_pos:x_pos + block_width] = block

    return flat_mosaic

def update_canvas(flat_mosaic):
    global canvas, canvas_window
    if canvas_window is None:
        canvas_window = tk.Toplevel()
        canvas = tk.Canvas(canvas_window, width=canvas_width, height=canvas_height)
        canvas.pack()

    mosaic_image = Image.fromarray(np.uint8(flat_mosaic))
    mosaic_image_tk = ImageTk.PhotoImage(mosaic_image)
    canvas.delete('all')
    canvas.create_image(0, 0, anchor=tk.NW, image=mosaic_image_tk)
    canvas.image = mosaic_image_tk

def start_mosaic():
    global is_running
    if image_data and not is_running:
        is_running = True
        run_mosaic_animation()

def run_mosaic_animation():
    global current_flat_mosaic, is_running
    if is_running:
        current_flat_mosaic = generate_random_mosaic(image_data)
        mosaic_storage[(x, y)] = current_flat_mosaic
        update_canvas(current_flat_mosaic)
        root.after(update_interval, run_mosaic_animation)

def stop_mosaic():
    global is_running
    is_running = False

def save_image():
    global current_flat_mosaic
    if current_flat_mosaic is not None and current_flat_mosaic.size > 0:
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        save_path = os.path.join(desktop_path, "mosaic_image.png")
        mosaic_image = Image.fromarray(np.uint8(current_flat_mosaic))
        mosaic_image.save(save_path)
        print(f"Изображение сохранено по: {save_path}")

def move_left():
    global x
    x -= 1
    update_mosaic()

def move_right():
    global x
    x += 1
    update_mosaic()

def move_up():
    global y
    y += 1
    update_mosaic()

def move_down():
    global y
    y -= 1
    update_mosaic()

def update_mosaic():
    global current_flat_mosaic

    if (x, y) in mosaic_storage:
        current_flat_mosaic = mosaic_storage[(x, y)]
    else:
        current_flat_mosaic = generate_random_mosaic(image_data)
        mosaic_storage[(x, y)] = current_flat_mosaic

    update_canvas(current_flat_mosaic)
    update_coordinates_display()

def update_coordinates_display():
    coordinates_label.config(text=f"Координаты - x: {x}, y: {y}, z: {z}, Seed: {seed}")

def toggle_auto_random():
    global auto_random_running, auto_random_thread
    if auto_random_running:
        auto_random_running = False
        if auto_random_thread is not None:
            auto_random_thread.join() 
        auto_random_button.config(text="Запустить авторандом")
    else:
        auto_random_running = True
        auto_random_button.config(text="Остановить авторандом")
        auto_random_thread = threading.Thread(target=auto_random_coordinates)
        auto_random_thread.start()

def auto_random_coordinates():
    global x, y, z, auto_random_delay
    while auto_random_running:
        x = random.randint(0, 10000)
        y = random.randint(0, 10000)
        z = random.randint(0, 10000)
        update_mosaic()
        update_coordinates_display()
        time.sleep(auto_random_delay) 

def set_seed():
    global seed
    try:
        seed = int(seed_entry.get())
        update_coordinates_display()
    except ValueError:
        seed_entry.delete(0, tk.END)
        seed_entry.insert(0, str(seed))

def set_auto_random_delay():
    global auto_random_delay
    try:
        delay = float(auto_random_delay_entry.get())
        if delay > 0:
            auto_random_delay = delay
    except ValueError:
        auto_random_delay_entry.delete(0, tk.END)
        auto_random_delay_entry.insert(0, str(auto_random_delay))

# Создание основного окна
root = tk.Tk()
root.title("Генератор мозаики")
root.geometry("400x700")

coordinates_label = tk.Label(root, text=f"Координаты - x: {x}, y: {y}, z: {z}, Seed: {seed}")
coordinates_label.pack()

load_image_button = tk.Button(root, text="Загрузить изображения/видео", command=load_images)
load_image_button.pack()

start_button = tk.Button(root, text="Запустить мозаику", command=start_mosaic)
start_button.pack()

stop_button = tk.Button(root, text="Остановить мозаику", command=stop_mosaic)
stop_button.pack()

save_image_button = tk.Button(root, text="Сохранить мозаику", command=save_image)
save_image_button.pack()

seed_label = tk.Label(root, text="Сид:")
seed_label.pack()

seed_entry = tk.Entry(root)
seed_entry.pack()
seed_entry.insert(0, str(seed))

set_seed_button = tk.Button(root, text="Установить сид", command=set_seed)
set_seed_button.pack()

auto_random_button = tk.Button(root, text="Запустить авторандом", command=toggle_auto_random)
auto_random_button.pack()

auto_random_delay_label = tk.Label(root, text="Скорость авторандома (сек):")
auto_random_delay_label.pack()

auto_random_delay_entry = tk.Entry(root)
auto_random_delay_entry.pack()
auto_random_delay_entry.insert(0, str(auto_random_delay))

set_auto_random_delay_button = tk.Button(root, text="Установить задержку", command=set_auto_random_delay)
set_auto_random_delay_button.pack()

image_listbox = tk.Listbox(root, width=60, height=15)
image_listbox.pack()

move_buttons_frame = tk.Frame(root)
move_buttons_frame.pack()

left_button = tk.Button(move_buttons_frame, text="Влево", command=move_left)
left_button.grid(row=0, column=0)

right_button = tk.Button(move_buttons_frame, text="Вправо", command=move_right)
right_button.grid(row=0, column=2)

up_button = tk.Button(move_buttons_frame, text="Вверх", command=move_up)
up_button.grid(row=1, column=1)

down_button = tk.Button(move_buttons_frame, text="Вниз", command=move_down)
down_button.grid(row=2, column=1)

root.mainloop()
