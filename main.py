import websocket
import json
import ssl
import time
import requests
from collections import Counter
from datetime import datetime

# === CẤU HÌNH TELEGRAM ===
BOT_TOKEN = "7566826154:AAG2cFe3VZzvXLP2c3QIB8jvQUU0Keus3M8"  # Token của bạn
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage" 

# === BIẾN TOÀN CỤC ===
id_phien = 0
ket_qua = []  # Lưu dưới dạng 't' hoặc 'x'
last_prediction = None
active = False  # Trạng thái bot
allowed_chats = []  # Bắt đầu trống - không cho phép ai mặc định
api_keys = set()  # Key hợp lệ
authorized_users = {}  # {user_id: chat_id} - người dùng đã nhập đúng /key

# === MẪU CẦU GHI TRONG CODE (AI) ===
PATTERNS = {
    "XXXXXXXX": "x", "XXXXXXTX": "x", "XXXXXTXX": "x", "XXXXTXTX": "x",
    "XXXTXTXX": "t", "XXTXTXTX": "x", "XXTXTXTX": "t", "TXTXTXTX": "x",
    "XXTXTXTX": "t", "XTXTXTXT": "t", "TXTXTTTT": "x", "XTXTXTTX": "x",
    "TXTXTTXX": "x", "XTXTXXXT": "t", "TXTXXXTX": "x", "XTXXXTXT": "x",
    "TTXXXTXX": "x", "TXXXTXXX": "t", "XXXTXXTX": "x", "XXTXXTXT": "x",
    "XTXXTXXX": "t", "TXXXTXXT": "x", "XXXTXXTX": "t", "XXTXXTXT": "x",
    "XTXXTXTX": "x", "TXXTXTXX": "t", "XXTXTXXT": "x", "XTXTXXTX": "x",
    "TXTXXTXX": "t", "XTXXTXXT": "x", "TXXTXXTX": "x", "XXTXXTXT": "t",
    "XTXXTTXT": "x", "TXTTXTTX": "t", "XTTXTXTX": "x", "TXTTTTXT": "t",
    "XTTTTTTX": "x", "TTTTTTTX": "t", "TTTTTTXT": "x", "TTTTTXTX": "x",
    "TTTTXTXX": "x", "TTTXTXXX": "t", "TTXTXXXT": "x", "TXTXXXTX": "x",
    "TTTTTTTT": "x", "TTTTXXXX": "t", "XXXTTTTT": "x", "TXXTXXXT": "x",
    "XXXTXXXT": "t", "TTXXXTXX": "x", "XXTXXXTT": "t", "XXTTTTTX": "x",
    "XTXXXTTT": "t", "XTTTTTTT": "x", "TTTTXXTT": "t", "XXTTTTTX": "x",
    "TTXTXXTT": "x", "TTXTXTTT": "x", "TXTXTTTT": "x", "XXTTTTXT": "t",
    "TTTTXTXT": "x", "XXXTXTXT": "t", "TTTXTXTX": "x", "XXTXTXTX": "t",
    "TTXTTTTX": "x", "XXXTTTTT": "t", "TXTXTXXT": "x", "TXTTTTTX": "x",
    "TTXXTTXT": "x", "XTTTTTTX": "t", "TXXXTTXT": "x", "TXTTTXXT": "x",
    "TTXTTTXX": "x", "TTTXTXXT": "x", "TTTTTTTX": "x", "XXXXXXXT": "t",
    "TTTTXXTT": "x", "XXXXXXTT": "t", "TTTTTTTT": "x", "XXXXXXXX": "t",
    "TTTTXXXX": "t", "XXXTTTTT": "x", "TXXTXTXT": "x", "XXTXTXTT": "t",
    "TTXXTTXX": "x", "XXTTXXTT": "t", "TTTTTXXX": "x", "XXXTTTTT": "t",
    "TTTXXTTT": "x", "XXXTTXXX": "t", "TTXTXXTX": "x", "XXTXXTXT": "t",
    "TXXTTXXT": "x", "XTTXXTTX": "t", "TTTXTXTT": "x", "XXXTXTXX": "t",
    "TTXXTXXT": "x", "XXTTXTXT": "t", "TXXTXTXT": "x", "XTXTXTXT": "t",
    "TTTTXTXT": "x", "XXXXTXTT": "t", "TTXTTTXT": "x", "XXTXXXTT": "t",
    "TXTXXXTT": "x", "XTXTTTXT": "t", "TTTXTXTX": "x", "XXXTXTXT": "t",
    "TTXXTXTX": "x", "XXTTXTXT": "t", "TXXTXXTX": "x", "XTXTXXTT": "t",
    "TTXTXXTT": "x", "XXTXXTTT": "t", "TXXTTXTT": "x", "XTTXXTTT": "t",
    "TTXXTTXX": "x", "XXTTXXTT": "t", "XTXTXTXT": "t", "TXTXTXTX": "x",
    "XTXTXTXT": "x", "TXTXTXTT": "t", "XTXTXTTX": "x", "TTTTTTTT": "x",
    "XXXXXXXT": "t", "TTTTTTTX": "x", "XXXXXXXX": "t", "TXTXTXTX": "t",
    "XTXTXTXT": "x", "TXTXTXTT": "t", "XTXTXTTX": "x", "TXTX": "t",
    "XXTT": "t", "XXXX": "x", "XXXT": "x", "XXTX": "t", "XTTT": "t",
    "TTXT": "x", "TTTX": "t", "XTTX": "t", "TXTT": "t", "TXXX": "t",
    "TTTT": "x", "TTXX": "x", "XTXT": "x", "TXXT": "t", "XTXX": "x"
}

