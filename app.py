#!/usr/bin/env python3
"""
Bot Telegram Tim Oryphem
Fitur: Manajemen Lomba, Role Registration, Pengingat Otomatis, Pembersihan Data
"""

import os
import logging
import sqlite3
import calendar
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.helpers import escape_markdown
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
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
WITA = ZoneInfo("Asia/Makassar")

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
        conn.execute("DROP TABLE IF EXISTS lomba")
        conn.execute("""
            CREATE TABLE lomba (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                judul TEXT NOT NULL,
                link TEXT NOT NULL,
                tanggal_buka TEXT NOT NULL,
                tanggal_tutup TEXT NOT NULL,
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


def tambah_lomba(judul, link, tanggal_buka, tanggal_tutup):
    conn = sqlite3.connect(DATABASE)
    try:
        cursor = conn.cursor()
        now = datetime.now(WITA).isoformat()
        cursor.execute(
            "INSERT INTO lomba (judul, link, tanggal_buka, tanggal_tutup, created_at) VALUES (?, ?, ?, ?, ?)",
            (judul, link, tanggal_buka, tanggal_tutup, now)
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
            "SELECT id, judul, link, tanggal_buka, tanggal_tutup FROM lomba ORDER BY tanggal_buka ASC"
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
            "SELECT id, judul, link, tanggal_buka, tanggal_tutup FROM lomba WHERE id = ?",
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
        today = datetime.now(WITA).date().isoformat()
        cursor.execute("DELETE FROM lomba WHERE tanggal_tutup < ?", (today,))
        deleted = cursor.rowcount
        conn.commit()
        return deleted
    finally:
        conn.close()


def get_lomba_yang_perlu_diingatkan():
    today = datetime.now(WITA).date()
    conn = sqlite3.connect(DATABASE)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, judul, link, tanggal_tutup FROM lomba")
        rows = cursor.fetchall()
        results = []
        for l_id, judul, link, tgl_tutup in rows:
            try:
                tutup = datetime.strptime(tgl_tutup, "%Y-%m-%d").date()
                days_left = (tutup - today).days
                if days_left in (7, 3, 1):
                    results.append((l_id, judul, link, tgl_tutup, days_left))
            except ValueError:
                continue
        return results
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
        return False
    conn = sqlite3.connect(DATABASE)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT role FROM users WHERE user_id = ?", (user_id,))
        existing = cursor.fetchone()
        if existing:
            return False
        now = datetime.now(WITA).isoformat()
        cursor.execute(
            "INSERT INTO users (user_id, username, role, registered_at) VALUES (?, ?, ?, ?)",
            (user_id, username, role, now)
        )
        conn.commit()
        return True
    finally:
        conn.close()


def ubah_role(user_id, role):
    if role not in ROLES:
        return False
    conn = sqlite3.connect(DATABASE)
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET role = ? WHERE user_id = ?", (role, user_id))
        conn.commit()
        return cursor.rowcount > 0
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


# --- BANTUAN KALENDER ---

MONTH_NAMES = [
    "", "Januari", "Februari", "Maret", "April", "Mei", "Juni",
    "Juli", "Agustus", "September", "Oktober", "November", "Desember"
]
DAY_NAMES = ["Min", "Sen", "Sel", "Rab", "Kam", "Jum", "Sab"]

def build_calendar(year, month, prefix="cal"):
    today = datetime.now(WITA).date()
    cal = calendar.Calendar()

    keyboard = [
        [
            InlineKeyboardButton("⬅️", callback_data=f"{prefix}_prev_{year}_{month}"),
            InlineKeyboardButton(f"{MONTH_NAMES[month]} {year}", callback_data="cal_ignore"),
            InlineKeyboardButton("➡️", callback_data=f"{prefix}_next_{year}_{month}"),
        ],
        [InlineKeyboardButton(d, callback_data="cal_ignore") for d in DAY_NAMES],
    ]

    for week in cal.monthdayscalendar(year, month):
        row = []
        for day in week:
            if day == 0:
                row.append(InlineKeyboardButton(" ", callback_data="cal_ignore"))
            else:
                row.append(InlineKeyboardButton(str(day), callback_data=f"{prefix}_day_{year}_{month}_{day}"))
        keyboard.append(row)

    keyboard.append([
        InlineKeyboardButton("🎯 Hari Ini", callback_data=f"{prefix}_today"),
        InlineKeyboardButton("🎯 Besok", callback_data=f"{prefix}_tomorrow"),
        InlineKeyboardButton("🎯 +7 Hari", callback_data=f"{prefix}_plus7"),
    ])
    keyboard.append([InlineKeyboardButton("❌ Batal", callback_data="menu_cancel")])

    return InlineKeyboardMarkup(keyboard)


def format_date_relative(date_str):
    today = datetime.now(WITA).date()
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d").date()
        delta = (d - today).days
        if delta == 0:
            return f"{date_str} (Hari Ini 🚨)"
        elif delta == 1:
            return f"{date_str} (Besok)"
        elif delta == 2:
            return f"{date_str} (Lusa)"
        elif delta > 0:
            return f"{date_str} ({delta} hari lagi)"
        else:
            return f"{date_str} (Sudah Lewat {abs(delta)} hari)"
    except ValueError:
        return date_str


# --- MAIN MENU ---

def main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("📋 Tambah Lomba", callback_data="menu_tambah")],
        [InlineKeyboardButton("📋 Daftar Lomba", callback_data="menu_list")],
        [InlineKeyboardButton("👤 Role Saya", callback_data="menu_role")],
        [InlineKeyboardButton("👥 Anggota Tim", callback_data="menu_anggota")],
        [InlineKeyboardButton("ℹ️ Bantuan", callback_data="menu_bantuan")],
    ]
    return InlineKeyboardMarkup(keyboard)


# --- COMMAND /START ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    username = user.username
    user_id = user.id

    if not username or not is_authorized(username):
        await update.message.reply_text(
            "⛔ *Akses Ditolak!*\n\nBot ini hanya untuk anggota tim Oryphem.",
            parse_mode="Markdown"
        )
        return

    member = TEAM_MEMBERS[username]
    name = member["name"]
    role = member["role"]
    quote = member["quote"]

    existing = get_role(user_id)
    if not existing:
        daftar_user(user_id, username, role)

    msg = (
        f"🚀 *Halo {name}!*\n\n"
        f"Kamu adalah anggota Oryphem sebagai *{ROLE_DISPLAY.get(role, role)}* ⚡\n"
        f"{quote}"
    )

    await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=main_menu_keyboard())


# --- MAIN MENU CALLBACK ---

async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user = query.from_user
    username = user.username

    if not is_authorized(username):
        await query.edit_message_text("⛔ *Akses Ditolak!*", parse_mode="Markdown")
        return

    if data == "menu_tambah":
        context.user_data.clear()
        context.user_data["state"] = "JUDUL"
        await query.edit_message_text(
            "📌 *Judul lomba?*\n\nKetik nama lombanya.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Batal", callback_data="menu_cancel")]])
        )
        return

    elif data == "menu_list":
        await show_list_lomba(update, context)
        return

    elif data == "menu_role":
        await show_role(update, context)
        return

    elif data == "menu_anggota":
        await show_anggota(update, context)
        return

    elif data == "menu_bantuan":
        await show_help(update, context)
        return

    elif data == "menu_back" or data == "menu_cancel":
        context.user_data.clear()
        member = TEAM_MEMBERS.get(username)
        if member:
            name = member["name"]
            role = member["role"]
            msg = f"🚀 *{name}!* Kamu adalah *{ROLE_DISPLAY.get(role, role)}* ⚡"
        else:
            msg = "🚀 *Menu Utama* ⚡"
        await query.edit_message_text(msg, parse_mode="Markdown", reply_markup=main_menu_keyboard())
        return


# --- CONVERSATION: TAMBAH LOMBA ---

async def handle_conversation_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.username):
        return

    state = context.user_data.get("state")
    if not state:
        return

    text = update.message.text.strip()

    if state == "JUDUL":
        if len(text) > 200:
            await update.message.reply_text("❌ *Judul terlalu panjang!* Maksimal 200 karakter.", parse_mode="Markdown")
            return
        if not text:
            await update.message.reply_text("❌ *Judul tidak boleh kosong!*", parse_mode="Markdown")
            return
        context.user_data["judul"] = text
        await update.message.reply_text(
            "🔗 *Link lomba?*\n\nKirim link atau paste URL-nya.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Batal", callback_data="menu_cancel")]])
        )
        context.user_data["state"] = "LINK"

    elif state == "LINK":
        if not text.startswith(("http://", "https://")):
            await update.message.reply_text(
                "❌ *Link tidak valid!* Pastikan dimulai dengan `http://` atau `https://`.",
                parse_mode="Markdown"
            )
            return
        context.user_data["link"] = text
        now = datetime.now(WITA)
        await update.message.reply_text(
            "📅 *Pilih tanggal pendaftaran dibuka:*",
            parse_mode="Markdown",
            reply_markup=build_calendar(now.year, now.month, prefix="buka")
        )
        context.user_data["state"] = "BUKA"


# --- CALLBACK HANDLERS ---

async def handle_calendar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_authorized(query.from_user.username):
        await query.edit_message_text("⛔ *Akses Ditolak!*", parse_mode="Markdown")
        return
    data = query.data
    parts = data.split("_")
    prefix = parts[0]

    now = datetime.now(WITA)

    if data == f"{prefix}_today":
        selected = now.date().isoformat()
    elif data == f"{prefix}_tomorrow":
        selected = (now.date() + timedelta(days=1)).isoformat()
    elif data == f"{prefix}_plus7":
        selected = (now.date() + timedelta(days=7)).isoformat()
    elif parts[1] == "prev":
        y, m = int(parts[2]), int(parts[3])
        if m == 1:
            y, m = y - 1, 12
        else:
            m -= 1
        teks = {"buka": "📅 *Pilih tanggal pendaftaran dibuka:*", "tutup": "📅 *Pilih tanggal tutup pendaftaran:*"}
        await query.edit_message_text(
            teks.get(prefix, "📅 *Pilih tanggal:*"),
            parse_mode="Markdown",
            reply_markup=build_calendar(y, m, prefix=prefix)
        )
        return
    elif parts[1] == "next":
        y, m = int(parts[2]), int(parts[3])
        if m == 12:
            y, m = y + 1, 1
        else:
            m += 1
        teks = {"buka": "📅 *Pilih tanggal pendaftaran dibuka:*", "tutup": "📅 *Pilih tanggal tutup pendaftaran:*"}
        await query.edit_message_text(
            teks.get(prefix, "📅 *Pilih tanggal:*"),
            parse_mode="Markdown",
            reply_markup=build_calendar(y, m, prefix=prefix)
        )
        return
    elif parts[1] == "day":
        y, m, d = int(parts[2]), int(parts[3]), int(parts[4])
        selected = f"{y:04d}-{m:02d}-{d:02d}"
    else:
        return

    if prefix == "buka":
        context.user_data["buka"] = selected
        now = datetime.now(WITA)
        await query.edit_message_text(
            "📅 *Pilih tanggal tutup pendaftaran:*",
            parse_mode="Markdown",
            reply_markup=build_calendar(now.year, now.month, prefix="tutup")
        )
        context.user_data["state"] = "TUTUP"
    elif prefix == "tutup":
        buka = context.user_data.get("buka")
        if buka and selected <= buka:
            now = datetime.now(WITA)
            await query.edit_message_text(
                "❌ *Tanggal tutup harus setelah tanggal buka!*\n\nPilih tanggal yang lebih besar.",
                parse_mode="Markdown",
                reply_markup=build_calendar(now.year, now.month, prefix="tutup")
            )
            return
        context.user_data["tutup"] = selected
        await show_konfirmasi(query, context)


async def show_list_lomba(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    lomba_list = get_all_lomba()

    if not lomba_list:
        keyboard = [[InlineKeyboardButton("➕ Tambah Lomba", callback_data="menu_tambah")],
                     [InlineKeyboardButton("🔙 Kembali", callback_data="menu_back")]]
        await query.edit_message_text(
            "📭 *Belum ada lomba.*\n\nGunakan menu Tambah Lomba.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    msg = "📋 *Daftar Lomba:*\n\n"
    keyboard = []
    for l in lomba_list:
        l_id, judul, link, tgl_buka, tgl_tutup = l
        safe_judul = escape_markdown(judul, version=1)
        msg += f"🆔 *{l_id}* — {safe_judul}\n"
        msg += f"  Buka: {format_date_relative(tgl_buka)}\n"
        msg += f"  Tutup: {format_date_relative(tgl_tutup)}\n\n"
        keyboard.append([InlineKeyboardButton(f"❌ Hapus #{l_id}", callback_data=f"hapus_{l_id}")])

    keyboard.append([InlineKeyboardButton("➕ Tambah Baru", callback_data="menu_tambah")])
    keyboard.append([InlineKeyboardButton("🔙 Kembali", callback_data="menu_back")])

    await query.edit_message_text(msg, parse_mode="Markdown",
                                   reply_markup=InlineKeyboardMarkup(keyboard),
                                   disable_web_page_preview=True)


async def handle_hapus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_authorized(query.from_user.username):
        await query.edit_message_text("⛔ *Akses Ditolak!*", parse_mode="Markdown")
        return
    data = query.data
    lomba_id = int(data.replace("hapus_", ""))

    lomba = get_lomba_by_id(lomba_id)
    if not lomba:
        await query.edit_message_text(
            "❌ *Lomba tidak ditemukan!*",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Kembali", callback_data="menu_list")]])
        )
        return

    if hapus_lomba(lomba_id):
        judul = escape_markdown(lomba[1], version=1)
        await query.edit_message_text(
            f"✅ *Lomba dihapus:* {judul}",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Kembali", callback_data="menu_list")]])
        )
        logger.info(f"Lomba dihapus: {lomba[1]} (ID: {lomba_id})")
    else:
        await query.edit_message_text(
            "❌ *Gagal menghapus lomba!*",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Kembali", callback_data="menu_list")]])
        )


async def show_role(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    role = get_role(user_id)

    if role:
        msg = f"🧑‍💻 *Role Kamu:* {ROLE_DISPLAY.get(role, role)}"
    else:
        msg = "❌ *Belum terdaftar*"

    keyboard = [[InlineKeyboardButton("🔙 Kembali", callback_data="menu_back")]]
    await query.edit_message_text(msg, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))


async def show_anggota(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    users = get_all_users()

    grouped = {}
    for user_id, username, role in users:
        name = TEAM_MEMBERS.get(username, {}).get("name", username)
        grouped.setdefault(role, []).append(name)

    msg = "👥 *Anggota Tim Oryphem*\n\n"
    for r in ROLES:
        if r in grouped:
            msg += f"*{ROLE_DISPLAY.get(r, r)}:* {', '.join(grouped[r])}\n"
        else:
            msg += f"*{ROLE_DISPLAY.get(r, r)}:* (kosong)\n"

    keyboard = [[InlineKeyboardButton("🔙 Kembali", callback_data="menu_back")]]
    await query.edit_message_text(msg, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))


async def show_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    msg = (
        "📖 *Panduan Bot Oryphem*\n\n"
        "📋 *Tambah Lomba*\n"
        "Menu → Tambah Lomba → ikuti langkah\n\n"
        "👤 *Role*\n"
        "Menu → Role Saya\n\n"
        "⏰ *Pengingat Otomatis*\n"
        "• H-7 jam 09:00 WITA\n"
        "• H-3 jam 09:00 WITA\n"
        "• H-1 jam 09:00 WITA\n\n"
        "🧹 *Pembersihan Otomatis*\n"
        "Lomba dihapus setelah deadline lewat"
    )
    keyboard = [[InlineKeyboardButton("🔙 Kembali", callback_data="menu_back")]]
    await query.edit_message_text(msg, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))


async def show_konfirmasi(query, context):
    judul = context.user_data.get("judul", "?")
    link = context.user_data.get("link", "?")
    buka = context.user_data.get("buka", "?")
    tutup = context.user_data.get("tutup", "?")
    safe_judul = escape_markdown(judul, version=1)
    safe_link = link.replace(")", "%29")

    msg = (
        f"📌 *Judul:* {safe_judul}\n"
        f"🔗 *Link:* {safe_link}\n"
        f"📅 *Tanggal Buka:* {buka}\n"
        f"📅 *Tanggal Tutup:* {tutup}\n\n"
        "✅ *Simpan lomba ini?*"
    )
    keyboard = [
        [InlineKeyboardButton("✅ Simpan", callback_data="konfirmasi_simpan")],
        [InlineKeyboardButton("🔄 Ulang", callback_data="menu_tambah")],
        [InlineKeyboardButton("❌ Batal", callback_data="menu_back")],
    ]
    await query.edit_message_text(msg, parse_mode="Markdown",
                                  reply_markup=InlineKeyboardMarkup(keyboard),
                                  disable_web_page_preview=True)
    context.user_data["state"] = "KONFIRMASI"


async def handle_konfirmasi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_authorized(query.from_user.username):
        await query.edit_message_text("⛔ *Akses Ditolak!*", parse_mode="Markdown")
        return
    data = query.data

    if data == "konfirmasi_simpan":
        judul = context.user_data.get("judul", "?")
        link = context.user_data.get("link", "?")
        buka = context.user_data.get("buka", "?")
        tutup = context.user_data.get("tutup", "?")

        try:
            lomba_id = tambah_lomba(judul, link, buka, tutup)
            await query.edit_message_text(
                f"✅ *Lomba berhasil ditambahkan!* 🆔 {lomba_id}",
                parse_mode="Markdown",
                reply_markup=main_menu_keyboard()
            )
            logger.info(f"Lomba ditambahkan: {judul} (ID: {lomba_id})")
        except Exception as e:
            logger.error(f"Error saat menambah lomba: {e}")
            await query.edit_message_text(
                "❌ *Gagal menambahkan lomba!*",
                parse_mode="Markdown",
                reply_markup=main_menu_keyboard()
            )
        context.user_data.clear()

    return


# --- CALLBACK DISPATCHER ---

async def callback_dispatcher(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data

    if data.startswith("menu_"):
        await menu_callback(update, context)
        return

    if data.startswith("hapus_"):
        await handle_hapus(update, context)
        return

    if data.startswith("buka_") or data.startswith("tutup_"):
        await handle_calendar(update, context)
        return

    if data.startswith("konfirmasi_"):
        await handle_konfirmasi(update, context)
        return

    if data == "cal_ignore":
        await query.answer()
        return

    await query.answer()


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

    for l in lomba_list:
        l_id, judul, link, tgl_tutup, days_left = l
        safe_judul = escape_markdown(judul, version=1)
        safe_link = link.replace(")", "%29")

        if days_left == 7:
            pesan = f"""
🚨 *PENGINGAT H-7!*

📌 *{safe_judul}*
🔗 [Link Lomba]({safe_link})
📅 Deadline: {tgl_tutup}

⚠️ *Persiapan dokumen dan konsep mulai sekarang!*
Jangan sampai ketinggalan!

---
Tim Oryphem ⚡
"""
        elif days_left == 3:
            pesan = f"""
🚨 *PENGINGAT H-3!*

📌 *{safe_judul}*
🔗 [Link Lomba]({safe_link})
📅 Deadline: {tgl_tutup}

⚡ *Waktu semakin dekat!*
Cek progress dan kumpulkan bahan.

---
Tim Oryphem ⚡
"""
        elif days_left == 1:
            pesan = f"""
🚨 *PENGINGAT H-1!*

📌 *{safe_judul}*
🔗 [Link Lomba]({safe_link})
📅 Deadline: {tgl_tutup}

🔥 *Besok terakhir!*
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
            "❌ *Terjadi kesalahan!*\nSilakan coba lagi nanti.",
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
            time=time(9, 0, tzinfo=WITA),
            days=tuple(range(7)),
            name="daily_reminder"
        )
        logger.info("Daily reminder dijadwalkan pada jam 09:00 WITA setiap hari")
        job_queue.run_once(startup_cleanup, when=10, name="startup_cleanup")
    else:
        logger.warning("JobQueue tidak tersedia!")

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", start))

    application.add_handler(CallbackQueryHandler(callback_dispatcher))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_conversation_message))

    application.add_error_handler(error_handler)

    logger.info("Bot Oryphem sedang berjalan...")
    application.run_polling(allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    main()
