# picamera2 예제 capture_jpeg.py를 기반으로 함
#!/usr/bin/python3

# 프리뷰 모드가 실행 중인 상태에서 JPEG를 캡처합니다.
# 파일로 캡처하면 반환값은 해당 이미지의 메타데이터입니다.

import time, requests, signal, os

from picamera2 import Picamera2, Preview
from gpiozero import LED, Button
from Adafruit_Thermal import *
from wraptext import *
from datetime import datetime

# 프린터 초기화
printer = Adafruit_Thermal('/dev/serial0', 9600, timeout=5)

# 카메라 초기화
picam2 = Picamera2()
# 카메라 시작
picam2.start()
time.sleep(2) # 처음 몇 프레임의 품질이 낮을 수 있어 예열 시간을 둠

# 다음 3줄은 디버깅용 컴퓨터 미리보기 코드
# 프로그램 속도를 크게 떨어뜨립니다
# 카메라 객체 확인이 필요할 때만 사용하세요
# 할 일: 왜 이 프리뷰는 SSH 환경에서 동작하지 않을까?
#preview_config = picam2.create_preview_configuration(main={"size": (800, 600)})
#picam2.configure(preview_config)
#picam2.start_preview(Preview.QTGL)

# 버튼 초기화
shutter_button = Button(16)
power_button = Button(26, hold_time = 2)

#############################
# 핵심 사진-시 변환 함수
#############################
def take_photo_and_print_poem():
  # 사진을 촬영하고 저장합니다
  metadata = picam2.capture_file('/home/carolynz/CamTest/images/image.jpg')

  # 디버깅용: 메타데이터 출력
  #print(metadata)

  # 할 일? 사진을 찍어 메모리에 저장하는 방식
  #image = picam2.capture_image()
  #print(image)

  # 카메라 종료는 프로그램 마지막에만 가능해서 주석 처리
  # picam2.close()

  # 디버깅용: 이미지 저장 완료 표시
  print('----- SUCCESS: image saved locally')

  #######################
  # 영수증 프린터:
  # 날짜/시간/위치 머리말
  #######################

  # 현재 날짜와 시간을 가져와 출력과 파일명에 사용
  now = datetime.now()

  # 출력되는 날짜/시간 형식 예시:
  # 2023년 1월 1일
  # 오후 8:11
  printer.justify('C') # 헤더 텍스트를 가운데 정렬
  date_string = now.strftime('%b %-d, %Y')
  time_string = now.strftime('%-I:%M %p')
  printer.println('\n')
  printer.println(date_string)
  printer.println(time_string)


  # 할 일: 위치 정보도 가져와 출력

  # 시각적 간격 조정
  printer.setLineHeight(56) # 기본 한 줄보다 약간 더 크게 설정
  printer.println()
  printer.setLineHeight() # 기본값(32)으로 복원

  printer.println("`'. .'`'. .'`'. .'`'. .'`'. .'`")
  printer.println("   `     `     `     `     `   ")

  #########################
  # 저장한 이미지를 API로 전송
  #########################
  api_url = 'https://poetry-camera.carozee.repl.co/pic_to_poem'

  # 예전 방식: 메모리에서 PIL 이미지 객체 가져오기
  # files = {'file': image}

  # 디스크에 저장한 파일을 바이트 배열로 읽기
  with open('/home/carolynz/CamTest/images/image.jpg', 'rb') as f:
    byte_im = f.read()

    # API 호출용 형식 준비
    image_filename = 'rpi-' + now.strftime('%Y-%m-%d-at-%I.%M-%p')
    files = {'file': (image_filename, byte_im, 'image/jpg')}

  # 바이트 배열을 API로 전송
  response = requests.post(api_url, files=files)
  response_data = response.json()

  # 디버깅용: 응답 내용을 콘솔에 출력
  #print(response_data['poem'])

  ############
  # 시 출력
  ############

  # 텍스트를 줄당 32자로 줄바꿈(영수증 프린터 최대 폭)
  printable_poem = wrap_text(response_data['poem'], 32)

  printer.justify('L') # 시 본문을 왼쪽 정렬
  printer.println(printable_poem)

  ##############
  # 푸터 출력
  ##############
  printer.justify('C') # 푸터 텍스트를 가운데 정렬
  printer.println("   .     .     .     .     .   ")
  printer.println("_.` `._.` `._.` `._.` `._.` `._")
  printer.println('\n')
  printer.println(' This poem was written by AI.')
  printer.println()
  printer.println('Explore the archives at')
  printer.println('poetry.camera')
  printer.println('\n\n\n\n')

  print('-----DONE PRINTING')
  return

##############
# 전원 버튼
##############
def shutdown():
  print('shutdown button held for 2s')
  print('shutting down now')
  os.system('sudo shutdown -h now')

#################################
# Raspberry Pi 디버깅용:
# Ctrl+C로 스크립트를 안전하게 종료합니다
# (그렇지 않으면 Pi 전체가 종료될 수 있음)
#################################
def handle_keyboard_interrupt(sig, frame):
  print('Ctrl+C received, stopping script')

  # Pi가 비정상 종료되지 않도록 RPi 포럼에서 찾은 우회 방법
  os.kill(os.getpid(), signal.SIGUSR1)

signal.signal(signal.SIGINT, handle_keyboard_interrupt)

################################
# 버튼 입력 이벤트 대기
################################
shutter_button.when_pressed = take_photo_and_print_poem
power_button.when_held = shutdown

signal.pause()
