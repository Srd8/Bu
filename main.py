import telebot
from telebot import types
import re
import time
import random

# ⚠️ ضع التوكن الخاص ببوتك هنا
TOKEN = "5494778203:AAFrPy4BiP3jsmYBCjGl0YdtM9KwEunXvqg"
bot = telebot.TeleBot(TOKEN)

# 👑 بيانات المطور الأساسية
DEVELOPER_ID = 5220076610
DEVELOPER_USERNAME = "@njr10r"

# قائمة بالكلمات المحظورة
PROHIBITED_WORDS = [
    "سكس", "اباحي", "شرموطه", "قحبه", "منيكه", "كس", "زب", 
   
]

# كلمات لعبة التفكيك
PUZZLE_WORDS = {"تيليجرام": "م ا ر ج ي ل ت", "بايثون": "ن و ث ي ا ب", "العراق": "ق ا ر ع ل ا", "برمجة": "ة ج م ر ب"}

# متغيرات الألعاب لتتبع الحالات
secret_numbers = {}
current_puzzles = {}
user_messages = {}
user_warnings = {}

# قاموس لحفظ بيانات ألعاب XO النشطة
# الهيكل: {chat_id: { 'board': [...], 'player_x': id, 'player_o': id, 'turn': id }}
xo_games = {}

def is_admin(chat_id, user_id):
    if user_id == DEVELOPER_ID: return True
    try:
        chat_member = bot.get_chat_member(chat_id, user_id)
        return chat_member.status in ['creator', 'administrator']
    except Exception: return False

# 1. أمر /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "🖤✨ **أهلاً بك في بوت VIP المطور للحماية والترفيه!**\n\n"
        "🎮 **أدوات الترفيه والألعاب:**\n"
        "• `العاب` : لعرض قائمة الألعاب.\n"
        "• `xo` أو `اكس او` : لبدء تحدي X-O بالأزرار التفاعلية!\n\n"
        f"👑 **المطور الرسمي:** {DEVELOPER_USERNAME}"
    )
    bot.reply_to(message, welcome_text, parse_mode="Markdown")

# 2. عرض معلومات المطور
@bot.message_handler(func=lambda message: message.text == "المطور")
def show_developer(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text="💬 تواصل مع المطور", url=f"t.me/{DEVELOPER_USERNAME.replace('@', '')}"))
    bot.reply_to(message, f"👑 **مطور البوت الرسمي:** {DEVELOPER_USERNAME}\n🆔 **آيدي المطور:** `{DEVELOPER_ID}`", reply_markup=markup, parse_mode="Markdown")

# 3. عرض قائمة الألعاب
@bot.message_handler(func=lambda message: message.text == "العاب")
def show_games_list(message):
    games_text = (
        "🎮 **قائمة الألعاب والترفيه المتاحة:**\n\n"
        "1️⃣ **لعبة حجر ورقة مقص:** أرسل (حجر أو ورقة أو مقص).\n"
        "2️⃣ **لعبة التخمين:** أرسل كلمة `خمن` للبدء.\n"
        "3️⃣ **لعبة التفكيك:** أرسل كلمة `تفكيك` للبدء.\n"
        "4️⃣ **لعبة XO التفاعلية:** أرسل كلمة `xo` أو `اكس او` للعب بالأزرار المتطورة!\n"
        "5️⃣ **نسبة الحب:** أرسل `نسبة الحب` بالرد على أي عضو."
    )
    bot.reply_to(message, games_text, parse_mode="Markdown")

# --- [ قسم لعبة X-O بالأزرار التفاعلية ] ---

def create_xo_board(board):
    """دالة لإنشاء لوحة أزرار XO بناءً على مصفوفة اللعبة الحالية"""
    markup = types.InlineKeyboardMarkup()
    row = []
    for i in range(9):
        display_text = board[i] if board[i] in ['❌', '⭕'] else " "
        row.append(types.InlineKeyboardButton(text=display_text, callback_data=f"xo_click_{i}"))
        if len(row) == 3:
            markup.row(*row)
            row = []
    return markup

