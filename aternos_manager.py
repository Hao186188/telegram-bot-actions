import os
import asyncio
import datetime
import requests
from playwright.async_api import async_playwright

# --- CẤU HÌNH LẤY TỪ GITHUB SECRETS ---
TELEGRAM_TOKEN = os.getenv("TG_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TG_CHAT_ID")

# Kiểm tra nếu thiếu cấu hình
if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
    print("!! LỖI: Thiếu cấu hình TG_TOKEN hoặc TG_CHAT_ID trong môi trường.")
    exit()

# --- CẤU HÌNH HỆ THỐNG ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USER_DATA_DIR = os.path.join(BASE_DIR, "aternos_auth")
ATERNOS_URL = "https://aternos.org/server/"
HEADLESS_MODE = True 

def send_telegram(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
        requests.post(url, data=data)
    except Exception as e:
        print(f"Lỗi gửi Telegram: {e}")

async def run_server_logic(page):
    try:
        await page.goto(ATERNOS_URL, wait_until="domcontentloaded", timeout=60000)
        
        if "login" in page.url:
            send_telegram("⚠️ *Cảnh báo:* Aternos yêu cầu đăng nhập lại thủ công!")
            return

        status_locator = page.locator(".statuslabel-label")
        await status_locator.wait_for(state="visible", timeout=30000)
        status = (await status_locator.inner_text()).strip()

        if "Offline" in status:
            await page.click("#start", timeout=10000)
            try:
                confirm_btn = page.locator("#confirm, .btn-success")
                await confirm_btn.wait_for(state="visible", timeout=15000)
                await confirm_btn.click()
                send_telegram("✅ *Thành công:* Server đang trong hàng chờ/khởi động!")
            except:
                send_telegram("🚀 *Hệ thống:* Server đang bắt đầu chạy!")
        elif "Online" in status:
            print("Server đã mở.")
        
    except Exception as e:
        send_telegram(f"❌ *Lỗi Hệ Thống:* {str(e)[:100]}")

async def main_controller():
    send_telegram("🤖 *Bot khởi động:* Bắt đầu giám sát Aternos...")
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            USER_DATA_DIR,
            headless=HEADLESS_MODE,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            args=["--disable-blink-features=AutomationControlled"]
        )
        page = context.pages[0] if context.pages else await context.new_page()

        while True:
            await run_server_logic(page)
            await asyncio.sleep(600) # 10 phút/chu kỳ

if __name__ == "__main__":
    if not os.path.exists(USER_DATA_DIR):
        os.makedirs(USER_DATA_DIR)
    asyncio.run(main_controller())