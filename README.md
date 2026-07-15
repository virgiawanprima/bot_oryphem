# Bot Telegram Tim Oryphem

Bot untuk manajemen lomba dan role registration anggota tim Oryphem.

## Fitur

- **Role Registration**: Daftar role anggota tim (data, fullstack, uiux, blockchain, frontend)
- **Manajemen Lomba**: Tambah, lihat, dan batalkan lomba
- **Pengingat Otomatis**: H-7 dan H-1
- **Pembersihan Otomatis**: Hapus lomba setelah H-1 lewat

## Perintah

### Manajemen Lomba

| Perintah | Deskripsi | Contoh |
|----------|-----------|--------|
| `/ikut [judul] \| [link] \| [tgl_h7] \| [tgl_h1]` | Tambah lomba | `/ikut Lomba Data \| https://... \| 2026-07-13 \| 2026-07-19` |
| `/list` | Lihat semua lomba | `/list` |
| `/batal [id]` | Batalkan lomba | `/batal 3` |

### Role Registration

| Perintah | Deskripsi | Contoh |
|----------|-----------|--------|
| `/daftar [role]` | Daftarkan role kamu | `/daftar data` |
| `/ubahrole [role]` | Ganti role | `/ubahrole fullstack` |
| `/role` | Lihat role sendiri | `/role` |
| `/listrole` | Lihat semua anggota tim | `/listrole` |

### Role Tersedia

| Role | Deskripsi |
|------|-----------|
| `data` | Data Scientist / MLE |
| `fullstack` | Full Stack Developer |
| `uiux` | UI/UX Designer |
| `blockchain` | Blockchain Developer |
| `frontend` | Front End Developer |

## Cara Deploy di FPS.ms

1. Upload file `app.py`, `requirements.txt`, dan `.env` ke server FPS.ms
2. Klik **Restart** di tab Console
3. Bot akan berjalan otomatis

## Catatan

- Jangan commit file `.env` ke repository publik
- Token bot aman disimpan di `.env`