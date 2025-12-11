import os
import time
import threading
import requests
import xml.etree.ElementTree as ET
from flask import Flask

# =========================
# تنظیمات ربات
# =========================

BOT_TOKEN   = "8541225332:AAEf2ndNwokYM43Gq5NGl5tX-5aliicTe_4"
CHANNEL_ID  = "@Akhbar_Matni"

# دو منبع: عمومی + ورزشی
SOURCES = {
    "general": "https://www.khabaronline.ir/rss",
    "sports":  "https://www.khabaronline.ir/rss/tp/6"
}

CHECK_EVERY = 120   # هر ۲ دقیقه
sent_titles = set()  # جلوگیری از تکراری‌ها در طول اجرای فعلی

# =========================
# وب‌سرور کوچک برای Render
# =========================

app = Flask(name)

@app.route("/")
def home():
    return "Akhbar Matni bot is running ✅"

def run_server():
    # Render متغیر PORT را می‌فرستد، از همون استفاده می‌کنیم
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# =========================
# منطق ربات خبر
# =========================

def get_latest_item(url):
    """خواندن اولین خبر از RSS"""
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()

        root = ET.fromstring(r.content)
        item = root.find("./channel/item")

        if item is None:
            print("❌ Hich itemi peyda nashod.")
            return None, None

        title = item.find("title").text or ""
        desc_tag = item.find("description")
        desc = desc_tag.text if desc_tag is not None else ""

        return title.strip(), desc.strip()

    except Exception as e:
        print("❌ Error dar khandane RSS:", e)
        return None, None


def send_to_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": CHANNEL_ID,
        "text": text,
        "parse_mode": "HTML"
    }
    try:
        r = requests.post(url, data=data, timeout=10)
        if not r.ok:
            print("❌ Error ersal be Telegram:", r.text)
    except Exception as e:
        print("❌ Exception ersal be Telegram:", e)


def format_general(title, desc):
    return (
        f"📰 <b>{title}</b>\n\n"
        f"{desc}\n\n"
        "———————————————\n"
        "برای دریافت آخرین اخبار روز، کانال اخبار متنی را دنبال کنید 📰\n"
        "@Akhbar_Matni"
    )


def format_sports(title, desc):
    return (
        "🏅 <b>خبر ورزشی</b>\n\n"
        f"📰 <b>{title}</b>\n\n"
        f"{desc}\n\n"
        "———————————————\n"
        "برای دریافت آخرین اخبار روز، کانال اخبار متنی را دنبال کنید 📰\n"
        "@Akhbar_Matni"
    )


def bot_loop():
    global sent_titles
    print("🚀 Robot Akhbar Matni start shod...")

    while True:
        # اخبار عمومی
        title_g, desc_g = get_latest_item(SOURCES["general"])
        if title_g and title_g not in sent_titles:
            sent_titles.add(title_g)
            msg = format_general(title_g, desc_g)
            send_to_telegram(msg)
            print("✔ General ersal shod:", title_g)

        # اخبار ورزشی
        title_s, desc_s = get_latest_item(SOURCES["sports"])
        if title_s and title_s not in sent_titles:
            sent_titles.add(title_s)
            msg = format_sports(title_s, desc_s)
            send_to_telegram(msg)
            print("✔ Sports ersal shod:", title_s)

        print("⏳ Checking again...")
        time.sleep(CHECK_EVERY)


if name == "main":
    # یک Thread برای وب‌سرور (برای Render Web Service)
    server_thread = threading.Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()

    # حلقه اصلی ربات
    bot_loop()