from PyQt5.QAxContainer import *   # PyQt5.QAxConyainer 불러오는 코드
from PyQt5.QtCore import *   # PyQt5.QtCore 안에 이벤트 루프를 실행하는 QEventLoop() 함수를 불러오는 라이브러리
from config.errorCode import *   # config 에러 발생시 나오는 변수 저장소
from PyQt5.QtTest import *

class Kiwoom(QAxWidget):
    def __init__(self):
        super().__init__()
        print("Kiwoom() class start.")

        ####### event loop를 실행하기 위한 변수모음
        self.login_event_loop = QEventLoop() # 로그인을 이벤트 루프 안에서 실행하도록 만들기 위해 선언한 변수
        self.detail_account_info_event_loop = QEventLoop() # 예수금 요청용 이벤트 루프, 쓰레드 간섭 방지


        ### 계좌 관련된 변수 #######################################################################################
        self.account_num = None # 계좌번호 담아주는 변수
        self.deposit = 0 # 예수금
        self.use_money = 0 # 실제 투자에 사용할 금액
        self.use_money_percent = 0.5 # 예수금에서 실제 사용할 비율
        self.output_deposit = 0 # 출금가능 금액
        self.total_profit_loss_money = 0 # 총평가손익금액
        self.total_profit_loss_rate = 0.0 # 총수익률(%)
        self.account_stock_dict = {}
        self.not_account_stock_dict = {}
        self.account_num1 = None # 계좌번호 담아줄 변수
        #self.account_num2 = None # 계좌번호 담아줄 변수


        ### 요청 스크린 번호 #######################################################################################
        self.screen_my_info = "2000" # 계좌 관련된 스크린 번호


        ### 초기 셋팅 함수들 바로 실행 #######################################################################################
        self.get_ocx_instance() # Ocx 방식을 파이썬에 사용할 수 있게 변환해 주는 함수 실행
        self.event_slots() # 키움과 연결하기 위한 signal / slot 모음 함수 실행
        self.signal_login_commConnect() # 로그인 시도 함수 실행
        self.get_account_info() # 계좌번호 가져오기
        self.detail_account_info() # 예수금 요청 시그널 포함
        self.detail_account_mystock() # 계좌평가잔고내역 가져오기
        


    ### "메서드" = 클래스 안에 정의된 "함수" 선언 #######################################################################################
    def get_ocx_instance(self):
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1") # 레지스트리에 저장된 API 모듈 불러오기

    def event_slots(self):
        self.OnEventConnect.connect(self.login_slot) # 로그인 관련 이벤트
        self.OnReceiveTrData.connect(self.trdata_slot) # 트랜잭션(여러 작업을 하나의 '묶음'으로 처리하는 것) 요청 관련 이벤트
        
    def signal_login_commConnect(self):
        self.dynamicCall("CommConnect()")
        self.login_event_loop.exec_()
        
    def login_slot(self, err_code):
        print(errors(err_code)[1])
        self.login_event_loop.exit()
    
    ### 계좌 번호 불러오기 ##################################################################################################################    
    def get_account_info(self):
        
        self.account_list_num = self.dynamicCall("GetLoginInfo(QString)", "ACCOUNT_CNT") # 보유계좌수
        account_list = self.dynamicCall("GetLoginInfo(QString)", "ACCNO") # 계좌번호 불러오기 QString 은 PtQt5에서 제공하는 자동으로 String(문자열)으로 자동으로 변환해주는 기능이다.
        
        # self.account_num1 = account_list_num # 보유계좌수 변수 선언
        self.account_num = account_list.split(';')[0] # a;b;c > [a,b,c]
        
        # self.account_num = account_num # 책에서 안써도 되는 구문이 들어있다 위에서 self.account_num으로 선언되어있어서 어카운트 넘을 다시 어카운트 넘으로 지정 안해도 되는네 지정하는 구문이 추가되있어 지웠다.
        print("보유계좌 수량 : %s" % self.account_list_num)
        print("계좌번호 : %s" % self.account_num)
        
        
    ### 예수금상세현황요청 전문 ##################################################################################################################    
    def detail_account_info(self, sPrevNext="0"):
        self.dynamicCall("SetInputValue(QString, QString)", "계좌번호", self.account_num)
        self.dynamicCall("SetInputValue(QString, QString)", "비밀번호", "0000")
        self.dynamicCall("SetInputValue(QString, QString)", "비밀번호입력매체구분", "00")
        self.dynamicCall("SetInputValue(QString, QString)", "조회구분", "1")
        self.dynamicCall("CommRqData(QString, QString, int, QString)", "예수금상세현황요청", "OPW00001", sPrevNext, self.screen_my_info)
        #self.detail_account_info_event_loop = QEventLoop()
        self.detail_account_info_event_loop.exec_()


    ### 계좌평가잔고내역요청 전문 ##################################################################################################################    
    def detail_account_mystock(self, sPrevNext="0"):
        self.dynamicCall("SetInputValue(QString, QString)", "계좌번호", self.account_num)
        self.dynamicCall("SetInputValue(QString, QString)", "비밀번호", "0000")
        self.dynamicCall("SetInputValue(QString, QString)", "비밀번호입력매체구분", "00")
        self.dynamicCall("SetInputValue(QString, QString)", "조회구분", "1")
        #self.dynamicCall("SetInputValue(QString, QString)", "거래소구분", "KRX:한국거래소")
        self.dynamicCall("CommRqData(QString, QString, int, QString)", "계좌평가잔고내역요청", "OPW00018", sPrevNext, self.screen_my_info)
        #self.detail_account_info_event_loop = QEventLoop()
        self.detail_account_info_event_loop.exec_()


    ### 계좌 미체결불러오기 전문 ##################################################################################################################    
    def not_concluded_account(self, sPrevNext="0"):
        print("미체결 종목 요청")
        
        self.dynamicCall("SetInputValue(QString, QString)", "계좌번호", self.account_num)
        self.dynamicCall("SetInputValue(QString, QString)", "체결구분", "1")
        self.dynamicCall("SetInputValue(QString, QString)", "매매구분", "0")
        self.dynamicCall("CommRqData(QString, QString, int, QString)", "실시간미체결요청", "opt10075", sPrevNext, self.screen_my_info)
        
        self.detail_account_info_event_loop.exec_()
        
        
    ### 멀티 데이터 불러오기 #######################################################################################
    def trdata_slot(self, sScrNo, sRQName, sTrCode, sRecordName, sPrevNext):
        
        ### 예수금 상사현황 불러오기 #######################################################################################
        if sRQName == "예수금상세현황요청":
            self.stop_screen_cancel(self.screen_my_info)
            deposit = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, "예수금")
            self.deposit = int(deposit)

            use_money = float(self.deposit) * self.use_money_percent
            self.use_money = int(use_money)
            self.use_money = self.use_money / 4 # 한 종목 매수 시 돈을 다 쓰지 않게 4종목으로 나눔

            output_deposit = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, "출금가능금액")
            self.output_deposit = int(output_deposit)

            print("예수금 : %s" % self.output_deposit)
            
            self.detail_account_info_event_loop.exit() # 루프 이벤트 발생 변수

        ### 계좌평가잔고내역요청 #######################################################################################
        elif sRQName == "계좌평가잔고내역요청":
            self.stop_screen_cancel(self.screen_my_info)
            total_buy_money = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, "총매입금액")
            self.total_buy_money = int(total_buy_money)

            total_profit_loss_money = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, "총평가손익금액")
            self.total_profit_loss_money = int(total_profit_loss_money)

            total_profit_loss_rate = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, "총수익률(%)")
            self.total_profit_loss_rate = float(total_profit_loss_rate)

            print("계좌평가잔고내역요청 실시간 데이터 : %s - %s - %s" % (total_buy_money, total_profit_loss_money, total_profit_loss_rate))
            
            rows = self.dynamicCall("GetRepeatCnt(QString, QString)", sTrCode, sRQName)
            
            
            ### 멀티데이터 불러오는 포문 #######################################################################################
            for i in range(rows):
                code = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "종목번호")
                code = code.strip()[1:]
                code_nm = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "종목명")
                stock_quantity = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "보유수량")
                buy_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "매입가")
                learn_rate = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "수익률(%)")
                current_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "현재가")
                total_chegual_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "매입금액")
                possible_quantity = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "매매가능수량")
                
                print("종목번호: %s - 종목명: %s - 보유수량: %s - 매입가: %s - 수익률: %s - 현재가: %s" % (code, code_nm, stock_quantity, buy_price, learn_rate, current_price))
                
                if code in self.account_stock_dict:
                    print("매매기록이 없습니다.")
                    pass
                else:
                    self.account_stock_dict[code] = {}
                
                code_nm = code_nm.strip()
                stock_quantity = int(stock_quantity.strip())
                buy_price = int(buy_price.strip())
                learn_rate = float(learn_rate.strip())
                current_price = int(current_price.strip())
                total_chegual_price = int(total_chegual_price.strip())
                possible_quantity = int(possible_quantity.strip())
                
                self.account_stock_dict[code].update({"종목명": code_nm})
                self.account_stock_dict[code].update({"보유수량": stock_quantity})
                self.account_stock_dict[code].update({"매입가": buy_price})
                self.account_stock_dict[code].update({"수익률(%)": learn_rate})
                self.account_stock_dict[code].update({"현재가": current_price})
                self.account_stock_dict[code].update({"매입금액": total_chegual_price})
                self.account_stock_dict[code].update({"매매가능수량": possible_quantity})
                
                print("sPreNext: %s" % sPrevNext)
                print("계좌에 가지고 있는 종목은 %s " % rows)
            
            if sPrevNext == "2":
                self.detail_account_mystock(sPrevNext="2")
            else:
                self.detail_account_info_event_loop.exit()
                
                
        elif sRQName == "실시간미체결요청":
            rows =self.dynamicCall("GetRepeatCnt(QString, QString)", sTrCode, sRQName)
            
            for i in range(rows):
                code = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "종목코드")
                code_nm = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "종목명")
                order_no = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "주문번호")
                order_status = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "주문상태")
                order_quantity = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "주문수량")
                order_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "주문가격")
                order_gubun = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "주문구분") # -매도, +매수, -매도정정, +매수정정
                not_quantity = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "미체결수량")
                ok_quantity = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "체결량")
                
                code = code.strip()
                code_nm = code_nm.strip()
                order_no = int(order_no.strip())
                order_status = order_status.strip()
                order_quantity = int(order_quantity.strip())
                order_price = int(order_price.strip())
                order_gubun = order_gubun.strip().lstrip('+').lstrip('-')
                not_quantity = int(not_quantity.strip())
                ok_quantity = int(ok_quantity.strip())
                
                if order_no in self.not_account_stock_dict:
                    print("미채결 종목이 없습니다.")
                    pass
                else:
                    self.not_account_stock_dict[order_no] = {}
                    self.not_account_stock_dict[order_no].update({'종목코드': code})
                    self.not_account_stock_dict[order_no].update({'종목명': code_nm})
                    self.not_account_stock_dict[order_no].update({'주문번호': order_no})
                    self.not_account_stock_dict[order_no].update({'주문상태': order_status})
                    self.not_account_stock_dict[order_no].update({'주문수량': order_quantity})
                    self.not_account_stock_dict[order_no].update({'주문가격': order_price})
                    self.not_account_stock_dict[order_no].update({'주문구분': order_gubun})
                    self.not_account_stock_dict[order_no].update({'미체결수량': not_quantity})
                    self.not_account_stock_dict[order_no].update({'체결량': ok_quantity})
                    
                    print("미체결종목 : %s" % self.not_account_stock_dict[order_no])
                    
            self.detail_account_info_event_loop.exit()


    def stop_screen_cancel(self, sScrNo=None):
        self.dynamicCall("DisconnectRealData(QString)", sScrNo) # 스크린 번호 연결 끊기
