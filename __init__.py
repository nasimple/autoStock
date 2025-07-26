from kiwoom.kiwoom import*
import sys
from PyQt5.QtWidgets import* # QtWidgets 안에 있는 클래스를 사용하기 위해 임포트 한다.QApplication 클래스는 프로그램을 앱처럼 실행하거나 
                              # 홈페이지처럼 실행할 수있도록 그래픽적인 요소를 제어하는 기능을 포함한다.
                              # 그 기능중 동시성 처리를 할 수 있게 해주는 함수도 포함돼 있다.  

class Main():
   def __init__(self):
      print("Main() start")
      
      self.app = QApplication(sys.argv) # PyQt5로 실행할 파일명을 자동 설정
      self.kiwoom = Kiwoom() # 키움 클래스 객체화
      self.app.exec_() # 이벤트 루프 실행 sys 에서 받아온 (sys.argv)의 리스트를 self.app으로 변수명을 정하고 QApplication 의 
      
if __name__ == "__main__":
   Main()


# git add .   # git 에 파일을 추가하겠다 ( " . " 점 띄어쓰기 꼭해야함)
# git commit -m "수정사항"   # 수정 버젼관리 이름
# git push   # 최종 업데이트 명령어
# git pull origin main  # 깃에서 최신버전으로 불러오기 pull

# 가상 계좌번호 : 8103418811
