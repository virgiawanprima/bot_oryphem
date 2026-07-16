#!/usr/bin/env python3
"""
Bot Telegram Tim Oryphem
Fitur: Manajemen Lomba, Role Registration, Pengingat Otomatis, Pembersihan Data
"""

import os
import logging
import sqlite3
from datetime import datetime, time
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
from telegram import Update
from telegram.helpers import escape_markdown
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- KONFIGURASI ---
BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN tidak ditemukan di environment variables!")

DATABASE = "lomba.db"
WIB = ZoneInfo("Asia/Jakarta")

_raw_chat_id = os.environ.get("CHAT_ID")
if _raw_chat_id:
    try:
        CHAT_ID = int(_raw_chat_id)
    except ValueError:
        logger.warning("CHAT_ID tidak valid, harus berupa angka. Pengingat dinonaktifkan.")
        CHAT_ID = None
else:
    CHAT_ID = None


# --- ANGGOTA TIM ---

TEAM_MEMBERS = {
    "alex123566": {
        "name": "Prima",
        "role": "data-mle",
        "quote": '📊 "In God we trust, all others must bring data."',
    },
    "Anjayehan": {
        "name": "Raihan",
        "role": "uiux-designer",
        "quote": '🎨 "Design is not just what it looks like. Design is how it works."',
    },
    "Zbisrih": {
        "name": "Iqbal",
        "role": "blockchain-developer",
        "quote": '⛓️ "Trust the code, not the middleman."',
    },
    "ken14_14": {
        "name": "Baits",
        "role": "fullstack-developer",
        "quote": "🛠️ \"Full stack is not about knowing everything. It's about connecting everything.\"",
    },
    "hikkigayahachiman": {
        "name": "Jamal",
        "role": "frontend-developer",
        "quote": '✨ "A user interface is like a joke. If you have to explain it, it\'s not that good."',
    },
}

ALLOWED_USERNAMES = set(TEAM_MEMBERS.keys())


# --- FUNGSI DATABASE ---

