import telebot

error_message = "Что-то пошло не так, пожалуйста напишите @Aris12122"

def get_file(path):
    with open(path) as f:
        return f.readline()

def add_to_file(path, message):
    with open(path, 'a') as f:
        f.write(message)

bot = telebot.TeleBot(get_file("secret/botAPI"))

def check_registered(message, tg_handle = "", cf_handle = ""):
    try:
        if (tg_handle == "") :
            tg_handle = message.from_user.username

        print("Checking... " + str(tg_handle))

        if udata.is_user_registered(tg_handle) == False:
            print("Not registered " + str(tg_handle))
            bot.send_message(message.chat.id, "Тра та та")
            return False
    
    except Exception as e:
        bot.send_message(message.chat.id, error_message)
        print("Fail check_registered " + str(e))
        return False

    print("Successfully checked " + str(tg_handle) + " " + str(cf_handle))
    # add_to_file("data/registered_users", " " + tg_handle)
    # add_to_file("data/cf_handles", " " + cf_handle)
    # add_contestant(message=message, tg_handle=tg_handle, cf_handle=cf_handle)

    return True



@bot.message_handler(commands=["start"])
def start(message):

    bot.send_message(message.chat.id, "Перейдите пожалуйста по ссылке, чтобы предоставить доступ к вашему гугл календарю")
    
    

# @bot.message_handler(commands=["token"])
# def get_token(message):




@bot.message_handler(content_types=["text"])
def handle_text(message):
    bot.send_message(message.chat.id, "Я не умею отвечать на сообщения, пожалуйста используйте команды, описанные в /help")


# @bot.message_handler(commands=["print_memes"])
# def get_token(message):

#     if (message.from_user.username == "Aris12122") :
#         with open("data/contestants") as f:
#             contestants = f.readlines()
#         for i in range (0, len(contestants)):
#             contestant = contestants[i].split(' ')
#             message_id = contestant[0]
#             tg_handle = contestant[1]
#             cf_handle = contestant[2]
#             try:
#                 solved = get_solved(tg_handle=tg_handle, cf_handle=cf_handle, current_contest=current_contest)
#             except:
#                 print("Error occurred while processing " + cf_handle)
#                 return
#             print(cf_handle + " Solved ", solved, " of tasks")
#             token = get_token()
#             bot.send_message()

#     else:
#         bot.send_message(bot.chat.id, "У вас недостаточно прав для данной команды")


while True:
    try:
        print("BEGIN")
        bot.polling(non_stop=True)
    except Exception as e:
        print("Global fail: " + str(e))
        continue
    break