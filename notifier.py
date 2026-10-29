import os
import json
from datetime import datetime, timedelta
import urllib.request
import urllib.parse

BOT_TOKEN = os.getenv("9247475179:AAEd-8aH42Cl1HxaA_cF7nEaoTBn9OaVWJI")
MY_TELEGRAM_ID = os.getenv("886620460")
SEMESTER_START = datetime(2026, 10, 26)
DAY_NAMES_MAP = {0: "Понедельник", 1: "Вторник", 2: "Среда", 3: "Четверг", 4: "Пятница", 5: "Суббота"}

def load_schedule():
    with open('schedule.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def get_week_num(target_date):
    diff_days = (target_date - SEMESTER_START).days
    if diff_days < 0:
        return 1
    return ((diff_days // 7) % 4) + 1

def calculate_lesson_end(start_time_str):
    h, m = map(int, start_time_str.split(':'))
    total = h * 60 + m + 85
    return f"{str(total // 60 % 24).zfill(2)}:{str(total % 60).zfill(2)}"

def send_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = urllib.parse.urlencode({"chat_id": MY_TELEGRAM_ID, "text": text, "parse_mode": "Markdown"}).encode()
    req = urllib.request.Request(url, data=data)
    try:
        with urllib.request.urlopen(req) as response:
            return response.read()
    except Exception as e:
        print(f"Ошибка отправки в Telegram: {e}")

def main():
    now = datetime.now()
    js_day = now.weekday()
    
    if js_day == 6:
        send_telegram("☀️ **Доброе утро!**\n\n🎉 Сегодня воскресенье! Пар нет, полный чилл.")
        return

    week_num = str(get_week_num(now))
    day_name = DAY_NAMES_MAP[js_day]
    
    try:
        schedule = load_schedule()
        week_schedule = schedule.get(week_num, [])
        day_data = next((d for d in week_schedule if d["day"] == day_name), None)
        lessons = day_data.get("lessons", []) if day_data else []
    except Exception as e:
        lessons = []

    count = len(lessons)
    if count >= 4:
        vibe = "🔥 **Хардкор день!** Набирайся сил."
    elif count >= 2:
        vibe = "⚡ **Обычный рабочий день.**"
    elif count == 1:
        vibe = "☕ **Чилловый день**, всего одна пара!"
    else:
        vibe = "🎉 **Пар по расписанию нет!**"

    text = f"☀️ **Доброе утро! Расписание на сегодня ({now.strftime('%d.%m')})**\n"
    text += f"{vibe}\n\n"

    if lessons:
        for l in lessons:
            end_time = l.get('endTime', calculate_lesson_end(l['time']))
            room = f"📍 {l['room']}" if l.get('room') else ""
            text += f"⏰ `{l['time']} - {end_time}` | **{l['title']}** ({l['type']}) {room}\n"
    else:
        text += "Свободное время!\n"

    send_telegram(text)

if __name__ == "__main__":
    main()
