#!/usr/bin/env python

import html
import json
import re
from multiprocessing import Process, Pipe

from PyQt5.QtCore import Qt, QTimer, QObject
from PyQt5.QtGui import QPalette, QColor, QTextCursor, QTextObjectInterface, QTextFormat
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QTextBrowser
from playsound import playsound

import PlexLib

# import time

url_pattern = re.compile('(?!mailto:)(?:file:|(?:ht|f)tps?:\/\/)(?:\S+)?')

with open('PSChatDisplay/emoji.json', 'r') as fp:
    emoji = json.load(fp)

with open('PSChatDisplay/emoticons.json', 'r') as fp:
    emoticons = json.load(fp)

chat = []


def insert_emoji(text):
    # bench = time.clock()
    match = re.search(url_pattern, text)
    urls = []
    if match:
        i = 0
        try:
            while match.group(i):
                urls.append(match.group(i))
                i += 1
        except IndexError:
            pass
    n_text = re.sub(url_pattern, '{{url}}', text)
    for key in emoji:
        n_text = n_text.replace(key, emoji[key])
    for key in emoticons:
        n_text = re.sub(f"(?:^|\s)({re.escape(key)})(?:\s|$)", emoticons[key], n_text)
    for url in urls:
        n_text = n_text.replace('{{url}}', f'<a href="{url}">{url}</a>', 1)
    # print(f'bench {time.clock() - bench}')
    return n_text


def format_chat(lines):
    text = []
    for line in lines:
        if line['type'] == 'normal':
            text.append(f'<div style="color:{line["color"]};font-weight: 500;font-size:16px;font-family:Gilroy,'
                        f'system-ui,-apple-system,Segoe UI,Roboto,Ubuntu,Cantarell,Noto Sans,sans-ser'
                        f'if;"><b>&lt;{line["name"]}{line["gendertag"]}&gt;:</b> '
                        f'{insert_emoji(html.escape(line["message"]))}</div>')
        elif line['type'] == 'tip':
            if line["message"] == "":
                text.append(f'<div style="color:{line["color"]};font-weight: 500;background-color:#'
                            f'{"%0.6X" % (0xFFFFFF - int(line["color"].split("#")[1], 16))};font-size:16px;font-family'
                            f':Gilroy,system-ui,-apple-system,Segoe UI,Roboto,Ubuntu,Cantarell,Noto Sans,'
                            f'sans-serif;"><b>&lt;{line["name"]}{line["gendertag"]}&gt;:</b> Has just tipped '
                            f'{line["credits"]} PD!</div>')
            else:
                text.append(f'<div style="color:{line["color"]};font-weight: 500;background-color:#'
                            f'{"%0.6X" % (0xFFFFFF - int(line["color"].split("#")[1], 16))};font-size:16px;font-family'
                            f':Gilroy,system-ui,-apple-system,Segoe UI,Roboto,Ubuntu,Cantarell,Noto Sans,'
                            f'sans-serif;"><b>&lt;{line["name"]}{line["gendertag"]}&gt;:</b> Has just tipped '
                            f'{line["credits"]} PD for: <i>{insert_emoji(html.escape(line["message"]))}</i></div>')
        elif line['type'] == 'subscription':
            text.append(f'<div style="color:{line["color"]};font-weight: 500;background-color:#'
                        f'{"%0.6X" % (0xFFFFFF - int(line["color"].split("#")[1], 16))};font-size:16px;font-family'
                        f':Gilroy,system-ui,-apple-system,Segoe UI,Roboto,Ubuntu,Cantarell,Noto Sans,'
                        f'sans-serif;"><b>{line["name"]}{line["gendertag"]} '
                        f'{insert_emoji(html.escape(line["message"]))}</b></div>')
        elif line['type'] == 'milestone':
            text.append(f'<div style="color:{line["color"]};font-weight: 500;background-color:#'
                        f'{"%0.6X" % (0xFFFFFF - int(line["color"].split("#")[1], 16))};font-size:16px;font-family'
                        f':Gilroy,system-ui,-apple-system,Segoe UI,Roboto,Ubuntu,Cantarell,Noto Sans,'
                        f'sans-serif;"><b>&lt;{line["name"]}:</b> <i>'
                        f'{insert_emoji(html.escape(line["message"]))}</i></div>')
        elif line['type'] == 'system':
            text.append(f'<div style="color:{line["color"]};font-weight: 500;font-size:16px;font-family:Gilroy,'
                        f'system-ui,-apple-system,Segoe UI,Roboto,Ubuntu,Cantarell,Noto Sans,sans-ser'
                        f'if;"><i>&lt;{line["name"]}{line["gendertag"]}&gt;: '
                        f'{insert_emoji(html.escape(line["message"]))}</i></div>')
    return ''.join(text)


def tag_gender(gender, trans):
    tag = ""
    if gender == "female":
        tag = ' <img src="PSChatDisplay/icons/female.svg">'
    elif gender == "male":
        tag = ' <img src="PSChatDisplay/icons/male.svg">'
    elif gender == "couple":
        tag = ' <img src="PSChatDisplay/icons/couple.svg">'
    elif gender == "team":
        tag = ' <img src="PSChatDisplay/icons/team.svg">'
    elif gender == "non-binary":
        tag = ' <img src="PSChatDisplay/icons/non-binary.svg">'
    if trans:
        tag += '<img src="PSChatDisplay/icons/trans.svg">'
    return tag


