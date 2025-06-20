from flask import Flask, request, jsonify
import threading
from websocket_thread import start_websocket

app = Flask(__name__)

@app.route('/api/taixiu', methods=['POST'])
def nhan_ket_qua():
    data = request.get_json()
    print("📥 Nhận dữ liệu từ WebSocket:", data)
    return jsonify({"message": "Đã nhận", "data": data})

if __name__ == '__main__':
    threading.Thread(target=start_websocket, daemon=True).start()
    app.run(host='0.0.0.0', port=8080)
