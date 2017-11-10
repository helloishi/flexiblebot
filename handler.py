import engine as e
import os
import sqlite3

SCRIPT_DIR = os.getcwd() + '/Answers'

ALL_ANSWERS = {}
ADMIN_IDS = []
QUESTION_USERS = []

DB = sqlite3.connect('chat_ids.sqlite')

### LOAD ADMIN_IDS ###
with open('admins.txt', 'r') as f:
    for i in f.readlines():
        ADMIN_IDS.append(int(i.rstrip()))

### LOAD ALL_ANSWERS ###
def load_answers_from_dir(current_dir, dictionary):
    """Загружает текстовую информацию из файла
    current_dir = папка откуда будем брать txtшники, обходит рекурсивно все папки
    dictionary = словарь, куда все выгружается
    """
    DIR_NAMES = os.scandir(current_dir)
    for x in DIR_NAMES:
        if x.is_dir():
            load_answers_from_dir(current_dir + '/' + x.name, dictionary)
        else:
            f = open(current_dir + '/' + x.name, 'r')
            dictionary[x.name[:-4]] = f.readlines()


def decode_answers(dictionary):
    """Декодирует текстовую информацию, полученую из load_answers_from_dir"""
    for answer in dictionary:
        return_dict = {
            'text': [],
            'photo': [],
            'document': [],
            'markup': None
        }

        text = ''
        mode = ''
        markup = []

        for line in dictionary[answer]:
            if line[0] == '#':
                mode = line.rstrip()
                if mode != '#text_end':
                    continue

            if mode == '#text':
                text += line

            elif mode == '#text_end':
                if not text:
                    continue

                if markup:
                    markup = {'keyboard': markup, 'resize_keyboard': True}
                    return_dict['markup'] = markup
                return_dict['text'].append(text)

                text = ''

            elif mode == '#markup':
                buttons = line.rstrip().split('%')
                buttons_line = [{"text": x} for x in buttons]
                markup.append(buttons_line)

            elif mode == '#photo':
                photo_id = line.rstrip()
                if photo_id:
                    return_dict['photo'].append(photo_id)

            elif mode == '#document':
                document_id = line.rstrip()
                if document_id:
                    document_id['document'].append(document_id)

        dictionary[answer] = return_dict

load_answers_from_dir(SCRIPT_DIR, ALL_ANSWERS)
decode_answers(ALL_ANSWERS)

"""
ALL_ANSWERS:
{
    'text' = ['TEXT', 'TEXT'],
    'photo' = ['PHOTO_ID', 'PHOTO_ID'],
    'document' = ['DOC_ID'],
    'markup' = []
}
"""


def message_handler(query):
    chat_id = query["chat_id"]

    if 'text' in query.keys():
        command_message(chat_id, query["text"])

    if 'photo' in query.keys():
        if chat_id in ADMIN_IDS:
            photo_message(chat_id, query['photo'])

    if 'document' in query.keys():
        if chat_id in ADMIN_IDS:
            document_message(chat_id, query['document'])


def callback_query_handler(query):
    chat_id = query['chat_id']
    data = query['data']
    message_id = query['message_id']
    callback_query_id = query["callback_query_id"]


def photo_message(chat_id, photo_info):
    answer = 'Фото:\n'
    for i in photo_info:
        answer += str(i['height']) + ' x ' + str(i['width'])\
                  + '\n' + i['file_id'] + '\n\n'

    e.sendMessage(chat_id, answer)


def document_message(chat_id, document_info):
    answer = 'Документ:\n'
    answer += document_info['file_id']

    e.sendMessage(chat_id, answer)


def command_message(chat_id, text):

    if '@' in text:
        res = text.find('@')
        text = text[:res]

    if text[0] == '/':
        text = text[1:]

    if text == 'id':
        e.sendMessage(chat_id, 'Ваш id = ' + str(chat_id))
        return

    if text == 'off':
        params = (str(chat_id),)
        res = DB.execute('select id from users where id=?', params)
        if res.fetchone():
            DB.execute("""delete from users where id=?""", params)
        DB.commit()
        e.sendMessage(chat_id, 'Подписка отключена')
        return

    if text == 'on':
        params = (str(chat_id),)
        res = DB.execute("""select id from users where id=?""", params)
        if not res.fetchone():
            DB.execute("""insert into users values (?)""", params)
        DB.commit()
        e.sendMessage(chat_id, 'Подписка включена')
        return

    if text == 'Отмена':
        try:
            QUESTION_USERS.remove(chat_id)
        except ValueError:
            pass

    if chat_id in QUESTION_USERS:
        for i in ADMIN_IDS:
            e.sendMessage(i,str(chat_id) + ' (задает вопрос):\n' + text)
            e.sendMessage(i, 'Испопльзуйте синтаксис /a id текст чтобы овтетить')
        return

    if text == '❓Задать вопрос':
        QUESTION_USERS.append(chat_id)

    if chat_id in ADMIN_IDS:

        ### ADMIN MODE ###
        if text[:4] == 'send':
            text = text[5:]
            res = DB.execute("""select id from users""")
            e.sendMessage(chat_id, 'Рассылка отправлена')
            for send_id in res:
                e.sendMessage(send_id[0], text)
            return

        if text[0] == 'a':
            text = text[2:]
            res = text.find(' ')

            try:
                user_id = int(text[:res])
            except ValueError:
                e.sendMessage(chat_id, 'Не получилось разбить строку')
                return

            e.sendMessage(chat_id, 'Ответ отправлен, спасибо!')
            e.sendMessage(user_id, 'Ответ на ваш вопрос:\n' + text[res+1:])
            return

    if text in ALL_ANSWERS.keys():

        if text == 'start':
            params = (str(chat_id),)
            res = DB.execute("""select id from users where id=?""", params)
            if not res.fetchone():
                DB.execute("""insert into users values (?)""", params)
            DB.commit()
        answer = ALL_ANSWERS[text]

        if answer['photo']:
            for i in answer['photo']:
                e.sendPhoto(chat_id, i)

        if answer['text']:
            markup = None
            if answer['markup']:
                markup = answer['markup']

            for i in answer['text']:
                e.sendMessage(chat_id, i, reply_markup=markup)

    else:
        e.sendMessage(chat_id, 'Такой команды нет')