def init_db():
    conn = sqlite3.connect(DATABASE)
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS lomba (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                judul TEXT NOT NULL,
                link TEXT NOT NULL,
                tanggal_h7 TEXT NOT NULL,
                tanggal_h1 TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                role TEXT NOT NULL,
                registered_at TEXT NOT NULL
            )
        """)
        for old, new in ROLE_MIGRATION.items():
            conn.execute("UPDATE users SET role = ? WHERE role = ?", (new, old))
        conn.commit()
    finally:
        conn.close()
    logger.info("Database initialized")


def tambah_lomba(judul, link, tanggal_h7, tanggal_h1):
    conn = sqlite3.connect(DATABASE)
    try:
        cursor = conn.cursor()
        now = datetime.now(WIB).isoformat()
        cursor.execute(
            "INSERT INTO lomba (judul, link, tanggal_h7, tanggal_h1, created_at) VALUES (?, ?, ?, ?, ?)",
            (judul, link, tanggal_h7, tanggal_h1, now)
        )
        lomba_id = cursor.lastrowid
        conn.commit()
        return lomba_id
    finally:
        conn.close()


def hapus_lomba(lomba_id):
    conn = sqlite3.connect(DATABASE)
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM lomba WHERE id = ?", (lomba_id,))
        affected = cursor.rowcount
        conn.commit()
        return affected > 0
    finally:
        conn.close()


def get_all_lomba():
    conn = sqlite3.connect(DATABASE)
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, judul, link, tanggal_h7, tanggal_h1 FROM lomba ORDER BY tanggal_h7 ASC"
        )
        rows = cursor.fetchall()
        return rows
    finally:
        conn.close()


def get_lomba_by_id(lomba_id):
    conn = sqlite3.connect(DATABASE)
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, judul, link, tanggal_h7, tanggal_h1 FROM lomba WHERE id = ?",
            (lomba_id,)
        )
        row = cursor.fetchone()
        return row
    finally:
        conn.close()


def hapus_lomba_otomatis():
    conn = sqlite3.connect(DATABASE)
    try:
        cursor = conn.cursor()
        today = datetime.now(WIB).date().isoformat()
        cursor.execute("DELETE FROM lomba WHERE tanggal_h1 < ?", (today,))
        deleted = cursor.rowcount
        conn.commit()
        return deleted
    finally:
        conn.close()


def get_lomba_yang_perlu_diingatkan():
    conn = sqlite3.connect(DATABASE)
    try:
        cursor = conn.cursor()
        today = datetime.now(WIB).date().isoformat()
        cursor.execute(
            "SELECT id, judul, link, tanggal_h7, tanggal_h1 FROM lomba WHERE tanggal_h7 = ? OR tanggal_h1 = ?",
            (today, today)
        )
        rows = cursor.fetchall()
        return rows
    finally:
        conn.close()


# --- FUNGSI DATABASE UNTUK USERS ---

ROLES = [
    "data-mle",
    "fullstack-developer",
    "uiux-designer",
    "blockchain-developer",
    "frontend-developer",
]

ROLE_DISPLAY = {
    "data-mle": "DATA & MLE",
    "fullstack-developer": "FULL STACK DEVELOPER",
    "uiux-designer": "UI/UX DESIGNER",
    "blockchain-developer": "BLOCKCHAIN DEVELOPER",
    "frontend-developer": "FRONT END DEVELOPER",
}

ROLE_MIGRATION = {
    "data": "data-mle",
    "fullstack": "fullstack-developer",
    "uiux": "uiux-designer",
    "blockchain": "blockchain-developer",
    "frontend": "frontend-developer",
}

ROLE_DISPLAY.update({k: ROLE_DISPLAY[v] for k, v in ROLE_MIGRATION.items()})


def get_role(user_id):
    conn = sqlite3.connect(DATABASE)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT role FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        return row[0] if row else None
    finally:
        conn.close()


def daftar_user(user_id, username, role):
    if role not in ROLES:
        role_list = "\n".join(f"• `{k}` — {v}" for k, v in ROLE_DISPLAY.items())
        return False, f"Role tidak valid!\n\nPilih salah satu:\n{role_list}"

    conn = sqlite3.connect(DATABASE)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT role FROM users WHERE user_id = ?", (user_id,))
        existing = cursor.fetchone()
        if existing:
            return False, f"Anda sudah terdaftar sebagai *{ROLE_DISPLAY.get(existing[0], existing[0])}*. Gunakan `/ubahrole [role]` jika ingin mengganti."

        now = datetime.now(WIB).isoformat()
        cursor.execute(
            "INSERT INTO users (user_id, username, role, registered_at) VALUES (?, ?, ?, ?)",
            (user_id, username, role, now)
        )
        conn.commit()
        return True, f"✅ Berhasil terdaftar sebagai *{ROLE_DISPLAY.get(role, role)}*!"
    finally:
        conn.close()


def ubah_role(user_id, role):
    if role not in ROLES:
        role_list = "\n".join(f"• `{k}` — {v}" for k, v in ROLE_DISPLAY.items())
        return False, f"Role tidak valid!\n\nPilih salah satu:\n{role_list}"

    conn = sqlite3.connect(DATABASE)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
        if not cursor.fetchone():
            return False, "Anda belum terdaftar. Gunakan `/daftar [role]` terlebih dahulu."

        cursor.execute("UPDATE users SET role = ? WHERE user_id = ?", (role, user_id))
        conn.commit()
        return True, f"✅ Role berhasil diubah menjadi *{ROLE_DISPLAY.get(role, role)}*!"
    finally:
        conn.close()


def get_all_users():
    conn = sqlite3.connect(DATABASE)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, username, role FROM users ORDER BY role")
        rows = cursor.fetchall()
        return rows
    finally:
        conn.close()


# --- ACCESS CONTROL ---

def is_authorized(username):
    return username in ALLOWED_USERNAMES


async def unauthorized_reply(update: Update):
    await update.message.reply_text(
        "⛔ *Akses Ditolak!*\n\nBot ini hanya untuk anggota tim Oryphem.",
        parse_mode="Markdown"
    )


# --- FUNGSI COMMAND HANDLER ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    username = user.username
    user_id = user.id

    if not username or not is_authorized(username):
        await unauthorized_reply(update)
        return

    member = TEAM_MEMBERS[username]
    name = member["name"]
    role = member["role"]
    quote = member["quote"]

    existing = get_role(user_id)
    if existing:
        msg = f"""
