
# 🔐 Keystroke Dynamics Authentication using Random Forest

Sistem ini mengimplementasikan autentikasi berbasis **Keystroke Dynamics**—biometrik perilaku yang menganalisis pola mengetik pengguna—dengan menggunakan algoritma **Random Forest**.

> 📄 **Penjelasan lengkap:** *(Medium link akan dimasukkan di sini)*  

---

## 🚀 Fitur Utama

- **Behavioral Biometrics:** Verifikasi identitas pengguna berdasarkan pola mengetik yang unik (kecepatan, ritme, durasi).
- **Random Forest Classifier per User:** Setiap user memiliki model ML sendiri yang dilatih dengan data keystroke yang diperoleh dari password.
- **Data Augmentasi Otomatis:** Menghasilkan variasi data untuk memperkuat model.
- **Web-based Interface:** Proses registrasi dan login dilakukan melalui antarmuka web sederhana.
- **Admin Dashboard:** Melihat log login dan statistik performa autentikasi.
- **SQLite Database:** Menyimpan data keystroke dan model pengguna.

---

## 🏗️ Arsitektur Sistem

```plaintext
[ User ] ⇄ [ Frontend (HTML/CSS/JS) ] ⇄ [ Backend (Flask + ML) ] ⇄ [ SQLite DB + Model Store ]
```

- **Frontend:** HTML, CSS, JavaScript
- **Backend:** Flask (Python) + scikit-learn
- **Database:** SQLite + Joblib untuk model `.pkl` per user

---

## 🔑 How It Works

### 🔹 1. Registrasi
1. Pengguna memasukkan User ID dan Password.
2. Password diketik sebanyak **10 kali** untuk merekam keystroke dynamics:
   - **Hold Time (H)**: Durasi tombol ditekan.
   - **Down–Down Time (DD)**: Waktu antar penekanan tombol.
   - **Up–Down Time (UD)**: Waktu antara melepaskan dan menekan tombol berikutnya.

3. Sistem melakukan:
   - Ekstraksi fitur → Augmentasi hingga 1000 data → Pelatihan model Random Forest → Simpan model ke `user_models/`.

### 🔹 2. Login
1. User mengetik password + keystroke sekali.
2. Sistem:
   - Ekstraksi fitur.
   - Load model milik user → Prediksi → Hitung:
     - **Confidence Score:** Probabilitas klasifikasi Random Forest.
     - **Cosine Similarity:** Kemiripan pola ketik dengan data latih.
   - Keputusan login diambil melalui **smart decision function**:

```python
total_score = 0.4 * confidence + 0.6 * similarity
```

3. Hasil login dicatat di `login_logs.json`.

---

## 📊 Example Results

Model dievaluasi menggunakan **Group K-Fold Cross Validation** per pengguna dengan metrik berikut:

| User ID | Accuracy | Precision | Recall | F1-Score |
|---------|----------|-----------|--------|----------|
| user01  | 100%     | 100%      | 100%   | 100%     |
| hebat12 | 99%      | 99%       | 99%    | 99%      |
| halo    | 100%     | 100%      | 100%   | 100%     |

> ⚠️ **Catatan:** Akurasi hampir sempurna ini menunjukkan kemungkinan **overfitting** akibat data augmentasi yang seragam.

---

## 📈 Admin Dashboard

Fitur:
- Menampilkan log login terakhir (status, confidence, similarity, waktu).
- Statistik per user: jumlah sampel, jumlah login sukses/gagal, dan status model.

Screenshot: *(tambahkan gambar di sini jika ada)*

---

## 📁 Struktur Proyek (Sederhana)

```
├── app_modular_per_user.py        # Aplikasi utama Flask
├── train_per_user.py              # Pipeline pelatihan model
├── model_loader_per_user.py       # Load model dan prediksi
├── utils.py                       # Ekstraksi & augmentasi fitur
├── db.py                          # Interaksi database
├── static/                        # JS, CSS, Admin Dashboard
├── templates/                     # HTML login/register
├── keystroke2.db                  # Database SQLite
├── login_logs.json                # Log autentikasi
└── user_models/                   # Folder model per user (.pkl)
```

---

## 🚦 Next Improvements

- Mencegah **overfitting** dengan augmentasi yang lebih realistis atau model regularisasi.
- Menggunakan model **ensemble** atau **multimodal biometrics**.
- Implementasi threshold adaptif berbasis perilaku.
- Peningkatan UI/UX.

---

## 📌 Cara Menjalankan

1. **Install Requirements:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Jalankan Aplikasi:**
   ```bash
   python app_modular_per_user.py
   ```

3. **Akses di Browser:**  
   `http://localhost:5000/`

---

## 📝 Lisensi
MIT License

---

## 👤 Pengembang
Muhammad Dzikri Muqimulhaq  
📧 muhamaddzikri2004@gmail.com  
Telkom University — Security Laboratory

> Mungkin terdapat beberapa kesalahan, akan diperbaiki secara berkala