def check_xo_winner(b):
    """دالة لفحص الفائز في لعبة XO"""
    win_coords = [(0,1,2), (3,4,5), (6,7,8), (0,3,6), (1,4,7), (2,5,8), (0,4,8), (2,4,6)]
    for coord in win_coords:
        if b[coord[0]] == b[coord[1]] == b[coord[2]] and b[coord[0]] in ['❌', '⭕']:
            return b[coord[0]]
    if all(x in ['❌', '⭕'] for x in b):
        return "تعادل"
    return None

@bot.message_handler(func=lambda message: message.text in ["xo", "اكس او", "اكس أو"])
def start_xo_game(message):
    chat_id = message.chat.id
    if chat_id in xo_games:
        bot.reply_to(message, "⚠️ هناك مباراة قائمة بالفعل في هذا الكروب! أنهوها أولاً أو انتظروا قليلاً.")
        return
    
    # إعداد مباراة جديدة، اللاعب الأول يصبح تلقائياً صاحب الرمز ❌
    xo_games[chat_id] = {
        'board': [str(i) for i in range(9)],
        'player_x': message.from_user.id,
        'player_x_name': message.from_user.first_name,
        'player_o': None,
        'player_o_name': "بانتظار منافس...",
        'turn': message.from_user.id
    }
    
    markup = types.InlineKeyboardMarkup()
    join_btn = types.InlineKeyboardButton(text="🤝 انضمام للتحدي (⭕)", callback_data="xo_join")
    markup.add(join_btn)
    
    bot.send_message(chat_id, f"🎮 **تم فتح مباراة X-O جديدة!**\n\n👤 **اللاعب الأول (❌):** {message.from_user.first_name}\n🌐 بانتظار لاعب ثانٍ للضغط على زر الانضمام أدناه للبدء بـ (⭕).", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith('xo_'))
def handle_xo_callback(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    user_name = call.from_user.first_name
    
    if chat_id not in xo_games:
        bot.answer_callback_query(call.id, "❌ انتهت هذه اللعبة أو لم تعد صالحة.", show_alert=True)
        return
        
    game = xo_games[chat_id]

    # انضمام اللاعب الثاني
    if call.data == "xo_join":
        if user_id == game['player_x']:
            bot.answer_callback_query(call.id, "❌ لا يمكنك اللعب ضد نفسك يا بطل!", show_alert=False)
            return
        if game['player_o'] is not None:
            bot.answer_callback_query(call.id, "❌ اكتمل عدد اللاعبين بالفعل!", show_alert=False)
            return
            
        game['player_o'] = user_id
        game['player_o_name'] = user_name
        
        bot.edit_message_text(
            chat_id=chat_id, message_id=call.message.message_id,
            text=f"🔥 **بدأت المعركة الآن!**\n\n❌ {game['player_x_name']}\n⭕ {game['player_o_name']}\n\nدور اللاعب الحركي الآن: ❌ [{game['player_x_name']}]",
            reply_markup=create_xo_board(game['board'])
        )
        return

    # معالجة الضغط على مربعات اللعب
    if call.data.startswith("xo_click_"):
        if game['player_o'] is None:
            bot.answer_callback_query(call.id, "❌ انتظر انضمام اللاعب الثاني أولاً!", show_alert=False)
            return
        if user_id != game['player_x'] and user_id != game['player_o']:
            bot.answer_callback_query(call.id, "❌ هذه اللعبة ليست لك! أرسل 'xo' لفتح لعبة جديدة.", show_alert=False)
            return
        if user_id != game['turn']:
            bot.answer_callback_query(call.id, "⏳ ليس دورك الآن! انتظر الخصم ليتحرك.", show_alert=False)
            return
            
        cell = int(call.data.split('_')[2])
        if game['board'][cell] in ['❌', '⭕']:
            bot.answer_callback_query(call.id, "❌ هذا المربع محجوز! اختر مكاناً آخر.", show_alert=False)
            return
            
        # وضع الرمز المناسب
        current_sign = '❌' if user_id == game['player_x'] else '⭕'
        game['board'][cell] = current_sign
        
        # فحص الفوز والتعادل
        winner = check_xo_winner(game['board'])
        if winner:
            if winner == "تعادل":
                end_text = f"🤝 **انتهت المباراة بالتعادل!**\n\n• بين {game['player_x_name']} و {game['player_o_name']}"
            else:
                winner_name = game['player_x_name'] if winner == '❌' else game['player_o_name']
                end_text = f"🎉 **مبروك الفوز!**\n\n🏆 المنتصر هو: {winner_name} ({winner})"
                
            bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text=end_text, reply_markup=create_xo_board(game['board']))
            del xo_games[chat_id]
            return
            
        # تغيير الدور
        game['turn'] = game['player_o'] if game['turn'] == game['player_x'] else game['player_x']
        next_player_name = game['player_x_name'] if game['turn'] == game['player_x'] else game['player_o_name']
        next_sign = '❌' if game['turn'] == game['player_x'] else '⭕'
        
        bot.edit_message_text(
            chat_id=chat_id, message_id=call.message.message_id,
            text=f"🎮 **مباراة X-O مستمرة:**\n\n❌ {game['player_x_name']}\n⭕ {game['player_o_name']}\n\nالدور الحالي لـ: {next_sign} [{next_player_name}]",
            reply_markup=create_xo_board(game['board'])
        )

