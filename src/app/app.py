from flask import Flask, request, jsonify
from flask_cors import CORS
import tempfile
import os
from ocr_google import detect_text

app = Flask(__name__)
CORS(app)

@app.route('/ocr', methods=['POST'])
def ocr():
    try:
        if 'file' in request.files:
            file = request.files['file']
            if file.filename != '':
                # 임시 파일로 저장
                with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
                    file.save(temp_file.name)
                    # 실제 OCR 함수에 파일 경로 전달
                    #result = detect_text(temp_file.name)
                    result, purchase_date = detect_text(temp_file.name)  #  구매일자도 같이 받기
                os.unlink(temp_file.name)  # 임시 파일 삭제

                print("result:", result)
                ingredients = []
                for product in result:
                    ingredients.append({
                        'name': product.get('matchedName', product.get('originalName', product)) if isinstance(product, dict) else product,
                        'confidence': 80,
                        'text': product.get('originalName', product) if isinstance(product, dict) else product,
                        'category': product.get('mainCategory', '미분류') if isinstance(product, dict) else '미분류'
                    })
                #return jsonify({'ingredients': ingredients})
                # 구매일자도 같이 내려줌
                return jsonify({'ingredients': ingredients, 'purchaseDate': purchase_date})

        # JSON으로 파일명 받는 경우도 처리
        elif request.is_json:
            data = request.get_json()
            filename = data.get('filename')
            base_dir = os.path.dirname(os.path.abspath(__file__))
            file_path = os.path.join(base_dir, filename)
            if filename and os.path.exists(file_path):
                #result = detect_text(file_path)
                result, purchase_date = detect_text(file_path)
                ingredients = []
                for product in result:
                    ingredients.append({
                        'name': product.get('matchedName', product.get('originalName', product)) if isinstance(product, dict) else product,
                        'confidence': 80,
                        'text': product.get('originalName', product) if isinstance(product, dict) else product,
                        'category': product.get('mainCategory', '미분류') if isinstance(product, dict) else '미분류'
                    })
                return jsonify({'ingredients': ingredients, 'purchaseDate': purchase_date})
            else:
                return jsonify({'error': 'File not found'}), 404
        return jsonify({'error': 'No file or filename provided'}), 400

    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8012)