🚀 *Halo {name}!*

Kamu adalah anggota Oryphem sebagai *{ROLE_DISPLAY.get(role, role)}* ⚡
{quote}

📋 *Perintah:*
/ikut — Tambah lomba baru
/list — Lihat daftar lomba
/batal [id] — Batalkan lomba
/role — Cek role kamu
/listrole — Lihat semua anggota tim
/help — Panduan lengkap
        """
        await update.message.reply_text(msg, parse_mode="Markdown")
        return

    display_name = user.full_name or username
    daftar_user(user_id, display_name, role)

    msg = f"""
🚀 *Halo {name}!*

Kamu adalah anggota Oryphem sebagai *{ROLE_DISPLAY.get(role, role)}* ⚡
{quote}

📋 *Perintah:*
/ikut — Tambah lomba baru
/list — Lihat daftar lomba
/batal [id] — Batalkan lomba
/role — Cek role kamu
/listrole — Lihat semua anggota tim
/help — Panduan lengkap
    """
    await update.message.reply_text(msg, parse_mode="Markdown")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.username):
        await unauthorized_reply(update)
        return
    help_text = """
📖 *Panduan Penggunaan Bot*

*1. Registrasi Role Anggota*
Daftarkan role kamu sekali saja:
`/daftar [role]`

Role: data, fullstack, uiux, blockchain, frontend

Contoh: `/daftar data`

Cek role: `/role`
Lihat semua anggota: `/listrole`
Ganti role: `/ubahrole [role]`

*2. Menambahkan Lomba*
`/ikut [judul] | [link] | [tgl_h7] | [tgl_h1]`

Contoh:
`/ikut Lomba Data Science | https://lomba.com | 2026-07-13 | 2026-07-19`

*3. Melihat Daftar Lomba*
`/list`

*4. Membatalkan Lomba*
`/batal [id]`

Contoh: `/batal 3`

*5. Pengingat Otomatis*
Bot akan mengirim pengingat pada:
- H-7: Persiapan dokumen dan konsep
- H-1: Cek kembali berkas dan kodingan

*6. Pembersihan Otomatis*
Lomba otomatis dihapus setelah tanggal H-1 lewat.

