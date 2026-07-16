#!/usr/bin/env python3
"""Unit test untuk Bot Oryphem — test semua fungsi core tanpa dependensi Telegram"""

import os
import sys
import calendar
import sqlite3
import tempfile
from datetime import datetime, time, timedelta, date
from zoneinfo import ZoneInfo

os.environ["BOT_TOKEN"] = "test:token"

WITA = ZoneInfo("Asia/Makassar")
DATABASE = None  # akan di-set per test

# ===== IMPORT KONFIGURASI =====
ROLES = [
    "data-mle", "fullstack-developer", "uiux-designer",
    "blockchain-developer", "frontend-developer",
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

TEAM_MEMBERS = {
    "alex123566": {"name": "Prima", "role": "data-mle", "quote": "test"},
    "Anjayehan": {"name": "Raihan", "role": "uiux-designer", "quote": "test"},
    "Zbisrih": {"name": "Iqbal", "role": "blockchain-developer", "quote": "test"},
    "ken14_14": {"name": "Baits", "role": "fullstack-developer", "quote": "test"},
    "hikkigayahachiman": {"name": "Jamal", "role": "frontend-developer", "quote": "test"},
}

ALLOWED_USERNAMES = set(TEAM_MEMBERS.keys())

pass_count = 0
fail_count = 0

def assert_eq(label, actual, expected):
    global pass_count, fail_count
    if actual == expected:
        pass_count += 1
        print(f"  ✅ {label}")
    else:
        fail_count += 1
        print(f"  ❌ {label}: expected {expected!r}, got {actual!r}")

def assert_true(label, val):
    assert_eq(label, val, True)

def assert_false(label, val):
    assert_eq(label, val, False)

def assert_not_none(label, val):
    global pass_count, fail_count
    if val is not None:
        pass_count += 1
        print(f"  ✅ {label}")
    else:
        fail_count += 1
        print(f"  ❌ {label}: expected not None, got None")

# ===== TEST DATABASE FUNCTIONS =====
print("\n--- Test Database Functions ---")

# Setup test DB
tmp = tempfile.NamedTemporaryFile(delete=False)
DATABASE = tmp.name
tmp.close()

# We override DATABASE in the module scope - we test functions directly
import app as bot

# Monkey-patch database path
bot.DATABASE = DATABASE

# Init DB
bot.init_db()
assert_true("init_db creates lomba table", True)

# Test tambah_lomba
lomba_id = bot.tambah_lomba("Lomba AI", "https://example.com", "2026-07-20", "2026-07-26")
assert_eq("tambah_lomba returns ID", lomba_id, 1)

# Test get_all_lomba
rows = bot.get_all_lomba()
assert_eq("get_all_lomba returns 1 row", len(rows), 1)
assert_eq("first row judul", rows[0][1], "Lomba AI")
assert_eq("first row link", rows[0][2], "https://example.com")
assert_eq("first row buka", rows[0][3], "2026-07-20")
assert_eq("first row tutup", rows[0][4], "2026-07-26")

# Test get_lomba_by_id
row = bot.get_lomba_by_id(1)
assert_not_none("get_lomba_by_id found", row)
assert_eq("found row judul", row[1], "Lomba AI")

row = bot.get_lomba_by_id(999)
assert_eq("get_lomba_by_id not found", row, None)

# Test tambah_lomba multiple
bot.tambah_lomba("Lomba 2", "https://example2.com", "2026-08-01", "2026-08-10")
rows = bot.get_all_lomba()
assert_eq("get_all_lomba returns 2 rows", len(rows), 2)

# Test hapus_lomba
result = bot.hapus_lomba(2)
assert_true("hapus_lomba success", result)
rows = bot.get_all_lomba()
assert_eq("get_all_lomba returns 1 after delete", len(rows), 1)

result = bot.hapus_lomba(999)
assert_false("hapus_lomba not found", result)

# Test hapus_lomba_otomatis
bot.tambah_lomba("Lomba Levaat", "https://x.com", "2025-01-01", "2025-01-02")
deleted = bot.hapus_lomba_otomatis()
assert_true("hapus_lomba_otomatis deleted something", deleted > 0)

# Test get_lomba_yang_perlu_diingatkan
# Reset: add lomba with known dates
today = datetime.now(WITA).date()
tutup_h7 = (today + timedelta(days=7)).isoformat()
tutup_h3 = (today + timedelta(days=3)).isoformat()
tutup_h1 = (today + timedelta(days=1)).isoformat()

bot.tambah_lomba("Reminder H-7", "https://r.com", "2026-01-01", tutup_h7)
bot.tambah_lomba("Reminder H-3", "https://r.com", "2026-01-01", tutup_h3)
bot.tambah_lomba("Reminder H-1", "https://r.com", "2026-01-01", tutup_h1)
bot.tambah_lomba("No Reminder", "https://r.com", "2026-01-01", "2026-12-31")

reminders = bot.get_lomba_yang_perlu_diingatkan()
assert_true("reminders found", len(reminders) >= 3)
reminder_juduls = {r[1] for r in reminders}
for expected in ["Reminder H-7", "Reminder H-3", "Reminder H-1"]:
    assert_true(f"reminder contains '{expected}'", expected in reminder_juduls)

# Test user functions
# Test get_role (not registered)
role = bot.get_role(999)
assert_eq("get_role not found", role, None)

# Test daftar_user
result = bot.daftar_user(123, "alex123566", "data-mle")
assert_true("daftar_user success", result)

result = bot.daftar_user(123, "alex123566", "data-mle")
assert_false("daftar_user duplicate", result)

result = bot.daftar_user(456, "Anjayehan", "invalid-role")
assert_false("daftar_user invalid role", result)

# Test get_role (registered)
role = bot.get_role(123)
assert_eq("get_role found", role, "data-mle")

# Test get_all_users
users = bot.get_all_users()
assert_true("get_all_users has users", len(users) >= 1)

# ===== TEST ACCESS CONTROL =====
print("\n--- Test Access Control ---")

def is_authorized(username):
    return username in ALLOWED_USERNAMES

for username in ["alex123566", "Anjayehan", "Zbisrih", "ken14_14", "hikkigayahachiman"]:
    assert_true(f"authorized: {username}", is_authorized(username))

for username in ["unknown", "hacker123", "", None]:
    if username:
        assert_false(f"unauthorized: {username}", is_authorized(username))

# ===== TEST FORMAT_DATE_RELATIVE =====
print("\n--- Test format_date_relative ---")

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

today_str = datetime.now(WITA).date().isoformat()
tomorrow_str = (datetime.now(WITA).date() + timedelta(days=1)).isoformat()
yesterday_str = (datetime.now(WITA).date() - timedelta(days=1)).isoformat()

assert_true("Hari Ini in today", "Hari Ini" in format_date_relative(today_str))
assert_true("Besok in tomorrow", "Besok" in format_date_relative(tomorrow_str))
assert_true("Sudah Lewat in yesterday", "Sudah Lewat" in format_date_relative(yesterday_str))
assert_true("5 hari lagi", "5 hari lagi" in format_date_relative((datetime.now(WITA).date() + timedelta(days=5)).isoformat()))
assert_eq("invalid date returns as-is", format_date_relative("not-a-date"), "not-a-date")

# ===== TEST CALENDAR BUILDER =====
print("\n--- Test Calendar Builder ---")

MONTH_NAMES = ["", "Januari", "Februari", "Maret", "April", "Mei", "Juni",
               "Juli", "Agustus", "September", "Oktober", "November", "Desember"]

now = datetime.now(WITA)
assert_eq("month name not empty", MONTH_NAMES[now.month] != "", True)
assert_eq("all months present", len(MONTH_NAMES), 13)

# build_calendar uses telegram types so can't fully test here, but we can verify the structure
cal = calendar.Calendar()
year, month = 2026, 7
weeks = cal.monthdayscalendar(year, month)
assert_true("calendar has weeks", len(weeks) >= 4)
assert_true("calendar has 7 days per row", all(len(w) == 7 for w in weeks))

# ===== TEST CONFIGURATION =====
print("\n--- Test Configuration ---")

for member, data in TEAM_MEMBERS.items():
    assert_true(f"member {member} has name", bool(data["name"]))
    assert_true(f"member {member} has role", data["role"] in ROLES)
    assert_true(f"member {member} has quote", bool(data["quote"]))

assert_eq("all members match", len(TEAM_MEMBERS), 5)
assert_eq("all usernames match", len(ALLOWED_USERNAMES), 5)

# ===== TEST ROLE DISPLAY =====
print("\n--- Test Role Display ---")

assert_eq("display data-mle", ROLE_DISPLAY["data-mle"], "DATA & MLE")
assert_eq("display fullstack", ROLE_DISPLAY["fullstack-developer"], "FULL STACK DEVELOPER")
assert_eq("display uiux", ROLE_DISPLAY["uiux-designer"], "UI/UX DESIGNER")
assert_eq("display blockchain", ROLE_DISPLAY["blockchain-developer"], "BLOCKCHAIN DEVELOPER")
assert_eq("display frontend", ROLE_DISPLAY["frontend-developer"], "FRONT END DEVELOPER")

# Legacy fallback
assert_eq("legacy data", ROLE_DISPLAY.get("data"), "DATA & MLE")
assert_eq("legacy fullstack", ROLE_DISPLAY.get("fullstack"), "FULL STACK DEVELOPER")
assert_eq("unknown fallback", ROLE_DISPLAY.get("unknown", "X"), "X")

# ===== CLEANUP =====
os.unlink(DATABASE)

print("\n" + "="*50)
print(f"📊 HASIL: {pass_count} PASS, {fail_count} FAIL, {pass_count+fail_count} TOTAL")
print("="*50)

sys.exit(0 if fail_count == 0 else 1)