# --- [ نظام الترحيب المطور + التحقق البشري ] ---
@bot.message_handler(content_types=['new_chat_members'])
def welcome_and_show_info(message):
    chat_id = message.chat.id
    for member in message.new_chat_members:
        try: bot.restrict_chat_member(chat_id, member.id, can_send_messages=False)
        except Exception: pass
        username = f"@{member.username}" if member.username else "لا يوجد معرف"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(text="✅ اضغط هنا لإثبات إنك إنسان", callback_data=f"verify_{member.id}"))
        welcome_msg = f"🖤✨ **عضو جديد انضم!**\n\n👤 **الاسم:** {member.first_name}\n🆔 **الآيدي:** `{member.id}`\n🌐 **المعرف:** {username}\n\n⚠️ اضغط على الزر أدناه لتفعيل صلاحية الكلام!"
        bot.send_message(chat_id, welcome_msg, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith('verify_'))
def handle_verification(call):
    user_id = call.from_user.id
    target_user_id = int(call.data.split('_')[1])
    if user_id == target_user_id:
        try:
            bot.restrict_chat_member(call.message.chat.id, user_id, can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True)
            bot.answer_callback_query(call.id, "✨ تم التحقق بنجاح!", show_alert=True)
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except Exception: pass
    else: bot.answer_callback_query(call.id, "❌ ليس مخصصاً لك!", show_alert=False)

# 4. أمر ايدي لعرض المعلومات الكاملة مع الصورة
@bot.message_handler(func=lambda message: message.text in ["معلوماتي", "ايدي", "ايديه", "id", "ID"])
def get_user_info(message):
    user = message.from_user
    photos = bot.get_user_profile_photos(user.id)
    username = f"@{user.username}" if user.username else "لا يوجد"
    info_text = f"👤 **الاسم:** {user.first_name}\n🆔 **الآيدي:** `{user.id}`\n🌐 **المعرف:** {username}"
    if photos.total_count > 0:
        bot.send_photo(message.chat.id, photos.photos[0][0].file_id, caption=info_text, parse_mode="Markdown", reply_to_message_id=message.message_id)
    else: bot.reply_to(message, info_text, parse_mode="Markdown")

