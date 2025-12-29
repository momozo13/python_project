#-*- coding: utf-8 -*-
from kivy.app import App
from kivy.properties import ListProperty,NumericProperty
from kivy.core.text import LabelBase, DEFAULT_FONT
from kivy.resources import resource_add_path
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.core.window import Window
from kivy.uix.dropdown import DropDown
from kivy.uix.behaviors.focus import FocusBehavior
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.utils import get_color_from_hex
from kivy.uix.textinput import TextInput
import random
import textinput4ja

# KVファイルのロード
# Builder.load_file('MainWidget.kv')

# Windowsサイズ
# Window.size = (1400, 900)
Window.fullscreen = 'auto'

# デフォルトに使用するフォントを変更する
resource_add_path('./fonts')
LabelBase.register(DEFAULT_FONT, 'mplus-2c-regular.ttf')

# 色セット
red = get_color_from_hex('#FF7777')
green3 = get_color_from_hex('#1A5319')
green2 = get_color_from_hex('#508D4E')
green = get_color_from_hex('#80AF81')
default = [1, 1, 1, 1]
disable = [0, 0, 0, 0]

# ゲーム参加者クラス
class Player:
    def __init__(self, name, position='', is_alive=True):
        self.name = name
        self.position = position
        self.is_alive = is_alive

    def __str__(self):
        return f"Player(name={self.name}, position={self.position}, is_alive={self.is_alive})"

