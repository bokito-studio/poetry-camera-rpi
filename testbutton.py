# picamera2 예제 capture_jpeg.py를 기반으로 함
#!/usr/bin/python3

import time, requests, signal, os

from gpiozero import LED, Button

# 버튼 초기화
shutter_button = Button(16, hold_time = 2)
led = LED(20)

def handle_pressed():
  print("button pressed!")
  led.on()

def handle_held():
  print("button held!")

def handle_released():
  print("button released!")
  led.off()


#################################
# Raspberry Pi 디버깅용:
# Ctrl+C로 스크립트를 안전하게 종료합니다
# (그렇지 않으면 Pi 전체가 종료될 수 있음)
#################################
def handle_keyboard_interrupt(sig, frame):
  print('Ctrl+C received, stopping script')
  led.off() # 종료 전에 LED가 꺼져 있도록 보장
  # Pi가 비정상 종료되지 않도록 RPi 포럼에서 찾은 우회 방법
  os.kill(os.getpid(), signal.SIGUSR1)


################################
# 버튼 입력 이벤트 대기
################################
shutter_button.when_pressed = handle_pressed
shutter_button.when_held = handle_held
shutter_button.when_released = handle_released

# Ctrl+C 종료를 안전하게 처리
signal.signal(signal.SIGINT, handle_keyboard_interrupt)

# LED 단독 동작 테스트
led.on()
time.sleep(1)
led.off()

signal.pause()
