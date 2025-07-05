import os
import joblib
import numpy as np
import pandas as pd
import sqlite3
from utils import extract_features
from sklearn.metrics.pairwise import cosine_similarity

MODEL_DIR = "user_models"

def load_user_model(user_id):
    model_path = os.path.join(MODEL_DIR, f"model_{user_id}.pkl")
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model untuk user '{user_id}' tidak ditemukan.")
    model, feature_names = joblib.load(model_path)
    return model, feature_names

def load_model_and_predict(user_id, password, typed_password_events):
    # Ekstrak fitur login
    features = extract_features(typed_password_events, password)
    if not features:
        raise ValueError("Fitur login tidak valid.")

    # Load model
    model_path = os.path.join(MODEL_DIR, f"model_{user_id}.pkl")
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model untuk user {user_id} tidak ditemukan.")
    model, feature_names = joblib.load(model_path)

    df_login = pd.DataFrame([features])[feature_names]

    # Prediksi klasifikasi
    prediction = model.predict(df_login)[0]
    confidence = model.predict_proba(df_login)[0][1]

    # ✅ Batas maksimum confidence agar tidak overconfident
    confidence = min(confidence, 0.98)

    # Ambil semua data training user
    conn = sqlite3.connect("keystroke2.db")
    df_train = pd.read_sql_query("SELECT * FROM features WHERE user_id = ?", conn, params=(user_id,))
    conn.close()

    if df_train.empty:
        raise ValueError("Data training tidak ditemukan.")

    # Bersihkan data dan hitung similarity
    df_train = df_train[feature_names].fillna(0.0)
    df_train = df_train.applymap(lambda x: 0.0 if x is None or x < 0 or x > 2000 else x)

    login_vec = df_login.iloc[0].values.reshape(1, -1)
    train_vecs = df_train.values

    similarities = cosine_similarity(login_vec, train_vecs)[0]
    avg_similarity = float(np.mean(similarities))

    return prediction, confidence, round(avg_similarity, 4)