# メインクラス
class MainWidget(Widget):

    # 参加者表示用リスト
    memberCaptionList = ListProperty(['' for _ in range(20)])
    #memberCaptionList = ['めかぶ','ももぞー','MOKO','マロン＠カフェ','けい','さるのすけ','まみこ','まっこり','りーこ','volvox','もも','akkiy','ナギ','よう☆','のんひる','','','','','']
    
    # ゲームメンバー管理用リスト
    regCaptionList = ListProperty(['' for _ in range(16)])

    # 役職数
    jinroCount = NumericProperty(3)
    uragiriCount = NumericProperty(1)
    reibaiCount = NumericProperty(1)
    uranaiCount = NumericProperty(1)
    bodyguardCount = NumericProperty(1)

    # 人狼数調整
    def adjustJinroCount(self, number):
        if (self.jinroCount < 4 and number > 0) or (self.jinroCount > 1 and number < 0):
            self.jinroCount += number

    # 裏切り者数調整
    def adjustUragiriCount(self, number):
        if (self.uragiriCount < 3 and number > 0) or (self.uragiriCount > 0 and number < 0):
            self.uragiriCount += number

    # 占い師数調整
    def adjustUranaiCount(self, number):
        if (self.uranaiCount < 1 and number > 0) or (self.uranaiCount > 0 and number < 0):
            self.uranaiCount += number

    # 霊媒師数調整
    def adjustReibaiCount(self, number):
        if (self.reibaiCount < 2 and number > 0) or (self.reibaiCount > 0 and number < 0):
            self.reibaiCount += number

    # ボディガード数調整
    def adjustBodyguardCount(self, number):
        if (self.bodyguardCount < 1 and number > 0) or (self.bodyguardCount > 0 and number < 0):
            self.bodyguardCount += number

    # 村カウント除外
    def adjustMuraCount(self, regMenmberNo):
        # リストインデックス外であれば変更できない
        if len(self.regList) < regMenmberNo:
            return
        # その人が人狼であれば変更できない
        if self.ids['position_' + str(regMenmberNo)].text == self.POS_JINRO:
        #if self.regList[regMenmberNo-1].position == self.POS_JINRO:
            self.ids['muracnt_' + str(regMenmberNo)].text = '✕'
            return
        # そうでなければ切り替え
        if self.ids['muracnt_' + str(regMenmberNo)].text == '':
            self.ids['muracnt_' + str(regMenmberNo)].text = '✕'
        else: 
            self.ids['muracnt_' + str(regMenmberNo)].text = ''

    def __init__(self, **kwargs):
        super(MainWidget, self).__init__(**kwargs)
        # 参加者管理用リスト
        self.memberList = []
        #self.memberList = ['めかぶ','ももぞー','MOKO','マロン＠カフェ','けい','さるのすけ','まみこ','まっこり','りーこ','volvox','もも','akkiy','ナギ','よう☆','のんひる']
        # ゲームメンバー管理用リスト
        self.regList = []
        # 経過日数
        self.dayNo = 0
        # 前日護衛先
        self.goeiNo = -1
        # 占い履歴
        self.uranaiList = []
        # 処刑先
        self.syokeiIdx = -1

    # 役職名
    POS_JINRO = '人狼'
    POS_URANAI = '占い師'
    POS_REIBAI = '霊媒師'
    POS_BODYGUARD = 'ボディガード'
    POS_KYOJIN = '狂人'

    # 参加者の登録
    def memberRegButtonClicked(self, regName):
        if not regName:
            raise ValueError("名前が入力されていません")
        if len(self.memberList) >= len(self.memberCaptionList):
            raise OverflowError("これ以上登録できません")
        if regName in self.memberList:
            raise ValueError("既に登録されています")
        self.memberList.append(regName)
        self.memberCaptionList[len(self.memberList)-1] = regName
    
    # ポップアップ生成
    def create_popup(self, title, content, size=(800, 400)):
        popup = Popup(
            title=title,
            content=content,
            size_hint=(None, None),
            size=size
        )
        return popup

    # 参加者登録ポップアップ
    def member_reg_popup_open(self):
        def set_focus(dt):
            content_input.focus = True
        def reg():
            try:
                self.memberRegButtonClicked(content_input.text)
                content_message.text = "登録しました"
            except (ValueError,OverflowError) as e:
                content_message.text = str(e)
            if content_message.text == '登録しました':
                content_input.text = ''
            Clock.schedule_once(set_focus, 1)
        content = BoxLayout(orientation="vertical")
        content_select_box = BoxLayout()
        content.add_widget(content_select_box)
        content_input = TextInputX(multiline=False, hint_text='参加者名を入力してください', size_hint_x=8)
        content_select_box.add_widget(content_input)
        content_regist = Button(text="登録", size_hint_x=2)
        content_select_box.add_widget(content_regist)
        content_message = Label()
        content.add_widget(content_message)
        content_close = Button(text="閉じる")
        content.add_widget(content_close)
        popup = self.create_popup('参加者登録', content, size=(800, 400))
        content_close.bind(on_release=popup.dismiss)
        content_input.bind(on_text_validate=lambda content_input: reg())
        content_regist.bind(on_press=lambda content_regist: reg())
        popup.open()

    # 参加者の個別削除
    def memberDelete(self, index):
        if len(self.memberList) > index:
            del self.memberList[index]
            self.memberCaptionList.append('')
            del self.memberCaptionList[index]

    # ゲームメンバーの登録
    def buttonMemberClicked(self, text):
        if text == '':
            print('参加者が登録されていません')
            return
        if len(self.regList) == len(self.regCaptionList):
            print('これ以上登録できません')
            return
        if self.dayNo > 0:
            print('既にゲームが開始されています')
        if any(player.name == text for player in self.regList):
            print('既に登録されています')
            return
        self.regList.append(Player(text))
        self.regCaptionList[len(self.regList)-1] = text

    # ゲームメンバーの個別削除
    def regDelete(self, index):
        if len(self.regList) > index:
            del self.regList[index]
            self.regCaptionList.append('')
            del self.regCaptionList[index]

    # 役職ポップアップ
    def position_popup_open(self, regNo):
        if int(regNo) > len(self.regList):
            return
        content = BoxLayout(orientation="vertical")
        popup = self.create_popup('役職選択', content, size=(700, 600))
        content_select_box = BoxLayout(orientation="vertical")
        content.add_widget(content_select_box)
        # 役職選択ボタン
        positions = [self.POS_JINRO, self.POS_URANAI, self.POS_REIBAI, self.POS_BODYGUARD, self.POS_KYOJIN]
        for pos in positions:
            btn = Button(text=pos)
            btn.bind(on_press=lambda btn, pos=pos: self.selectPosition(regNo, pos))
            btn.bind(on_release=popup.dismiss)
            content_select_box.add_widget(btn)
        # 役職自由入力
        content_edit = BoxLayout(orientation="horizontal")
        content_edit_box = TextInputX(multiline=False, hint_text='役職名を入力してください', size_hint_x=8)
        content_edit.add_widget(content_edit_box)
        btn = Button(text='選択', size_hint_x=2)
        btn.bind(on_press=lambda btn: self.selectPosition(regNo, content_edit_box.text))
        btn.bind(on_release=popup.dismiss)
        content_edit.add_widget(btn)
        content_select_box.add_widget(content_edit)
        content_none = Button(text="なし")
        content_select_box.add_widget(content_none)
        content_none.bind(on_press=lambda content_none: self.selectPosition(regNo, ''))
        content_none.bind(on_release=popup.dismiss)
        popup.open()
    
    #役職選択
    def selectPosition(self, regNo, position):
        self.ids['position_' + str(regNo)].text = position
        if position == self.POS_JINRO:
           self.ids['muracnt_' + str(regNo)].text = '✕'
        else:
            self.ids['muracnt_' + str(regNo)].text = ''
        
    #処刑先選択
    def selectSyokeisaki(self, dayNumber, text, color):
        self.ids['syokei_' + str(dayNumber)].text = text
        self.ids['syokei_' + str(dayNumber)].color = color
        self.syokeiIdx = -1
        try:
            targetName = text[text.find('.')+1:]
        except:
            targetName = ''
        for index, player in enumerate(self.regList):
            if player.name == targetName:
                self.syokeiIdx = index

    # 処刑者選択Popup
    def syokei_popup_open(self, dayNumber):
        content = BoxLayout(orientation="vertical")
        # popup定義
        popup = self.create_popup('処刑者確認', content, size=(500, 1400))
        # 選択アクション
        def selectSyokei(text, color):
            self.selectSyokeisaki(dayNumber, text, color)
            popup.dismiss()
            result = self.judgeResult()
            if result == 1:
                self.confirm_popup_open('村人陣営の勝利です！')
            elif result == 2:
                self.confirm_popup_open('人狼陣営の勝利です！')
        # 日付ラベル
        content.add_widget(Label(text=str(dayNumber) + '日目'))
        # 対象者
        for index, player in enumerate(self.regList):
            if player.is_alive == True:
                if player.position == self.POS_JINRO:
                    btn = Button(text=str(index+1)+'.'+player.name, height=60, background_color=red)
                    btn.bind(on_press=lambda btn: selectSyokei(btn.text, btn.background_color))
                else:
                    btn = Button(text=str(index+1)+'.'+player.name, height=60, background_color=green)
                    btn.bind(on_press=lambda btn: selectSyokei(btn.text, default))
                content.add_widget(btn)
        # 処刑者なし追加
        btn = Button(text='ー', size_hint_y=None, height=60, background_color=green)
        btn.bind(on_press=lambda btn: selectSyokei('選択', default))
        content.add_widget(btn)
        # 選択ボタン
        content_select_box = BoxLayout(orientation="horizontal")
        content.add_widget(content_select_box)
        content_close = Button(text="閉じる", size_hint_y=None, height=80)
        content_select_box.add_widget(content_close)
        content_close.bind(on_release=popup.dismiss)
        popup.open()

    #占い先選択
    def selectUranaisaki(self, dayNumber, text, color):
        self.ids['uranai_' + str(dayNumber)].text = text
        self.ids['uranai_' + str(dayNumber)].color = color

    # 占い先選択Popup
    def uranai_popup_open(self, dayNumber):
        content = BoxLayout(orientation="vertical")
        # popup定義
        popup = self.create_popup('占い先確認', content, size=(500, 1400))
        # 選択アクション
        def selectUranai(text, color):
            self.selectUranaisaki(dayNumber, text, color)
            popup.dismiss()
        # 日付ラベル
        content.add_widget(Label(text=str(dayNumber) + '日目'))
        # 占い師生死判断
        existFlg = False
        for index, player in enumerate(self.regList):
            if player.is_alive == True and player.position == self.POS_URANAI and self.syokeiIdx != index:
                existFlg = True        
        # 対象者
        if existFlg:
            for index, player in enumerate(self.regList):
                if player.is_alive == True:
                    if player.position == self.POS_URANAI:
                        continue
                    elif index in self.uranaiList:
                        continue
                    elif self.ids['syokei_' + str(dayNumber)].text != '選択' and index == int(self.ids['syokei_' + str(dayNumber)].text[:self.ids['syokei_' + str(dayNumber)].text.find('.')])-1:
                        continue
                    elif player.position == self.POS_JINRO:
                        btnContents = BoxLayout(orientation="horizontal", height=60)
                        btn = Button(text=str(index+1)+'.'+player.name, size_hint_x=8, height=60, background_color=red)
                        self.ids['select' + str(index+1)] = btn
                        btn.bind(on_press=lambda btn: selectUranai(btn.text, btn.background_color))
                        btn2 = Button(text=str(index+1), size_hint_x=2, height=60, background_color=green)
                        btn2.bind(on_press=lambda btn2: self.membar_name_popup_open(self.ids['select' + str(btn2.text)].text, ''))
                        btnContents.add_widget(btn2)
                        btnContents.add_widget(btn)
                        content.add_widget(btnContents)
                    else:
                        btnContents = BoxLayout(orientation="horizontal", height=60)
                        btn = Button(text=str(index+1)+'.'+player.name, size_hint_x=8, height=60, background_color=green)
                        self.ids['select' + str(index+1)] = btn
                        btn.bind(on_press=lambda btn: selectUranai(btn.text, default))
                        btn2 = Button(text=str(index+1), size_hint_x=2, height=60, background_color=green)
                        btn2.bind(on_press=lambda btn2: self.membar_name_popup_open(self.ids['select' + str(btn2.text)].text, ''))
                        btnContents.add_widget(btn2)
                        btnContents.add_widget(btn)
                        content.add_widget(btnContents)
            # 占い先なし追加
            btn = Button(text='ー', size_hint_y=None, height=60, background_color=green)
            btn.bind(on_press=lambda btn: selectUranai('選択', default))
            content.add_widget(btn)
        else:
            selectUranai('選択', default)
            content.add_widget(Label(text=self.POS_URANAI + 'が生存していません'))
        # 選択ボタン
        content_select_box = BoxLayout(orientation="horizontal")
        content.add_widget(content_select_box)
        content_close = Button(text="閉じる", size_hint_y=None, height=80)
        content_select_box.add_widget(content_close)
        content_close.bind(on_release=popup.dismiss)
        popup.open()

    #護衛先選択
    def selectGoeisaki(self, dayNumber, text, color):
        self.ids['goei_' + str(dayNumber)].text = text
        self.ids['goei_' + str(dayNumber)].color = color

    # 護衛先選択Popup
    def goei_popup_open(self, dayNumber):
        content = BoxLayout(orientation="vertical")
        # popup定義
        popup = self.create_popup('護衛先確認', content, size=(500, 1400))
        # 選択アクション
        def selectGoei(text, color):
            self.selectGoeisaki(dayNumber, text, color)
            popup.dismiss()
        # 日付ラベル
        content.add_widget(Label(text=str(dayNumber) + '日目'))
        # ボディガード生死判断
        existFlg = False
        for index, player in enumerate(self.regList):
            if player.is_alive == True and player.position == self.POS_BODYGUARD and self.syokeiIdx != index:
                existFlg = True        
        # 対象者
        if existFlg:
            for index, player in enumerate(self.regList):
                if player.is_alive == True:
                    if player.position == self.POS_BODYGUARD:
                        continue
                    elif self.goeiNo == index:
                        continue
                    elif self.ids['syokei_' + str(dayNumber)].text != '選択' and index == int(self.ids['syokei_' + str(dayNumber)].text[:self.ids['syokei_' + str(dayNumber)].text.find('.')])-1:
                        continue
                    elif player.position == self.POS_JINRO:
                        btnContents = BoxLayout(orientation="horizontal", height=60)
                        btn = Button(text=str(index+1)+'.'+player.name, size_hint_x=8, height=60, background_color=red)
                        self.ids['select' + str(index+1)] = btn
                        btn.bind(on_press=lambda btn: selectGoei(btn.text, btn.background_color))
                        btn2 = Button(text=str(index+1), size_hint_x=2, height=60, background_color=green)
                        btn2.bind(on_press=lambda btn2: self.membar_name_popup_open(self.ids['select' + str(btn2.text)].text, ''))
                        btnContents.add_widget(btn2)
                        btnContents.add_widget(btn)
                        content.add_widget(btnContents)
                    else:
                        btnContents = BoxLayout(orientation="horizontal", height=60)
                        btn = Button(text=str(index+1)+'.'+player.name, size_hint_x=8, height=60, background_color=green)
                        self.ids['select' + str(index+1)] = btn
                        btn.bind(on_press=lambda btn: selectGoei(btn.text, default))
                        btn2 = Button(text=str(index+1), size_hint_x=2, height=60, background_color=green)
                        btn2.bind(on_press=lambda btn2: self.membar_name_popup_open(self.ids['select' + str(btn2.text)].text, ''))
                        btnContents.add_widget(btn2)
                        btnContents.add_widget(btn)
                        content.add_widget(btnContents)
            # 護衛先なし追加
            btn = Button(text='ー', size_hint_y=None, height=60, background_color=green)
            btn.bind(on_press=lambda btn: selectGoei('選択', default))
            content.add_widget(btn)
        else:
            selectGoei('選択', default)
            content.add_widget(Label(text=self.POS_BODYGUARD + 'が生存していません'))
        # 選択ボタン
        content_select_box = BoxLayout(orientation="horizontal")
        content.add_widget(content_select_box)
        content_close = Button(text="閉じる", size_hint_y=None, height=80)
        content_select_box.add_widget(content_close)
        content_close.bind(on_release=popup.dismiss)
        popup.open()

    #襲撃先選択
    def selectSyugekisaki(self, dayNumber, text, color):
        self.ids['syugeki_' + str(dayNumber)].text = text
        self.ids['syugeki_' + str(dayNumber)].color = color

    # 襲撃先選択Popup
    def syugeki_popup_open(self, dayNumber):
        content = BoxLayout(orientation="vertical")
        # popup定義
        popup = self.create_popup('襲撃先確認', content, size=(500, 1400))
        # 選択アクション
        def selectSyugeki(text, color):
            self.selectSyugekisaki(dayNumber, text, color)
            popup.dismiss()
        # 日付ラベル
        content.add_widget(Label(text=str(dayNumber) + '日目'))     
        # 対象者
        for index, player in enumerate(self.regList):
            if player.is_alive == True:
                if player.position == self.POS_JINRO:
                    continue
                elif self.ids['syokei_' + str(dayNumber)].text != '選択' and index == int(self.ids['syokei_' + str(dayNumber)].text[:self.ids['syokei_' + str(dayNumber)].text.find('.')])-1:
                    continue
                else:
                    btnContents = BoxLayout(orientation="horizontal", height=60)
                    btn = Button(text=str(index+1)+'.'+player.name, size_hint_x=8, height=60, background_color=green)
                    self.ids['select' + str(index+1)] = btn
                    btn.bind(on_press=lambda btn: selectSyugeki(btn.text, default))
                    btn2 = Button(text=str(index+1), size_hint_x=2, height=60, background_color=green)
                    btn2.bind(on_press=lambda btn2: self.membar_name_popup_open(self.ids['select' + str(btn2.text)].text, ''))
                    btnContents.add_widget(btn2)
                    btnContents.add_widget(btn)
                    content.add_widget(btnContents)
        # 襲撃先なし追加
        btn = Button(text='ー', size_hint_y=None, height=60, background_color=green)
        btn.bind(on_press=lambda btn: selectSyugeki('選択', default))
        content.add_widget(btn)
        # 選択ボタン
        content_select_box = BoxLayout(orientation="horizontal")
        content.add_widget(content_select_box)
        content_close = Button(text="閉じる", size_hint_y=None, height=80)
        content_select_box.add_widget(content_close)
        content_close.bind(on_release=popup.dismiss)
        popup.open()

    #追加死亡1先選択
    def selectTsuikashibou1(self, dayNumber, text, color):
        self.ids['tsuikashibou1_' + str(dayNumber)].text = text
        self.ids['tsuikashibou1_' + str(dayNumber)].color = color

    # 追加死亡1Popup
    def tsuikashibou1_popup_open(self, dayNumber):
        content = BoxLayout(orientation="vertical")
        # popup定義
        popup = self.create_popup('追加死亡者1確認', content, size=(500, 1400))
        # 選択アクション
        def selectTsuikashibou1(text, color):
            self.selectTsuikashibou1(dayNumber, text, color)
            popup.dismiss()
        # 日付ラベル
        content.add_widget(Label(text=str(dayNumber) + '日目'))
        # 対象者
        for index, player in enumerate(self.regList):
            if self.ids['syokei_' + str(dayNumber)].text != '選択' and index == int(self.ids['syokei_' + str(dayNumber)].text[:self.ids['syokei_' + str(dayNumber)].text.find('.')])-1:
                continue
            elif self.ids['syugeki_' + str(dayNumber)].text != '選択' and index == int(self.ids['syugeki_' + str(dayNumber)].text[:self.ids['syugeki_' + str(dayNumber)].text.find('.')])-1:
                continue
            elif player.is_alive == True:
                btn = Button(text=str(index+1)+'.'+player.name, height=60, background_color=green)
                btn.bind(on_press=lambda btn: selectTsuikashibou1(btn.text, default))
                content.add_widget(btn)
        # 死亡者なし追加
        btn = Button(text='ー', size_hint_y=None, height=60, background_color=green)
        btn.bind(on_press=lambda btn: selectTsuikashibou1('選択', default))
        content.add_widget(btn)
        # 選択ボタン
        content_select_box = BoxLayout(orientation="horizontal")
        content.add_widget(content_select_box)
        content_close = Button(text="閉じる", size_hint_y=None, height=80)
        content_select_box.add_widget(content_close)
        content_close.bind(on_release=popup.dismiss)
        popup.open()

    #追加死亡2先選択
    def selectTsuikashibou2(self, dayNumber, text, color):
        self.ids['tsuikashibou2_' + str(dayNumber)].text = text
        self.ids['tsuikashibou2_' + str(dayNumber)].color = color

    # 追加死亡2Popup
    def tsuikashibou2_popup_open(self, dayNumber):
        content = BoxLayout(orientation="vertical")
        # popup定義
        popup = self.create_popup('追加死亡者2確認', content, size=(500, 1400))
        # 選択アクション
        def selectTsuikashibou2(text, color):
            self.selectTsuikashibou2(dayNumber, text, color)
            popup.dismiss()
        # 日付ラベル
        content.add_widget(Label(text=str(dayNumber) + '日目'))
        # 対象者
        for index, player in enumerate(self.regList):
            if self.ids['syokei_' + str(dayNumber)].text != '選択' and index == int(self.ids['syokei_' + str(dayNumber)].text[:self.ids['syokei_' + str(dayNumber)].text.find('.')])-1:
                continue
            elif self.ids['syugeki_' + str(dayNumber)].text != '選択' and index == int(self.ids['syugeki_' + str(dayNumber)].text[:self.ids['syugeki_' + str(dayNumber)].text.find('.')])-1:
                continue
            elif player.is_alive == True:
                btn = Button(text=str(index+1)+'.'+player.name, height=60, background_color=green)
                btn.bind(on_press=lambda btn: selectTsuikashibou2(btn.text, default))
                content.add_widget(btn)
        # 死亡者なし追加
        btn = Button(text='ー', size_hint_y=None, height=60, background_color=green)
        btn.bind(on_press=lambda btn: selectTsuikashibou2('選択', default))
        content.add_widget(btn)
        # 選択ボタン
        content_select_box = BoxLayout(orientation="horizontal")
        content.add_widget(content_select_box)
        content_close = Button(text="閉じる", size_hint_y=None, height=80)
        content_select_box.add_widget(content_close)
        content_close.bind(on_release=popup.dismiss)
        popup.open()

    #追加死亡3先選択
    def selectTsuikashibou3(self, dayNumber, text, color):
        self.ids['tsuikashibou3_' + str(dayNumber)].text = text
        self.ids['tsuikashibou3_' + str(dayNumber)].color = color

    # 追加死亡3Popup
    def tsuikashibou3_popup_open(self, dayNumber):
        content = BoxLayout(orientation="vertical")
        # popup定義
        popup = self.create_popup('追加死亡者3確認', content, size=(500, 1400))
        # 選択アクション
        def selectTsuikashibou3(text, color):
            self.selectTsuikashibou3(dayNumber, text, color)
            popup.dismiss()
        # 日付ラベル
        content.add_widget(Label(text=str(dayNumber) + '日目'))
        # 対象者
        for index, player in enumerate(self.regList):
            if self.ids['syokei_' + str(dayNumber)].text != '選択' and index == int(self.ids['syokei_' + str(dayNumber)].text[:self.ids['syokei_' + str(dayNumber)].text.find('.')])-1:
                continue
            elif self.ids['syugeki_' + str(dayNumber)].text != '選択' and index == int(self.ids['syugeki_' + str(dayNumber)].text[:self.ids['syugeki_' + str(dayNumber)].text.find('.')])-1:
                continue
            elif player.is_alive == True:
                btn = Button(text=str(index+1)+'.'+player.name, height=60, background_color=green)
                btn.bind(on_press=lambda btn: selectTsuikashibou3(btn.text, default))
                content.add_widget(btn)
        # 死亡者なし追加
        btn = Button(text='ー', size_hint_y=None, height=60, background_color=green)
        btn.bind(on_press=lambda btn: selectTsuikashibou3('選択', default))
        content.add_widget(btn)
        # 選択ボタン
        content_select_box = BoxLayout(orientation="horizontal")
        content.add_widget(content_select_box)
        content_close = Button(text="閉じる", size_hint_y=None, height=80)
        content_select_box.add_widget(content_close)
        content_close.bind(on_release=popup.dismiss)
        popup.open()

    # 確認ポップアップ
    def confirm_popup_open(self, message):
        content = BoxLayout(orientation="vertical")
        content.add_widget(Label(text=message))
        content_select_box = BoxLayout(orientation="horizontal")
        content.add_widget(content_select_box)
        content_close = Button(text="閉じる")
        content_select_box.add_widget(content_close)
        popup = self.create_popup('確認', content, size=(1000, 400))
        content_close.bind(on_release=popup.dismiss)
        popup.open()

    # 選択ポップアップ
    def select_popup_open(self, message, syoriType):
        content = BoxLayout(orientation="vertical")
        content.add_widget(Label(text=message))
        content_select_box = BoxLayout(orientation="horizontal")
        content.add_widget(content_select_box)
        content_close = Button(text="いいえ")
        content_yes = Button(text="はい")
        content_select_box.add_widget(content_close)
        content_select_box.add_widget(content_yes)
        popup = self.create_popup('確認', content, size=(900, 400))
        content_close.bind(on_release=popup.dismiss)
        if syoriType == 1:
            content_yes.bind(on_press=lambda content_yes: self.memberResetExecute())
        elif syoriType == 2:
            content_yes.bind(on_press=lambda content_yes: self.regResetExecute())
        elif syoriType == 3:
            content_yes.bind(on_press=lambda content_yes: self.gameResetExecute())
        elif syoriType == 5:
            content_yes.bind(on_press=lambda content_yes: self.next_day())
        elif syoriType == 6:
            content_yes.bind(on_press=lambda content_yes: self.game_start_execute())
        elif syoriType == 7:
            content_yes.bind(on_press=lambda content_yes: self.autoPositon())
        content_yes.bind(on_release=popup.dismiss)
        popup.open()

    # メンバー名拡張表示　ポップアップ
    def membar_name_popup_open(self, name, no):
        if name == '':
            return
        if no == '':
            no = name[:name.find('.')]
            name = name[name.find('.')+1:]
        content = BoxLayout(orientation="vertical")
        content_close = Button(text="閉じる",size_hint_y=0.1, size_hint_x=1.0)
        content.add_widget(content_close)
        content.add_widget(Label(text=no,font_size='250sp'))
        content.add_widget(Label(text=name,font_size='150sp'))
        popup = self.create_popup('メンバー名称', content, size=(2570, 1550))
        content_close.bind(on_release=popup.dismiss)
        popup.open()

    # ランダム処刑　ポップアップ
    def randam_syokei_popup_open(self):
        targetNameList = ['','','']
        content = BoxLayout(orientation="horizontal")
        selectBox = BoxLayout(orientation="vertical",)
        # 対象者
        for index, player in enumerate(self.regList):
            if player.is_alive == True:
                btn = Button(text=str(index+1)+'.'+player.name, height=60, background_color=green)
                selectBox.add_widget(btn)
        content.add_widget(selectBox)
        targetBox = BoxLayout(orientation="vertical")
        target1Box = BoxLayout(orientation="horizontal")
        target1Button = Button(text=targetNameList[0])
        target1DelButton = Button(text="✕")
        target1Box.add_widget(target1Button)
        target1Box.add_widget(target1DelButton)
        targetBox.add_widget(target1Box)
        target2Box = BoxLayout(orientation="horizontal")
        target2Button = Button(text=targetNameList[1])
        target2DelButton = Button(text="✕")
        target2Box.add_widget(target2Button)
        target2Box.add_widget(target2DelButton)
        targetBox.add_widget(target2Box)
        target3Box = BoxLayout(orientation="horizontal")
        target3Button = Button(text=targetNameList[2])
        target3DelButton = Button(text="✕")
        target3Box.add_widget(target3Button)
        target3Box.add_widget(target3DelButton)
        targetBox.add_widget(target3Box)
        content.add_widget(targetBox)
        #content.add_widget(Label(text='1',font_size='300sp'))
        #content.add_widget(Label(text='moko',font_size='150sp'))
        content_close = Button(text="閉じる")
        #content.add_widget(content_close)
        popup = self.create_popup('メンバー名称', content, size=(2500, 1500))
        content_close.bind(on_release=popup.dismiss)
        popup.open()

    # 参加者とゲームメンバーの登録をクリアする
    def memberResetClicked(self):
        self.select_popup_open("参加者とゲームメンバー登録をリセットします", 1)

    # 参加者リセット
    def memberResetExecute(self):
        self.memberList = []
        self.memberCaptionList = ['' for _ in range(20)]
        self.regList = []
        self.regCaptionList = ['' for _ in range(16)]

    # ゲームメンバーの登録をクリアする
    def regResetClicked(self):
        self.select_popup_open("ゲームメンバー登録をリセットします", 2)

    # ゲームメンバーリセット
    def regResetExecute(self):
        self.gameResetExecute()
        self.regList = []
        self.regCaptionList = ['' for _ in range(16)]

    # ゲーム内容をリセットする
    def gameResetClicked(self):
        self.select_popup_open("ゲーム内容をリセットします", 3)

    # ゲームリセット
    def gameResetExecute(self):
        for i in range(1,self.dayNo+1):
            targetBox = self.ids['day' + str(i) + '_result']
            targetBox.clear_widgets()
        self.dayNo = 0
        self.goeiNo = -1
        self.uranaiList = []
        for index,player in enumerate(self.regList):
            player.position = ''
            player.is_alive = True
            self.ids['reg_delete_' + str(index + 1)].disabled = False
            self.ids['position_' + str(index + 1)].text = ''
            self.ids['position_' + str(index + 1)].disabled = False
            self.ids['otsuge_' + str(index + 1)].text = ''
            self.ids['otsuge_' + str(index + 1)].disabled = False
            self.ids['muracnt_' + str(index + 1)].text = ''
            self.ids['muracnt_' + str(index + 1)].disabled = False
            self.ids['reg' + str(index + 1)].background_color=default
            
    # ゲーム開始ボタン
    def game_start(self):
        if self.dayNo > 0:
            self.confirm_popup_open("既にゲームは開始しています")
            return
        jinroCnt = int(self.ids['jinroCnt'].text)
        uragiriCnt = int(self.ids['uragiriCnt'].text)
        reibaiCnt = int(self.ids['reibaiCnt'].text)
        totalCnt = jinroCnt + uragiriCnt + reibaiCnt + 2
        if len(self.regList) < totalCnt:
            self.confirm_popup_open("ゲーム参加者は最低"+str(totalCnt)+"人必要です")
            return
        jinroCnt = 0
        for index in range(len(self.regList)):
            if self.ids['position_' + str(index + 1)].text == self.POS_JINRO:
                jinroCnt += 1
        if jinroCnt == 0:
            self.confirm_popup_open("人狼役を最低一人は設定してください")
            return
        self.select_popup_open("ゲームを開始します。役職、お告げ設定を確認してください。", 6)

    # ゲーム開始
    def game_start_execute(self):
        if self.dayNo == 0:
            for index,player in enumerate(self.regList):
                player.position = self.ids['position_' + str(index + 1)].text
                if player.position == self.POS_JINRO:
                    self.ids['reg' + str(index + 1)].background_color=red
                self.ids['position_' + str(index + 1)].disabled = True
                if self.ids['otsuge_' + str(index + 1)].text == '◯':
                    self.uranaiList.append(index)
                self.ids['reg_delete_' + str(index + 1)].disabled = True
                self.ids['otsuge_' + str(index + 1)].disabled = True
                self.ids['muracnt_' + str(index + 1)].disabled = True
                player.is_alive = True # 1を生存、0は死亡とする
            self.dayNo += 1
            self.next_step(self.dayNo)
            return
        else:
            self.confirm_popup_open("既にゲームは開始しています")

    # 自動お告げ
    def autoSetting(self):
        if self.dayNo > 0:
            self.confirm_popup_open("既にゲームは開始しています")
            return
        if len(self.regList) == 0:
            return
        otsugeList = []
        for index,player in enumerate(self.regList):
            player.position = self.ids['position_' + str(index + 1)].text
            self.ids['otsuge_' + str(index + 1)].text = ''
            if player.position != self.POS_JINRO and player.position != self.POS_URANAI:
                otsugeList.append(index)
        if otsugeList:
            self.ids['otsuge_' + str(random.choice(otsugeList) + 1)].text = '◯'     

    # 自動配役確認
    def autoPositionClicked(self):
        self.select_popup_open("配役をリセットし、自動配役を行います", 7) 

    # 自動配役
    def autoPositon(self):
        if self.dayNo > 0:
            self.confirm_popup_open("既にゲームは開始しています")
            return
        jinroCnt = int(self.ids['jinroCnt'].text)
        uragiriCnt = int(self.ids['uragiriCnt'].text)
        uranaiCnt = int(self.ids['uranaiCnt'].text)
        reibaiCnt = int(self.ids['reibaiCnt'].text)
        bodyguardCnt = int(self.ids['bodyguardCnt'].text)
        totalCnt = jinroCnt + uragiriCnt + uranaiCnt + reibaiCnt + bodyguardCnt
        if len(self.regList) < totalCnt:
            self.confirm_popup_open("ゲームメンバーが足りません")
            return
        posList = []
        for index,player in enumerate(self.regList):
            player.position = ''
            self.ids['position_' + str(index + 1)].text = ''
            self.ids['otsuge_' + str(index + 1)].text = ''
            self.ids['muracnt_' + str(index + 1)].text = ''
        # 人狼1配役
        for index,player in enumerate(self.regList):
            if player.position == '':
                posList.append(index)
        if posList:
            selected = random.choice(posList)
            self.ids['position_' + str(selected + 1)].text = self.POS_JINRO
            self.ids['muracnt_' + str(selected + 1)].text = '✕'
            self.regList[selected].position = self.POS_JINRO
        # 人狼2配役
        if jinroCnt > 1: 
            posList = []
            for index,player in enumerate(self.regList):
                if player.position == '':
                    posList.append(index)
            if posList:
                selected = random.choice(posList)
                self.ids['position_' + str(selected + 1)].text = self.POS_JINRO
                self.ids['muracnt_' + str(selected + 1)].text = '✕'
                self.regList[selected].position = self.POS_JINRO
        # 人狼3配役
        if jinroCnt > 2: 
            posList = []
            for index,player in enumerate(self.regList):
                if player.position == '':
                    posList.append(index)
            if posList:
                selected = random.choice(posList)
                self.ids['position_' + str(selected + 1)].text = self.POS_JINRO
                self.ids['muracnt_' + str(selected + 1)].text = '✕'
                self.regList[selected].position = self.POS_JINRO
        # 人狼4配役
        if jinroCnt > 3: 
            posList = []
            for index,player in enumerate(self.regList):
                if player.position == '':
                    posList.append(index)
            if posList:
                selected = random.choice(posList)
                self.ids['position_' + str(selected + 1)].text = self.POS_JINRO
                self.ids['muracnt_' + str(selected + 1)].text = '✕'
                self.regList[selected].position = self.POS_JINRO
        # 占い師配役
        if uranaiCnt > 0:
            posList = []
            for index,player in enumerate(self.regList):
                if player.position == '':
                    posList.append(index)
            if posList:
                selected = random.choice(posList)
                self.ids['position_' + str(selected + 1)].text = self.POS_URANAI
                self.regList[selected].position = self.POS_URANAI
        # 霊媒師1配役
        if reibaiCnt > 0:
            posList = []
            for index,player in enumerate(self.regList):
                if player.position == '':
                    posList.append(index)
            if posList:
                selected = random.choice(posList)
                self.ids['position_' + str(selected + 1)].text = self.POS_REIBAI
                self.regList[selected].position = self.POS_REIBAI
        # 霊媒師2配役
        if reibaiCnt > 1:
            posList = []
            for index,player in enumerate(self.regList):
                if player.position == '':
                    posList.append(index)
            if posList:
                selected = random.choice(posList)
                self.ids['position_' + str(selected + 1)].text = self.POS_REIBAI
                self.regList[selected].position = self.POS_REIBAI
        # ボディガード配役
        if bodyguardCnt > 0:
            posList = []
            for index,player in enumerate(self.regList):
                if player.position == '':
                    posList.append(index)
            if posList:
                selected = random.choice(posList)
                self.ids['position_' + str(selected + 1)].text = self.POS_BODYGUARD
                self.regList[selected].position = self.POS_BODYGUARD
        # 裏切者1配役
        if uragiriCnt > 0:
            posList = []
            for index,player in enumerate(self.regList):
                if player.position == '':
                    posList.append(index)
            if posList:
                selected = random.choice(posList)
                self.ids['position_' + str(selected + 1)].text = self.POS_KYOJIN
                self.regList[selected].position = self.POS_KYOJIN
        # 裏切者2配役
        if uragiriCnt > 1:
            posList = []
            for index,player in enumerate(self.regList):
                if player.position == '':
                    posList.append(index)
            if posList:
                selected = random.choice(posList)
                self.ids['position_' + str(selected + 1)].text = self.POS_KYOJIN
                self.regList[selected].position = self.POS_KYOJIN
        # 裏切者3配役
        if uragiriCnt > 2:
            posList = []
            for index,player in enumerate(self.regList):
                if player.position == '':
                    posList.append(index)
            if posList:
                selected = random.choice(posList)
                self.ids['position_' + str(selected + 1)].text = self.POS_KYOJIN
                self.regList[selected].position = self.POS_KYOJIN

    # 夜へ
    def next_step(self, dayNumber):
        result = self.judgeResult()
        if result == 1:
            self.confirm_popup_open('村人陣営の勝利です！')
            return
        elif result == 2:
            self.confirm_popup_open('人狼陣営の勝利です！')
            return
        targetBox = self.ids['day' + str(dayNumber) + '_result']
        # 日付ラベル
        button = Button(text=str(dayNumber) + '日目', font_size=20, background_color=green3);
        targetBox.add_widget(button)
        # 処刑先
        label = Label(text='【処刑者】', size_hint_y=None, height=80);
        targetBox.add_widget(label)
        #dropdown = DropDown()
        #syokeiOpeBox = BoxLayout(orientation="horizontal", size_hint_y=None, height=80)
        mainbutton = Button(text="選択", size_hint=(1, 0.8), pos_hint={"y": 0.9}, disabled_color=default)
        targetBox.add_widget(mainbutton)
        #randombutton = Button(text="ランダム", size_hint=(1, 0.8), pos_hint={"y": 0.9}, disabled_color=default)
        #targetBox.add_widget(randombutton)
        self.ids['syokei_' + str(dayNumber)] = mainbutton
        mainbutton.bind(on_release= lambda btn: self.syokei_popup_open(dayNumber))
        #randombutton.bind(on_release= lambda btn: self.randam_syokei_popup_open())
        #targetBox.add_widget(syokeiOpeBox)
        # 占い先
        label = Label(text='【占い先】', size_hint_y=None, height=80);
        targetBox.add_widget(label)
        existFlg = False
        for player in self.regList:
            if player.is_alive == True and player.position == self.POS_URANAI:
                existFlg = True
        if existFlg:
            mainbutton2 = Button(text="選択", size_hint=(1, 0.8), pos_hint={"y": 0.9}, disabled_color=default)
            self.ids['uranai_' + str(dayNumber)] = mainbutton2
            mainbutton2.bind(on_release= lambda btn: self.uranai_popup_open(dayNumber))
        else:
            mainbutton2 = Button(text="-", size_hint=(1, 0.8), pos_hint={"y": 0.9}, disabled_color=default)
            self.ids['uranai_' + str(dayNumber)] = mainbutton2
        targetBox.add_widget(mainbutton2)
        # 護衛先
        label = Label(text='【護衛先】', size_hint_y=None, height=80);
        targetBox.add_widget(label)
        existFlg = False
        for player in self.regList:
            if player.is_alive == True and player.position == self.POS_BODYGUARD:
                existFlg = True
        if existFlg:
            mainbutton3 = Button(text="選択", size_hint=(1, 0.8), pos_hint={"y": 0.9}, disabled_color=default)
            self.ids['goei_' + str(dayNumber)] = mainbutton3
            mainbutton3.bind(on_release= lambda btn: self.goei_popup_open(dayNumber))
        else:
            mainbutton3 = Button(text="-", size_hint=(1, 0.8), pos_hint={"y": 0.9}, disabled_color=default)
            self.ids['goei_' + str(dayNumber)] = mainbutton3
        targetBox.add_widget(mainbutton3)
        # 襲撃先
        label = Label(text='【襲撃先】', size_hint_y=None, height=80);
        targetBox.add_widget(label)
        mainbutton4 = Button(text="選択", size_hint=(1, 0.8), pos_hint={"y": 0.9}, disabled_color=default)
        self.ids['syugeki_' + str(dayNumber)] = mainbutton4
        mainbutton4.bind(on_release= lambda btn: self.syugeki_popup_open(dayNumber))
        targetBox.add_widget(mainbutton4)
        # 追加死亡1
        label = Label(text='【追加死亡】', size_hint_y=None, height=80);
        targetBox.add_widget(label)
        mainbutton5 = Button(text="選択", size_hint=(1, 0.8), pos_hint={"y": 0.9}, disabled_color=default)
        self.ids['tsuikashibou1_' + str(dayNumber)] = mainbutton5
        mainbutton5.bind(on_release= lambda btn: self.tsuikashibou1_popup_open(dayNumber))
        targetBox.add_widget(mainbutton5)
        # 追加死亡2
        mainbutton6 = Button(text="選択", size_hint=(1, 0.8), pos_hint={"y": 0.9}, disabled_color=default)
        self.ids['tsuikashibou2_' + str(dayNumber)] = mainbutton6
        mainbutton6.bind(on_release= lambda btn: self.tsuikashibou2_popup_open(dayNumber))
        targetBox.add_widget(mainbutton6)
        # 追加死亡3
        mainbutton7 = Button(text="選択", size_hint=(1, 0.8), pos_hint={"y": 0.9}, disabled_color=default)
        self.ids['tsuikashibou3_' + str(dayNumber)] = mainbutton7
        mainbutton7.bind(on_release= lambda btn: self.tsuikashibou3_popup_open(dayNumber))
        targetBox.add_widget(mainbutton7)
        # 決定ボタン
        btn = Button(text='決定', size_hint_y=None, height=150, background_color=green2)
        btn.bind(on_release= lambda btn: self.select_popup_open('次の日に進んでもよろしいですか', 5))
        self.ids['next_day_' + str(dayNumber)] = btn
        targetBox.add_widget(btn)

    # 結果判定
    def judgeResult(self):
        result = 0
        jinro = 0
        mura = 0
        for index, player in enumerate(self.regList):
            if player.is_alive == True and index != self.syokeiIdx:
                if player.position == self.POS_JINRO:
                    jinro += 1
                elif self.ids['muracnt_' + str(index + 1)].text == '':
                    mura += 1
        if jinro == 0:
            result = 1 #村陣営勝利
        elif mura <= jinro:
            result = 2 #人狼陣営勝利
        return result

    # 次の日へ（いったん7日目までとする）
    def next_day(self):
        if self.dayNo < 7:
            syokei = self.ids['syokei_' + str(self.dayNo)].text
            uranaiSyokeiFlg = False
            bodyGuardSyokeiFlg = False
            try:
                syokeiTgtIdx = int(syokei[:syokei.find('.')])-1
                if self.regList[syokeiTgtIdx].position == self.POS_URANAI:
                    uranaiSyokeiFlg = True
                elif self.regList[syokeiTgtIdx].position == self.POS_BODYGUARD:
                    bodyGuardSyokeiFlg = True
            except:
                syokeiTgtIdx = -1
            uranai = self.ids['uranai_' + str(self.dayNo)].text
            try:
                uranaiTgtIdx = int(uranai[:uranai.find('.')])-1
                if uranaiSyokeiFlg:
                    self.confirm_popup_open(self.POS_URANAI + 'は処刑されています。占い先を更新してください。')
                    return
            except:
                uranaiTgtIdx = -1
            goei = self.ids['goei_' + str(self.dayNo)].text
            try:
                goeiTgtIdx = int(goei[:goei.find('.')])-1
                if bodyGuardSyokeiFlg:
                    self.confirm_popup_open(self.POS_BODYGUARD + 'は処刑されています。護衛先を更新してください。')
                    return
            except:
                goeiTgtIdx = -1
            syugeki = self.ids['syugeki_' + str(self.dayNo)].text
            try:
                syugekiTgtIdx = int(syugeki[:syugeki.find('.')])-1
            except:
                syugekiTgtIdx = -1
            tsuikashibou1 = self.ids['tsuikashibou1_' + str(self.dayNo)].text
            try:
                tsuikashibou1TgtIdx = int(tsuikashibou1[:tsuikashibou1.find('.')])-1
            except:
                tsuikashibou1TgtIdx = -1
            tsuikashibou2 = self.ids['tsuikashibou2_' + str(self.dayNo)].text
            try:
                tsuikashibou2TgtIdx = int(tsuikashibou2[:tsuikashibou2.find('.')])-1
            except:
                tsuikashibou2TgtIdx = -1
            tsuikashibou3 = self.ids['tsuikashibou3_' + str(self.dayNo)].text
            try:
                tsuikashibou3TgtIdx = int(tsuikashibou3[:tsuikashibou3.find('.')])-1
            except:
                tsuikashibou3TgtIdx = -1
            # 襲撃処理
            targetBox = self.ids['day' + str(self.dayNo) + '_result']
            targetBox.remove_widget(self.ids['next_day_' + str(self.dayNo)])
            for index, player in enumerate(self.regList):
                if syokeiTgtIdx == index:
                    player.is_alive = False
                    self.ids['reg' + str(index + 1)].background_color=disable
                    if player.position == self.POS_JINRO:
                        self.ids['syokei_' + str(self.dayNo)].disabled_color=red
                    self.syokeiIdx = -1
                if uranaiTgtIdx == index:
                    self.uranaiList.append(index)
                    if player.position == self.POS_JINRO:
                        self.ids['uranai_' + str(self.dayNo)].disabled_color=red
                if goeiTgtIdx == index:
                    self.goeiNo = index
                    if player.position == self.POS_JINRO:
                        self.ids['goei_' + str(self.dayNo)].disabled_color=red
                if syugekiTgtIdx == index and syugeki != goei:
                    player.is_alive = False
                    self.ids['reg' + str(index + 1)].background_color=disable
                if tsuikashibou1TgtIdx == index:
                    player.is_alive = False
                    self.ids['reg' + str(index + 1)].background_color=disable
                if tsuikashibou2TgtIdx == index:
                    player.is_alive = False
                    self.ids['reg' + str(index + 1)].background_color=disable
                if tsuikashibou3TgtIdx == index:
                    player.is_alive = False
                    self.ids['reg' + str(index + 1)].background_color=disable
            self.ids['syokei_' + str(self.dayNo)].disabled = True
            self.ids['uranai_' + str(self.dayNo)].disabled = True
            self.ids['goei_' + str(self.dayNo)].disabled = True
            self.ids['syugeki_' + str(self.dayNo)].disabled = True
            self.ids['tsuikashibou1_' + str(self.dayNo)].disabled = True
            self.ids['tsuikashibou2_' + str(self.dayNo)].disabled = True
            self.ids['tsuikashibou3_' + str(self.dayNo)].disabled = True
            self.dayNo += 1
            if syugekiTgtIdx == goeiTgtIdx:
                self.confirm_popup_open('昨晩の犠牲者はいませんでした！')
            else:
                self.confirm_popup_open('昨晩の犠牲者は、【' + syugeki + '】さんでした！')
            self.next_step(self.dayNo)
        else:
            self.confirm_popup_open('これ以上はアプリでは進行できません。')

class TextInputX(textinput4ja.TextInput_JA):
    def __init__(self, **kwargs):
        super(TextInputX, self).__init__(**kwargs)
        def set_focus(dt):
            self.focus = True
        Clock.schedule_once(set_focus, 0.1)

class JinroGmApp(App):
    def __init__(self, **kwargs):
        super(JinroGmApp, self).__init__(**kwargs)
        self.title = '人狼GMツール'

if __name__ == '__main__':
    JinroGmApp().run()
