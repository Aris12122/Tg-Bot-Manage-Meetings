import telebot

error_message = "Что-то пошло не так, пожалуйста напишите @Aris12122"


def get_file(path):
    with open(path) as f:
        return f.readline()


def add_to_file(path, message):
    with open(path, 'a') as f:
        f.write(message)


bot = telebot.TeleBot(get_file("secret/botAPI"))


@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(message.from_user.id, text='Привет!')


@bot.message_handler(commands=["instruction"])
def instruction(message):
    bot.send_message(message.chat.id,
                     "немного терпения, мы разрабатываем эту функцию")


@bot.message_handler(commands=["access"])
def access(message):
    bot.send_message(message.chat.id,
                     "немного терпения, мы разрабатываем эту функцию")


@bot.message_handler(commands=['help'])
def help(message):
    bot.send_message(message.chat.id, "Привет! Я бот, который поможет тебе планировать встречи\n"
                                      "вот список моих команд:\n"
                                      "/start - начало работы\n"
                                      "/instruction - инструкция по подключению\n"
                                      "/access - подключение гугл. календаря \n"
                                      "/set_meeting- назначить встречу\n"
                                      "/help - справочник \n")


@bot.message_handler(content_types=["text"])
def handle_text(message):
    bot.send_message(message.chat.id,
                     "Я не умею отвечать на сообщения, пожалуйста используйте команды, описанные в /help")


while True:
    try:
        print("BEGIN")
        bot.polling(non_stop=True)
    except Exception as e:
        print("Global fail: " + str(e))
        continue
    break