def gui_thread(pipe):
    class SvgTextObject(QObject, QTextObjectInterface):
        def intrinsicSize(self, doc, pos_in_document, t_format):
            renderer = QSvgRenderer(t_format.property(Window.SvgData))
            size = renderer.defaultSize()

            if size.height() > 25:
                size *= 25.0 / size.height()

            return QSizeF(size)

        def drawObject(self, painter, rect, doc, pos_in_document, t_format):
            renderer = QSvgRenderer(t_format.property(Window.SvgData))
            renderer.render(painter, rect)

    class TextEdit(QTextBrowser):
        def __init__(self):
            QTextBrowser.__init__(self)
            self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            self.timer = QTimer()
            self.timer.timeout.connect(self.handleTimer)
            self.timer.start(100)

        def handleTimer(self):
            self.setHtml(pipe.recv())
            self.moveCursor(QTextCursor.End)
            self.ensureCursorVisible()

    class Window(QWidget):
        SvgTextFormat = QTextFormat.UserObject + 1

        SvgData = 1

        def __init__(self):
            super(Window, self).__init__()
            self.textEdit = TextEdit()
            self.textEdit.setReadOnly(True)
            self.textEdit.setTextInteractionFlags(Qt.TextInteractionFlag.LinksAccessibleByMouse)
            self.textEdit.setOpenExternalLinks(True)
            self.textEdit.setFontFamily("Gilroy,system-ui,-apple-system,Segoe UI,Roboto,Ubuntu,Cantarell,Noto Sans,"
                                        "sans-serif")
            main_layout = QVBoxLayout()
            main_layout.addWidget(self.textEdit)
            self.setLayout(main_layout)
            self.setWindowTitle("Chat Window")

    width = 300
    height = 700

    app = QApplication([])

    window = Window()
    # window.setWindowOpacity(.5) # Hopefully this is not needed on Windows, but its here just in case
    window.setAttribute(Qt.WA_TranslucentBackground, True)
    window.setAttribute(Qt.WA_NoSystemBackground, True)
    window.setWindowFlags(Qt.FramelessWindowHint)
    window.resize(width, height)

    palette = QPalette()
    palette.setColor(QPalette.Text, Qt.white)
    palette.setColor(QPalette.Base, QColor(35, 17, 55, 128))
    app.setPalette(palette)

    window.show()
    app.exec_()


parent_conn, child_conn = Pipe()
p = Process(target=gui_thread, args=(child_conn,), daemon=True)
p.start()

color_names = {"deep_sky_blue": "#00BFFF", "light_green": "#90EE90", "california": "#FE9D04", "malachite": "#369496",
               "razzmatazz": "#E30B5C", "crusta": "#FD7B33", "supernova": "#FFC901", "dolly": "#F9FF8B",
               "java_green": "#1FC2C2", "pomegranate": "#F34723", "sunset": "#FE4C40", "radical_red": "#FF355E",
               "ecstasy": "#FA7814", "edward": "#A2AEAB", "riptide": "#8BE6D8", "han_purple": "#5218FA",
               "iris_blue": "#5A4FCF", "saffron": "#F4C430", "indigo": "#4B0082", "medium_purple": "#9370DB",
               "slate_purple": "#8A5ACD", "yellow": "#FFFF00", "spray_blue": "#C5DBCA"}


class ChatDisplay:
    @staticmethod
    def on_message(channel, message):
        if message['user']:
            color = message['user']['color']
            if color in color_names:
                color = color_names[color]
            if color[0] != '#':
                print(f"Unknown color: {color}")
                color = '#FFFFFF'
            if message['type'] == 'normal':
                chat.append({"id": message['id'], "type": "normal", "name": message['user']['name'],
                             "gendertag": tag_gender(message['user']['gender'], message['user']['is_trans']),
                             "color": color, "message": message['content'], "credits": message['credits']})
            elif message['type'] == 'tip':
                chat.append({"id": message['id'], "type": "tip", "name": message['user']['name'],
                             "gendertag": tag_gender(message['user']['gender'], message['user']['is_trans']),
                             "color": color, "message": message['content'], "credits": message['credits']})
                if message['play_sound']:
                    playsound('scripts/PSChatDisplay/sfx/tip.mp3')
            elif message['type'] == 'subscription':
                chat.append({"id": message['id'], "type": "subscription", "name": message['user']['name'],
                             "gendertag": tag_gender(message['user']['gender'], message['user']['is_trans']),
                             "color": color, "message": "Subscribed to the channel!", "credits": message['credits']})
                if message['play_sound']:
                    playsound('scripts/PSChatDisplay/sfx/subscription.mp3')
        elif message['type'] == 'milestone':
            chat.append({"id": message['id'], "type": "milestone", "name": "Milestone Reached", "gendertag": "",
                         "color": "#00ff00", "message": message['content'], "credits": message['credits']})
            if message['play_sound']:
                playsound('scripts/PSChatDisplay/sfx/milestone.mp3')
        elif message['type'] == 'system':
            chat.append({"id": message['id'], "type": "system", "name": "System", "gendertag": "", "color": "#00ff00",
                         "message": message['content'], "credits": message['credits']})
        while len(chat) > 50:
            chat.pop(0)
        parent_conn.send(format_chat(chat))

    @staticmethod
    def on_messagedeleted(channel, message_id):
        for line in chat:
            if line['id'] == message_id:
                chat.remove(line)
                parent_conn.send(format_chat(chat))


PlexLib.register_callback("on_message", ChatDisplay.on_message)