# === NHẬN DIỆN CẦU TỪ MẪU GHI TRONG CODE ===
def predict_from_pattern(history):
    history_str = ''.join(history)
    result_count = Counter()
    for length in range(min(12, len(history_str)), 3, -1):  # Nhận diện chuỗi dài hơn
        if len(history_str) >= length:
            key = history_str[-length:]
            if key in PATTERNS:
                result_count[PATTERNS[key]] += 1
    if result_count:
        return result_count.most_common(1)[0][0]  # Chọn kết quả xuất hiện nhiều nhất
    return None

# === TỰ ĐỘNG THÊM CẦU MỚI VÀO PATTERNS ===
def update_patterns(history, result):
    if len(history) < 4:
        return
    for i in range(len(history) - 3):
        pattern = ''.join(history[i:i+4])
        outcome = history[i+4] if i+4 < len(history) else result
        if pattern not in PATTERNS:
            PATTERNS[pattern] = outcome

# === GỬI TIN NHẮN TELEGRAM ===
def send_telegram_message(chat_id, text):
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    try:
        r = requests.post(TELEGRAM_API_URL, data=payload, timeout=5)
        if r.status_code != 200:
            print(f"Lỗi gửi Telegram: {r.text}")
    except Exception as e:
        print(f"Exception gửi Telegram: {e}")

# === GỬI TIN NHẮN DỰ ĐOÁN ===
def send_telegram_message_custom(next_pred, dice_values, total_point, result_tx, timestamp, chat_id):
    now = datetime.fromtimestamp(timestamp / 1000).strftime("%H:%M:%S %d/%m/%Y")
    d1, d2, d3 = dice_values
    result_emoji = "❄️XỈU" if result_tx == "x" else "🔥 TÀI"
    pred_emoji = "🔥 TÀI" if next_pred == "t" else "❄️ XỈU" if next_pred == "x" else "❓ Không rõ"
    trend = Counter(ket_qua[-15:]).most_common()
    trend_str = f"{trend[0][0].upper()} ({trend[0][1]}/15)" if trend else "Không có dữ liệu"
    text = f"""🎲 @AtomixzZz 🎲
══════════════════════════
>ID Phiên: {id_phien}
🎲 Xúc xắc: {d1}-{d2}-{d3}
🧮 Tổng điểm: {total_point} | Kết quả: {result_emoji}
──────────────────────────
🔮 Dự đoán phiên {id_phien + 1}: {pred_emoji}
🎯 Khuyến nghị: {'Tài' if next_pred == 't' else 'Xỉu' if next_pred == 'x' else 'Không rõ'}
📉 Xu hướng Sunwin: 📉 Xu hướng {trend_str}
⏱️ Giờ VN: {now}
🧩 Pattern: {''.join(ket_qua)}
══════════════════════════
DevBot🧑‍💻 :@AtomixzZz👥"""
    send_telegram_message(chat_id, text)

