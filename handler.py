import engine as e
import os

SCRIPT_DIR = os.getcwd() + '/Answers'

ALL_ANSWERS = {}


def load_answers_from_dir(current_dir):
    DIR_NAMES = os.scandir(current_dir)
    for x in DIR_NAMES:
        if x.is_dir():
            load_answers_from_dir(current_dir + '/' + x.name)
        else:
            f = open(current_dir + '/' + x.name, 'r')
            ALL_ANSWERS[x.name[:-4]] = f.readlines()
load_answers_from_dir(SCRIPT_DIR)

def message_handler(query):
    chat_id = query["chat_id"]

    if 'text' in query.keys():
        command_message(chat_id, query["text"])

    if 'photo' in query.keys():
        photo_message(chat_id, query['photo'])

    if 'document' in query.keys():
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

    print(ALL_ANSWERS.keys())
    if not text in ALL_ANSWERS.keys():
        e.sendMessage(chat_id, 'Такой команды нет')

    else:
        decode_answer(chat_id, ALL_ANSWERS[text])


def decode_answer(chat_id, query):

    text = ''
    mode = ''
    markup = []

    for line in query:
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
            e.sendMessage(chat_id, text, reply_markup=markup)

            text = ''
            markup = []

        elif mode == '#markup':
            buttons = line.rstrip().split('%')
            buttons_line = [{"text": x} for x in buttons]
            markup.append(buttons_line)

        elif mode == '#photo':
            photo_id = line.rstrip()
            e.sendPhoto(chat_id, photo_id)

        elif mode == '#document':
            document_id = line.rstrip()
            e.sendDocument(chat_id, document_id)



