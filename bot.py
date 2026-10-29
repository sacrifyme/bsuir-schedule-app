import os
import json
import asyncio
from datetime import datetime, timedelta
import aiogram
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

# Токен берем из переменных окружения (настраивается на Render)
BOT_TOKEN = os.getenv("BOT_TOKEN")
# Твой Telegram ID (чтобы бот знал, кому слать утренние пуши)
MY_TELEGRAM_ID = os.getenv("MY_TELEGRAM_ID")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Дата начала семестра (26 октября 2026 года)
SEMESTER_START = datetime(2026, 10, 30)

def load_schedule():
    with open('schedule.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def get_week_num(target_date):
    diff_days = (target_date - SEMESTER_START).days
    if diff_days < 0:
        return 1
    return ((diff_days // 7) % 4) + 1

def generate_daily_summary(target_date):
    week_num = str(get_week_num(target_date))
    days_map = {0: "Понедельник", 1: "Вторник", 2: "Среда", 3: "Четверг", 4: "Пятница", 5: "Суббота"}

    js_day = target_date.weekday()
    if js_day == 6:
        return "🎉 Воскресенье! Пар нет, чилл полнейший."

    day_name = days_map[js_day]
    schedule = load_schedule()

    week_schedule = schedule.get(week_num, [])
    day_data = next((d for d in week_schedule if d["day"] == day_name), None)

    if not day_data or not day_data.get("lessons"):
        return f"📅 **{day_name}** ({target_date.strftime('%d.%m')}):\nПар нет! Можно отдыхать."

    lessons = day_data["lessons"]
    count = len(lessons)

    # Оценка дня
    if count >= 4:
        vibe = "🔥 **Хардкор день!** Набирайся сил."
    elif count >= 2:
        vibe = "⚡ **Обычный рабочий день.**"
    else:
        vibe = "☕ **Чилловый день**, всего одна пара!"

    text = f"📅 **Расписание на {day_name} ({target_date.strftime('%d.%m')})**\n"
    text += f"{vibe}\n\n"

    for l in lessons:
        end_time = l.get('endTime', '---')
        room_info = f"📍 {l['room']}" if l.get('room') else ""
        text += f"⏰ `{l['time']} - {end_time}` | **{l['title']}** ({l['type']}) {room_info}\n"

    return text

@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.answer("Салам! Я твой бот-расписание. Напиши /today или /tomorrow чтобы узнать пары.")

@dp.message(Command("today"))
async def today_cmd(message: types.Message):
    summary = generate_daily_summary(datetime.now())
    await message.answer(summary, parse_mode="Markdown")

@dp.message(Command("tomorrow"))
async def tomorrow_cmd(message: types.Message):
    tomorrow_date = datetime.now() + timedelta(days=1)
    summary = generate_daily_summary(tomorrow_date)
    await message.answer(summary, parse_mode="Markdown")

# Фоновая задача: утренняя рассылка в 08:00
async def morning_scheduler():
    while True:
        now = datetime.now()
        # Время рассылки — 08:00 утр
        target = now.replace(hour=8, minute=0, second=0, microsecond=0)
        if now >= target:
            target += timedelta(days=1)

        # Ждем до 8 утра
        await asyncio.sleep((target - now).total_seconds())

        if MY_TELEGRAM_ID:
            try:
                summary = generate_daily_summary(datetime.now())
                await bot.send_message(chat_id=MY_TELEGRAM_ID, text=f"☀️ **Доброе утро!**\n\n{summary}", parse_mode="Markdown")
            except Exception as e:
                print(f"Ошибка отправки: {e}")

async def main():
    asyncio.create_task(morning_scheduler())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())