from flask import Flask, request, jsonify
from flask_cors import CORS
from ocr_google import detect_text

app = Flask(__name__)
CORS(app)

@app.route('/ocr', methods=['POST'])
def ocr():
    try:
        # JSON으로 filename이 들어온 경우
        if request.is_json:
            data = request.get_json()
            filename = data.get('filename')
            if filename:
                result = detect_text(filename)
                ingredients = []
                for product in result:
                    ingredients.append({
                        'name': product,
                        'confidence': 80, #신뢰도는 80으로 고정시킴
                        'text': product,
                        'category': '미분류'
                    })
                return jsonify({'ingredients': ingredients})

        return jsonify({'error': 'No file or filename provided'}), 400

    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)