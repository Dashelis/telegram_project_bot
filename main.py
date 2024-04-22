import re
import requests
import logging
import sqlite3
from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import Application, MessageHandler, filters, CommandHandler, ConversationHandler, CallbackContext

# from config import BOT_TOKEN
reply_keyboard = [['/start', '/help_command'],
                  ['/translate', '/add_words'],
                  ['/learn_words', '/stop_add'],
                  ['/stop_translate', '/stop_learn'],
                  ['Продолжить']]
markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
con = sqlite3.connect("user_words.sqlite")
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG
)

logger = logging.getLogger(__name__)


def check_language(ru, en):
    rus_pattern = re.compile("[а-яё]+", re.I)
    eng_pattern = re.compile("[a-z]+", re.I)

    if rus_pattern.fullmatch(ru) and eng_pattern.fullmatch(en):
        return True
    else:
        return False


async def start(update, context):
    """Отправляет сообщение когда получена команда /start"""
    user = update.effective_user
    await update.message.reply_html(
        rf"Привет {user.mention_html()}! "
        "Этот бот поможет вам выучить английские слова \n"
        "В боте есть функции:\n"
        "/translate - переведет любое слово с русского на английский \n"
        "/add_words - добавит слова в твой словарик перед изучением \n"
        "/learn_words - функция для изучения слов(перед использованием не забудьте добавить слова!)",
        reply_markup=markup
    )


async def add_words(update, context):
    reply_markup = markup
    await update.message.reply_text(
        "Введите слова для изучения разными сообщениями, сначала слово на русском и затем через пробел его перевод\n"
        "Вы можете закончить, послав команду /stop_add.\n")
    await update.message.reply_text(
        "Пример сообщения:\n"
        "собака dog\n")
    return 1


async def first_response(update, context):
    reply_markup = markup
    words = update.message.text
    # logger.info(words)
    wrds = words.split('\n')
    print(wrds)
    try:
        for i in wrds:
            print(i)
            cur = con.cursor()
            user = update.effective_user
            name = user.id
            ru = str(i.split(' ')[0]).lower()
            en = str(i.split(' ')[1]).lower()
            if check_language(ru, en):
                cur.execute("INSERT INTO words(name, word_ru, word_eng) VALUES(?, ?, ?)", (name, ru, en))
                con.commit()
                await update.message.reply_text("Слово успешно добавлено! Пишите следующее")
                return 1
            else:
                await update.message.reply_text("Кажется, произошла ошибка. Попробуй снова!")
                return 1
    except:
        await update.message.reply_text("Кажется, произошла ошибка. Попробуй снова!")
        return 1


async def stop_add(update, context):
    reply_markup = markup
    await update.message.reply_text("Всего доброго!")
    return ConversationHandler.END


async def help_command(update, context):
    reply_markup = markup
    """Отправляет сообщение когда получена команда /help_command"""
    await update.message.reply_text("Функции:"
                                    "/translate - переведет любое слово с русского на английский \n"
                                    "/add_words - добавит слова в твой словарик перед изучением \n"
                                    "/learn_words - функция для изучения слов(перед использованием не забудьте добавить слова!) \n"
                                    "/stop_add - заканчивает добавление слов \n"
                                    "/stop_learn - заканчивает изучение слов \n"
                                    "/stop_translate - заканчивает перевод слов")


async def translate(update, context):
    reply_markup = markup
    await update.message.reply_text(
        "Введите слово на русском языке для перевода его на английский\n"
        "Вы можете закончить, послав команду /stop_translate.\n"
        "\n"
        "«Реализовано с помощью сервиса «Яндекс.Словарь» - https://tech.yandex.ru/dictionary.")
    return 1


async def res_translate(update, context):
    reply_markup = markup
    text = update.message.text
    try:
        response = requests.get(
            f"https://dictionary.yandex.net/api/v1/dicservice.json/lookup?key=dict.1.1.20240417T184509Z.95b67bb2af772514.58f01ae3e475db995e93cb63c6db585b02a069cb&lang=ru-en&text={text}")
        res = response.json()
        await update.message.reply_text(res["def"][0]["tr"][0]["text"])
        return 1
    except:
        await update.message.reply_text("Кажется, произошла ошибка. Попробуй снова!")
        return 1


async def stop_translate(update, context):
    reply_markup = markup
    await update.message.reply_text("Всего доброго!")
    return ConversationHandler.END


async def learn_words(update, context):
    reply_markup = markup
    await update.message.reply_text(
        "Готовы изучать слова? Напишите 'Продолжить' и начнем!\n"
        "Я отправлю вам слово на русском языке, ваша задача правильно написать перевод слова на английский\n"
        "Вы можете закончить, послав команду /stop_learn.\n")
    return 1


async def learn_process1(update: Update, context: CallbackContext):
    reply_markup = markup
    try:
        cur = con.cursor()
        user = update.effective_user
        name = user.id
        res = cur.execute(
            f"SELECT word_ru, word_eng FROM words WHERE name = {user.id} AND persent < 80 ORDER BY RANDOM() LIMIT 1;").fetchall()
        word_ru = res[0][0]
        word_eng = res[0][1]
        context.user_data['word_ru'] = word_ru
        context.user_data['word_eng'] = word_eng
        await update.message.reply_text(word_ru)
        return 2
    except:
        await update.message.reply_text("Все ваши слова выучены! Добавьте новых слов с помощью /add_words")


async def learn_process2(update, context):
    reply_markup = markup
    cur = con.cursor()
    user = update.effective_user
    name = user.id
    if (update.message.text).lower() == context.user_data['word_eng']:
        cur.execute("UPDATE words SET al = al + 1, right = right + 1 WHERE word_eng = ? and name = ?;",
                    (context.user_data['word_eng'], name))
        con.commit()
        cur.execute("UPDATE words SET persent = 100 * right/al WHERE word_eng = ? and name = ?;",
                    (context.user_data['word_eng'], name))
        con.commit()
        await update.message.reply_text("Верно! Продолжим?(Нажмите кнопку 'Продолжить')\n ")

    else:
        await update.message.reply_text("Неверно!")
        cur.execute("UPDATE words SET al = al + 1 WHERE word_eng = ? and name = ?;",
                    (context.user_data['word_eng'], name))
        con.commit()
        cur.execute("UPDATE words SET persent = 100 * right/al WHERE word_eng = ? and name = ?;",
                    (context.user_data['word_eng'], name))
        con.commit()
    return 1


async def stop_learn(update, context):
    reply_markup = markup
    await update.message.reply_text("Досвидания, возвращайтесь к изучению слов!")
    return ConversationHandler.END


def main():
    reply_markup = markup
    application = Application.builder().token('6821226097:AAHhJ49vpScbDM8wYxQRrmvIH46ws_NNXrA').build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help_command", help_command))
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('add_words', add_words)],
        states={
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, first_response)],
        },
        fallbacks=[CommandHandler('stop_add', stop_add)]
    )
    application.add_handler(conv_handler)
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('translate', translate)],
        states={
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, res_translate)],
        },
        fallbacks=[CommandHandler('stop_translate', stop_translate)]
    )
    application.add_handler(conv_handler)

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('learn_words', learn_words)],
        states={
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, learn_process1)],
            2: [MessageHandler(filters.TEXT & ~filters.COMMAND, learn_process2)],
        },
        fallbacks=[CommandHandler('stop_learn', stop_learn)]
    )
    application.add_handler(conv_handler)

    application.run_polling()


if __name__ == '__main__':
    main()
