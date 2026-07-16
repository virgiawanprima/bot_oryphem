# Bot Telegram Tim Oryphem ⚡

Bot manajemen lomba dan role registration untuk tim Oryphem.  
Dibangun dengan [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) v20+ dan SQLite.

---

## ✨ Fitur

| Fitur | Detail |
|-------|--------|
| **Role Registration** | Daftar anggota tim via tombol interaktif (`/start`) atau command `/daftar` |
| **Manajemen Lomba** | Tambah, lihat, dan batalkan lomba yang diikuti |
| **Pengingat Otomatis** | Notifikasi H-7, H-3, H-1 setiap jam 09:00 WITA |
| **Pembersihan Otomatis** | Lomba otomatis dihapus setelah H-1 lewat |
| **Role Management** | Lihat role, ubah role, dan daftar semua anggota tim |

---

## 🚀 Cara Mulai

Chat **@oryphem_bot** di Telegram, kirim `/start`, lalu tap tombol role yang tersedia.

Atau daftar manual dengan perintah:

```
/daftar data-mle
```

---

## 📋 Perintah

### Role Registration

| Perintah | Deskripsi | Contoh |
|----------|-----------|--------|
| `/start` | Registrasi role lewat tombol interaktif | `/start` |
| `/daftar [role]` | Daftar role (alternatif manual) | `/daftar data-mle` |
| `/ubahrole [role]` | Ganti role | `/ubahrole fullstack-developer` |
| `/role` | Lihat role kamu saat ini | `/role` |
| `/listrole` | Lihat semua anggota tim | `/listrole` |

### Manajemen Lomba

| Perintah | Deskripsi | Contoh |
|----------|-----------|--------|
| `/ikut [judul] \| [link] \| [tgl_h7] \| [tgl_h1]` | Tambah lomba baru | `/ikut Lomba AI \| https://... \| 2026-07-20 \| 2026-07-26` |
| `/list` | Lihat semua lomba + sisa hari | `/list` |
| `/batal [id]` | Batalkan lomba berdasarkan ID | `/batal 1` |

### Lainnya

| Perintah | Deskripsi |
|----------|-----------|
| `/help` | Panduan lengkap penggunaan |

---

## 🧑‍💻 Role Tersedia

| Slug (command) | Display Name |
|----------------|--------------|
| `data-mle` | DATA & MLE |
| `fullstack-developer` | FULL STACK DEVELOPER |
| `uiux-designer` | UI/UX DESIGNER |
| `blockchain-developer` | BLOCKCHAIN DEVELOPER |
| `frontend-developer` | FRONT END DEVELOPER |

---

## 🛠️ Menjalankan Lokal

```bash
# 1. Clone repository
git clone https://github.com/virgiawanprima/bot_oryphem.git
cd bot_oryphem

# 2. Buat virtual environment
python3 -m venv .venv

# 3. Install dependencies
.venv/bin/pip install -r requirements.txt

# 4. Isi file .env
# BOT_TOKEN=token_dari_botfather
# CHAT_ID=id_grup_atau_kosongkan

# 5. Jalankan
./run.sh
```

Atau langsung:

```bash
.venv/bin/python3 app.py
```

---

## 📦 Deploy

### FPS.ms

1. Upload `app.py`, `requirements.txt`, `.env`
2. Klik **Restart** di tab Console

### Run di background (Linux)

```bash
nohup .venv/bin/python3 app.py > bot.log 2>&1 &
```

---

## 🔒 Keamanan

- File `.env` sudah di `.gitignore` — token tidak akan tercommit
- Semua query SQL menggunakan parameterized query (`?`) — aman dari SQL injection
- Input user di-escape sebelum ditampilkan di Markdown

---

## 📁 Struktur Project

```
bot_oryphem/
├── app.py             # Bot utama (721+ baris)
├── run.sh             # Script menjalankan bot
├── requirements.txt   # Dependencies
├── .env               # Konfigurasi (token, dll) — tidak di-commit
├── .gitignore         # File yang diabaikan git
└── README.md          # Dokumentasi ini
```