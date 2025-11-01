print("🤖 Telegram Bot Started!")
import os
import time
os.environ['NO_PROXY'] = 'api.telegram.org'

import datetime
import re
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = "8442410256:AAF8rRzh-MehRWYXMT5qP7q383mOj2woel8"
ADMIN_CHAT_ID = 5846819259
CHANNEL_USERNAME = "@eggssssi115"

blacklist = set()
user_stats = {}
daily_stats = {}
awaiting_ban = False

async def check_subscription(user_id, context):
    try:
        chat_member = await context.bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return chat_member.status in ['creator', 'administrator', 'member']
    except:
        return False

async def is_channel_admin(user_id, context):
    try:
        chat_admins = await context.bot.get_chat_administrators(CHANNEL_USERNAME)
        admin_ids = [admin.user.id for admin in chat_admins]
        return user_id in admin_ids
    except:
        return False

def update_user_stats(user_id, username, first_name):
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    if user_id not in user_stats:
        user_stats[user_id] = {"username": username, "first_name": first_name, "actions": 0}
    user_stats[user_id]["actions"] += 1
    daily_stats[today] = daily_stats.get(today, 0) + 1

async def ban_user_by_id(user_id, context):
    if user_id == ADMIN_CHAT_ID:
        return False, "❌ Нельзя забанить главного администратора"
    blacklist.add(user_id)
    
    try:
        await context.bot.send_message(user_id, "🚫 Вы были заблокированы в боте. Доступ ограничен.")
    except:
        pass
    
    return True, f"🚫 Пользователь ID: {user_id} забанен"

async def ban_user_by_username(username, context):
    try:
        if username.startswith('@'):
            username = username[1:]
        
        user = await context.bot.get_chat(f"@{username}")
        user_id = user.id
        
        if user_id == ADMIN_CHAT_ID:
            return False, "❌ Нельзя забанить главного администратора"
            
        blacklist.add(user_id)
        
        try:
            await context.bot.send_message(user_id, "🚫 Вы были заблокированы в боте. Доступ ограничен.")
        except:
            pass
            
        return True, f"🚫 Пользователь @{username} (ID: {user_id}) забанен"
    except Exception:
        return False, f"❌ Не удалось найти пользователя @{username}"

