import logging
import random

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

JS_TO_CHAR = {
    'Period': '.', 'Comma': ',', 'Space': ' ',
    'Digit0': '0', 'Digit1': '1', 'Digit2': '2', 'Digit3': '3',
    'Digit4': '4', 'Digit5': '5', 'Digit6': '6', 'Digit7': '7',
    'Digit8': '8', 'Digit9': '9',
    'Enter': 'Return', 'Shift': 'Shift', 'Backspace': 'Backspace'
}

def map_key(key):
    if len(key) == 1:
        return key.lower()
    return JS_TO_CHAR.get(key, key)

def generate_feature_columns(password):
    cols = []
    for i, ch in enumerate(password):
        cols.append(f"H.{ch}_{i}")
    for i in range(len(password) - 1):
        ch1 = password[i]
        ch2 = password[i + 1]
        cols.append(f"DD.{ch1}_{i}.{ch2}_{i+1}")
        cols.append(f"UD.{ch1}_{i}.{ch2}_{i+1}")
    return cols

def extract_features(events, password):
    import logging
    logger = logging.getLogger(__name__)
    features = {}

    if not events or len(password) < 2:
        logger.warning("❌ [extract_features] Data kosong atau password terlalu pendek.")
        return features

    logger.info(f"✅ [extract_features] Mulai proses. Jumlah event: {len(events)}, password: {password}")

    keydown_seq = []
    keyup_seq = []

    for e in events:
        if not all(k in e for k in ['type', 'key', 'time']):
            continue
        key = e['key']
        if key is None or key == 'Backspace' or len(key) > 5:
            continue
        if e['type'] == 'keydown':
            keydown_seq.append((key, e['time']))
        elif e['type'] == 'keyup':
            keyup_seq.append((key, e['time']))

    # Batasi ke panjang password
    keydown_seq = keydown_seq[:len(password)]
    keyup_seq = keyup_seq[:len(password)]

    # Validasi panjang sama
    if len(keydown_seq) != len(keyup_seq):
        logger.warning(f"⚠️ Panjang keydown dan keyup tidak sama: {len(keydown_seq)} vs {len(keyup_seq)}")
        return {}

    # HOLD TIME: H.1 - H.9
    for i in range(9):
        if i >= len(password):
            features[f"H.{i+1}"] = 0.0
            continue

        if keydown_seq[i][0] != keyup_seq[i][0]:
            logger.warning(f"⚠️ Key mismatch di H.{i+1}: {keydown_seq[i][0]} vs {keyup_seq[i][0]}")
            features[f"H.{i+1}"] = 0.0
            continue

        hold = keyup_seq[i][1] - keydown_seq[i][1]
        if hold < 0:
            logger.warning(f"⚠️ Hold time negatif di H.{i+1}: {hold}")
            hold = 0.0
        features[f"H.{i+1}"] = hold

    # DELAY TIME: DD.1.2 - DD.8.9, UD.1.2 - UD.8.9
    for i in range(8):
        if i+1 >= len(password):
            features[f"DD.{i+1}.{i+2}"] = 0.0
            features[f"UD.{i+1}.{i+2}"] = 0.0
            continue

        dd = keydown_seq[i+1][1] - keydown_seq[i][1]
        ud = keydown_seq[i+1][1] - keyup_seq[i][1]

        features[f"DD.{i+1}.{i+2}"] = dd if dd >= 0 else 0.0
        features[f"UD.{i+1}.{i+2}"] = ud if ud >= 0 else 0.0

    logger.info(f"✅ [extract_features] Jumlah fitur: {len(features)}")
    return features

def augment_keystroke(feature_dict, augment_size=100, variation_range=(0.2, 0.4), absolute_noise_range=(-20, 20)):
    augmented_data = []
    for _ in range(augment_size):
        new_sample = {}
        for key, value in feature_dict.items():
            if value is None or value == 0.0:
                new_sample[key] = 0.0
                continue

            # Tambahkan variasi relatif dan noise absolut
            variation = random.uniform(*variation_range)
            noise = random.uniform(*absolute_noise_range)
            direction = random.choice([-1, 1])
            augmented = value + (value * variation * direction) + noise

            # Perbaikan penting: buat hold time kecil tetap bervariasi
            if augmented < 5:
                augmented = random.uniform(5, 25)

            # Batasi maksimum agar tidak jadi outlier ekstrem
            if key.startswith("H.") and augmented > 350:
                augmented = 350.0
            elif key.startswith("DD.") and augmented > 2000:
                augmented = 2000.0
            elif key.startswith("UD.") and augmented > 3000:
                augmented = 3000.0

            new_sample[key] = augmented
        augmented_data.append(new_sample)
    return augmented_data

def is_valid_feature(feature_dict, min_features=15, max_zero_ratio=0.3):
    if not feature_dict:
        return False

    total_keys = len(feature_dict)
    zero_values = sum(1 for v in feature_dict.values() if v == 0.0 or v is None)

    # Minimal jumlah fitur dan proporsi nilai non-zero
    if total_keys < min_features:
        return False
    if zero_values / total_keys > max_zero_ratio:
        return False

    return True