---
Tim Oryphem ⚡
    """
    await update.message.reply_text(help_text, parse_mode="Markdown")


async def ikut(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.username):
        await unauthorized_reply(update)
        return
    args = " ".join(context.args)

    if not args:
        await update.message.reply_text(
            "❌ *Format salah!*\n\n"
            "Gunakan format:\n"
            "`/ikut [judul] | [link] | [tgl_h7] | [tgl_h1]`\n\n"
            "Contoh:\n"
            "`/ikut Lomba Data Science | https://lomba.com | 2026-07-13 | 2026-07-19`",
            parse_mode="Markdown"
        )
        return

    parts = [p.strip() for p in args.split("|")]

    if len(parts) != 4:
        await update.message.reply_text(
            "❌ *Format salah!*\n\n"
            "Pastikan menggunakan 4 bagian yang dipisahkan dengan ` | `:\n"
            "`[judul] | [link] | [tgl_h7] | [tgl_h1]`\n\n"
            "Contoh:\n"
            "`/ikut Lomba Data Science | https://lomba.com | 2026-07-13 | 2026-07-19`",
            parse_mode="Markdown"
        )
        return

    judul, link, tanggal_h7, tanggal_h1 = parts

    try:
        datetime.strptime(tanggal_h7, "%Y-%m-%d")
        datetime.strptime(tanggal_h1, "%Y-%m-%d")
    except ValueError:
        await update.message.reply_text(
            "❌ *Format tanggal salah!*\n\n"
            "Gunakan format: `YYYY-MM-DD`\n"
            "Contoh: `2026-07-13`",
            parse_mode="Markdown"
        )
        return

    try:
        lomba_id = tambah_lomba(judul, link, tanggal_h7, tanggal_h1)
        safe_judul = escape_markdown(judul, version=1)
        safe_link = link.replace(")", "%29")
        await update.message.reply_text(
            f"✅ *Lomba berhasil ditambahkan!*\n\n"
            f"📌 *Judul:* {safe_judul}\n"
            f"🔗 *Link:* {safe_link}\n"
            f"📅 *H-7:* {tanggal_h7}\n"
            f"📅 *H-1:* {tanggal_h1}\n"
            f"🆔 *ID:* {lomba_id}\n\n"
            f"Gunakan `/list` untuk melihat semua lomba.",
            parse_mode="Markdown"
        )
        logger.info(f"Lomba ditambahkan: {judul} (ID: {lomba_id})")
    except Exception as e:
        logger.error(f"Error saat menambah lomba: {e}")
        await update.message.reply_text(
            "❌ *Gagal menambahkan lomba!*\n"
            "Terjadi kesalahan pada server. Silakan coba lagi."
        )


async def list_lomba(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.username):
        await unauthorized_reply(update)
        return
    lomba_list = get_all_lomba()

    if not lomba_list:
        await update.message.reply_text(
            "📭 *Belum ada lomba yang diikuti.*\n\n"
            "Gunakan `/ikut` untuk menambahkan lomba.",
            parse_mode="Markdown"
        )
        return

    today = datetime.now(WIB).date()
    message = "📋 *Daftar Lomba yang Diikuti:*\n\n"

    for l in lomba_list:
        l_id, judul, link, tgl_h7, tgl_h1 = l
        safe_judul = escape_markdown(judul, version=1)
        safe_link = link.replace(")", "%29")

        try:
            h7_date = datetime.strptime(tgl_h7, "%Y-%m-%d").date()
            h1_date = datetime.strptime(tgl_h1, "%Y-%m-%d").date()
            days_to_h7 = (h7_date - today).days
            days_to_h1 = (h1_date - today).days
        except ValueError:
            days_to_h7 = "?"
            days_to_h1 = "?"

        message += f"🆔 *{l_id}*\n"
        message += f"📌 {safe_judul}\n"
        message += f"🔗 [Link]({safe_link})\n"
        message += f"📅 H-7: {tgl_h7} "
        if isinstance(days_to_h7, int) and days_to_h7 > 0:
            message += f"({days_to_h7} hari lagi)\n"
        elif isinstance(days_to_h7, int) and days_to_h7 == 0:
            message += "(HARI INI! 🚨)\n"
        elif isinstance(days_to_h7, int) and days_to_h7 < 0:
            message += f"(sudah lewat {abs(days_to_h7)} hari)\n"
        else:
            message += "\n"

        message += f"📅 H-1: {tgl_h1} "
        if isinstance(days_to_h1, int) and days_to_h1 > 0:
            message += f"({days_to_h1} hari lagi)\n"
        elif isinstance(days_to_h1, int) and days_to_h1 == 0:
            message += "(HARI INI! 🚨)\n"
        elif isinstance(days_to_h1, int) and days_to_h1 < 0:
            message += f"(sudah lewat {abs(days_to_h1)} hari)\n"
        else:
            message += "\n"
        message += "\n"

    message += "\nGunakan `/batal [id]` untuk membatalkan lomba."

    await update.message.reply_text(message, parse_mode="Markdown", disable_web_page_preview=True)


async def batal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.username):
        await unauthorized_reply(update)
        return
    if not context.args:
        await update.message.reply_text(
            "❌ *Format salah!*\n\n"
            "Gunakan format:\n"
            "`/batal [id]`\n\n"
            "Gunakan `/list` untuk melihat ID lomba.",
            parse_mode="Markdown"
        )
        return

    try:
        lomba_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text(
            "❌ *ID harus berupa angka!*\n\n"
            "Contoh: `/batal 3`",
            parse_mode="Markdown"
        )
        return

    lomba = get_lomba_by_id(lomba_id)
    if not lomba:
        await update.message.reply_text(
            f"❌ *Lomba dengan ID {lomba_id} tidak ditemukan!*\n\n"
            "Gunakan `/list` untuk melihat daftar lomba.",
            parse_mode="Markdown"
        )
        return

    if hapus_lomba(lomba_id):
        safe_judul = escape_markdown(lomba[1], version=1)
        await update.message.reply_text(
            f"✅ *Lomba berhasil dibatalkan!*\n\n"
            f"📌 *Judul:* {safe_judul}\n"
            f"🆔 *ID:* {lomba_id}",
            parse_mode="Markdown"
        )
        logger.info(f"Lomba dibatalkan: {lomba[1]} (ID: {lomba_id})")
    else:
        await update.message.reply_text(
            "❌ *Gagal membatalkan lomba!*\n"
            "Terjadi kesalahan pada server. Silakan coba lagi."
        )


# --- FUNGSI COMMAND HANDLER UNTUK ROLE ---

async def daftar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.username):
        await unauthorized_reply(update)
        return
    if not context.args:
        role_list = "\n".join(f"• `{k}` — {v}" for k, v in ROLE_DISPLAY.items())
        await update.message.reply_text(
            f"❌ *Format salah!*\n\n"
            f"Gunakan: `/daftar [role]`\n\n"
            f"Role tersedia:\n{role_list}\n\n"
            f"Contoh: `/daftar data-mle`",
            parse_mode="Markdown"
        )
        return

    role = context.args[0].lower()
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.full_name

    success, message = daftar_user(user_id, username, role)
    await update.message.reply_text(message, parse_mode="Markdown")


async def ubahrole(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.username):
        await unauthorized_reply(update)
        return
    if not context.args:
        role_list = "\n".join(f"• `{k}` — {v}" for k, v in ROLE_DISPLAY.items())
        await update.message.reply_text(
            f"❌ *Format salah!*\n\n"
            f"Gunakan: `/ubahrole [role]`\n\n"
            f"Role tersedia:\n{role_list}\n\n"
            f"Contoh: `/ubahrole fullstack-developer`",
            parse_mode="Markdown"
        )
        return

    role = context.args[0].lower()
    user_id = update.effective_user.id

    success, message = ubah_role(user_id, role)
    await update.message.reply_text(message, parse_mode="Markdown")


async def role(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.username):
        await unauthorized_reply(update)
        return
    user_id = update.effective_user.id
    role_user = get_role(user_id)

    if role_user:
        await update.message.reply_text(
            f"🧑‍💻 *Role Anda:* {ROLE_DISPLAY.get(role_user, role_user)}\n\n"
            f"Gunakan `/ubahrole [role]` jika ingin mengganti.",
            parse_mode="Markdown"
        )
    else:
        role_list = "\n".join(f"• `{k}` — {v}" for k, v in ROLE_DISPLAY.items())
        await update.message.reply_text(
            "❌ *Anda belum terdaftar!*\n\n"
            f"Gunakan `/daftar [role]` untuk mendaftar.\n\n"
            f"Role tersedia:\n{role_list}",
            parse_mode="Markdown"
        )


async def list_role(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.username):
        await unauthorized_reply(update)
        return
    users = get_all_users()

    if not users:
        await update.message.reply_text(
            "📭 *Belum ada anggota yang terdaftar.*\n\n"
            "Gunakan `/daftar [role]` untuk mendaftar.",
            parse_mode="Markdown"
        )
        return

    grouped = {}
    for user_id, username, role in users:
        name = TEAM_MEMBERS.get(username, {}).get("name", username)
        grouped.setdefault(role, []).append(name)

    message = "👥 *Daftar Anggota Tim Oryphem*\n\n"
    for r in ROLES:
        if r in grouped:
            message += f"*{ROLE_DISPLAY.get(r, r)}:* {', '.join(grouped[r])}\n"
        else:
            message += f"*{ROLE_DISPLAY.get(r, r)}:* (kosong)\n"

    await update.message.reply_text(message, parse_mode="Markdown")


# --- CALLBACK HANDLER UNTUK TOMBOL ROLE ---

async def role_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not is_authorized(query.from_user.username):
        await query.edit_message_text("⛔ *Akses Ditolak!*", parse_mode="Markdown")
        return

    role = query.data.replace("role_", "")
    user_id = query.from_user.id
    username = query.from_user.username or query.from_user.full_name

    success, message = daftar_user(user_id, username, role)
    if success:
        await query.edit_message_text(
            f"✅ *Selamat! Kamu terdaftar sebagai* {ROLE_DISPLAY.get(role, role)}! ⚡\n\n"
            "Gunakan `/role` untuk cek role kamu.\n"
            "Gunakan `/help` untuk melihat semua perintah.",
            parse_mode="Markdown"
        )
    else:
        await query.edit_message_text(message, parse_mode="Markdown")


# --- FUNGSI JOB (TUGAS OTOMATIS) ---

async def daily_reminder(context: ContextTypes.DEFAULT_TYPE):
    logger.info("Menjalankan daily_reminder...")

    deleted = hapus_lomba_otomatis()
    if deleted > 0:
        logger.info(f"{deleted} lomba dihapus (sudah lewat H-1)")

    lomba_list = get_lomba_yang_perlu_diingatkan()

    if not lomba_list:
        logger.info("Tidak ada lomba yang perlu diingatkan hari ini")
        return

    today = datetime.now(WIB).date().isoformat()

    for l in lomba_list:
        l_id, judul, link, tgl_h7, tgl_h1 = l
        safe_judul = escape_markdown(judul, version=1)
        safe_link = link.replace(")", "%29")

        if tgl_h7 == today:
            pesan = f"""
