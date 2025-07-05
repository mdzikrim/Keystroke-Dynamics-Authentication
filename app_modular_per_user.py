from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import db
from utils import extract_features, augment_keystroke, is_valid_feature
from model_loader_per_user import load_model_and_predict
from train_per_user import train_specific_user
import json
import os
import datetime
import sqlite3
from collections import defaultdict
from datetime import datetime

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return render_template('login_register.html')

@app.route('/admin')
def admin_page():
    return send_from_directory('static', 'admin.html')

@app.route('/static/<path:path>')
def static_files(path):
    return send_from_directory('static', path)

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    user_id = data.get("user_id")
    password = data.get("password")
    keystroke_sets = data.get("keystroke")

    if not (user_id and password and keystroke_sets):
        return jsonify({"status": "error", "message": "Incomplete registration data"}), 400

    if len(password) < 7 or len(password) > 9:
        return jsonify({"status": "error", "message": "Password harus 7 - 9 karakter"}), 400
    
    if db.user_exists(user_id):
        return jsonify({"status": "error", "message": f"User '{user_id}' sudah terdaftar"}), 400
    
    try:
        db.insert_user(user_id, password)
        all_features = []

        for i, sample in enumerate(keystroke_sets):
            features = extract_features(sample, password)
            if features:
                all_features.append(features)  # simpan data asli
                augmented = augment_keystroke(features, augment_size=99, variation_range=(0.3, 0.4))
                all_features.extend(augmented)
            else:
                print(f"[WARNING] Sample ke-{i+1} tidak valid")

        if not all_features:
            return jsonify({"status": "error", "message": "Keystroke data tidak valid"}), 400

        db.insert_features(user_id, password, all_features)

        # Otomatis train model untuk user yang baru
        train_specific_user(user_id)

        print(f"[INFO] User '{user_id}' registered with {len(all_features)} features.")
        return jsonify({"status": "success", "message": "Registration complete"})

    except Exception as e:
        print("ERROR during registration:", e)
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user_id = data.get('user_id')
    password = data.get('password')
    typed_password = data.get('typed_password')

    if not user_id or not password or not typed_password:
        return jsonify({"message": "Missing fields"}), 400

    # Ekstrak fitur keystroke
    features = extract_features(typed_password, password)

    zero_count = sum(1 for v in features.values() if v == 0.0)
    print("[DEBUG] Fitur login (dibersihkan):", features)
    print(f"[DEBUG] Jumlah fitur = {len(features)}, fitur nol = {zero_count} ({(zero_count/len(features))*100:.1f}%)")
    if not features:
        return jsonify({"message": "Gagal mengekstrak fitur keystroke"}), 400

    try:
        prediction, confidence, similarity = load_model_and_predict(user_id, password, typed_password)

        def smart_login_decision(conf, sim):
            total_score = 0.4 * conf + 0.6 * sim

            # Log untuk debug
            print(f"[DECISION] Confidence: {conf:.2f}, Similarity: {sim:.2f}, Total Score: {total_score:.2f}")

            if conf >= 0.90 and sim >= 0.85:
                return True
            elif total_score >= 0.80 and min(conf, sim) >= 0.75:
                return True
            else:
                return False

        if prediction and smart_login_decision(confidence, similarity):
            status = "success"
            if confidence >= 0.85 and similarity >= 0.75 and is_valid_feature(features):
                try:
                    db.insert_features(user_id, password, [features])
                    train_specific_user(user_id)
                    print(f"Data login ditambahkan dan model retrain untuk user '{user_id}'")
                except Exception as e:
                    print(f"Gagal menyimpan data login atau retrain model: {e}")
        else:
            status = "fail"

        # Simpan log
        log_entry = {
            "user_id": user_id,
            "status": status,
            "confidence": float(confidence),
            "similarity": float(similarity),
            "total_score": round(0.6 * confidence + 0.4 * similarity, 4),  # masih dicatat untuk analisis
            "timestamp": datetime.now().isoformat(),
            "features": features
        }

        with open("login_logs.json", "a") as f:
            f.write(json.dumps(log_entry) + "\n")

        return jsonify({
            "message": "Login berhasil" if status == "success" else "Login gagal",
            "confidence": confidence,
            "similarity": similarity,
            "total_score": log_entry["total_score"]
        })

    except FileNotFoundError:
        return jsonify({"message": f"Model untuk user '{user_id}' tidak ditemukan."}), 404
    except Exception as e:
        print("Login error:", e)
        return jsonify({"message": f"Terjadi error: {str(e)}"}), 500

@app.route('/admin/logins')
def get_login_logs():
    logs = []
    if os.path.exists("login_logs.json"):
        with open("login_logs.json", "r") as f:
            for line in f:
                try:
                    logs.append(json.loads(line))
                except:
                    continue
    logs = sorted(logs, key=lambda x: x["timestamp"], reverse=True)[:100]
    return jsonify(logs)

@app.route('/admin/user_stats')
def get_user_stats():
    DB_PATH = "keystroke2.db"
    login_log_path = "login_logs.json"
    stats = defaultdict(lambda: {
        "samples": 0,
        "login_success": 0,
        "login_fail": 0,
        "confidence_sum": 0.0,
        "confidence_count": 0,
        "model_exists": False
    })

    # Ambil jumlah data per user dari DB
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT user_id, COUNT(*) FROM features GROUP BY user_id")
        for user_id, count in c.fetchall():
            stats[user_id]["samples"] = count
        conn.close()
    except Exception as e:
        print("[ERROR] Gagal akses DB:", e)

    # Proses login_logs.json
    if os.path.exists(login_log_path):
        with open(login_log_path, "r") as f:
            for line in f:
                try:
                    row = json.loads(line)
                    user = row["user_id"]
                    if row["status"] == "success":
                        stats[user]["login_success"] += 1
                    else:
                        stats[user]["login_fail"] += 1
                    stats[user]["confidence_sum"] += row.get("confidence", 0.0)
                    stats[user]["confidence_count"] += 1
                except:
                    continue

    # Cek model availability
    model_dir = "user_models"
    for user_id in stats:
        model_path = os.path.join(model_dir, f"model_{user_id}.pkl")
        stats[user_id]["model_exists"] = os.path.exists(model_path)

    # Format output
    output = []
    for user_id, data in stats.items():
        avg_conf = (data["confidence_sum"] / data["confidence_count"]) if data["confidence_count"] else 0.0
        output.append({
            "user_id": user_id,
            "samples": data["samples"],
            "login_success": data["login_success"],
            "login_fail": data["login_fail"],
            "avg_confidence": round(avg_conf, 3),
            "model_exists": data["model_exists"]
        })

    return jsonify(output)

if __name__ == '__main__':
    db.init_db()
    app.run(debug=True)
