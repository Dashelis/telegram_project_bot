import logging
from telegram.ext import Application, MessageHandler, filters, CommandHandler, ConversationHandler

# from config import BOT_TOKEN

# Запускаем логгирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG
)

logger = logging.getLogger(__name__)


async def start(update, context):
    """Отправляет сообщение когда получена команда /start"""
    user = update.effective_user
    await update.message.reply_html(
        rf"Привет {user.mention_html()}! все работает!!!",
    )


async def add_words(update, context):
    await update.message.reply_text(
        "Введите слова для изучения в одном сообщении, сначала слово на русском и затем через пробел его перевод\n"
        "Вы можете закончить, послав команду /stop_add.\n")
    return 1


async def first_response(update, context):
    words = update.message.text
    logger.info(words)
    await update.message.reply_text("Слова успешно добавлены!")
    return ConversationHandler.END


async def stop_add(update, context):
    await update.message.reply_text("Всего доброго!")
    return ConversationHandler.END


async def guess_words(update, context):
    """Отправляет сообщение когда получена команда /guess_words"""
    user = update.effective_user
    await update.message.reply_html(
        rf"Привет {user.mention_html()}! все работает!!!",
    )


async def help_command(update, context):
    """Отправляет сообщение когда получена команда /help_command"""
    await update.message.reply_text("Я пока не умею помогать, но мы научимся все впереди!")


def main():
    application = Application.builder().token('6821226097:AAHhJ49vpScbDM8wYxQRrmvIH46ws_NNXrA').build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help_command", help_command))
    application.add_handler(CommandHandler("guess_words", guess_words))
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('add_words', add_words)],
        states={
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, first_response)],
        },
        fallbacks=[CommandHandler('stop_add', stop_add)]
    )
    application.add_handler(conv_handler)
    application.run_polling()


if __name__ == '__main__':
    main()
