import streamlit as st
import telebot
import os
import json
import threading
from huggingface_hub import HfApi

# --- TOKEN & ID KAMU ---
TOKEN = "8409698507:AAFAAceW1p-OFpnYxLamqW7RXCKz7bKC3w8"
ADMIN_ID = 5422932688
# Ganti dengan nama Space lama kamu buat simpan database
# (Render punya internet, jadi dia BISA akses database di HF)
SPACE_REPO = "rfsneal/gudang-file-baru" 

bot = telebot.TeleBot(TOKEN)
DB_FILE = "database.json"

# Kita pakai Token HF dari Environment Variable nanti di Render
# Biar aman dan bisa akses database
HF_TOKEN = os.environ.get("HF_TOKEN")

# --- DATABASE SYSTEM (Tetap Pakai HF sebagai Gudang Data) ---
def load_db():
    try:
        api = HfApi()
        # Download database dari Hugging Face
        api.hf_hub_download(repo_id=SPACE_REPO, filename=DB_FILE, local_dir=".", repo_type="space", token=HF_TOKEN)
        with open(DB_FILE, 'r') as f: return json.load(f)
    except Exception as e:
        print(f"Gagal load DB (Mungkin baru): {e}")
        return {}

def save_db(data):
    # Simpan lokal
    with open(DB_FILE, 'w') as f: json.dump(data, f)
    # Upload ke Hugging Face (Backup)
    try:
        if HF_TOKEN:
            api = HfApi()
            api.upload_file(
                path_or_fileobj=DB_FILE, 
                path_in_repo=DB_FILE, 
                repo_id=SPACE_REPO, 
                repo_type="space", 
                token=HF_TOKEN, 
                commit_message="AutoSave from Render"
            )
    except Exception as e: 
        print(f"Gagal upload DB: {e}")

# --- PERINTAH BOT ---
@bot.message_handler(commands=['start'])
def sapa(message):
    bot.reply_to(message, "👋 HALO BOS! Bot sudah pindah ke Render! Internet Lancar Jaya.")

@bot.message_handler(commands=['simpan'])
def simpan(message):
    if message.from_user.id != ADMIN_ID: return
    if not message.reply_to_message:
        bot.reply_to(message, "❌ Reply file dulu!")
        return
    
    try:
        nama = message.text.split()[1].lower()
        msg = message.reply_to_message
        
        file_id = None
        if msg.document: file_id = msg.document.file_id
        elif msg.video: file_id = msg.video.file_id
        elif msg.photo: file_id = msg.photo[-1].file_id
        elif msg.audio: file_id = msg.audio.file_id
        
        if file_id:
            db = load_db()
            db[nama] = file_id
            save_db(db)
            bot.reply_to(message, f"✅ AMAN! File disimpan: `{nama}`")
        else:
            bot.reply_to(message, "❌ Jenis file tidak didukung.")
    except:
        bot.reply_to(message, "❌ Format: /simpan nama")

@bot.message_handler(commands=['get'])
def ambil(message):
    try:
        nama = message.text.split()[1].lower()
        db = load_db()
        if nama in db:
            bot.send_document(message.chat.id, db[nama], caption=f"📦 Nih pesananmu: {nama}")
        else:
            bot.reply_to(message, "❌ Gak nemu file itu.")
    except: return

# --- JANTUNG BOT ---
def run_bot():
    print("🚀 Bot Telebot Mulai...")
    bot.infinity_polling()

if __name__ == "__main__":
    st.title("🤖 SERVER BOT RENDER")
    st.write("Status: **ONLINE** 🟢")
    
    if "bot_active" not in st.session_state:
        st.session_state.bot_active = True
        t = threading.Thread(target=run_bot, daemon=True)
        t.start()
