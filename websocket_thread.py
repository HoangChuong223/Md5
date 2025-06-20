import websocket, json, time, ssl, requests

API_URL = "https://your-railway-project.up.railway.app/api/taixiu"
id_phien = None

def on_message(ws, message):
    global id_phien
    try:
        data = json.loads(message)
    except:
        return

    if isinstance(data, list) and len(data) >= 2 and isinstance(data[1], dict):
        payload = data[1]
        cmd = payload.get("cmd")
        if cmd == 2007:
            id_phien = payload.get("sid")

        elif "d1" in payload and "d2" in payload and "d3" in payload:
            d1, d2, d3 = payload["d1"], payload["d2"], payload["d3"]
            tong = d1 + d2 + d3
            ket_qua = "Tài" if tong > 10 else "Xỉu"

            print(f"🎲 {d1},{d2},{d3} = {tong} → {ket_qua}")

            try:
                requests.post(API_URL, json={
                    "Ket_qua": ket_qua,
                    "Phien": id_phien,
                    "Tong": tong,
                    "Xuc_xac_1": d1,
                    "Xuc_xac_2": d2,
                    "Xuc_xac_3": d3,
                    "id": "Wanglin"
                })
            except Exception as e:
                print("❌ Gửi API lỗi:", e)

def on_open(ws):
    print("✅ Kết nối WebSocket")
    # gửi lệnh khởi tạo
    ws.send(json.dumps([
        1, "MiniGame", "saoban", "ere2234", {
            "info": "{\"ipAddress\":\"125.235.239.187\",\"userId\":\"2ef4335a-6562-4c64-b012-46ef83a25800\",\"username\":\"S8_saoban\",\"timestamp\":1749643344994,\"refreshToken\":\"...\"}",
            "signature": "20399D..."
        }
    ]))
    time.sleep(1)
    ws.send(json.dumps([6, "MiniGame", "taixiuUnbalancedPlugin", {"cmd": 2000}]))

def start_websocket():
    while True:
        try:
            ws = websocket.WebSocketApp(
                "wss://websocket.atpman.net/websocket",
                on_open=on_open,
                on_message=on_message
            )
            ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
        except Exception as e:
            print("🔁 WebSocket lỗi:", e)
            time.sleep(5)
