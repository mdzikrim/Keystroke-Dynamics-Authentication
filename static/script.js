let recordedKeystrokes = [];
let keystrokeSamples = [];
let recordingStarted = false;
let loginKeystroke = [];

// ================= REGISTER ==================
function startRecording(inputId) {
  if (recordingStarted) return;
  recordingStarted = true;

  const input = document.getElementById(inputId);
  recordedKeystrokes = [];
  keystrokeSamples = [];
  updateCounter();

  const keyDownTimes = {};

  input.addEventListener('keydown', function (event) {
    if (!event.key || event.key === "Backspace" || event.key.length > 5) return;
    if (keystrokeSamples.length >= 10) return;

    if (!keyDownTimes[event.key]) {
      keyDownTimes[event.key] = performance.now();
    }
  });

  input.addEventListener('keyup', function (event) {
    if (!event.key || event.key === "Backspace" || event.key.length > 5) return;
    if (keystrokeSamples.length >= 10) return;

    const downTime = keyDownTimes[event.key];
    const upTime = performance.now();
    if (downTime) {
      recordedKeystrokes.push({ type: 'keydown', key: event.key, time: downTime });
      recordedKeystrokes.push({ type: 'keyup', key: event.key, time: upTime });
      delete keyDownTimes[event.key];
    }
  });
}

function submitOneInput() {
  const input = document.getElementById('typePassword');
  const password = document.getElementById('password').value;

  if (!input.value) {
    alert("Silakan ketik password terlebih dahulu.");
    return;
  }

  if (keystrokeSamples.length >= 10) {
    alert("Sudah 10 data dikumpulkan.");
    return;
  }

  setTimeout(() => {
    const downs = recordedKeystrokes.filter(e => e.type === 'keydown');
    const ups = recordedKeystrokes.filter(e => e.type === 'keyup');

    if (downs.length !== ups.length || downs.length !== password.length) {
      alert("Data tidak valid. Pastikan jumlah ketikan sesuai panjang password.");
      return;
    }

    keystrokeSamples.push(recordedKeystrokes.slice());
    recordedKeystrokes = [];
    input.value = '';
    updateCounter();
    input.focus();

    if (keystrokeSamples.length === 10) {
      input.disabled = true;
      document.getElementById("submitSingleInput").disabled = true;
      sendKeystrokeData();
    }
  }, 150);
}

function updateCounter() {
  const counter = document.getElementById('keystrokeCounter');
  if (counter) {
    counter.textContent = `${keystrokeSamples.length} / 10 keystroke direkam`;
  }
}

function sendKeystrokeData() {
  const user_id = document.getElementById('user_id').value;
  const password = document.getElementById('password').value;

  if (!user_id || !password) {
    alert("User ID dan Password harus diisi!");
    return;
  }

  fetch('/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      user_id: user_id,
      password: password,
      keystroke: keystrokeSamples
    })
  })
    .then(response => response.json())
    .then(data => {
      alert(data.message || 'Register selesai.');
    })
    .catch(error => {
      console.error('Error:', error);
      alert('Gagal register.');
    });
}

function manualRegister() {
  if (keystrokeSamples.length < 10) {
    alert("Data belum cukup. Ketik password 10x dan tekan Enter untuk setiap input.");
    return;
  }
  document.getElementById('typePassword').disabled = true;
  sendKeystrokeData();
}

// ================ LOGIN =======================
function setupLoginRecording() {
  const loginInput = document.getElementById('keystroke_input');
  const keyDownTimes = {};
  loginKeystroke = [];

  loginInput.addEventListener('keydown', function (event) {
    if (!event.key || event.key === "Backspace" || event.key.length > 5) return;
    if (!keyDownTimes[event.key]) {
      keyDownTimes[event.key] = performance.now();
    }
  });

  loginInput.addEventListener('keyup', function (event) {
    if (!event.key || event.key === "Backspace" || event.key.length > 5) return;

    const key = event.key;
    const downTime = keyDownTimes[key];
    const upTime = performance.now();

    if (downTime) {
      loginKeystroke.push({ type: 'keydown', key: key, time: downTime });
      loginKeystroke.push({ type: 'keyup', key: key, time: upTime });
      delete keyDownTimes[key];
    }
  });
}

document.getElementById('loginForm')?.addEventListener('submit', function (e) {
  e.preventDefault();

  const user_id = document.getElementById('login_user_id').value;
  const password = document.getElementById('login_password').value;

  const downs = loginKeystroke.filter(e => e.type === 'keydown');
  const ups = loginKeystroke.filter(e => e.type === 'keyup');

  if (downs.length !== ups.length || downs.length !== password.length) {
    alert("Keystroke tidak lengkap atau tidak sesuai panjang password. Silakan ketik ulang.");
    return;
  }

  fetch('/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      user_id: user_id,
      password: password,
      typed_password: loginKeystroke
    })
  })
    .then(response => response.json())
    .then(data => {
      const msg = data.message || 'Login selesai.';
      const extra = data.similarity !== undefined
        ? `\nSimilarity: ${(data.similarity * 100).toFixed(2)}%\nConfidence: ${(data.confidence * 100).toFixed(2)}%`
        : '';
      alert(msg + extra);
    })
    .catch(error => {
      console.error('Error:', error);
      alert('Gagal login.');
    });
});

window.onload = function () {
  startRecording('typePassword');  // register
  setupLoginRecording();           // login
};