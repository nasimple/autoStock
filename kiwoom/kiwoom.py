from PyQt5.QAxContainer import *
from PyQt5.QtCore import *
from config.errorCode import *

class Kiwoom(QAxWidget):
   def __init__(self):
      super().__init__()
      print("Kiwoom() class start.")
      
      ####### event loop를 실행하기 위한 변수모음
      self.login_event_loop = QEventLoop() #로그인을 이벤트 루프 안에서 실행하도록 만들기 위해 선언한 변수
      #########################################
      

      ######### 초기 셋팅 함수들 바로 실행
      self.get_ocx_instance() #Ocx 방식을 파이썬에 사용할 수 있게 변환해 주는 함수 실행
      self.event_slots() #키움과 연결하기 위한 signal / slot 모음 함수 실행
      self.signal_login_commConnect() #로그인 시도 함수 실행
      self.get_account_info() #계좌번호 가져오기
      
      #########################################

   def get_account_info(self):
      account_list = self.dynamicCall("GetLoginInfo(QString)","ACCNO") #계좌번호 변환
      self.account_num = account_list.split(';')[0] # a;b;c > [a,b,c]
      
      print("계좌번호 : %s" %self.account_num)
   
      
   def get_ocx_instance(self):
      self.setControl("KHOPENAPI.KHOpenAPICtrl.1") # 레지스트리에 저장된 API 모듈 불러오기
      
   def event_slots(self):
      self.OnEventConnect.connect(self.login_slot) # 로그인 관련 이벤트
   
      
   def signal_login_commConnect(self):
      self.dynamicCall("CommConnect()")
      
      self.login_event_loop.exec_()

   
   def login_slot(self, err_code):
      print(errors(err_code)[1])
      
      # 로그인 처리가 완료되었으면 이벤트 루프를 종료한다
      self.login_event_loop.exit()      