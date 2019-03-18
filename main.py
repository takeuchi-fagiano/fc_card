from kivy.app import App
from kivy.core.text import LabelBase, DEFAULT_FONT
from kivy.uix.screenmanager import ScreenManager , Screen
from kivy.config import Config
from kivy.clock import Clock
from functools import partial
from kivy.resources import resource_add_path
import sys
import pygame.mixer
import configparser
import csv
import serial

###EXE化対応
if hasattr(sys,'_MEIPASS'):
	resource_add_path(sys._MEIPASS)

###初期化
pygame.init()

###
#resource_add_path('sound')


#起動時にウィンドウを最大化
Config.set('graphics','window_state','maximized')

#デフォルトのフォント設定
LabelBase.register(DEFAULT_FONT, "NotoSansCJKjp-Bold.otf")


#設定ファイルの読み込み
inifile =  configparser.ConfigParser()
inifile.read('config.txt','utf-8')

#シリアル通信
serial_baudrate = 9600
if ( 'baudrate' in map(lambda x:x[0], inifile.items('com'))):
    serial_baudrate = int(inifile.get('com','baudrate' ))

serial_eod = '\r\n'
if ( 'eod' in map(lambda x:x[0], inifile.items('com'))):
    serial_eod = eval('"'+inifile.get('com','eod')+'"')

print('com name='+inifile.get('com','name')+' , baudrate='+ str(serial_baudrate) + ' , eod=' + serial_eod)


#会員番号の辞書
memberdic = {}

#CSVファイルの読み込み
csvfile = open( inifile.get('data','filename') , 'r' , encoding='ms932' , errors='' , newline='') 
f = csv.reader(csvfile , delimiter="," , doublequote=True , lineterminator="\r\n" , quotechar='"' , skipinitialspace=True)
header = next(f)  #1行目はスキップ
for row in f:
    memberdic[row[1]] = row[0]
csvfile.close()


#for key in memberdic.keys():
#    print (key+'='+memberdic[key])


#音の読み込み
found_sound = pygame.mixer.Sound('found.wav')
error_sound = pygame.mixer.Sound('error.wav')


#画面遷移のための準備
sm = ScreenManager()


class MainScreen(Screen):
    #クリアボタンを押したとき
    def clearInput(self):
        self.ids["input_code"].text = ""
        self.ids["member_id"].text = ""
        #self.ids["barcode"].text = ""
        self.ids['message'].text = 'ファンクラブカードをかざしてください' 
        self.ids['message'].color = [0,0,0,1]
        self.bgcolor = [0.9,0.9,0.9,1]
        self.ids['execbtn'].disabled = True 
        #clearsound.play()
        Clock.schedule_once(self.set_focus,0.5)
        return

    #QRコード入力欄にフォーカスを移動する。タイマーで呼び出す必要があるので、関数化しておく
    def set_focus(self,*args):
        self.ids['input_code'].focus = True
        return

    #実行ボタンを押したとき
    def sendID(self):
        #print("send "+ self.ids["member_id"].text)
        try:
            #シリアル通信
            s = serial.Serial(inifile.get('com','name') , serial_baudrate)
            send_data = self.ids["member_id"].text + serial_eod
            s.write(send_data.encode())
            s.close()
            #実行ボタンを不可に。二度押しを避けるため。
            self.ids['execbtn'].disabled = True 
            #次の入力に備えて、入力情報をクリアする
            self.clearInput()
        except ( OSError, serial.SerialException):
            #エラーメッセージの表示
            self.disp_error("レジと通信できませんでした")
        return

    #エラーメッセージの表示
    def disp_error(self,msg):
        self.ids["message"].text = msg
        self.ids['message'].color = [1,0,0,1]
        self.bgcolor = [1,1,0.6,1]
        error_sound.play()

    #画面右上に表示する年度を返す
    def getYear(self):
        return inifile.get('data','year')

    #QRコードを読み込んだ時
    def enterCode(self):
        code = self.ids['input_code'].text

        #csvファイルにデータがあるかどうか確認
        if  code in memberdic.keys():
            #会員番号の表示
            self.ids['member_id'].text = memberdic[code] 
            #会員番号をバーコードで表示
            #self.ids['barcode'].text = memberdic[code]  #TODO JANCODE化
            #メッセージを表示
            self.ids['message'].text = '実行を押してください'
            self.ids['message'].color = [0,0,0,1]
            self.bgcolor = [0.9,0.9,0.9,1]
            #実行ボタンを押せるようにする
            self.ids['execbtn'].disabled = False 
            #音を鳴らす
            found_sound.play()
        else:
            #QRコードがcsvになかった(カード間違いなど)
            #読みこんんだQRコードをクリア
            self.ids['input_code'].text = ''
            #会員番号をクリア（念のため）
            self.ids['member_id'].text = ''
            #self.ids["barcode"].text = ""
            #メッセージを表示
            self.disp_error('カードを確認してください\nパートナーパス・法人パス等は対象外です。') 
            #QRコード読み込み欄にフォーカスを移動。Clockつかってやらないと、フォーカスは移動しない
            Clock.schedule_once(self.set_focus,0.5)
        
        return
    
###TOPクラス
class ExpenseApp(App):
    def build(self):
        sm.add_widget(MainScreen(name="main"))
        return sm

###実行
if __name__ == '__main__':
    ExpenseApp().run()