🚨 *PENGINGAT H-7!*

📌 *{safe_judul}*
🔗 [Link Lomba]({safe_link})
📅 H-7: {tgl_h7}

⚠️ *Persiapan dokumen dan konsep mulai sekarang!*
Jangan sampai ketinggalan!

---
Tim Oryphem ⚡
"""
        elif tgl_h1 == today:
            pesan = f"""
🚨 *PENGINGAT H-1!*

📌 *{safe_judul}*
🔗 [Link Lomba]({safe_link})
📅 H-1: {tgl_h1}

🔥 *Besok hari-H!*
Cek kembali:
✅ Berkas pendaftaran
✅ Kodingan dan testing
✅ Semua persyaratan

Semangat, Tim Oryphem! ⚡
"""
        else:
            continue

        if CHAT_ID:
            try:
                await context.bot.send_message(
                    chat_id=CHAT_ID,
                    text=pesan,
                    parse_mode="Markdown",
                    disable_web_page_preview=True
                )
                logger.info(f"Pengingat dikirim untuk: {judul}")
            except Exception as e:
                logger.error(f"Gagal mengirim pengingat untuk {judul}: {e}")
        else:
            logger.info(f"Pengingat untuk {judul} tidak dikirim (CHAT_ID tidak diset)")


async def startup_cleanup(context: ContextTypes.DEFAULT_TYPE):
    deleted = hapus_lomba_otomatis()
    if deleted > 0:
        logger.info(f"{deleted} lomba dihapus saat startup (sudah lewat H-1)")


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    update_id = update.update_id if update else "unknown"
    logger.error(f"Update {update_id} caused error {context.error}")
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "❌ *Terjadi kesalahan!*\n"
            "Silakan coba lagi nanti atau hubungi admin.",
            parse_mode="Markdown"
        )


# --- FUNGSI UTAMA ---

def main():
    init_db()

    application = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .build()
    )

    job_queue = application.job_queue

    if job_queue:
        job_queue.run_daily(
            daily_reminder,
            time=time(8, 0, tzinfo=WIB),
            days=tuple(range(7)),
            name="daily_reminder"
        )
        logger.info("Daily reminder dijadwalkan pada jam 08:00 WIB setiap hari")

        job_queue.run_once(
            startup_cleanup,
            when=10,
            name="startup_cleanup"
        )
    else:
        logger.warning("JobQueue tidak tersedia!")

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("ikut", ikut))
    application.add_handler(CommandHandler("list", list_lomba))
    application.add_handler(CommandHandler("batal", batal))

    application.add_handler(CommandHandler("daftar", daftar))
    application.add_handler(CommandHandler("ubahrole", ubahrole))
    application.add_handler(CommandHandler("role", role))
    application.add_handler(CommandHandler("listrole", list_role))

    application.add_handler(CallbackQueryHandler(role_callback, pattern="^role_"))

    application.add_error_handler(error_handler)

    logger.info("Bot Oryphem sedang berjalan...")
    application.run_polling(allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    main()