# === XỬ LÝ LỆNH TELEGRAM ===
def handle_telegram_command(msg):
    global active, allowed_chats, api_keys, authorized_users
    chat_id = str(msg["message"]["chat"]["id"])
    from_id = str(msg["message"]["from"]["id"])  # ID người dùng
    text = msg["message"].get("text", "").strip().lower()

    if text.startswith("/key "):
        _, input_key = text.split(" ", 1)
        if input_key.strip() in api_keys:
            authorized_users[from_id] = chat_id
            allowed_chats.append(chat_id)
            send_telegram_message(chat_id, "<b>🔑 Key hợp lệ! Bạn đã được cấp quyền sử dụng bot.</b>")
        else:
            send_telegram_message(chat_id, "<b>❌ Key không đúng. Vui lòng thử lại.</b>")

    elif text.startswith("/start"):
        if from_id in authorized_users:
            active = True
            send_telegram_message(chat_id, "<b>✅ Bot đã bắt đầu!</b>")
        else:
            send_telegram_message(chat_id, "<b>🚫 Bạn chưa nhập key hoặc nhập sai. Vui lòng dùng /key [mã_key].</b>")

    elif text.startswith("/stop"):
        if from_id in authorized_users:
            active = False
            send_telegram_message(chat_id, "<b>🛑 Bot đã dừng!</b>")
        else:
            send_telegram_message(chat_id, "<b>🚫 Bạn không có quyền dừng bot.</b>")

    elif text.startswith("/addkey"):
        if from_id == "7623590839":  # Chỉ admin chính được thêm key
            _, key = text.split(" ", 1)
            api_keys.add(key.strip())
            send_telegram_message(chat_id, "<b>✅ Key đã được thêm!</b>")
        else:
            send_telegram_message(chat_id, "<b>🚫 Bạn không có quyền thêm key.</b>")

    elif text.startswith("/removekey"):
        if from_id == "7623590839":
            _, key = text.split(" ", 1)
            api_keys.discard(key.strip())
            send_telegram_message(chat_id, "<b>❌ Key đã bị xoá!</b>")
        else:
            send_telegram_message(chat_id, "<b>🚫 Bạn không có quyền xoá key.</b>")

    elif text.startswith("/addgroup"):
        if from_id in authorized_users:
            allowed_chats.append(chat_id)
            send_telegram_message(chat_id, "<b>✅ Nhóm này đã được thêm vào danh sách chạy bot!</b>")
        else:
            send_telegram_message(chat_id, "<b>🚫 Bạn chưa được xác thực. Vui lòng dùng /key [mã_key].</b>")

