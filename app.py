from flask import Flask, request, jsonify, send_file
from PIL import Image, ImageEnhance, ImageFilter
import io
import base64
import numpy as np
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)

# Конфигурация
UPLOAD_FOLDER = 'temp'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# Создаем папку для временных файлов
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def apply_color_effects(image, effect_type="enhance"):
    """Применяет различные цветовые эффекты к изображению"""
    
    if effect_type == "enhance":
        # Усиление цветов
        enhancer = ImageEnhance.Color(image)
        image = enhancer.enhance(1.5)  # Увеличиваем насыщенность на 50%
        
    elif effect_type == "vintage":
        # Винтажный эффект (сепия)
        image = image.convert('RGB')
        pixels = np.array(image)
        
        # Применяем сепию
        sepia_filter = np.array([
            [0.393, 0.769, 0.189],
            [0.349, 0.686, 0.168],
            [0.272, 0.534, 0.131]
        ])
        
        sepia_img = pixels @ sepia_filter.T
        sepia_img = np.clip(sepia_img, 0, 255)
        image = Image.fromarray(sepia_img.astype(np.uint8))
        
    elif effect_type == "cool":
        # Холодный фильтр (синеватый)
        enhancer = ImageEnhance.Color(image)
        image = enhancer.enhance(0.8)
        
        # Добавляем синий оттенок
        pixels = np.array(image.convert('RGB'))
        pixels[:, :, 2] = np.clip(pixels[:, :, 2] * 1.2, 0, 255)  # Усиливаем синий
        pixels[:, :, 0] = np.clip(pixels[:, :, 0] * 0.9, 0, 255)  # Уменьшаем красный
        image = Image.fromarray(pixels.astype(np.uint8))
        
    elif effect_type == "warm":
        # Теплый фильтр (красноватый)
        pixels = np.array(image.convert('RGB'))
        pixels[:, :, 0] = np.clip(pixels[:, :, 0] * 1.1, 0, 255)  # Усиливаем красный
        pixels[:, :, 1] = np.clip(pixels[:, :, 1] * 1.05, 0, 255)  # Немного желтого
        pixels[:, :, 2] = np.clip(pixels[:, :, 2] * 0.9, 0, 255)  # Уменьшаем синий
        image = Image.fromarray(pixels.astype(np.uint8))
        
    elif effect_type == "grayscale":
        # Черно-белый с легким оттенком
        image = image.convert('L').convert('RGB')
        
    elif effect_type == "vibrant":
        # Очень яркие цвета
        enhancer = ImageEnhance.Color(image)
        image = enhancer.enhance(2.0)
        contrast_enhancer = ImageEnhance.Contrast(image)
        image = contrast_enhancer.enhance(1.2)
    
    return image

@app.route('/')
def home():
    return jsonify({
        "status": "running",
        "message": "Photo Color Processing Service",
        "available_effects": ["enhance", "vintage", "cool", "warm", "grayscale", "vibrant"]
    })

@app.route('/process', methods=['POST'])
def process_image():
    try:
        # Проверяем, есть ли файл в запросе
        if 'image' not in request.files:
            return jsonify({"error": "No image file provided"}), 400
        
        file = request.files['image']
        effect = request.form.get('effect', 'enhance')
        
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        if file and allowed_file(file.filename):
            # Открываем изображение
            image = Image.open(file.stream)
            
            # Применяем эффект
            processed_image = apply_color_effects(image, effect)
            
            # Сохраняем в память
            img_io = io.BytesIO()
            processed_image.save(img_io, format='JPEG', quality=95)
            img_io.seek(0)
            
            # Конвертируем в base64 для отправки
            img_base64 = base64.b64encode(img_io.getvalue()).decode()
            
            return jsonify({
                "status": "success",
                "message": f"Image processed with {effect} effect",
                "processed_image": img_base64,
                "effect_applied": effect
            })
        
        else:
            return jsonify({"error": "Invalid file format"}), 400
            
    except Exception as e:
        return jsonify({"error": f"Processing failed: {str(e)}"}), 500

@app.route('/process-url', methods=['POST'])
def process_image_from_url():
    """Обработка изображения по URL (для Make.com)"""
    try:
        data = request.get_json()
        
        if not data or 'image_data' not in data:
            return jsonify({"error": "No image data provided"}), 400
        
        effect = data.get('effect', 'enhance')
        
        # Декодируем base64 изображение или принимаем бинарные данные
        try:
            if isinstance(data['image_data'], str):
                # Если это base64 строка
                image_data = base64.b64decode(data['image_data'])
            else:
                # Если это уже бинарные данные
                image_data = data['image_data']
                
            image = Image.open(io.BytesIO(image_data))
        except:
            return jsonify({"error": "Invalid image data"}), 400
        
        # Применяем эффект
        processed_image = apply_color_effects(image, effect)
        
        # Сохраняем в память
        img_io = io.BytesIO()
        processed_image.save(img_io, format='JPEG', quality=95)
        img_io.seek(0)
        
        # Конвертируем в base64
        img_base64 = base64.b64encode(img_io.getvalue()).decode()
        
        return jsonify({
            "status": "success",
            "message": f"Image processed with {effect} effect",
            "processed_image": img_base64,
            "effect_applied": effect
        })
        
    except Exception as e:
        return jsonify({"error": f"Processing failed: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