# 5. معالجة بقية الرسائل والألعاب الأخرى والحماية
@bot.message_handler(func=lambda message: True)
def main_handler(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    text = message.text.strip().lower()

    # ألعاب الشات النصية الأخرى
    if text in ["حجر", "ورقة", "مقص"]:
        bot_choice = random.choice(["حجر", "ورقة", "مقص"])
        if text == bot_choice: result = f"🤝 تعادل! اخترت {bot_choice} أيضاً."
        elif (text == "حجر" and bot_choice == "مقص") or (text == "ورقة" and bot_choice == "حجر") or (text == "مقص" and bot_choice == "ورقة"):
            result = f"🎉 كفو! فزت عليّ، اخترت {bot_choice} 🤖."
        else: result = f"🤪 هاردلك فزت عليك! اخترت {bot_choice} 🤖."
        bot.reply_to(message, result)
        return

    if text == "خمن":
        secret_numbers[chat_id] = random.randint(1, 10)
        bot.reply_to(message, "🔢 اخترت رقماً سرياً من (1 إلى 10)! خمن الرقم واكتبه.")
        return

    if chat_id in secret_numbers and text.isdigit():
        if int(text) == secret_numbers[chat_id]:
            bot.reply_to(message, f"🎉 أحسنت يا {message.from_user.first_name}! الإجابة صحيحة ({text}).")
            del secret_numbers[chat_id]
        return

    if text == "تفكيك":
        word, scrambled = random.choice(list(PUZZLE_WORDS.items()))
        current_puzzles[chat_id] = word
        bot.reply_to(message, f"🧩 رتب الحروف لتكوين الكلمة:\n\n👈 ` {scrambled} `")
        return

    if chat_id in current_puzzles and text == current_puzzles[chat_id]:
        bot.reply_to(message, f"🏆 ممتاز! إجابتك صحيحة وهي: **{current_puzzles[chat_id]}**.")
        del current_puzzles[chat_id]
        return

    if text == "نسبة الحب" and message.reply_to_message:
        bot.reply_to(message, f"❤️ نسبة الحب والصداقة بينكما هي: **{random.randint(0, 100)}%** 📊")
        return

    # أوامر الإشراف بالرد
    if message.reply_to_message and is_admin(chat_id, user_id):
        target_user = message.reply_to_message.from_user
        if text in ["كتم", "تقييد"]:
            bot.restrict_chat_member(chat_id, target_user.id, can_send_messages=False)
            bot.reply_to(message, f"🔇 تم كتم العضو.")
            return
        if text in ["الغاء الكتم", "الغاء التقييد"]:
            bot.restrict_chat_member(chat_id, target_user.id, can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True)
            bot.reply_to(message, f"🔊 تم إلغاء الكتم.")
            return
        if text in ["طرد", "حظر"]:
            bot.ban_chat_member(chat_id, target_user.id)
            bot.reply_to(message, f"🚷 تم الحظر.")
            return
        if text == "تحذير":
            if target_user.id not in user_warnings: user_warnings[target_user.id] = 0
            user_warnings[target_user.id] += 1
            if user_warnings[target_user.id] >= 3:
                bot.restrict_chat_member(chat_id, target_user.id, can_send_messages=False)
                bot.reply_to(message, f"🚨 كتم تلقائي لتجاوز 3 تحذيرات!")
                user_warnings[target_user.id] = 0
            else: bot.reply_to(message, f"⚠️ تحذير حالي: ({user_warnings[target_user.id]}/3)")
            return

    if text == "معلومات الكروب" and is_admin(chat_id, user_id):
        bot.reply_to(message, f"📊 **إحصائيات الكروب:**\n\n👥 الأعضاء: {bot.get_chat_member_count(chat_id)}")
        return

    # --- [ فلاتر الحماية لغير المشرفين والمطور ] ---
    if is_admin(chat_id, user_id): return

    url_pattern = r"(https?://[^\s]+|t\.me/[^\s]+|[a-zA-Z0-9-]+\.[a-zA-Z]{2,})"
    if re.search(url_pattern, message.text):
        try: bot.delete_message(chat_id, message.message_id)
        except Exception: pass
        bot.send_message(chat_id, f"⚠️ {message.from_user.first_name}، الروابط ممنوعة! 🚫")
        return

    for word in PROHIBITED_WORDS:
        if word in message.text:
            try: bot.delete_message(chat_id, message.message_id)
            except Exception: pass
            bot.send_message(chat_id, f"🔞 تم حذف رسالة غير لائقة لـ {message.from_user.first_name}.")
            return

    # منع السبام
    current_time = time.time()
    if user_id not in user_messages: user_messages[user_id] = []
    user_messages[user_id].append(current_time)
    user_messages[user_id] = [t for t in user_messages[user_id] if current_time - t < 5]
    if len(user_messages[user_id]) > 4:
        try: bot.restrict_chat_member(chat_id, user_id, can_send_messages=False)
        except Exception: pass
        bot.send_message(chat_id, f"🚨 تم كتم العضو {message.from_user.first_name} بسبب السبام! 🔇")

# 6. منع الملصقات لغير المشرفين
@bot.message_handler(content_types=['sticker', 'animation'])
def monitor_stickers(message):
    if is_admin(message.chat.id, message.from_user.id): return
    try: bot.delete_message(message.chat.id, message.message_id)
    except Exception: pass

print(f"⚙️ النسخة الكاملة الفاخرة XO + ألعاب + حماية تعمل بنجاح.. المطور: {DEVELOPER_USERNAME}")
bot.infinity_polling()
