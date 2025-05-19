import os
import hashlib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.neighbors import NearestNeighbors
from sklearn.model_selection import train_test_split
import joblib
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ApplicationBuilder
import telegram
from flask import Flask, request
import threading

# ================== CONFIG ==================
BOT_TOKEN = '7915783739:AAFoaBlYwa60ete0oBFVpCXLzjE64w15wzY'  # Thay bằng token của bạn
PORT = int(os.environ.get('PORT', 5000))  # Render sẽ cấp PORT tự động
APP_URL = os.environ.get("RENDER_EXTERNAL_URL")  # Ví dụ: https://your-bot.onrender.com 
bot = telegram.Bot(token=BOT_TOKEN)

# ================== HASHING ==================
def generate_md5(text):
    return hashlib.md5(text.encode()).hexdigest()

# ================== TẠO DỮ LIỆU GIẢ LẬP ==================
def create_dataset(num_samples=5000):
    X, y = [], []
    for _ in range(num_samples):
        label = np.random.choice(['number', 'word', 'mixed'])
        if label == 'number':
            text = ''.join(np.random.choice(list('0123456789'), 10))
        elif label == 'word':
            text = ''.join(np.random.choice(list('abcdefghijklmnopqrstuvwxyz'), 10))
        else:
            text = ''.join(np.random.choice(list('abc123!@#'), 10))
        md5_hash = generate_md5(text)
        bin_vec = bin(int(md5_hash, 16))[2:].zfill(128)
        X.append([int(b) for b in bin_vec])
        y.append(label)
    return np.array(X), np.array(y)

# ================== LOAD HOẶC TRAIN RANDOM FOREST MODEL ==================
RF_PATH = 'rf_md5_classifier.pkl'
if not os.path.exists(RF_PATH):
    print("Training RF model...")
    X, y = create_dataset()
    X_train, _, y_train, _ = train_test_split(X, y, test_size=0.2)
    rf_model = RandomForestClassifier(n_estimators=20, max_depth=5)
    rf_model.fit(X_train, y_train)
    joblib.dump(rf_model, RF_PATH)
else:
    rf_model = joblib.load(RF_PATH)

# ================== LOAD HOẶC TRAIN KNN SEARCH ==================
known_strings = ['password', 'admin123', 'letmein', '123456', 'hello123']
known_hashes = [generate_md5(s) for s in known_strings]
X_knn = np.array([[int(b) for b in bin(int(h, 16))[2:].zfill(128)] for h in known_hashes])

KNN_PATH = 'knn_md5_searcher.pkl'
if not os.path.exists(KNN_PATH):
    print("Training KNN model...")
    knn_model = NearestNeighbors(n_neighbors=1, metric='hamming')
    knn_model.fit(X_knn)
    joblib.dump(knn_model, KNN_PATH)
else:
    knn_model = joblib.load(KNN_PATH)

# ================== HÀM PHÂN TÍCH MD5 ==================
def analyze_md5(text_input):
    if len(text_input) > 100:
        return "⚠️ Chuỗi quá dài. Vui lòng nhập chuỗi dưới 100 ký tự."

    try:
        md5_hash = generate_md5(text_input)
        bin_vec = bin(int(md5_hash, 16))[2:].zfill(128)
        bin_array = np.array([[int(b) for b in bin_vec]])

        # Dự đoán loại chuỗi
        predicted_type = rf_model.predict(bin_array)[0]

        # Tìm chuỗi gần giống
        dist, idx = knn_model.kneighbors(bin_array)
        similar_str = known_strings[idx[0][0]] if dist[0][0] < 0.2 else "Không tìm thấy"

        result = (
            f"🔹 *Chuỗi đầu vào:* `{text_input}`\n"
            f"🔹 *MD5 Hash:* `{md5_hash}`\n\n"
            f"[AI] Dự đoán loại chuỗi: *{predicted_type}*\n"
            f"[KNN] Gần giống với: *{similar_str}*"
        )
        return result
    except Exception as e:
        return f"❌ Có lỗi xảy ra: {str(e)}"

# ================== FLASK SERVER ==================
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot đang hoạt động!"

@app.route(f'/webhook', methods=['POST'])
def webhook():
    update = telegram.Update.de_json(request.get_json(force=True), bot)
    application = setup_application()
    application.process_update(update)
    return 'OK'

# ================== SET UP BOT HANDLERS ==================
def setup_application():
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    def start(update: telegram.Update, context: telegram.ext.CallbackContext):
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="👋 Chào mừng bạn đến với **MD5 Analyzer Bot**!\n"
                                      "Gửi bất kỳ chuỗi nào để tạo và phân tích MD5.\n"
                                      "Bot nhẹ, nhanh, thông minh và hoàn toàn miễn phí!",
                                 parse_mode=telegram.ParseMode.MARKDOWN)

    def handle_message(update: telegram.Update, context: telegram.ext.CallbackContext):
        user_input = update.message.text.strip()
        response = analyze_md5(user_input)
        context.bot.send_message(chat_id=update.effective_chat.id, text=response,
                                 parse_mode=telegram.ParseMode.MARKDOWN)

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    return application

# ================== START SERVER ==================
def main():
    app.run(host='0.0.0.0', port=PORT)

if __name__ == '__main__':
    main()
