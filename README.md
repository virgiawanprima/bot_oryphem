# Bot Telegram Tim Oryphem ⚡

Bot manajemen lomba untuk tim Oryphem.  
Full tap interface — gak perlu hapal command.  
Dibangun dengan [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) v22+ dan SQLite.

---

## ✨ Fitur

| Fitur | Detail |
|-------|--------|
| **Auto-Registrasi** | `/start` langsung daftarkan role sesuai anggota tim |
| **Akses Eksklusif** | Hanya 5 anggota tim yang bisa pakai bot |
| **Full Tap Menu** | Semua interaksi lewat tombol, gak perlu ngetik command |
| **Tambah Lomba** | Input judul, link, tanggal buka & tutup via kalender tap |
| **Pengingat Otomatis** | H-7, H-3, H-1 otomatis dari tanggal tutup (jam 09:00 WITA) |
| **Pembersihan Otomatis** | Lomba dihapus setelah deadline lewat |
| **Backup Database** | Backup otomatis tiap hari jam 09:00 WITA ke folder `backups/` |
| **Role Permanent** | Role tidak bisa diganti — sesuai mapping tim |

---

## 🚀 Cara Mulai

Buka Telegram, cari **@oryphem_bot**, kirim `/start`.  
Bot langsung sapa kamu dan tampilkan menu utama.

---

## 📋 Cara Pakai

### Main Menu
```
[📋 Tambah Lomba]  [📋 Daftar Lomba]
[👤 Role Saya]     [👥 Anggota Tim]
[ℹ️ Bantuan]
```

### Tambah Lomba
1. Tap **📋 Tambah Lomba**
2. Ketik judul lomba → kirim
3. Ketik/paste link → kirim
4. **Tap tanggal** di kalender untuk tanggal buka
5. **Tap tanggal** di kalender untuk tanggal tutup
6. Tap ✅ Simpan
7. Kalau salah tanggal tutup ≤ tanggal buka → ada peringatan

### Melihat & Hapus Lomba
Tap **📋 Daftar Lomba** → setiap lomba ada tombol ❌ Hapus.

### Role & Anggota
- **👤 Role Saya** — Lihat role kamu
- **👥 Anggota Tim** — Lihat semua anggota dengan nama panggilan

---

## 👥 Tim

| Username | Nama | Role |
|----------|------|------|
| `@alex123566` | Prima | DATA & MLE |
| `@Anjayehan` | Raihan | UI/UX DESIGNER |
| `@Zbisrih` | Iqbal | BLOCKCHAIN DEVELOPER |
| `@ken14_14` | Baits | FULL STACK DEVELOPER |
| `@hikkigayahachiman` | Jamal | FRONT END DEVELOPER |

---

## ⏰ Jadwal Pengingat Otomatis

Bot kirim notifikasi ke grup setiap jam **09:00 WITA**:

| Waktu | Pesan |
|-------|-------|
| **H-7** dari deadline | Persiapan dokumen dan konsep |
| **H-3** dari deadline | Cek progress, kumpulkan bahan |
| **H-1** dari deadline | Cek berkas, kodingan, testing |

---

## 🛠️ Menjalankan Lokal

```bash
# 1. Clone
git clone https://github.com/virgiawanprima/bot_oryphem.git
cd bot_oryphem

# 2. Virtual env
python3 -m venv .venv

# 3. Install
.venv/bin/pip install -r requirements.txt

# 4. Isi .env
# BOT_TOKEN=token_dari_botfather
# CHAT_ID=id_grup_atau_kosongkan

# 5. Jalankan
./run.sh
```

Atau:

```bash
.venv/bin/python3 app.py
```

---

## 📦 Deploy

### FPS.ms
1. Upload `app.py`, `requirements.txt`, `.env`
2. Klik **Restart** di tab Console

### Background (Linux)
```bash
nohup .venv/bin/python3 app.py > bot.log 2>&1 &
```

---

## 🔒 Keamanan

- `.env` di `.gitignore` — token tidak tercommit
- Semua query SQL parameterized (`?`) — **zero SQL injection**
- Input user di-escape sebelum ditampilkan di Markdown
- Hanya 5 username tertentu yang bisa akses bot

---

## 📁 Struktur Project

```
bot_oryphem/
├── app.py             # Bot utama (~1000 baris)
├── run.sh             # Script jalanin bot
├── requirements.txt   # Dependencies
├── .env               # Token & config (tidak di-commit)
├── .gitignore         # File yang diabaikan git
├── README.md          # Dokumentasi ini
├── backups/           # Backup database otomatis (tidak di-commit)
└── lomba.db           # Database SQLite (tidak di-commit)
```