# === KHỞI TẠO LỆNH KẾT NỐI WEBSOCKET ===
messages_to_send = [
    [1, "MiniGame", "SC_dungtrong1205", "dung1205", {
        "info": "{\"ipAddress\":\"125.235.239.187\",\"userId\":\"cada855a-eff2-4494-8d69-c2a521331d97\",\"username\":\"SC_dungtrong1205\",\"timestamp\":1748964599196,\"refreshToken\":\"5b31001fbbc34aa1b18dcbd1a1392919.6bdeec9b2e0e49a485154602c2c8ce36\"}",
        "signature": "82DCB99CD25DDB77D86E1B41C078688183D4F4BC6C9FFE54D17B505BA7B71A644ED7AB3245410FE2DDCE60E05E107772BBB3B367D2C7F869F206FBA404E9EC573FF3D4BBED8EE4DA390CD4A93DE7BE776614EF0BC72D8C4CA300918D18BD14711583DFE9705A601A0DAFE4F4E87BB220ADA0ACBE15FECE92AC77C40DC56BA568"
    }],
    [6, "MiniGame", "taixiuPlugin", {"cmd": 1005}],
    [6, "MiniGame", "lobbyPlugin", {"cmd": 10001}]
]

# === XỬ LÝ WEBSOCKET ===
def on_message(ws, message):
    global id_phien, ket_qua, last_prediction
    try:
        data = json.loads(message)
    except json.JSONDecodeError:
        print("Không thể parse message:", message)
        return
    if isinstance(data, list) and len(data) >= 2 and isinstance(data[1], dict):
        # Nhận phiên mới
        if data[1].get("cmd") == 1008 and "sid" in data[1]:
            new_id = data[1]["sid"]
            if new_id != id_phien:
                id_phien = new_id
                last_prediction = predict_from_pattern(ket_qua)
        # Nhận kết quả xúc xắc
        if "gBB" in str(data) and data[1].get("cmd") == 1003:
            d1 = data[1].get("d1")
            d2 = data[1].get("d2")
            d3 = data[1].get("d3")
            if not all([d1, d2, d3]):
                return
            total = d1 + d2 + d3
            result_tx = "t" if total > 10 else "x"
            ket_qua.append(result_tx)
            if len(ket_qua) > 20:
                ket_qua.pop(0)
            update_patterns(ket_qua, result_tx)
            if active:
                for chat_id in allowed_chats:
                    send_telegram_message_custom(
                        next_pred=last_prediction,
                        dice_values=(d1, d2, d3),
                        total_point=total,
                        result_tx=result_tx,
                        timestamp=int(time.time() * 1000),
                        chat_id=chat_id
                    )

def on_error(ws, error):
    print(f"Lỗi WebSocket: {error}")

def on_close(ws, close_status_code, close_msg):
    print(f"Kết nối đóng: {close_status_code}, {close_msg}")

def on_open(ws):
    for msg in messages_to_send:
        ws.send(json.dumps(msg))
        time.sleep(1)

def run_websocket():
    header = ["Host: websocket.azhkthg1.net", "Origin: https://play.sun.win",  "User-Agent: Mozilla/5.0"]
    while True:
        try:
            ws = websocket.WebSocketApp(
                "wss://websocket.azhkthg1.net/websocket",
                on_open=on_open,
                on_message=on_message,
                on_error=on_error,
                on_close=on_close,
                header=header
            )
            ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE}, ping_interval=15, ping_timeout=10)
        except Exception as e:
            print(f"Lỗi chạy WebSocket: {e}")
            time.sleep(5)

# === XỬ LÝ TELEGRAM BOT ===
def start_telegram_bot():
    offset = 0
    while True:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset={offset}"
        try:
            response = requests.get(url, timeout=10)
            updates = response.json()
            for update in updates.get("result", []):
                if update["update_id"] >= offset:
                    offset = update["update_id"] + 1
                if "message" in update and "text" in update["message"]:
                    handle_telegram_command(update)
        except Exception as e:
            print(f"Lỗi Telegram: {e}")
        time.sleep(1)

# === MAIN FUNCTION ===  
if __name__ == "__main__":
    print("🤖 BOT TÀI XỈU SUN.WIN ĐANG CHẠY...")
    from threading import Thread
    ws_thread = Thread(target=run_websocket, daemon=True)
    tg_thread = Thread(target=start_telegram_bot, daemon=True)
    ws_thread.start()
    tg_thread.start()
    ws_thread.join()
    tg_thread.join()
