from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, BotCommand, BotCommandScopeDefault, MenuButtonCommands
from aiogram.filters.command import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
import logging
import sqlite3
from datetime import datetime
import os
import asyncio
from typing import Dict, List

# تنظیمات اولیه
logging.basicConfig(level=logging.INFO)
bot = Bot(token='7340863969:AAHHy2NfeONgVCqw5NQscocpK-Khe_ySEwQ')
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# تعریف رشته‌ها و درس‌ها
DEPARTMENTS = {
    "computer": "مهندسی کامپیوتر 💻",
    "electrical": "مهندسی برق ⚡",
    "mechanical": "مهندسی مکانیک 🔧",
    "civil": "مهندسی عمران 🏗",
    "chemistry": "مهندسی شیمی 🧪"
}

COURSES: Dict[str, List[str]] = {
    "computer": [
        "برنامه‌نویسی پیشرفته",
        "ساختمان داده",
        "پایگاه داده",
        "هوش مصنوعی",
        "شبکه‌های کامپیوتری"
    ],
    "electrical": [
        "مدارهای الکتریکی",
        "الکترونیک ۱",
        "الکترونیک ۲",
        "سیستم‌های دیجیتال",
        "مخابرات"
    ],
    "mechanical": [
        "استاتیک",
        "دینامیک",
        "مقاومت مصالح",
        "ترمودینامیک",
        "سیالات"
    ],
    "civil": [
        "مقاومت مصالح",
        "تحلیل سازه",
        "مکانیک خاک",
        "بتن",
        "سازه‌های فولادی"
    ],
    "chemistry": [
        "شیمی عمومی",
        "شیمی آلی",
        "انتقال حرارت",
        "ترمودینامیک",
        "کنترل فرآیند"
    ]
}

# تعریف وضعیت‌ها
class BotStates(StatesGroup):
    # states برای جزوات
    waiting_for_department = State()
    waiting_for_course = State()
    waiting_for_pdf = State()
    waiting_for_book = State()
    waiting_for_teacher_name = State()
    waiting_for_rating = State()
    waiting_for_teacher_comment = State()
    viewing_department = State()
    viewing_course = State()

# تنظیمات دیتابیس
def setup_database():
    conn = sqlite3.connect('university_bot.db')
    c = conn.cursor()
    
    # حذف جدول قبلی اگر وجود داشته باشد
    c.execute('DROP TABLE IF EXISTS pamphlets')
    
    # ایجاد جدول جدید با ستون‌های مورد نیاز
    c.execute('''CREATE TABLE pamphlets
                 (id INTEGER PRIMARY KEY,
                  title TEXT,
                  file_id TEXT,
                  department TEXT,
                  course TEXT,
                  uploaded_by TEXT,
                  upload_date TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS books
                 (id INTEGER PRIMARY KEY, title TEXT, file_id TEXT, 
                  uploaded_by TEXT, upload_date TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS teacher_ratings
                 (id INTEGER PRIMARY KEY,
                  teacher_name TEXT,
                  rating INTEGER,
                  comment TEXT,
                  rated_by TEXT,
                  date TEXT)''')
    
    conn.commit()
    conn.close()

