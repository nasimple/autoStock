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
        self.detail_account_info_event_loop = QEventLoop() # 예수금 요청용 이벤트 루프, 쓰레드간 간섭 방지
        self.calculator_event_loop = QEventLoop() # 키움 종목및 일봉데이터 이벤트 루프, 쓰레드간 간섭방지


        ### 계좌 관련된 변수 ###############################################################################################
        self.account_num = None # 계좌번호 담아주는 변수
        self.deposit = 0 # 예수금
        self.use_money = 0 # 실제 투자에 사용할 금액
        self.use_money_percent = 0.5 # 예수금에서 실제 사용할 비율
        self.output_deposit = 0 # 출금가능 금액
        
        self.total_buy_money = 0 # 총 매수한 금액
        self.total_profit_loss_money = 0 # 총평가손익금액
        self.total_profit_loss_rate = 0.0 # 총수익률(%)
        
        self.account_stock_dict = {}    # 계좌정보 가져온거 담는 딕
        self.not_account_stock_dict = {}    # 미체결 정보 담는 딕 


        ### 종목 분석 용 ##################################################################################################
        self.calcul_data = []


        ### 요청 스크린 번호 ###############################################################################################
        self.screen_my_info = "2000" # 계좌 관련된 스크린 번호
        self.screen_calculation_stock = "4000" # 계산용 스크린 번호


        ### 초기 셋팅 함수들 바로 실행 #######################################################################################
        self.get_ocx_instance() # Ocx 방식을 파이썬에 사용할 수 있게 변환해 주는 함수 실행
        self.event_slots() # 키움과 연결하기 위한 signal / slot 모음 함수 실행
        self.signal_login_commConnect() # 로그인 시도 함수 실행
        self.get_account_info() # 계좌번호 가져오기
        
        self.detail_account_info() # 예수금상세현황요청
        self.detail_account_myStock() # 계좌평가잔고내역가져오기
        QTimer.singleShot(5000, self.not_concluded_account) ### 5초 뒤에 미체결 종목들 가져오기 실행


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
        self.dynamicCall("CommRqData(QString, QString, int, QString)", "예수금상세현황요청", "OPW00001", int(sPrevNext), self.screen_my_info) # CommRqData(요청이름(sRQName), TR코드(sTrCode), 연속조회여부(nPrevNext), 스크린번호(sScreenNo)) ← 순서 고정!
        
        self.detail_account_info_event_loop.exec_() #이벤트 루프 실행


    ### 계좌평가잔고내역요청 전문 ##################################################################################################################    
    def detail_account_myStock(self, sPrevNext="0"):
        self.dynamicCall("SetInputValue(QString, QString)", "계좌번호", self.account_num)
        self.dynamicCall("SetInputValue(QString, QString)", "비밀번호", "0000")
        self.dynamicCall("SetInputValue(QString, QString)", "비밀번호입력매체구분", "00")
        self.dynamicCall("SetInputValue(QString, QString)", "조회구분", "2") 
        self.dynamicCall("CommRqData(QString, QString, int, QString)", "계좌평가잔고내역요청", "OPW00018", int(sPrevNext), self.screen_my_info) # CommRqData(요청이름(sRQName), TR코드(sTrCode), 연속조회여부(nPrevNext), 스크린번호(sScreenNo)) ← 순서 고정!

        self.detail_account_info_event_loop.exec_() #이벤트 루프 실행


    ### 계좌 미체결불러오기 전문 ##################################################################################################################    
    def not_concluded_account(self, sPrevNext="0"):
        print("미체결요청")
        
        self.dynamicCall("SetInputValue(QString, QString)", "계좌번호", self.account_num)
        self.dynamicCall("SetInputValue(QString, QString)", "전체조회", "1")  # ✅ 전체조회
        self.dynamicCall("SetInputValue(QString, QString)", "매매구분", "0")
        self.dynamicCall("SetInputValue(QString, QString)", "체결구분", "1")
        self.dynamicCall("CommRqData(QString, QString, int, QString)", "미체결요청", "OPT10075", int(sPrevNext), self.screen_my_info)
        
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
            
            print("예수금 : %s" % self.deposit)
            print("출금가능금액 : %s" % self.output_deposit)
            
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
            
            #self.stop_screen_cancel(self.screen_my_info) # 스크린 번호 지우기
            #self.detail_account_info_event_loop.exit() # 이벤트 루프 끊기
            
            
            ### 계좌평가잔고내역중 보유 종목 불러오기 ### 멀티데이터 불러오는 포문 #######################################################################################
            if rows ==0:### rows 는 계좌평가잔고내역의 수량을 카운팅 해주니 아무것도 없을때는 if 문이돌면서 이벤트 루프를 종료하고 내용이 있으면 else를 돈다
                print("보유종목이 없습니다.")
                self.stop_screen_cancel(self.screen_my_info) # 스크린 번호 지우기 
                self.detail_account_info_event_loop.exit()
            
            else:
                for i in range(rows):
                    code = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "종목번호")
                    code = code.strip()[1:] ### 키움에서 받아오는 종목번호의 앞자리를 지운다 ex: "A77777" 이면 A삭제
                    code_nm = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "종목명")
                    stock_quantity = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "보유수량")
                    buy_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "매입가")
                    learn_rate = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "수익률(%)")
                    current_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "현재가")
                    total_chegual_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "매입금액")
                    possible_quantity = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "매매가능수량")
                    
                    print("종목번호: %s - 종목명: %s - 보유수량: %s - 매입가: %s - 수익률: %s - 현재가: %s" % (code, code_nm, stock_quantity, buy_price, learn_rate, current_price))
                    
                    if code in self.account_stock_dict:
                        pass
                    else:
                        self.account_stock_dict[code] = {}
                    
                    code_nm = code_nm.strip() # .strip()은 문자열의 앞뒤 공백을 제거한 새 문자열을 반환하며, 이를 다시 code_nm에 저장
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
                
                if sPrevNext == "2": # sPrevNext 에서 넘어오는 값이 2와같을때는 아래 self.detail_account_myStock(sPrevNext="2") 를 실행한다
                    self.detail_account_myStock(sPrevNext="2") # detail_account_myStock을 sPrevNext="2"로 재호출하여 추가 데이터를 요청한다.
                    
                else:
                    self.stop_screen_cancel(self.screen_my_info) # 스크린 번호 지우기 
                    self.detail_account_info_event_loop.exit()
                    print("계좌잔고 이벤트루프 끝")
        
        
        ### 미체결요청 값 받기 #######################################################################################        
        elif sRQName == "미체결요청":
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
                    
                    
            if sPrevNext == "2":
                print("👉 미체결 다음 페이지 요청")
                QTimer.singleShot(300, lambda: self.not_concluded_account(sPrevNext="2"))
            else:
                self.stop_screen_cancel(self.screen_my_info)
                self.detail_account_info_event_loop.exit()
                print("미체결 이벤트루프 끝")
        
        
        
        ### 주식 일봉차트 조회값 받기 ing #######################################################################################
        elif sRQName =="주식일봉차트조회":
            code = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, "종목코드")
            # data = self.dynamicCall("GetCommDataEx(QString, QString)", sTrCode, sRQName) ###600개 이하의 이전 종목 가져올때 사용하는 코드 (페이지를 넘길수 있는 값을 넘기지 않는다.)
            code = code.strip()
            cnt = self.dynamicCall("GetRepeatCnt(QString, QString)", sTrCode, sRQName)
            print("남은일자 수 %s" % cnt)
            
            for i in range(cnt):
                data = []
                current_price = self.dynamicCall("GetCommData(QString, QString, int, QString)" , sTrCode, sRQName, i, "현재가") #출력 : 000070
                value = self.dtnamicCall("GetCommdata(QString, QString, int, QString)", sTrCode, sRQName, i, "거래량") # 출력 : 000070
                trading_value= self.dynamicCall("GetCommdata(QString, QString, int, QString)", sTrCode, sRQName, i, "거래대금")
                data = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "일자")
                start_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "시가")
                high_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "고가")
                low_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "저가")
                
                data.append("")
                data.append(current_price.strip())
                data.append(value.strip()) 
                data.append(trading_value.strip())
                data.append(data.strip())
                data.append(start_price.strip())
                data.append(high_price.strip())
                data.append(low_price.strip())
                data.append("")
                
                self.calcul_data.append(data. copy())
            
            
            # 과거 일봉 값 받기 ing ################################################################################################
            if sPrevNext == "2":
                self.day_kiwoom_db(code=code, sPrevNext=sPrevNext)  #sPrevNext의 값이 "2"일때는
            
            else:
                print("총 일수 %s" % len(self.calcul_data)) # len() 데이터 수를 세주는 내장함수
                pass_success = False
                
                
                # 120일 이평선을 그릴만큼의 데이터가 있는지 체크
                if self.calcul_data == None or len(self.calcul_data) < 120:
                    pass_success=False
                
                else:
                    # 120일 이평선의 최근 가격 구함
                    toral_price = 0
                    for value in self.calcul_data[:120]:
                        total_price += int(value[1])
                    moving_average_price = total_price /120
                    
                self.calculator_event_loop.exit()   # sPrevNext의 값이 "2"가 아닐때는 무한루프에서 나와라
        
        ### if문 끝 #######################################################################################


    ### 스크린 끊기 ########################################################################################################
    def stop_screen_cancel(self, sScrNo=None):
        self.dynamicCall("DisconnectRealData(QString)", sScrNo) # 스크린 번호 연결 끊기


    ### 코스닥 종목 받아오기 전문 1_1 ############################################################################################
    def get_code_list_by_market(self, market_code): # market_code는 시장을 구분하는 코드이다 0응 장내 종목, 10은 코스닥 종목을 의미한다.
        code_list = self.dynamicCall("GetCodeListByMarket(QString)" , market_code)
        code_list = code_list.split(';')[:-1]   # split(';')은 ';'을 기준으로 (000233;001034;)이런식으로 넘어오는 값을 ;기준으로 나누어 리스트에 저장한다. split()는 앞뒤 여백을 지우는 파이썬 지정 함수이다.
                                                # 넘어오는 값의 맨뒤에도 ; 값이 있기에 [:-1] 이걸로 삭제한다.    
        return code_list

    ### 코스닥 종목 받아오기 전문 1_2 ############################################################################################ 
    def calculator_fnc(self):
        code_list = self.get_code_list_by_market("10") ### get_code_list_by_market()함수를 실행하고 "10"의 값을 할당한다.
        
        print("코스닥 갯수 %s " % len(code_list))
        
        for idx, code in enumerate(code_list):
            self.dynamicCall("DisconnectRealData(QString)" , self.screen_calculation_stock) # 스크린 연결
            
            print("%s / %s : KOSDAQ Stock Code : %s is updating..." % (idx + 1, len(code_list), code))
            self.day_kiwoom_db(code=code) #특정날자를 인자로 전달 하는 방법 (code=code, date = "20250105")

    def day_kiwoom_db(self, code=None, date=None, sPrevNext="0"):
        
        QTest.qWait(3600) #3.6초 간격으로 딜레이를 준다.
        
        self.dynamicCall("SetInputValue(QString, QString)", "종목코드", code)
        self.dynamicCall("CommRqData(QString, QString)" , "수정주가구분", "1") # CommRqData(요청이름(sRQName), TR코드(sTrCode), 연속조회여부(nPrevNext), 스크린번호(sScreenNo)) ← 순서 고정!
        
        if date != None: # 특정날자를 조회할때 쓰인다 빈값은 오늘날짜부터 조회  값의 입력은 ex : YYYYMMDD(년도4자리, 월2자리, 일2자리)
            self.dynamicCall("SetInputValue(QString, QString)", "기준일자", date)


        self.dynamicCall("CommRqData(QString, QString, int, QString)", "주식일봉차트조회", "opt10081", int(sPrevNext), self.screen_calculation_stock) # CommRqData(요청이름(sRQName), TR코드(sTrCode), 연속조회여부(nPrevNext), 스크린번호(sScreenNo)) ← 순서 고정!
        
        self.calculator_event_loop.exec_() #계산 이벤트 루프 실행
