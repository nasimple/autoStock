from kiwoom.kiwoom import*
import sys
from PyQt5.QtWidgets import*

class Main():
   def __init__(self):
      print("Main() start")
      
      self.app =QApplication(sys.argv) # PyQt5로 실행할 파일명을 자동 설정
      self.kiwoom = Kiwoom() # 키움 클래스 객체화
      self.app.exec_() # 이벤트 루프 실행
      
if __name__ == "__main__":
   Main()


#git add .   # git 에 파일을 추가하겠다
#git commit -m "수정사항"   # 수정 버젼관리 이름
#git push   # 최종 업데이트 명령어