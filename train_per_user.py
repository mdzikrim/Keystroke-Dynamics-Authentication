import os
import joblib
import pickle
import pandas as pd
import sqlite3
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

DB_PATH = "keystroke2.db"
MODEL_DIR = "user_models"
os.makedirs(MODEL_DIR, exist_ok=True)

# Ambil data dari database
conn = sqlite3.connect(DB_PATH)
df = pd.read_sql_query("SELECT * FROM features", conn)
conn.close()

# Siapkan kolom fitur
hold_cols = [f"H.{i}" for i in range(1, 10)]
dd_cols = [f"DD.{i}.{i+1}" for i in range(1, 9)]
ud_cols = [f"UD.{i}.{i+1}" for i in range(1, 9)]
feature_cols = hold_cols + dd_cols + ud_cols
feature_cols = [col for col in feature_cols if col in df.columns]

df = df.dropna(subset=feature_cols, how='all')
df[feature_cols] = df[feature_cols].fillna(0.0).astype(float)

all_users = df["user_id"].unique()
print(f"[INFO] Melatih model untuk {len(all_users)} user...")

for user in all_users:
    df_pos = df[df["user_id"] == user]
    df_neg = df[df["user_id"] != user].sample(n=min(len(df_pos), len(df[df["user_id"] != user])), random_state=42)

    df_pos["label"] = 1
    df_neg["label"] = 0
    df_user = pd.concat([df_pos, df_neg])

    X = df_user[feature_cols]
    y = df_user["label"]

    # Model dengan parameter anti-overfitting
    clf = RandomForestClassifier(
        n_estimators=100,
        max_depth=8,
        min_samples_split=10,
        min_samples_leaf=5,
        random_state=42
    )
    clf.fit(X, y)

    y_pred = clf.predict(X)
    print(f"== [User: {user}] ==")
    print(classification_report(y, y_pred, zero_division=0))

    model_path = os.path.join(MODEL_DIR, f"model_{user}.pkl")
    with open(model_path, "wb") as f:
        pickle.dump((clf, feature_cols), f)

    print(f"[INFO] Model user '{user}' disimpan di: {model_path}\n")

def train_model_for_user(user_id, df_user):
    print(f"== [User: {user_id}] ==")

    # Pisahkan fitur dan label
    X = df_user.drop(columns=["user_id", "label"])
    y = df_user["label"]

    # Split train-test
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Buat model Random Forest
    clf = RandomForestClassifier(
        n_estimators=100,
        max_depth=8,
        min_samples_leaf=4,
        random_state=42
    )
    clf.fit(X_train, y_train)

    # Evaluasi
    y_pred = clf.predict(X_test)
    print(classification_report(y_test, y_pred, digits=2))

    # Simpan model
    os.makedirs("user_models", exist_ok=True)
    model_path = os.path.join("user_models", f"model_{user_id}.pkl")
    joblib.dump(clf, model_path)
    print(f"[INFO] Model user '{user_id}' disimpan di: {model_path}")

def train_specific_user(user_id, db_path="keystroke2.db"):
    print(f"[INFO] Melatih ulang model untuk user '{user_id}'...")
    
    # Ambil data user dari database
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("SELECT * FROM features WHERE user_id = ?", conn, params=(user_id,))
    df_all = pd.read_sql_query("SELECT * FROM features", conn)
    conn.close()

    # Siapkan kolom fitur
    hold_cols = [f"H.{i}" for i in range(1, 10)]
    dd_cols = [f"DD.{i}.{i+1}" for i in range(1, 9)]
    ud_cols = [f"UD.{i}.{i+1}" for i in range(1, 9)]
    feature_cols = [col for col in hold_cols + dd_cols + ud_cols if col in df.columns]
    df[feature_cols] = df[feature_cols].fillna(0.0).astype(float)

    # Ambil data negatif dan gabungkan
    df_neg = df_all[df_all["user_id"] != user_id].sample(
        n=min(len(df), len(df_all[df_all["user_id"] != user_id])),
        random_state=42
    )
    df["label"] = 1
    df_neg["label"] = 0
    df_user = pd.concat([df, df_neg])

    # Panggil fungsi pelatihan
    train_model_for_user(user_id, df_user)
