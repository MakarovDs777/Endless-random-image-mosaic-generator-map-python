import tkinter as tk
from tkinter import filedialog
import numpy as np
from PIL import Image, ImageTk
import random
import os

# Параметры холста
canvas_width = 640
canvas_height = 480
image_data = []
current_flat_mosaic = None
update_interval = 100
is_running = False
canvas = None  # Инициализация переменной canvas
canvas_window = None  # Инициализация переменной canvas_window

# Параметры координат
x, y, z = 0, 0, 0
used_blocks = []  # Хранит уже использованные блоки для избежания повторений
mosaic_storage = {}  # Сохраняет мозаики по координатам

def load_images():
    global image_data
    file_paths = filedialog.askopenfilenames(filetypes=[("Image files", "*.jpg;*.png;*.jpeg")])
    if file_paths:
        image_data.clear()  # Очистить предыдущие изображения
        for fp in file_paths:
            img = np.array(Image.open(fp).resize((canvas_width, canvas_height)).convert("RGB"))
            image_data.append(img)
            image_listbox.insert(tk.END, fp)

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
    used_blocks = []  # Сброс используемых блоков перед новой генерацией

    if len(images) == 0:
        return np.zeros((canvas_height, canvas_width, 3), dtype=np.uint8)

    flat_mosaic = np.zeros((canvas_height, canvas_width, 3), dtype=np.uint8)

    while len(used_blocks) < len(images) * 50:  # Ограничивающий фактор
        img = random.choice(images)
        blocks = split_image(img)

        for block in blocks:
            if block.tobytes() not in used_blocks:
                used_blocks.append(block.tobytes())
                block_height, block_width, _ = block.shape

                # Находим случайные координаты
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

    # Добавляем табло с порезанными кадрами
    image_frame = tk.Frame(canvas_window)
    image_frame.pack()

    for image in image_data:
        image_pil = Image.fromarray(np.uint8(image))
        image_tk = ImageTk.PhotoImage(image_pil)
        image_label = tk.Label(image_frame, image=image_pil)
        image_label.image = image_pil
        image_label.pack(side=tk.LEFT)

def start_mosaic():
    global is_running
    if image_data and not is_running:
        is_running = True
        run_mosaic_animation()

def run_mosaic_animation():
    global current_flat_mosaic, is_running
    if is_running:
        current_flat_mosaic = generate_random_mosaic(image_data)
        # Сохраняем мозаику по текущей координате
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

    # Проверяем, существует ли мозайка для текущих координат
    if (x, y) in mosaic_storage:
        current_flat_mosaic = mosaic_storage[(x, y)]  # Используем сохранённую мозаику
    else:
        current_flat_mosaic = generate_random_mosaic(image_data)  # Генерируем новую, если нет сохраненной
        mosaic_storage[(x, y)] = current_flat_mosaic  # Сохраняем новую мозаику

    update_canvas(current_flat_mosaic)
    update_coordinates_display()  # Обновляем табло координат после обновления мозаики

def update_coordinates_display():
    coordinates_label.config(text=f"Координаты - x: {x}, y: {y}, z: {z}")

# Основной интерфейс
root = tk.Tk()
root.title("Генератор мозаики")
root.geometry("400x700")

# Табло для координат
coordinates_label = tk.Label(root, text=f"Координаты - x: {x}, y: {y}, z: {z}")
coordinates_label.pack()

# Кнопки загрузки и управления
load_image_button = tk.Button(root, text="Загрузить изображения", command=load_images)
load_image_button.pack()

start_button = tk.Button(root, text="Запустить мозаику", command=start_mosaic)
start_button.pack()

stop_button = tk.Button(root, text="Остановить мозаику", command=stop_mosaic)
stop_button.pack()

save_image_button = tk.Button(root, text="Сохранить мозаику", command=save_image)
save_image_button.pack()

image_listbox = tk.Listbox(root, width=60, height=15)
image_listbox.pack()

# Кнопки перемещения
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
