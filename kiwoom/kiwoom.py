import os
import sys
from PyQt5.QAxContainer import *   # PyQt5.QAxContainer 불러오는 코드
from PyQt5.QtCore import *   # PyQt5.QtCore 안에 이벤트 루프를 실행하는 QEventLoop() 함수를 불러오는 라이브러리
from config.errorCode import *   # config 에러 발생시 나오는 변수 저장소
from PyQt5.QtTest import *
from config.kiwoomType import *
from config.log_class import*
from datetime import datetime


class Kiwoom(QAxWidget):
    
    ### init (초기 자동 실행)  ##################################################################################################
    def __init__(self):
        super().__init__()
        
        ### 실시간 값을 정의해놓은 클래스 불러오기 함수호출
        self.realType = RealType() 
        
        
        
        ### 로그 분석 구문
        self.logging = Logging()    ### 로그 분석해서 호출 함수
        self.logging.logger.debug("Kiwoom() class start.") ### 프린트 방식을 로그 출력 형태로 변경
        # print("Kiwoom() class start.")    ### 이전 키움 로그인 시 정상으로 키움 클래스를 실행하는지 프린트 해주는 구문
        
        ####### event loop를 실행하기 위한 변수모음
        self.login_event_loop = QEventLoop() # 로그인을 이벤트 루프 안에서 실행하도록 만들기 위해 선언한 변수
        self.detail_account_info_event_loop = QEventLoop() # 예수금 요청용 이벤트 루프, 쓰레드간 간섭 방지
        self.calculator_event_loop = QEventLoop() # 키움 종목및 일봉데이터 이벤트 루프, 쓰레드간 간섭방지
        
        ### 전체 종목 관리  ###############################################################################################
        self.all_stock_dict = {}                # 전체 종목 관리 하는 딕 여기서 값을 가져가는게 있는지 주시 필요!
        
        ### 계좌 관련된 변수 ###############################################################################################
        self.account_stock_dict = {}            # 계좌정보 가져온거 담는 딕
        self.not_account_stock_dict = {}        # 미체결 정보 담는 딕 
                
        self.account_num = None # 계좌번호 담아주는 변수
        self.deposit = 0 # 예수금 (주식 거래를 위해 계좌에 넣어둔 현금 자산 영어 해석 : 보증금, 착수금)
        self.use_money = 0 # 실제 투자에 사용할 금액
        self.use_money_percent = 0.5 # 예수금에서 실제 사용할 비율
        self.output_deposit = 0 # 출금가능 금액
        self.total_buy_money = 0 # 총 매수한 금액
        self.total_profit_loss_money = 0 # 총평가손익금액
        self.total_profit_loss_rate = 0.0 # 총수익률(%)
        
        ### 종목 정보
        self.all_stock_daily_data = {}          # 일봉 정보 있는 종목 만 정보 다가져오기
        self.portfolio_stock_dict = {}          # 분석한 종목 정보 가져오기
        self.jango_dict = {}
        
        
        ### 종목 분석 용 ##################################################################################################
        self.calcul_data = []
        
        ### 요청 스크린 번호 ###############################################################################################
        self.screen_my_info = "2000" # 계좌 관련된 스크린 번호
        self.screen_calculation_stock = "4000" # 계산용 스크린 번호
        self.screen_real_stock = "5000" # 종목별 할당할 스크린번호
        self.screen_meme_stock = "6000" # 종목별 할당할 주문용 스크린 번호
        self.screen_start_stop_real = "1000" # 장 시작/종료 실시간 스크린 번호
        
        
        ### 초기 셋팅 함수들 바로 실행 #######################################################################################
        self.get_ocx_instance() # Ocx 방식을 파이썬에 사용할 수 있게 변환해 주는 함수 실행
        self.event_slots() # 키움과 연결하기 위한 signal / 슬롯 모음 함수 실행
        self.real_event_slot() # 실시간 이벤트 시그널 / 슬롯 연결 함수 실행
        self.signal_login_commConnect() # 로그인 시도 함수 실행
        self.get_account_info() # 계좌번호 가져오기
        
        self.detail_account_info() # 예수금상세현황요청
        self.detail_account_myStock() # 계좌평가잔고내역가져오기

        QTimer.singleShot(2000, self.not_concluded_account) ### 5초 뒤에 미체결 종목들 가져오기 실행
        
        QTest.qWait(2000)
        
        self.read_code()
        self.screen_number_setting() # 스크린넘버 받아주는게 없어서 지움
        
        QTest.qWait(2000)

        #실시간 수신 관련 함수
        self.dynamicCall("SetRealReg(QString, QString, QString, QString)", self.screen_start_stop_real, "", self.realType.REALTYPE['장시작시간']['장운영구분'], "0")
        
        # 실시간 등록 (실시간 체결 정보 받기)
        # self.dynamicCall("SetRealReg(QString, QString,QString, QString)", "9000", "035420", self.realType.REALTYPE['주식체결']['체결시간'], "0")
        
        if self.portfolio_stock_dict:
            
            for code in self.portfolio_stock_dict.keys():
                print(f"시간 정상 출력 : [{datetime.now().strftime('%H:%M:%S')}] 종목 코드: {code}")
                
                stock_info = self.portfolio_stock_dict[code]
            
                if '스크린번호' not in stock_info:
                    print(f"❗경고: {code}에 스크린번호 없음. 건너뜀")
                    continue  # ✅ 이 줄에서 아래 코드를 실행하지 않고 다음 루프로 넘어감
                screen_num =self.portfolio_stock_dict[code]['스크린번호']       # 포트폴리오에서 받아온 종목 과 스크린 번호를 screen_num 에 넘겨줌
                fids = self.realType.REALTYPE['주식체결']['체결시간']           # 주식 체결 시간 을 fids에 넘겨줌
                self.dynamicCall("SetRealReg(QString, QString, QString, QString)", screen_num, code, fids, "1")  #fid는 RealType()클래스 안의 20 반환
            
        else:
            print("포트폴리오에 종목이 없습니다.")

        
    ### init (초기 자동 실행) END   ##################################################################################################

    ### "메서드" = 클래스 안에 정의된 "함수" 선언 #######################################################################################
    def get_ocx_instance(self):
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1") # 레지스트리에 저장된 API 모듈 불러오기
        
    def event_slots(self):
        self.OnEventConnect.connect(self.login_slot) # 로그인 관련 이벤트
        self.OnReceiveTrData.connect(self.trdata_slot) # 트랜잭션(여러 작업을 하나의 '묶음'으로 처리하는 것) 요청 관련 이벤트
        self.OnReceiveMsg.connect(self.msg_slot)    # 메세지를 받는 슬롯 생성
            
    def real_event_slot(self):
        self.OnReceiveRealData.connect(self.realdata_slot) # 실시간 이벤트 슬롯
        self.OnReceiveChejanData.connect(self.chejan_slot) # 종목 주문체결 관련한 이벤트
    
        
    def signal_login_commConnect(self):
        self.dynamicCall("CommConnect()")
        self.login_event_loop.exec_()
        
    def login_slot(self, err_code):
        print("로그인상태 :", errors(err_code)[1])
        self.login_event_loop.exit() #login_event_loop.exit() 로그인 이벤트 루프 끊기


    ### 계좌 번호 불러오기 ##################################################################################################################    
    def get_account_info(self):
        
        self.account_list_num = self.dynamicCall("GetLoginInfo(QString)", "ACCOUNT_CNT") # 보유계좌수
        account_list = self.dynamicCall("GetLoginInfo(QString)", "ACCNO") # 계좌번호 불러오기 QString 은 PtQt5에서 제공하는 자동으로 String(문자열)으로 자동으로 변환해주는 기능이다.
        
        self.account_num = account_list.split(';')[0] # a;b;c > [a,b,c]
        
        # self.account_num = account_num # 책에서 안써도 되는 구문이 들어있다 위에서 self.account_num으로 선언되어있어서 어카운트 넘을 다시 어카운트 넘으로 지정 안해도 되는네 지정하는 구문이 추가되있어 지웠다.
        print("보유계좌 수량 : %s" % self.account_list_num)
        print("계좌번호 : %s" % self.account_num)
        
        
    ### 예수금상세현황요청 전문 ##################################################################################################################    
    def detail_account_info(self, sPrevNext="0"):
        self.dynamicCall("SetInputValue(QString, QString)", "계좌번호", self.account_num)
        self.dynamicCall("SetInputValue(QString, QString)", "비밀번호", "0000")
        self.dynamicCall("SetInputValue(QString, QString)", "비밀번호입력매체구분", "00")
        self.dynamicCall("SetInputValue(QString, QString)", "조회구분", "3")
        self.dynamicCall("CommRqData(QString, QString, int, QString)", "예수금상세현황요청", "OPW00001", sPrevNext, self.screen_my_info) # CommRqData(요청이름(sRQName), TR코드(sTrCode), 연속조회여부(nPrevNext), 스크린번호(sScreenNo)) ← 순서 고정!
        
        self.detail_account_info_event_loop.exec_() #이벤트 루프 실행


    ### 계좌평가잔고내역요청 전문 ##################################################################################################################    
    def detail_account_myStock(self, sPrevNext="0"):
        self.dynamicCall("SetInputValue(QString, QString)", "계좌번호", self.account_num)
        self.dynamicCall("SetInputValue(QString, QString)", "비밀번호", "0000")
        self.dynamicCall("SetInputValue(QString, QString)", "비밀번호입력매체구분", "00")
        self.dynamicCall("SetInputValue(QString, QString)", "조회구분", "2") 
        self.dynamicCall("CommRqData(QString, QString, int, QString)", "계좌평가잔고내역요청", "OPW00018", sPrevNext, self.screen_my_info) # CommRqData(요청이름(sRQName), TR코드(sTrCode), 연속조회여부(nPrevNext), 스크린번호(sScreenNo)) ← 순서 고정!

        self.detail_account_info_event_loop.exec_() #이벤트 루프 실행


    ### 계좌 미체결불러오기 전문 ##################################################################################################################    
    def not_concluded_account(self, sPrevNext="0"):
        print("미체결요청")
        
        self.dynamicCall("SetInputValue(QString, QString)", "계좌번호", self.account_num)
        self.dynamicCall("SetInputValue(QString, QString)", "전체조회", "1")  # ✅ 전체조회
        self.dynamicCall("SetInputValue(QString, QString)", "매매구분", "0")
        self.dynamicCall("SetInputValue(QString, QString)", "체결구분", "1")
        self.dynamicCall("CommRqData(QString, QString, int, QString)", "미체결요청", "OPT10075", sPrevNext, self.screen_my_info)
        
        self.detail_account_info_event_loop.exec_() #이벤트 루프 실행
        
        
    ### slot으로 반환된 값 가져오기 ("CommRqData" 요청했던 값) #######################################################################################
    def trdata_slot(self, sScrNo, sRQName, sTrCode, sRecordName, sPrevNext): # sRQName는 CommRqData에서 첫번째로 요청한 QString 의 값("예수금상세현황요청" 등)을 그대로 가져온다.

        ### if문 시작 #######################################################################################
        if sRQName == "예수금상세현황요청":
            deposit = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, "예수금") #'0'은 예수금상세현황 TR이 싱글데이터라서, 첫 번째 (유일한) 행의 값을 가져온다는 의미
            self.deposit = int(deposit)
            
            use_money = float(self.deposit) * self.use_money_percent
            self.use_money = int(use_money)
            self.use_money = self.use_money / 4 # 한 종목 매수 시 돈을 다 쓰지 않게 4종목으로 나눔
            
            output_deposit = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, "출금가능금액")
            self.output_deposit = int(output_deposit)                                                                                                                                                               
            
            ## print("예수금 : %s" % self.deposit)
            ## print("출금가능금액 : %s" % self.output_deposit)
            
            self.stop_screen_cancel(self.screen_my_info) # 스크린 번호 지우기    
            self.detail_account_info_event_loop.exit() # 이벤트 루프 끊기
        
        
        ### 계좌평가잔고내역 값 받기 #######################################################################################
        elif sRQName == "계좌평가잔고내역요청":
            total_buy_money = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, "총매입금액")
            self.total_buy_money = int(total_buy_money)
            
            total_profit_loss_money = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, "총평가손익금액")
            self.total_profit_loss_money = int(total_profit_loss_money)
            
            total_profit_loss_rate = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, "총수익률(%)")
            self.total_profit_loss_rate = float(total_profit_loss_rate)
            
            print("계좌평가잔고내역요청 내역 : 총 매입 %s, 총평가손익 %s, 총수익률 %s" % (self.total_buy_money, self.total_profit_loss_money, self.total_profit_loss_rate))
            
            rows = self.dynamicCall("GetRepeatCnt(QString, QString)", sTrCode, sRQName)
            print("계좌평가잔고내역 페이지별 수량 :", rows)
            
            
            ### 계좌평가잔고내역중 보유 종목 불러오기 ### 멀티데이터 불러오는 포문 #######################################################################################
            
            #### rows == 계좌평가잔고내역의 수량을 카운팅 해주니 아무것도 없을때는 if 문이돌면서 이벤트 루프를 종료하고 내용이 있으면 else를 돈다
            if rows == 0:
                print("보유종목이 없습니다.")
                print("잔고 이벤트 루프 종료 시작")
                self.stop_screen_cancel(self.screen_my_info) # 스크린 번호 지우기
                self.detail_account_info_event_loop.exit()
                return  # ❗여기서 함수 탈출 (이후 줄 아예 실행 안됨)
            
            else:
                for i in range(rows):
                    print(f"[디버그] i={i}, code_raw={self.dynamicCall(..., ..., i, '종목번호')}")

                    code = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "종목번호")
                    code = code.strip()[1:] ### 키움에서 받아오는 종목번호의 앞자리를 지운다 ex: "A77777" 이면 A삭제
                    code_nm = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "종목명").strip()
                    stock_quantity = int(self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "보유수량").strip())
                    buy_price = int(self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "매입가").strip())
                    learn_rate = float(self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "수익률(%)").strip())
                    current_price = int(self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "현재가").strip())
                    total_chegual_price = int(self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "매입금액").strip())
                    possible_quantity = int(self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "매매가능수량").strip())
                    
                    ##### 계좌 평가 잔고내역 확인 구문 
                    print(
                        f"계좌평가잔고내역:\n"
                        f"종목번호: {code}\n"
                        f"종목명: {code_nm}\n"
                        f"보유수량: {stock_quantity}\n"
                        f"매입가: {buy_price}\n"
                        f"수익률: {learn_rate}\n"
                        f"현재가: {current_price}\n"
                        f"매입금액: {total_chegual_price}\n"
                        f"매매가능수량: {possible_quantity}\n"
                    )
                    
                    if code in self.account_stock_dict:
                        pass
                    else:
                        self.account_stock_dict[code] = {}
                                            
                    self.account_stock_dict[code].update({"종목명": code_nm})
                    self.account_stock_dict[code].update({"보유수량": stock_quantity})
                    self.account_stock_dict[code].update({"매입가": buy_price})
                    self.account_stock_dict[code].update({"수익률(%)": learn_rate})
                    self.account_stock_dict[code].update({"현재가": current_price})
                    self.account_stock_dict[code].update({"매입금액": total_chegual_price})
                    self.account_stock_dict[code].update({"매매가능수량": possible_quantity})
                    
                    print("sPreNext: %s" % sPrevNext)
                    print("계좌에 가지고 있는 종목은 %s " % rows)
                    
                if sPrevNext == "2": # sPrevNext 에서 넘어오는 값이 2와같을때는 아래 self.detail_account_myStock(sPrevNext="2") 를 실행한다
                    self.detail_account_myStock(sPrevNext="2") # detail_account_myStock을 sPrevNext="2"로 재호출하여 추가 데이터를 요청한다.
                    
                else:
                    self.stop_screen_cancel(self.screen_my_info) # 스크린 번호 지우기 
                    self.detail_account_info_event_loop.exit()
                    print("계좌잔고 이벤트루프 끝")
        ### 계좌평가잔고내역 값 받기 END    #######################################################################################
        
        ### 미체결요청 값 받기 #######################################################################################        
        elif sRQName == "미체결요청":
            rows =self.dynamicCall("GetRepeatCnt(QString, QString)", sTrCode, sRQName)
            
            if rows == 0:
                print("미채결 종목이 없습니다.")
            
            else:
                for i in range(rows):
                    code = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "종목코드").strip()
                    code_nm = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "종목명").strip()
                    order_no = int(self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "주문번호").strip()) ### 미체결 되었을때 주문번호의 값을 반환한다
                    order_status = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "주문상태").strip()
                    order_quantity = int(self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "주문수량").strip())
                    order_price = int(self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "주문가격").strip())
                    order_gubun = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "주문구분").strip().lstrip('+').lstrip('-')
                    not_quantity = int(self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "미체결수량").strip())
                    ok_quantity = int(self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "체결량").strip())
                    
                    if order_no in self.not_account_stock_dict:
                        pass
                    else:
                        self.not_account_stock_dict[order_no] = {
                            '종목코드': code,
                            '종목명': code_nm,
                            '주문번호': order_no,
                            '주문상태': order_status,
                            '주문상태': order_status,
                            '주문수량': order_quantity,
                            '주문가격': order_price,
                            '주문구분': order_gubun,
                            '미체결수량': not_quantity,
                            '체결량': ok_quantity,
                        }
                        
                        print("미체결종목 자꾸나와!!! : %s" % self.not_account_stock_dict[order_no])

            if sPrevNext == "2":
                print("👉 미체결 다음 페이지 요청")
                QTimer.singleShot(300, lambda: self.not_concluded_account(sPrevNext="2"))
            else:
                self.stop_screen_cancel(self.screen_my_info)
                self.detail_account_info_event_loop.exit()
                print(f"이벤트루프 False면 잘 끊김 → {self.detail_account_info_event_loop.isRunning()}")
                
        ### 미체결요청 값 받기 END  #######################################################################################
        
        ### 주식 일봉차트 조회값 받기 #######################################################################################
        elif sRQName =="주식일봉차트조회":
            code = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, "종목코드")
            # data = self.dynamicCall("GetCommDataEx(QString, QString)", sTrCode, sRQName) ###600개 이하의 이전 종목 가져올때 사용하는 코드 (페이지를 넘길수 있는 값을 넘기지 않는다.)
            
            code = code.strip()
            cnt = self.dynamicCall("GetRepeatCnt(QString, QString)", sTrCode, sRQName)
            print("남은일자 수 %s" % cnt) ####위치
            
            for i in range(cnt):
                data = []
                current_price = self.dynamicCall("GetCommData(QString, QString, int, QString)" , sTrCode, sRQName, i, "현재가") #출력 : 000070
                value = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "거래량") # 출력 : 000070
                trading_value= self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "거래대금")
                date = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "일자")
                start_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "시가")
                high_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "고가")
                low_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "저가")
                
                data.append("")
                data.append(current_price.strip())  # 1.현재가
                data.append(value.strip())          # 2.거래량
                data.append(trading_value.strip())  # 3.거래대금
                data.append(date.strip())           # 4.일자
                data.append(start_price.strip())    # 5.시가
                data.append(high_price.strip())     # 6.고가
                data.append(low_price.strip())      # 7.저가
                data.append("")
                
                self.calcul_data.append(data.copy())
            
            
            if sPrevNext == "2":
                self.day_kiwoom_db(code=code, sPrevNext=sPrevNext)
            
            else:
                print("총 일수 %s" % len(self.calcul_data))
                
                pass_success = False
                
                # 120일 이평선을 그릴만큼의 데이터가 있는지 체크
                if self.calcul_data == None or len(self.calcul_data) < 120:
                    pass_success = False
                else:
                    #120일 이평선의 최근 가격 구함
                    total_price = 0
                    for value in self.calcul_data[:120]:
                        total_price += int(value[1])
                    moving_average_price = total_price / 120
                    
                    # 오늘자 주가가 120일 이평선에 걸쳐있는지 확인
                    bottom_stock_price = False
                    check_price =None
                    if int(self.calcul_data[0][7]) <=moving_average_price and moving_average_price <= int(self.calcul_data[0][6]):
                        print("오늘의 주가가 120 이평선에 걸쳐있는지 확인")
                        bottom_stock_price = True
                        check_price = int(self.calcul_data[0][6])
                        
                    # 과거 일봉 데이터를 조회하면서 120일 이동평균선보다 주가가 계속 밑에 존재 하는지 확인    
                    prev_price = None
                    if bottom_stock_price == True:
                        moving_average_price_prev = 0
                        price_top_moving =False
                        
                        idx = 1
                        
                        while True:
                            if len(self.calcul_data[idx:]) < 120: # calcul_data에 있는 정보의 갯수가 idx의 값 이후로 120개의 일봉 데이터가 있는지 확인
                                print("120일 치가 없음")
                                break
                            
                            total_price = 0
                            for value in self.calcul_data[idx:120+idx]:
                                total_price += int(value[1])
                                
                            moving_average_price_prev = total_price / 120
                            
                            if moving_average_price_prev <= int(self.calcul_data[idx][6]) and idx <=20:
                                print("20일 동안 주가가 120일 이평선과 같거나 위에 있으면 조건 통과 못 함")
                                price_top_moving = False
                                break
                            
                            elif int(self.calcul_data[idx][7]) > moving_average_price_prev and idx > 20: # 120 일 이평선 위에 있는 구간 존재
                                print("120일치 이평선 위에 있는 구간 확인됨")
                                price_top_moving = True
                                prev_price = int(self.calcul_data[idx][7])
                                break
                            
                            idx +=1
                        
                        # 해당부분 이평선이 가장 최긘의 이평선 가격보다 낮은지 확인
                        if price_top_moving == True:
                            if moving_average_price > moving_average_price_prev and check_price > prev_price:
                                print("포착된 이평선의 가격이 오늘자 이평선 가격보다 낮은 것 확인")
                                print("포착된 부분의 일봉 저가가 오늘자 일봉의 고가보다 낮은지 확인")
                                pass_success = True
                                
                    if pass_success == True:
                        print("조건부 통과됨")
                        code_nm = self.dynamicCall("GetMasterCodeName(QString)", code)
                        f= open("files/condition_stock.txt", "a", encoding="utf8")
                        f.write("%s\t%s\t%s\n" %(code, code_nm, str(self.calcul_data[0][1]))) # code==종목코드, code_nm == 종목명
                        f.close()
                    elif pass_success == False:
                        print("조건부 통과 못 함")
                        
                    self.calcul_data.clear()
                    self.calculator_event_loop.exit()        
        ### 주식 일봉차트 조회값 받기 END   #######################################################################################


    ### 스크린 끊기 ########################################################################################################
    def stop_screen_cancel(self, sScrNo=None):
        self.dynamicCall("DisconnectRealData(QString)", sScrNo) # 스크린 번호 연결 끊기
    ### 스크린 끊기 END ########################################################################################################

    ### 코스닥 종목 받아오기 전문 1_1 ############################################################################################
    def get_code_list_by_market(self, market_code): # market_code는 시장을 구분하는 코드이다 0응 장내 종목, 10은 코스닥 종목을 의미한다.
        code_list = self.dynamicCall("GetCodeListByMarket(QString)" , market_code)
        code_list = code_list.split(';')[:-1]   # split(';')은 ';'을 기준으로 (000233;001034;)이런식으로 넘어오는 값을 ;기준으로 나누어 리스트에 저장한다. split()는 앞뒤 여백을 지우는 파이썬 지정 함수이다.
                                                # 넘어오는 값의 맨뒤에도 ; 값이 있기에 [:-1] 이걸로 삭제한다.    
        return code_list
    ### 코스닥 종목 받아오기 전문 1_1 END  ############################################################################################

    ### 코스닥 종목 받아오기 전문 1_2 ############################################################################################ 
    def calculator_fnc(self):
        code_list = self.get_code_list_by_market("10") ### get_code_list_by_market()함수를 실행하고 "10"의 값을 할당한다.
        print("코스닥 갯수 %s " % len(code_list))

        for idx, code in enumerate(code_list):
            self.dynamicCall("DisconnectRealData(QString)", self.screen_calculation_stock) # 스크린 먼저 끊어주기
            print(f"{idx+1} / {len(code_list)} : 코드 {code} 일봉 조회 시도")   # 일봉 조회시도하기
            # print("%s / %s : KOSDAQ Stock Code : %s is updating..." % (idx + 1, len(code_list), code))
            
            self.day_kiwoom_db(code=code) # 키움에요청하기 특정날자를 인자로 전달 하는 방법 (code=code, date = "20250105")
    ### 코스닥 종목 받아오기 전문 1_2 END   ############################################################################################ 
        
    
    ### 주식 일봉 데이터 조회 요청 함수     ############################################################################################ 
    def day_kiwoom_db(self, code=None, date=None, sPrevNext="0"):
        
        QTest.qWait(3600) #3.6초 간격으로 딜레이를 준다.
        
        self.dynamicCall("SetInputValue(QString, QString)", "종목코드", code)
        self.dynamicCall("SetInputValue(QString, QString)", "수정주가구분", "1") # CommRqData(요청이름(sRQName), TR코드(sTrCode), 연속조회여부(nPrevNext), 스크린번호(sScreenNo)) ← 순서 고정!
        
        if date != None: # 특정날자를 조회할때 쓰인다 빈값은 오늘날짜부터 조회  값의 입력은 ex : YYYYMMDD(년도4자리, 월2자리, 일2자리)
            self.dynamicCall("SetInputValue(QString, QString)", "기준일자", date)

        self.dynamicCall("CommRqData(QString, QString, int, QString)", "주식일봉차트조회", "opt10081", sPrevNext, self.screen_calculation_stock) # CommRqData(요청이름(sRQName), TR코드(sTrCode), 연속조회여부(nPrevNext), 스크린번호(sScreenNo)) ← 순서 고정!
        self.calculator_event_loop.exec_() #계산 이벤트 루프 실행
    ### 주식 일봉 데이터 조회 요청 함수 end    ############################################################################################ 
    
    ### 선정종목 파일저장함수   ############################################################################################ 
    def read_code(self):
        if os.path.exists("files/condition_stock.txt"): #해당경로에 파일이 있는지 체크한다. os.path.exists는 괄호안의 파일이 있다면 True를 반환해준다
            f = open("files/condition_stock.txt", "r", encoding="utf8")
            
            lines = f.readlines() #파일에 있는 내용들이 모두 읽어와 진다.
            for line in lines: #줄바꿈된 내용들이 한줄 씩 읽어와진다.
                if line !="":
                    ls = line.split("\t") # \t == 탭,  \t 기준으로 문자열을 잘라준다. 
                    
                    stock_code = ls[0]
                    stock_name = ls[1]
                    stock_price = int(ls[2].split("\n")[0])
                    stock_price = abs(stock_price)
                    
                    # self.portfolio_stock_dict.update({stock_code:{"종목명":stock_name, "현재가":stock_price}})
                    self.portfolio_stock_dict.update({
                        stock_code: {
                            "종목명": stock_name,
                            "현재가": stock_price,
                            "출처": "컨디션" ### 책에 없는내용
                        }
                    })
                    
            f.close()
    # 선정종목 파일저장함수 END   ############################################################################################
    
    
    
    #### 전체 종목을 관리하는 메소드 (함수)   ############################################################################################ 
    def merge_dict(self): # merge(머지) 합치다
        self.all_stock_dict.update({"계좌평가잔고내역": self.account_stock_dict})
        self.all_stock_dict.update({"미체결종목": self.not_account_stock_dict})
        self.all_stock_dict.update({"포트폴리오 종목": self.portfolio_stock_dict})
    #### 전체 종목을 관리하는 메소드 (함수) END  ############################################################################################
    #### 스크린 번호 관리   ############################################################################################
    def screen_number_setting(self):
        screen_overwrite = []
        
        # 계좌평가잔고내역에 있는 종목들
        for code in self.account_stock_dict.keys():
            if code not in screen_overwrite:
                screen_overwrite.append(code)
        # 미체결에 있는 종목들
        for order_number in self.not_account_stock_dict.keys():
            code = self.not_account_stock_dict[order_number]["종목코드"]
            
            if code not in screen_overwrite:
                screen_overwrite.append(code)
        #포트폴리오에 있는 종목들
        for code in self.portfolio_stock_dict.keys():
            if code not in screen_overwrite:
                screen_overwrite.append(code)
        #스크린 번호 할당        
        cnt=0
        for code in screen_overwrite:
            temp_screen = int(self.screen_real_stock)
            meme_screen = int(self.screen_meme_stock)
            if (cnt % 50) == 0:
                temp_screen += 1
                self.screen_real_stock = str(temp_screen) # str == 스트링(문자열)
            if (cnt % 50) == 0:
                meme_screen += 1
                self.screen_meme_stock = str(meme_screen)
            if code in self.portfolio_stock_dict.keys():
                self.portfolio_stock_dict[code].update({"스크린번호": str(self.screen_real_stock)})
                self.portfolio_stock_dict[code].update({"주문용스크린번호": str(self.screen_meme_stock)})
                
                # 출처가 없으면 '보유종목'으로 설정
                if "출처" not in self.portfolio_stock_dict[code]:
                    self.portfolio_stock_dict[code].update({"출처": "보유종목"}) 
                
        
            elif code not in self.portfolio_stock_dict.keys():
                self.portfolio_stock_dict.update({code:{"스크린번호": str(self.screen_real_stock), "주문용스크린번호": str(self.screen_meme_stock), "출처": "보유종목"}})
            cnt += 1
        
        print(self.portfolio_stock_dict)
    ### 스크린 번호 관리 END   ############################################################################################

    ### 실시간 데이터 불러오는 영역 #########################################################################################
    def realdata_slot(self, sCode, sRealType, sRealData):
        
        print(f"📡 실시간 데이터 수신됨! sRealType: {sRealType}, sCode: {sCode}")
        
        if sRealType == "장시작시간":  ### 장 상황을 구분해주기 위한 코드
            fid = self.realType.REALTYPE[sRealType]['장운영구분']   # 장운영 값 받아오는 변수지정 (0:장시작전, 2:장종료전(20분), 3:장시작, 4,8:장종료, 9:장마감)
            value = self.dynamicCall("GetCommRealData(QString, int)", sCode, fid)
            print(value)
            
            if value == '0':
                print("장 시작 전")
                
            elif value == '3':
                print("장 시작")
            elif value == '2':
                print("장 종료, 동시호가로 넘어감")
                
            elif value == '4':
                print("3시 30분 장 종료")
                
                for code in self.portfolio_stock_dict.keys():
                    self.dynamicCall("setRealRemove(QString, QString)", self.portfolio_stock_dict[code]['스크린번호'], code)
                
                QTest.qWait(5000)
                
                self.file_delete()
                self.calculator_fnc()
                
                sys.exit()  #시스템 종료
                
            elif value == '9':      ### 출력 되는지 확인하기 위해서 내가 추가한 코드
                print("장 마감")
                
        elif sRealType == "주식체결":
            a = self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType]['체결시간']) # a의 값은 "20", 출력 HHMMSS
            b = self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType]['현재가']) # b의 값은 "10", 출력 : +(-)2520
            b = abs(int(b)) ## abs()는 절댓값 함수여서. 음수를 양수로 바꿔준다. 즉, +-기호를 인트로 변경해 -만 나오게 하고 -일때는 양수로 변경되어서 결과적으로 +-를 모두 없애준다 
            
            c = self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType]['전일대비']) #출력 +(-)2520
            c = int(c)
            
            d= self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType]['등락율']) # 출력 : +(-)12.98
            d= float(d) # float는 정수를 부동 소수점(실수) 타입으로 받겠다는거
            
            e = self.dynamicCall("GetCommRealData(QString, ing)", sCode,self.realType.REALTYPE[sRealType]['(최우선)매도호가']) #출력 : +(-)2520
            e = abs(int(e))
            
            f = self.dynamicCall("GetCommRealData(QString, ing)", sCode,self.realType.REALTYPE[sRealType]['(최우선)매수호가']) #출력 : +(-)2515
            f = abs(int(f))
            
            g = self.dynamicCall("GetCommRealData(QString, ing)", sCode,self.realType.REALTYPE[sRealType]['거래량']) #출력 : 240124 매수일때, -2034 매도일때
            g = abs(int(g))
            
            h = self.dynamicCall("GetCommRealData(QString, ing)", sCode,self.realType.REALTYPE[sRealType]['누적거래량']) #출력 : 240124
            h = abs(int(h))
            
            i = self.dynamicCall("GetCommRealData(QString, ing)", sCode,self.realType.REALTYPE[sRealType]['고가']) #출력 : +(-)2530
            i = abs(int(i))
            
            j = self.dynamicCall("GetCommRealData(QString, ing)", sCode,self.realType.REALTYPE[sRealType]['시가']) #출력 : +(-)2520
            j = abs(int(j))
            
            k = self.dynamicCall("GetCommRealData(QString, ing)", sCode,self.realType.REALTYPE[sRealType]['저가']) #출력 : +(-)2530
            k = abs(int(k))
            
            
            if sCode not in self.portfolio_stock_dict:
                self.portfolio_stock_dict.update({sCode:{}})
                print()
                
            self.portfolio_stock_dict[sCode].update({"체결시간":a})
            self.portfolio_stock_dict[sCode].update({"현재가":b})
            self.portfolio_stock_dict[sCode].update({"전일대비":c})
            self.portfolio_stock_dict[sCode].update({"등락율":d})
            self.portfolio_stock_dict[sCode].update({"(최우선)매도호가":e})
            self.portfolio_stock_dict[sCode].update({"(최우선)매수호가":f})
            self.portfolio_stock_dict[sCode].update({"거래량":g})
            self.portfolio_stock_dict[sCode].update({"누적거래량":h})
            self.portfolio_stock_dict[sCode].update({"고가":i})
            self.portfolio_stock_dict[sCode].update({"시가":j})
            self.portfolio_stock_dict[sCode].update({"저가":k})
            
            
            ### 계좌 잔고 매도 조건문
            if sCode in self.account_stock_dict.keys() and sCode not in self.jango_dict.keys():
                asd = self.account_stock_dict[sCode]
                meme_rate = (b-asd['매입가']) / asd['매입가'] * 100
                
                if asd['매매가능수량'] > 0 and (meme_rate > 5 or meme_rate < -5):
                    order_success = self.dynamicCall(
                        "sendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
                        [
                            "신규매도",
                            self.portfolio_stock_dict[sCode]["주문용스크린번호"],
                            self.account_num,
                            2,
                            sCode,
                            asd['매매가능수량'],
                            0,
                            self.realType.SENDTYPE['거래구분']['시장가'],
                            ""
                        ]
                    )
                    
                    if order_success == 0:
                        print("매도주문 전달 성공")
                        del self.account_stock_dict[sCode]
                    else:
                        print("매도주문 전달 실패")
                    
                elif sCode in self.jango_dict.keys():
                    print("보유 종목 실시간 체크")
            
            ### 매수조건 조건문 ## 에러 구문에서 이부분이 잘못된거같아 집중해서 봐줘
            elif d > 2.0 and sCode not in self.jango_dict:
                print("매수조건 통과 %s" % sCode)
                
                result =(self.use_money * 0.1)/e    ### use 머니에 0.1을 곱해 10% 만 사용하려는거고 그 값에서 e(최우선 매도호가) 를 나누어 몇 주를 살 수있는지 계산 하는 코드
                quantity = int(result)  ### 매수할 수량을 인트 타입으로 변환해 소숫점 없이 만듬
                
                order_success = self.dynamicCall(
                    "SandOrder(QString, QString, QString, int, QString, int, int, QString, QString)", 
                    [
                        "신규매수", ###매수 종류
                        self.portfolio_stock_dict[sCode]["주문용스크린번호"], self.account_num, ### 
                        1,  ###
                        sCode, ### 종목 코드
                        quantity,   ### 몇주를 살지 계산되어 온 코드
                        e,  ### 최우선 매도 호가
                        self.realType.SENDTYPE['거래구분']['지정가'],   ### 지정가로 매수 하겠다 (RealType() 클래스에서 SENDTYPE안에 거래구분키 안에 지정가 키안의 값 호출 "00")
                        ""  ### 주문 고유번호 (신규주문시에는 주문번호가 없기때문에 빈 값으로 요청한다.) 
                    ]
                )
                
                if order_success == 0:
                    print("매수주문 전달 성공")
                else:
                    print("매수주문 전달 실패")
                    
            not_meme_list = list(self.not_account_stock_dict)   ###copy()와 같은 기능으로 키값만 모아서 복사를 하고 리스트에 담는다 
            
            for order_num in not_meme_list:
                code = self.not_account_stock_dict[order_num]["종목코드"]
                meme_price = self.not_account_stock_dict[order_num]['주문가격']
                not_quantity =self.not_account_stock_dict[order_num]['미체결수량']
                order_gubun = self.not_account_stock_dict[order_num]['주문구분']
                    
                if order_gubun =="매수" and not_quantity > 0 and e > meme_price:    ### order_gubun(주문구분)이 매수 키값이 같고 not_quantity(체결되지 않은게)0보다 크고 최우선매도가 보다 meme_price의 값이 클때
                    order_success = self.dynamicCall(
                        "sendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
                        [
                            "매수취소",
                            self.portfolio_stock_dict[sCode]["주문용스크린번호"],
                            self.account_num,
                            3,
                            code,
                            0,
                            0,
                            self.realType.SENDTYPE['거래구분']['지정가'], order_num
                        ]
                    )
                    
                    if order_success == 0:
                        print("매수취소 전달 성공")
                        
                    else:
                        print("매수취소 전달 실패")
                        
                elif not_quantity == 0:
                    del self.not_account_stock_dict[order_num] # self.not_account_stock_dict 딕셔너리에서, 주문번호 order_num에 해당하는 항목 중 수량(not_quantity)이 0이 된 주문을 삭제한다
            
            ### 실시간 매수종목 매도 조건문
            if sCode in self.jango_dict.keys():
                jd = self.jango_dict[sCode]
                meme_rate = (b-jd['매입단가']) / jd['매입단가'] * 100  ### b == 현재가 - jango_dict 안에있는 종목의 매입단가의 차액을  같은 종목의 매입단가로 나눈 후 100으로 곱한 값
                
                if jd['주문가능수량'] > 0 and (meme_rate > 5 or meme_rate < -5):
                    order_success = self.dynamicCall(
                        "SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
                        [
                            "신규매도",
                            self.portfolio_stock_dict[sCode]["주문용스크린번호"],
                            self.account_num,
                            2,
                            sCode,
                            jd['주문가능수량'],
                            0,
                            self.realType.SENDTYPE['거래구분']['시장가'],
                            ""
                        ]
                    )
                else:
                    print("매도주문 전달 실패")
                    
            elif d > 2.0 and sCode not in self.jango_dict:
                print("매수조건 통과 %s" % sCode)
    
    def chejan_slot(self, sCode, sRealType, sRealData):
        if int(sGubun) == 0: # 0은 주문체결 
            #pass ### 주문이 체결되었으니 넘어간다.
            account_num = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['계좌번호'])
            sCode = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['종목코드'])[1:]
            stock_name = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['종목명'])
            stock_name = stock_name.strip()
            
            origin_order_number = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['원주문번호'])   # 출력 : defaluse : "000000"
            order_number = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['주문번호'])   # 출력 0115061 마지막 주문번호
            order_status = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['주문상태'])   # 출력: 접수, 확인, 체결
            order_quan = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['주문수량'])   # 출력 : 3
            order_quan = int(order_quan)
            
            order_price = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['주문가격'])   # 출력 : 21000
            order_price = int(order_price)
            
            not_chegual_quan = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['미체결수량'])  #출력: 15, default: 0
            not_chegual_quan = int(not_chegual_quan)
            
            order_gubun = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['주문구분'])    #출력: -매도, +매수
            order_gubun = order_gubun.strip().lstrip('+').lstrip('-')
            
            chegual_time_str =self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['주문/체결시간'])   #출력: '151028'
            
            chegual_price = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['체결가'])    #출력: 2110 default : ''
            if chegual_price == '':
                chegual_price = 0
            else:
                chegual_price = int(chegual_price)
                
            chegual_quantity = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['체결량'])     #출력: 5 default : ''
            
            if chegual_quantity == '':
                chegual_quantity = 0
            else:
                chegual_quantity = int(chegual_quantity)
                
            current_price = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['현재가'])    #출력: -6000
            current_price = abs(int(current_price))
            
            first_sell_price = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['(최우선)매도호가'])   #출력: -6010
            first_sell_price = abs(int(first_sell_price))
            
            first_buy_price = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['(최우선)매수호가'])    #출력: -6000
            first_buy_price = abs(int(first_buy_price))
            
            ### 새로 들어온 주문이면 주문번호 할당
            if order_number not in self.not_account_stock_dict.keys():
                self.not_account_stock_dict.update({order-number: {}})
            
            self.not_account_stock_dict[order_number].update({"종목코드": sCode})
            self.not_account_stock_dict[order_number].update({"주문번호": order_number})
            self.not_account_stock_dict[order_number].update({"종목명": stock_name})
            self.not_account_stock_dict[order_number].update({"주문상태": order_status})
            self.not_account_stock_dict[order_number].update({"주문수량": order_quan})
            self.not_account_stock_dict[order_number].update({"주문가격": order_price})
            self.not_account_stock_dict[order_number].update({"미체결수량": not_chegual_quan})
            self.not_account_stock_dict[order_number].update({"원주문번호": origin_order_number})
            self.not_account_stock_dict[order_number].update({"주문구분":order_gubun})
            self.not_account_stock_dict[order_number].update({"주문/체결시간": chegual_time_str})
            self.not_account_stock_dict[order_number].update({"체결가": chegual_price})
            self.not_account_stock_dict[order_number].update({"체결량":chegual_quantity })
            self.not_account_stock_dict[order_number].update({"현재가": current_price})
            self.not_account_stock_dict[order_number].update({"(최우선)매도호가": first_sell_price})
            self.not_account_stock_dict[order_number].update({"(최우선)매수호가": first_buy_price})
        
        elif int (sGubun) == 1: #잔고
            pass ### 잔고가 있는것도 넘어간다.
        account_num =self.dynamicCall("GetchejanData(int)", self.realType.REALTYPE['잔고']['계좌번호'])
        sCode = self.dynamicCall("GetchejanData(int)", self.realType.REALTYPE['잔고']['종목코드'])[1:]
        stock_name =self.dynamicCall("GetchejanData(int)", self.realType.REALTYPE['잔고']['종목명'])
        stock_name =stock_name.strip()
        
        current_price = self.dynamicCall("GetchejanData(int)", self.realType.REALTYPE['잔고']['현재가'])
        current_price = abs(int(current_price))
        
        stock_quan = self.dynamicCall("GetchejanData(int)", self.realType.REALTYPE['잔고']['보유수량']) #quan 은 수랴이라고 쓰인다
        stock_quan = int(stock_quan)
        
        like_quan = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['잔고']['주문가능수량'])
        like_quan = int(like_quan)
        
        buy_price = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['잔고']['매입단가'])
        buy_price = abs(int(buy_price))
        
        total_buy_price = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['잔고']['총매입가'])  #계좌에 있는 종목의 총매입가
        total_buy_price = int(total_buy_price)
        
        meme_gubun = self.dynamicCall("GetChejanData(int)",self.realType.REALTYPE['잔고']['매도매수구분'])
        meme_gubun = self.realType.REALTYPE['매도수구분'][meme_gubun]
        
        first_sell_price = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['(최우선)매도호가'])
        first_sell_price = abs(int(first_sell_price))
        
        first_buy_price = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['잔고']['(최우선)매수호가'])
        first_buy_price = abs(int(first_buy_price))
        
        if sCode not in self.jango_dict.keys():
            self.jango_dict.update({sCode:{}})
            
        self.jango_dict[sCode].update({"현재가": current_price})
        self.jango_dict[sCode].update({"종목코드": sCode})
        self.jango_dict[sCode].update({"종목명": stock_name})
        self.jango_dict[sCode].update({"보유수량": stock_quan})
        self.jango_dict[sCode].update({"주문가능수량": like_quan})
        self.jango_dict[sCode].update({"매입단가": buy_price})
        self.jango_dict[sCode].update({"총매입가": total_buy_price})
        self.jango_dict[sCode].update({"매도매수구분": meme_gubun})
        self.jango_dict[sCode].update({"(최우선)매도호가": first_sell_price})
        self.jango_dict[sCode].update({"(최우선)매수호가": first_buy_price})
        
        if stock_quan == 0:
            del self.jango_dict[sCode]
        
        
    def msg_slot(self, sScrNo, sRQName, sTrCode, msg):
        #print("스크린: %s, 요청이름: %s, tr코드: %s --- %s"  %(sScrNo, sRQName, sTrCode, msg))
        print(f"[msg_slot] 스크린(sScrNo): {sScrNo}, 종목이름(sRQName): {sRQName}, 종목번호(sTrCode): {sTrCode}, msg: {msg}")

    def file_delets(self):
        if os.path.isfile("files/condition_stock.txt"):
            os.remove("files/condition_stock.txt")
            
### 시나리오별 시간당 매매 수익율 분석 정의
def get_strategy_time_ranges():
    return {
        "strategy_open": ("090000", "100000"),
        "strategy_midopen": ("093000", "100000"),
        "strategy_all": ("090000", "153000"),
    }