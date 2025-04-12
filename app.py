import cv2
import numpy as np
from PIL import Image
import io
import zipfile
from flask import Flask, request, jsonify, send_file

app = Flask(__name__)

@app.route('/api/extract', methods=['POST'])
def extract_objects():
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'}), 400
    
    file = request.files['image']
    img_bytes = file.read()
    
    # OpenCVで画像を読み込み
    nparr = np.frombuffer(img_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)
    
    # グレースケール変換
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # 二値化処理
    _, thresh = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY_INV)
    
    # 輪郭検出
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    objects = []
    for i, contour in enumerate(contours):
        # 小さすぎる輪郭は無視
        if cv2.contourArea(contour) < 500:
            continue
        
        # バウンディングボックスを取得
        x, y, w, h = cv2.boundingRect(contour)
        
        # オブジェクトを切り出し
        obj_img = img[y:y+h, x:x+w]
        
        # 一時ファイルに保存
        obj_id = f"object-{i+1}"
        obj_path = f"./temp/{obj_id}.png"
        cv2.imwrite(obj_path, obj_img)
        
        objects.append({
            'id': obj_id,
            'width': w,
            'height': h,
            'path': obj_path
        })
    
    return jsonify({'objects': objects})

@app.route('/api/download/<obj_id>', methods=['GET'])
def download_object(obj_id):
    bg_type = request.args.get('bg', 'transparent')
    bg_color = request.args.get('color', '#FFFFFF')
    
    # オブジェクト画像を読み込み
    obj_path = f"./temp/{obj_id}.png"
    img = Image.open(obj_path)
    
    # 背景設定の適用
    if bg_type == 'transparent':
        # 透明背景の処理
        img = img.convert('RGBA')
    elif bg_type == 'white':
        # 白背景の処理
        img = img.convert('RGB')
        # 必要に応じて背景を白に
    else:
        # カスタムカラー背景の処理
        rgb = tuple(int(bg_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
        img = img.convert('RGB')
        # 背景色を適用
    
    img_io = io.BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)
    
    return send_file(img_io, mimetype='image/png', as_attachment=True, download_name=f"{obj_id}.png")

@app.route('/api/download/zip', methods=['POST'])
def download_zip():
    obj_ids = request.json.get('ids', [])
    bg_type = request.json.get('bg', 'transparent')
    bg_color = request.json.get('color', '#FFFFFF')
    
    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w') as zf:
        for obj_id in obj_ids:
            obj_path = f"./temp/{obj_id}.png"
            img = Image.open(obj_path)
            
            # 背景設定の適用（上記と同様）
            
            img_io = io.BytesIO()
            img.save(img_io, 'PNG')
            img_io.seek(0)
            
            zf.writestr(f"{obj_id}.png", img_io.getvalue())
    
    memory_file.seek(0)
    return send_file(memory_file, mimetype='application/zip', as_attachment=True, download_name='objects.zip')

if __name__ == '__main__':
    app.run(debug=True)
