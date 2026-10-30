import os
import json
from datetime import datetime
import urllib.request
import urllib.parse

BOT_TOKEN = os.getenv("BOT_TOKEN")
MY_TELEGRAM_ID = os.getenv("MY_TELEGRAM_ID")
SEMESTER_START = datetime(2026, 10, 26)
DAY_NAMES_MAP = {0: "Понедельник", 1: "Вторник", 2: "Среда", 3: "Четверг", 4: "Пятница", 5: "Суббота"}

def load_json_file(filename):
    if not os.path.exists(filename):
        return {}
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}

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
    date_str = now.strftime('%Y-%m-%d')
    
    if js_day == 6:
        send_telegram("☀️ **Доброе утро!**\n\n🎉 Сегодня воскресенье! Пар нет, полный чилл.")
        return

    week_num = str(get_week_num(now))
    day_name = DAY_NAMES_MAP[js_day]
    
    schedule = load_json_file('schedule.json')
    week_schedule = schedule.get(week_num, [])
    day_data = next((d for d in week_schedule if d["day"] == day_name), None)
    lessons = day_data.get("lessons", []) if day_data else []

    # Загружаем кастомные события (формат: дата -> список событий/отмен)
    # Пример структуры custom_events.json:
    # {
    #   "2026-10-30": [
    #     {"time": "09:50", "title": "Поход к врачу", "type": "Личное", "cancel_lesson_time": "09:50"}
    #   ]
    # }
    custom_data = load_json_file('custom_events.json')
    todays_custom = custom_data.get(date_str, [])

    # Ищем отмененные пары на сегодня по времени
    cancelled_times = [e.get("cancel_lesson_time") for e in todays_custom if e.get("cancel_lesson_time")]

    text = f"☀️ **Доброе утро! Расписание на сегодня ({now.strftime('%d.%m')})**\n\n"

    all_items = []

    # Добавляем пары, проверяя, не отменил ли ты их
    for l in lessons:
        l_time = l['time']
        end_time = l.get('endTime', calculate_lesson_end(l_time))
        is_cancelled = l_time in cancelled_times
        
        all_items.append({
            "time": l_time,
            "end_time": end_time,
            "title": l['title'],
            "type": l['type'],
            "room": l.get('room', ''),
            "cancelled": is_cancelled
        })

    # Добавляем кастомные события (которые не отменяют пары, а идут плюсом)
    for c in todays_custom:
        if not c.get("cancel_lesson_time"): # если это не отмена пары, а отдельное дело
            all_items.append({
                "time": c.get('time', '00:00'),
                "end_time": c.get('endTime', ''),
                "title": c['title'],
                "type": c.get('type', 'Событие'),
                "room": c.get('room', ''),
                "cancelled": False,
                "is_custom": True
            })

    # Сортируем всё по времени
    all_items.sort(key=lambda x: x['time'])

    if not all_items:
        text += "🎉 На сегодня ничего нет! Отдыхай.\n"
    else:
        for item in all_items:
            t_range = f"`{item['time']}`" if not item['end_time'] else f"`{item['time']} - {item['end_time']}`"
            room_info = f"📍 {item['room']}" if item.get('room') else ""
            
            if item.get('cancelled'):
                text += f"❌ ~~{t_range} | **{item['title']}** ({item['type']})~~ ➔ **Сюда можешь сегодня не идти!** (отменено)\n"
            elif item.get('is_custom'):
                text += f"⭐ {t_range} | **{item['title']}** ({item['type']}) {room_info} *(Личное дело)*\n"
            else:
                text += f"⏰ {t_range} | **{item['title']}** ({item['type']}) {room_info}\n"

    send_telegram(text)

if __name__ == "__main__":
    main()