def get_main_keyboard():
    keyboard = [
        [InlineKeyboardButton(text="جزوات 📚", callback_data="pamphlets")],
        [InlineKeyboardButton(text="کتاب‌ها 📖", callback_data="books")],
        [InlineKeyboardButton(text="رتبه‌بندی اساتید 👨‍🏫", callback_data="teachers")],
        [InlineKeyboardButton(text="🔄 شروع مجدد ربات", callback_data="restart_bot")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

@dp.message(Command("start"))
async def start_command(message: types.Message):
    await message.reply(
        "به ربات دانشگاه خوش آمدید! 👋\n\n"
        "🔹 با این ربات می‌توانید:\n"
        "• جزوات و کتاب‌ها را مدیریت کنید\n"
        "• به اساتید امتیاز دهید\n\n"
        "🔸 دستورات مفید:\n"
        "/start - شروع ربات\n"
        "/restart - شروع مجدد ربات\n"
        "/help - راهنمای ربات\n"
        "/cancel - لغو عملیات\n\n"
        "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
        reply_markup=get_main_keyboard()
    )

@dp.callback_query()
async def process_callback(callback: types.CallbackQuery, state: FSMContext):
    if callback.data == "pamphlets":
        keyboard = [
            [InlineKeyboardButton(text="مشاهده جزوات", callback_data="view_pamphlets")],
            [InlineKeyboardButton(text="آپلود جزوه", callback_data="upload_pamphlet")],
            [InlineKeyboardButton(text="بازگشت به منو", callback_data="main_menu")]
        ]
        await callback.message.edit_text(
            "بخش جزوات - لطفا انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
        await callback.answer("وارد بخش جزوات شدید 📚")

    elif callback.data == "books":
        keyboard = [
            [InlineKeyboardButton(text="مشاهده کتاب‌ها", callback_data="view_books")],
            [InlineKeyboardButton(text="آپلود کتاب", callback_data="upload_book")],
            [InlineKeyboardButton(text="بازگشت به منو", callback_data="main_menu")]
        ]
        await callback.message.edit_text(
            "بخش کتاب‌ها - لطفا انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
        await callback.answer("وارد بخش کتاب‌ها شدید 📖")
        
    elif callback.data == "teachers":
        keyboard = [
            [InlineKeyboardButton(text="مشاهده رتبه‌بندی‌ها ⭐", callback_data="view_ratings")],
            [InlineKeyboardButton(text="ثبت رتبه جدید 📝", callback_data="new_rating")],
            [InlineKeyboardButton(text="🔙 برگشت به منوی اصلی", callback_data="main_menu")]
        ]
        await callback.message.edit_text(
            "👨‍🏫 بخش رتبه‌بندی اساتید\n\n"
            "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
        await callback.answer("وارد بخش رتبه‌بندی اساتید شدید")
        
    elif callback.data == "upload_pamphlet":
        keyboard = []
        for dept_id, dept_name in DEPARTMENTS.items():
            keyboard.append([InlineKeyboardButton(
                text=dept_name,
                callback_data=f"dept_{dept_id}"
            )])
        keyboard.append([InlineKeyboardButton(text="بازگشت", callback_data="pamphlets")])
        
        await callback.message.edit_text(
            "لطفاً رشته مورد نظر را انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
        await state.set_state(BotStates.waiting_for_department)
        await callback.answer("انتخاب رشته 🎓")
    
    elif callback.data.startswith("dept_"):
        department = callback.data.replace("dept_", "")
        await state.update_data(department=department)
        
        keyboard = []
        for course in COURSES[department]:
            keyboard.append([InlineKeyboardButton(
                text=course,
                callback_data=f"course_{course}"
            )])
        keyboard.append([InlineKeyboardButton(text="بازگشت", callback_data="upload_pamphlet")])
        
        await callback.message.edit_text(
            f"رشته: {DEPARTMENTS[department]}\n"
            "لطفاً درس مورد نظر را انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
        await state.set_state(BotStates.waiting_for_course)
        await callback.answer("انتخاب درس 📚")
    
    elif callback.data.startswith("course_"):
        course = callback.data.replace("course_", "")
        data = await state.get_data()
        department = data.get('department')
        
        await callback.message.edit_text(
            f"رشته: {DEPARTMENTS[department]}\n"
            f"درس: {course}\n\n"
            "لطفاً جزوه خود را به صورت PDF ارسال کنید.\n"
            "برای لغو، دستور /cancel را بفرستید."
        )
        await state.update_data(course=course)
        await state.set_state(BotStates.waiting_for_pdf)
        await callback.answer("آماده دریافت فایل 📤")
    
    elif callback.data == "view_pamphlets":
        keyboard = []
        for dept_id, dept_name in DEPARTMENTS.items():
            keyboard.append([InlineKeyboardButton(
                text=dept_name,
                callback_data=f"view_dept_{dept_id}"
            )])
        keyboard.append([InlineKeyboardButton(text="بازگشت", callback_data="pamphlets")])
        
        await callback.message.edit_text(
            "لطفاً رشته مورد نظر را انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
        await state.set_state(BotStates.viewing_department)
        await callback.answer("انتخاب رشته برای مشاهده 🎓")
    
    elif callback.data.startswith("view_dept_"):
        department = callback.data.replace("view_dept_", "")
        await state.update_data(department=department)
        
        keyboard = []
        for course in COURSES[department]:
            keyboard.append([InlineKeyboardButton(
                text=course,
                callback_data=f"view_course_{course}"
            )])
        keyboard.append([InlineKeyboardButton(text="🔙 برگشت به لیست رشته‌ها", callback_data="view_pamphlets")])
        
        await callback.message.edit_text(
            f"رشته: {DEPARTMENTS[department]}\n"
            "لطفاً درس مورد نظر را انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
        await state.set_state(BotStates.viewing_course)
        await callback.answer("انتخاب درس برای مشاهده 📚")
    
    elif callback.data.startswith("view_course_"):
        course = callback.data.replace("view_course_", "")
        data = await state.get_data()
        department = data.get('department')
        
        conn = sqlite3.connect('university_bot.db')
        c = conn.cursor()
        c.execute('''SELECT title, file_id, uploaded_by, upload_date 
                     FROM pamphlets 
                     WHERE department = ? AND course = ?
                     ORDER BY upload_date DESC''', (department, course))
        pamphlets = c.fetchall()
        conn.close()
        
        if pamphlets:
            await callback.message.edit_text(
                f"📚 جزوات درس {course}\n"
                f"🎓 رشته {DEPARTMENTS[department]}\n\n"
                "در حال ارسال جزوات..."
            )
            
            for title, file_id, uploader, date in pamphlets:
                await callback.message.answer_document(
                    document=file_id,
                    caption=f"📝 {title}\n"
                            f"👤 آپلود توسط: @{uploader}\n"
                            f"📅 تاریخ: {date}"
                )
            
            keyboard = [[InlineKeyboardButton(text="🔙 برگشت به لیست درس‌ها", 
                        callback_data=f"view_dept_{department}")]]
            await callback.message.reply(
                "همه جزوات این درس نمایش داده شدند.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
            )
        else:
            keyboard = [[InlineKeyboardButton(text="🔙 برگشت به لیست درس‌ها", 
                        callback_data=f"view_dept_{department}")]]
            await callback.message.edit_text(
                f"متأسفانه هنوز جزوه‌ای برای درس {course} آپلود نشده است! 😕",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
            )
        
        await callback.answer()

    elif callback.data == "main_menu":
        await state.clear()
        await callback.message.edit_text(
            "منوی اصلی:",
            reply_markup=get_main_keyboard()
        )
        await callback.answer("به منوی اصلی بازگشتید 🏠")
        
    elif callback.data.startswith("get_pamphlet_"):
        file_id = callback.data.replace("get_pamphlet_", "")
        try:
            await callback.message.answer_document(file_id)
            await callback.answer("فایل در حال ارسال است... ⏳")
        except Exception as e:
            await callback.answer("متأسفانه در دریافت فایل مشکلی پیش آمد! ❌")
            print(f"Error sending file: {e}")
    
    elif callback.data == "upload_book":
        await BotStates.waiting_for_book.set()
        await callback.message.edit_text(
            "لطفاً کتاب خود را به صورت PDF ارسال کنید.\n"
            "برای لغو، دستور /cancel را بفرستید."
        )
        await callback.answer("منتظر دریافت فایل کتاب... 📚")
        
    elif callback.data == "new_rating":
        await callback.message.edit_text(
            "👨‍🏫 لطفاً نام استاد را وارد کنید:\n"
            "مثال: دکتر محمدی\n\n"
            "برای لغو از دستور /cancel استفاده کنید."
        )
        await state.set_state(BotStates.waiting_for_teacher_name)
        await callback.answer("در حال ثبت رتبه جدید...")

    elif callback.data == "view_ratings":
        conn = sqlite3.connect('university_bot.db')
        c = conn.cursor()
        c.execute('''SELECT teacher_name, 
                     AVG(rating) as avg_rating,
                     COUNT(*) as total_ratings
                     FROM teacher_ratings 
                     GROUP BY teacher_name
                     ORDER BY avg_rating DESC''')
        ratings = c.fetchall()
        conn.close()

        if ratings:
            text = "📊 رتبه‌بندی اساتید:\n\n"
            for teacher, avg_rating, total in ratings:
                stars = "⭐" * round(avg_rating)
                text += f"👨‍🏫 {teacher}\n"
                text += f"⭐ امتیاز: {avg_rating:.1f} {stars}\n"
                text += f"📊 تعداد نظرات: {total}\n\n"
        else:
            text = "❌ هنوز هیچ رتبه‌بندی ثبت نشده است!\n"
            text += "برای ثبت اولین رتبه‌بندی، گزینه 'ثبت رتبه جدید' را انتخاب کنید."

        keyboard = [[InlineKeyboardButton(text="🔙 برگشت", callback_data="teachers")]]
        await callback.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
        await callback.answer("لیست رتبه‌بندی‌ها بارگذاری شد")

    elif callback.data == "restart_bot":
        await state.clear()  # پاک کردن همه state ها
        await callback.message.edit_text(
            "🔄 ربات با موفقیت ری‌استارت شد!\n"
            "به ربات دانشگاه خوش آمدید!\n"
            "برای شروع، یکی از گزینه‌های زیر را انتخاب کنید:",
            reply_markup=get_main_keyboard()
        )
        await callback.answer("ربات ری‌استارت شد ✅")

@dp.callback_query(lambda c: c.data.startswith("view_dept_"), BotStates.viewing_department)
async def view_courses(callback: types.CallbackQuery, state: FSMContext):
    department = callback.data.replace("view_dept_", "")
    await state.update_data(department=department)
    
    keyboard = []
    for course in COURSES[department]:
        keyboard.append([InlineKeyboardButton(
            text=course,
            callback_data=f"view_course_{course}"
        )])
    keyboard.append([InlineKeyboardButton(text="🔙 برگشت به لیست رشته‌ها", callback_data="view_pamphlets")])
    
    await callback.message.edit_text(
        f"رشته: {DEPARTMENTS[department]}\n"
        "لطفاً درس مورد نظر را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    await state.set_state(BotStates.viewing_course)
    await callback.answer("انتخاب درس 📚")

@dp.callback_query(lambda c: c.data.startswith("view_course_"), BotStates.viewing_course)
async def show_course_pamphlets(callback: types.CallbackQuery, state: FSMContext):
    course = callback.data.replace("view_course_", "")
    data = await state.get_data()
    department = data['department']
    
    conn = sqlite3.connect('university_bot.db')
    c = conn.cursor()
    c.execute('''SELECT title, file_id, uploaded_by, upload_date 
                 FROM pamphlets 
                 WHERE department = ? AND course = ?
                 ORDER BY upload_date DESC''', (department, course))
    pamphlets = c.fetchall()
    conn.close()
    
    if pamphlets:
        await callback.message.edit_text(
            f"📚 جزوات درس {course}\n"
            f"🎓 رشته {DEPARTMENTS[department]}\n\n"
            "در حال ارسال جزوات..."
        )
        
        for title, file_id, uploader, date in pamphlets:
            await callback.message.answer_document(
                document=file_id,
                caption=f"📝 {title}\n"
                        f"👤 آپلود توسط: @{uploader}\n"
                        f"📅 تاریخ: {date}"
            )
        
        keyboard = [[InlineKeyboardButton(text="🔙 برگشت به لیست درس‌ها", 
                    callback_data=f"view_dept_{department}")]]
        await callback.message.reply(
            "همه جزوات این درس نمایش داده شدند.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
    else:
        keyboard = [[InlineKeyboardButton(text="🔙 برگشت به لیست درس‌ها", 
                    callback_data=f"view_dept_{department}")]]
        await callback.message.edit_text(
            f"متأسفانه هنوز جزوه‌ای برای درس {course} آپلود نشده است! 😕",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
    
    await callback.answer()

@dp.message(Command("cancel"))
async def cancel_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return
    
    await state.clear()
    await message.reply(
        "عملیات لغو شد.",
        reply_markup=get_main_keyboard()
    )

@dp.message(Command("help"))
async def help_command(message: types.Message):
    help_text = """
🌟 راهنمای استفاده از ربات:

👉 بخش جزوات:
• آپلود جزوه
• مشاهده و دانلود جزوات

📖 بخش کتاب‌ها:
• آپلود کتاب
• مشاهده و دانلود کتاب‌ها

👨‍🏫 بخش اساتید:
• ثبت نظر و امتیاز
• مشاهده رتبه‌بندی‌ها

❓ دستورات:
/start - شروع ربات
/pamphlets - بخش جزوات
/books - بخش کتاب‌ها
/teachers - بخش اساتید
/help - راهنما
/cancel - لغو عملیات

📌 برای شروع، دستور /start را بزنید.
"""
    await message.reply(help_text)

@dp.message(Command("menu"))
async def menu_command(message: types.Message):
    await message.reply(
        "منوی اصلی ربات:",
        reply_markup=get_main_keyboard()
    )

async def set_commands():
    # تنظیم دکمه منو
    await bot.set_chat_menu_button(
        menu_button=MenuButtonCommands(type="commands")
    )
    
    # تنظیم دستورات
    commands = [
        BotCommand(
            command="start",
            description="شروع ربات 🚀"
        ),
        BotCommand(
            command="menu",
            description="منوی اصلی 📱"
        ),
        BotCommand(
            command="pamphlets",
            description="مدیریت جزوات 📚"
        ),
        BotCommand(
            command="books",
            description="مدیریت کتاب‌ها 📖"
        ),
        BotCommand(
            command="teachers",
            description="رتبه‌بندی اساتید 👨‍🏫"
        ),
        BotCommand(
            command="help",
            description="راهنمای ربات ❓"
        ),
        BotCommand(
            command="cancel",
            description="لغو عملیات ❌"
        )
    ]
    
    await bot.set_my_commands(commands, scope=BotCommandScopeDefault())

@dp.message(lambda message: message.document, BotStates.waiting_for_pdf)
async def handle_pdf_upload(message: types.Message, state: FSMContext):
    if message.document.mime_type == 'application/pdf':
        data = await state.get_data()
        department = data['department']
        course = data['course']
        
        file_id = message.document.file_id
        file_name = message.document.file_name
        user = message.from_user.username
        
        conn = sqlite3.connect('university_bot.db')
        c = conn.cursor()
        c.execute('''INSERT INTO pamphlets 
                     (title, file_id, department, course, uploaded_by, upload_date)
                     VALUES (?, ?, ?, ?, ?, ?)''', 
                     (file_name, file_id, department, course, user, 
                      datetime.now().strftime("%Y-%m-%d")))
        conn.commit()
        conn.close()
        
        await message.reply(
            f"✅ فایل با موفقیت آپلود شد!\n\n"
            f"📝 نام فایل: {file_name}\n"
            f"🎓 رشته: {DEPARTMENTS[department]}\n"
            f"📚 درس: {course}"
        )
        await state.clear()
    else:
        await message.reply("لطفاً فقط فایل PDF ارسال کنید!")

@dp.message(BotStates.waiting_for_teacher_name)
async def handle_teacher_name(message: types.Message, state: FSMContext):
    await state.update_data(teacher_name=message.text)
    
    keyboard = [
        [InlineKeyboardButton(text="⭐", callback_data="rate_1"),
         InlineKeyboardButton(text="⭐⭐", callback_data="rate_2"),
         InlineKeyboardButton(text="⭐⭐⭐", callback_data="rate_3"),
         InlineKeyboardButton(text="⭐⭐⭐⭐", callback_data="rate_4"),
         InlineKeyboardButton(text="⭐⭐⭐⭐⭐", callback_data="rate_5")]
    ]
    
    await message.reply(
        f"نام استاد: {message.text}\n"
        "لطفاً امتیاز خود را از 1 تا 5 انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    await state.set_state(BotStates.waiting_for_rating)

@dp.callback_query(lambda c: c.data.startswith("rate_"))
async def handle_rating(callback: types.CallbackQuery, state: FSMContext):
    rating = int(callback.data.split("_")[1])
    data = await state.get_data()
    teacher_name = data.get('teacher_name')
    
    await callback.message.edit_text(
        f"نام استاد: {teacher_name}\n"
        f"امتیاز: {'⭐' * rating}\n\n"
        "لطفاً نظر خود را درباره استاد بنویسید:\n"
        "(می‌توانید نقاط قوت و ضعف را ذکر کنید)\n\n"
        "برای لغو از دستور /cancel استفاده کنید."
    )
    
    await state.update_data(rating=rating)
    await state.set_state(BotStates.waiting_for_teacher_comment)
    await callback.answer()

@dp.message(BotStates.waiting_for_teacher_comment)
async def handle_comment(message: types.Message, state: FSMContext):
    data = await state.get_data()
    teacher_name = data.get('teacher_name')
    rating = data.get('rating')
    
    conn = sqlite3.connect('university_bot.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS teacher_ratings
                 (id INTEGER PRIMARY KEY,
                  teacher_name TEXT,
                  rating INTEGER,
                  comment TEXT,
                  rated_by TEXT,
                  date TEXT)''')
    
    c.execute('''INSERT INTO teacher_ratings 
                 (teacher_name, rating, comment, rated_by, date)
                 VALUES (?, ?, ?, ?, ?)''',
                 (teacher_name, rating, message.text, message.from_user.username,
                  datetime.now().strftime("%Y-%m-%d")))
    
    conn.commit()
    conn.close()
    
    await state.clear()
    await message.reply(
        "✅ نظر شما با موفقیت ثبت شد!\n\n"
        f"👨‍🏫 استاد: {teacher_name}\n"
        f"⭐ امتیاز: {rating}\n"
        f"💬 نظر: {message.text}\n\n"
        "برای بازگشت به منوی اصلی، /start را بزنید.",
        reply_markup=get_main_keyboard()
    )

@dp.callback_query(lambda c: c.data == "upload_pamphlet")
async def upload_pamphlet(callback: types.CallbackQuery, state: FSMContext):
    await BotStates.waiting_for_pdf.set()
    await callback.message.edit_text(
        "لطفاً جزوه خود را به صورت PDF ارسال کنید.\n"
        "برای لغو، دستور /cancel را بفرستید."
    )

@dp.callback_query(lambda c: c.data.startswith('dl_'))
async def download_pamphlet(callback: types.CallbackQuery):
    file_number = int(callback.data.split('_')[1])
    
    conn = sqlite3.connect('university_bot.db')
    c = conn.cursor()
    
    # دریافت file_id از جدول موقت
    c.execute('SELECT file_id FROM temp_files WHERE id = ?', (file_number,))
    result = c.fetchone()
    conn.close()
    
    if result:
        file_id = result[0]
        try:
            await callback.message.answer_document(file_id)
            await callback.answer("فایل در حال ارسال است... ⏳")
        except Exception as e:
            await callback.answer("متأسفانه در دریافت فایل مشکلی پیش آمد! ❌")
            print(f"Error sending file: {e}")
    else:
        await callback.answer("فایل مورد نظر یافت نشد! ❌")

@dp.error()
async def error_handler(update: types.Update, exception: Exception):
    print(f"Error occurred: {exception}")
    
    # اگر update و message موجود باشند
    if hasattr(update, 'message') and update.message:
        await update.message.reply(
            "❌ متأسفانه خطایی رخ داد!\n"
            "لطفاً دوباره تلاش کنید یا از دستور /restart استفاده کنید.",
            reply_markup=get_main_keyboard()
        )
    # اگر callback_query موجود باشد
    elif hasattr(update, 'callback_query') and update.callback_query:
        await update.callback_query.message.edit_text(
            "❌ متأسفانه خطایی رخ داد!\n"
            "لطفاً دوباره تلاش کنید یا از دستور /restart استفاده کنید.",
            reply_markup=get_main_keyboard()
        )

async def main():
    try:
        print("Setting up database...")
        setup_database()  # راه‌اندازی مجدد دیتابیس
        
        print("Bot is starting...")
        await dp.start_polling(bot)
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        raise e
if __name__ == '__main__':
    asyncio.run(main())