async def unban_user_by_id(user_id, context):
    if user_id in blacklist:
        blacklist.remove(user_id)
        
        try:
            await context.bot.send_message(user_id, "✅ Вы были разблокированы в боте. Доступ восстановлен.")
        except:
            pass
            
        return f"✅ Пользователь ID: {user_id} разбанен"
    return "❌ Пользователь не найден в ЧС"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    
    if user.id in blacklist:
        await update.message.reply_text('🚫 Вы заблокированы в этом боте. Доступ к функциям ограничен.\n\nДля разблока обратитесь к администратору.')
        return

    update_user_stats(user.id, user.username, user.first_name)
    is_subscribed = await check_subscription(user.id, context)
    if not is_subscribed:
        await update.message.reply_text(f'❌ Подпишись на канал: {CHANNEL_USERNAME}')
        return

    is_admin = await is_channel_admin(user.id, context) or user.id == ADMIN_CHAT_ID

    if is_admin:
        keyboard = [['📸 Фото', '🎥 Видео', '💬 Вопрос'], ['📊 Статистика', '🚫 Управление ЧС', '🆘 Помощь']]
    else:
        keyboard = [['📸 Фото', '🎥 Видео', '💬 Вопрос'], ['🆘 Помощь']]

    await update.message.reply_text(f'Привет {user.first_name}! ✅', reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
  if update.message.from_user.id in blacklist:
        await update.message.reply_text("🚫 Доступ запрещен")
        return
        
    user = update.message.from_user
    is_admin = await is_channel_admin(user.id, context) or user.id == ADMIN_CHAT_ID

    help_text = "🆘 ПОМОЩЬ:\n\n📸 Фото - Отправить фото админу\n🎥 Видео - Отправить видео админу\n💬 Вопрос - Задать вопрос админу\n🆘 Помощь - Показать это сообщение"

    if is_admin:
        help_text += "\n\n👑 АДМИН:\n📊 Статистика - Статистика бота\n🚫 Управление ЧС - Чёрный список"

    help_text += "\n\n💡 Просто нажми на нужную кнопку!"
    await update.message.reply_text(help_text)

async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id in blacklist:
        await update.message.reply_text("🚫 Доступ запрещен")
        return
        
    total_users = len(user_stats)
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    today_requests = daily_stats.get(today, 0)
    total_requests = sum(daily_stats.values())

    stats_text = f"📊 СТАТИСТИКА БОТА\n\n👥 Пользователей: {total_users}\n📨 Запросов сегодня: {today_requests}\n📨 Всего запросов: {total_requests}"
    await update.message.reply_text(stats_text)

async def blacklist_management(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id in blacklist:
        await update.message.reply_text("🚫 Доступ запрещен")
        return
        
    keyboard = [['🚫 Забанить', '📋 Список'], ['🔙 Назад']]
    await update.message.reply_text('🚫 Управление ЧС:\n\n• 🚫 Забанить - бан по ID, юзернейму или пересланному сообщению\n• 📋 Список - просмотр забаненных', reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))

async def show_blacklist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_channel_admin(update.message.from_user.id, context) and update.message.from_user.id != ADMIN_CHAT_ID:
        return

    if not blacklist:
        await update.message.reply_text('📝 ЧС пуст')
        return

    keyboard = []
    for user_id in list(blacklist)[:10]:
        try:
            user = await context.bot.get_chat(user_id)
            username = f"@{user.username}" if user.username else user.first_name
            button_text = f"✅ {username} (ID: {user_id})"
        except:
            button_text = f"✅ ID: {user_id}"
        keyboard.append([button_text])

    keyboard.append(['🔙 Назад'])

    await update.message.reply_text(f'📋 Забаненные ({len(blacklist)}):', reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    if user.id in blacklist:
        await update.message.reply_text("🚫 Вы заблокированы")
        return

    update_user_stats(user.id, user.username, user.first_name)
    is_subscribed = await check_subscription(user.id, context)
    if not is_subscribed:
        await update.message.reply_text(f'❌ Подпишись на канал: {CHANNEL_USERNAME}')
        return

    await update.message.reply_text('📸 Фото получено! Пересылаю админу...')
    await update.message.forward(ADMIN_CHAT_ID)

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    if user.id in blacklist:
        await update.message.reply_text("🚫 Вы заблокированы")
        return
    
    update_user_stats(user.id, user.username, user.first_name)
    is_subscribed = await check_subscription(user.id, context)
    if not is_subscribed:
        await update.message.reply_text(f'❌ Подпишись на канал: {CHANNEL_USERNAME}')
        return

    await update.message.reply_text('🎥 Видео получено! Пересылаю админу...')
    await update.message.forward(ADMIN_CHAT_ID)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    
    if user.id in blacklist:
        await update.message.reply_text("🚫 Вы заблокированы в этом боте")
        return
    update_user_stats(user.id, user.username, user.first_name)
    text = update.message.text
    is_subscribed = await check_subscription(user.id, context)
    if not is_subscribed:
        await update.message.reply_text(f'❌ Подпишись на канал: {CHANNEL_USERNAME}')
        return

    is_admin = await is_channel_admin(user.id, context) or user.id == ADMIN_CHAT_ID

    global awaiting_ban

    if is_admin and awaiting_ban and hasattr(update.message, 'forward_from') and update.message.forward_from:
        user_id = update.message.forward_from.id
        success, message = await ban_user_by_id(user_id, context)
        await update.message.reply_text(message)
        awaiting_ban = False
        return

    if text == '🔙 Назад':
        await start(update, context)
        return

    if text == '🆘 Помощь':
        await help_command(update, context)
        return

    if is_admin:
        if text == '🚫 Управление ЧС':
            await blacklist_management(update, context)
            return
        elif text == '🚫 Забанить':
            awaiting_ban = True
            await update.message.reply_text('Отправь для бана:\n• ID пользователя (цифры)\n• Юзернейм (с @ или без)\n• Пересланное сообщение от пользователя\n\nИли напиши "отмена" для отмены')
            return
        elif text == '📋 Список':
            await show_blacklist(update, context)
            return
        elif text == '📊 Статистика':
            await show_stats(update, context)
            return
        elif text.startswith('✅ '):
            match = re.search(r'ID: (\d+)', text)
            if match:
                user_id = int(match.group(1))
                message = await unban_user_by_id(user_id, context)
                await update.message.reply_text(message)
                await show_blacklist(update, context)
                return
        elif awaiting_ban:
            if text.lower() == 'отмена':
                awaiting_ban = False
                await blacklist_management(update, context)
                return
            elif text.isdigit():
                user_id = int(text)
                success, message = await ban_user_by_id(user_id, context)
                await update.message.reply_text(message)
                awaiting_ban = False
                return
            elif text.startswith('@') or (not text.isdigit() and len(text) > 3):
                success, message = await ban_user_by_username(text, context)
                await update.message.reply_text(message)
                awaiting_ban = False
                return

    if text == '📸 Фото':
        await update.message.reply_text('Отправь фото 📷')
    elif text == '🎥 Видео':
        await update.message.reply_text('Отправь видео 🎬')
    elif text == '💬 Вопрос':
        await update.message.reply_text('Напиши вопрос ✍️')
    else:
        await update.message.reply_text('✅ Сообщение отправлено админу!')
        await context.bot.send_message(ADMIN_CHAT_ID, f"💬 Сообщение от {user.first_name} (@{user.username}):\n{text}")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Ошибка: {context.error}")

def main():
    while True:
        try:
            print("🔄 Запуск бота...")
            application = Application.builder().token(BOT_TOKEN).build()

            application.add_handler(CommandHandler("start", start))
            application.add_handler(CommandHandler("help", help_command))
            application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
            application.add_handler(MessageHandler(filters.VIDEO, handle_video))
            application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
            application.add_error_handler(error_handler)

            print("✅ Бот запущен!")
            print("📱 Проверь в Telegram: /start")
            application.run_polling(drop_pending_updates=True)
            
        except Exception as e:
            print(f"💥 Ошибка соединения: {e}")
            print("🔄 Перезапуск через 30 секунд...")
            time.sleep(30)

if __name__ == '__main__':
    main()
