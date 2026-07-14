# Poetry Camera (시 카메라)
보는 것을 시로 출력하는 카메라입니다.

이 가이드는 [원본 프로젝트](https://github.com/bokito-studio/poetry-camera-rpi)를 참조하여 한국 환경에 맞게 설치 과정을 변형했습니다. 부품 구매는 알리익스프레스를 기준으로 작성되었으나, 국내 쇼핑몰(네이버 스마트스토어, 쿠팡 등)에서도 대부분 구매 가능합니다.

⚠️ 이 지침은 아직 작성 중입니다. ⚠️  시도해보시고 혼란스럽거나 작동하지 않는 부분이 있으면 알려주세요.

## 필요한 하드웨어
### 1. 컴퓨터: 헤더가 포함된 [Raspberry Pi Zero 2 W](https://www.raspberrypi.com/products/raspberry-pi-zero-2-w/)

<img src="./pics/a7da1fae.png" width="300" height="300">

Raspberry Pi는 단순화된 컴퓨터입니다. 가볍고 저렴하지만 처리 성능이 제한적이며, 일반 소비자 전자제품보다 더 취약합니다. 전원 공급에 매우 민감해서 전압이 너무 높으면 부품이 손상되고, 너무 낮으면 소프트웨어가 실행되지 않습니다. 또한 전원을 빼기 전에 소프트웨어를 수동으로 종료해야 파일 시스템/소프트웨어 손상을 방지할 수 있습니다.

원본 프로젝트에서는 처리 성능과 크기의 균형을 고려하여 [Raspberry Pi Zero 2 W](https://www.raspberrypi.com/products/raspberry-pi-zero-2-w/) 또는 [Pi 3B+](https://www.raspberrypi.com/products/raspberry-pi-3-model-b-plus/)를 권장합니다. Pi Zero는 처리 속도가 너무 느리고, [Pi 4](https://www.raspberrypi.com/products/raspberry-pi-4-model-b/)는 요구 전력이 커서 휴대용으로 쓰기에는 비현실적일 수 있습니다. 이 가이드에서는 Pi Zero 2 W를 기준으로 설명합니다.

**⚠️ 중요: 납땜에 대하여**
이 프로젝트는 배터리 회로, 버튼 연결 등 여러 부분에서 납땜이 필요합니다. 직접 납땜하는 것을 추천하지만, 납땜이 어려운 경우 헤더가 미리 납땜된 제품을 구매하거나 납땜 서비스를 이용하는 것을 권장합니다.

Raspberry Pi Zero 2는 종종 헤더(2x20 검은 금속 커넥터) 없이 판매됩니다. 헤더가 있으면 점퍼 와이어로 프린터와 버튼을 쉽게 연결할 수 있습니다. 

<img src="./pics/43c619a8.png" width="300">


### 2. Raspberry Pi 연결될 액세서리
  <img src="./pics/d482c0de.png" width="300">
  
    
### 3. 카메라: [Raspberry Pi Camera Module 3](https://www.raspberrypi.com/products/camera-module-3/)
  <img src="./pics/4fad7574.png" width="200">

  대체로 간단하지만, 하드웨어 손상에 주의하세요. Raspberry Pi 카메라는 섬세하고 정전기에 의해 쉽게 망가질 수 있습니다. 

  라즈베리 파이 카메라는 몇 가지 종류가 있으며, 이 가이드에서는 정품 Raspberry Pi Camera Module 3를 기준으로 작성되었습니다. 호환 카메라 모듈도 사용 가능하지만, 드라이버나 설정이 다를 수 있습니다.

  - **카메라 액세서리:**
    - **카메라 케이블**: 라즈베리 파이 모델에 따라 필요한 케이블이 다릅니다.
      
      <img src="./pics/K-20251027-221443198.jpg" width="400">
      
      위 이미지는 Raspberry Pi 3B+ 등 일반 Pi용 케이블로, 양쪽 커넥터의 폭이 동일합니다.
      
      <img src="./pics/K-20251027-221516461.jpg" width="400">
      
      위 이미지는 Raspberry Pi Zero/Zero 2 W 전용 케이블로, 양쪽 커넥터의 폭이 다릅니다 (한쪽은 좁고 한쪽은 넓음). 
      
      ⚠️ **주의**: 케이블 구매 시 반드시 사용하는 라즈베리 파이 모델에 맞는 케이블을 선택하세요!



### 4. Receipt printer: [Mini Thermal Printer w/ TTL Serial connection](https://www.adafruit.com/product/2752)

<img src="./pics/209bbe14.png" width="300">

이 프로젝트에는 Adafruit의 열전사 프린터 라인을 사용했지만, 현재는 단종되었습니다. 아마존/알리익스프레스에서 유사 제품을 찾을 수 있으며, 우리가 구매한 제품들은 [동일한 프린터 드라이버](https://github.com/adafruit/zj-58)로 동작했습니다(Adafruit 측 유지보수는 중단되었지만 여전히 동작하는 것으로 보임).

[Nano Thermal Printer](https://www.adafruit.com/product/2752) 또는 [Tiny Thermal Printer](https://www.adafruit.com/product/2751)가 더 컴팩트하지만, [배선이 약간 다릅니다](https://learn.adafruit.com/mini-thermal-receipt-printer/making-connections#for-product-number-2751-tiny-3133460).

중요한 점은 프린터가 TTL 직렬(Serial) 연결을 지원해야 Pi에 쉽게 연결할 수 있다는 것입니다. 아마존이나 알리익스프레스에서 부품을 찾을 때는 **"TTL embedded thermal printer"**로 검색해 보세요.

  - **아마존의 유사 영수증 프린터:**
    - [Adafruit Mini 프린터 대체품](https://www.amazon.com/HUIOP-Embedded-Printing-Commands-Apparatus/dp/B0CS3NRPV3)
    - [Adafruit Tiny 프린터 대체품](https://www.amazon.com/XIXIAN-Thermal-Embedded-Interface-Printing/dp/B0C5XGJWC4)

  - **영수증 프린터 액세서리:**
    - [5V 전원 어댑터](https://www.adafruit.com/product/276)
    - 프린터와 전원 공급을 연결하기 위한 [DC 전원 암 커넥터](https://www.adafruit.com/product/368)
    - 배선용 니퍼/와이어 스트리퍼/소형 드라이버
    - 영수증 용지: [EcoChit 열전사용지, 2.25"](https://www.amazon.com/EcoChit-Thermal-Paper-Rolls-Plants/dp/B076MMDL8Y) (페놀 무함유, 재활용 가능)
        - 일반 영수증 용지는 사용하지 마세요! [BPA가 함유된 경우가 많습니다](https://environmentaldefence.ca/2019/02/07/toxic-receipt-bpa-thermal-paper/). 특히 아동과 생식 건강에 매우 해롭습니다.


### 5. Batteries:
<img src="./pics/b3507b14.png" width="300">
<img src="./pics/5196a5ee.png" width="300">
<img src="./pics/f1340f50.png" width="300">

카메라를 휴대용으로 쓰고 싶다면 배터리가 필요합니다! Pi는 5V 1.2A의 안정적인 전원이 필요하고, 프린터는 5~9V를 요구하며 인쇄 중에는 약 2A를 소모합니다.

**권장 전원: AA 배터리 6개(6xAA)**

가장 가벼운 방법은 아니지만, 초보자에게 적합한 출발점입니다.
  - [DC 플러그가 달린 6 x AA 배터리 홀더](https://www.adafruit.com/product/248)
  - AA 배터리 6개 — 충전식 NiMH(예: 에네루프)는 7.2V, 일회용 알카라인(예: 듀라셀)은 9V를 제공합니다. 둘 다 사용 가능. 단, 서로 다른 종류를 섞지 마세요!
  - 회로 전원 제어용 [인라인 DC 배럴 잭 스위치](https://www.adafruit.com/product/1125)
  - 배터리를 회로에 연결할 [DC 와이어 터미널 블록](https://www.adafruit.com/product/368)
  - [스텝다운(벅) 컨버터 — 5V 3A 출력](https://www.adafruit.com/product/1385): 배터리 전압을 Raspberry Pi용 5V로 강하
  - Pi 전원 공급용 [MicroUSB 셸](https://www.adafruit.com/product/1826) 또는 MicroUSB 케이블 절개 사용
  - 납땜 인두

**다른 가능한 해법:**
  - 위 회로를 PCB로 만들어 납땜 대신 커넥터만 꽂도록 하기 — 우리는 실제로 그렇게 사용했습니다! 향후 거버 파일을 업로드할 예정입니다.
  - 7.2V 리튬 배터리(예: 18650 x 2)
  - [RC 카용 7.2V NiMH 배터리](https://www.amazon.com/s?k=7.2v+rc+battery&i=toys-and-games&crid=1FRMK7CHC0RRQ&sprefix=7.2v+rc+battery,toys-and-games,127)
  - 초경량 휴대성이 필요 없다면, Pi와 프린터를 꽂아 쓰는 [포터블 파워 스테이션](https://www.amazon.com/gp/product/B0CH2Z2JM9)도 방법
  - 납땜을 원치 않는다면 Pi와 프린터를 각각 다른 배터리로 구동하는 방법도 있습니다. 다만 흔히 추천되는 [PiSugar 3 배터리](https://www.tindie.com/products/pisugar/pisugar-3-battery-for-raspberry-pi-zero/)는 과열 문제가 있었습니다.
    
**작동하지 않는 전원 솔루션:**
  - 일반적인 9V 알카라인 배터리는 필요한 전류를 공급하지 못해 동작하지 않습니다
  - 일반 보조배터리(폰 보조 전원)는 Raspberry Pi에 연속 전원을 공급하지 못해 수분 내 자동 종료될 수 있습니다
  - 단일 5V 보조배터리에 Pi와 프린터를 함께 꽂기 — 인쇄 시 전류 요구치를 감당하지 못합니다. 인쇄 도중 Pi가 꺼지거나 프린터 출력이 부족해 인쇄가 실패합니다.


### 6. Shutter button & LED
<img src="./pics/90120571.png" width="300">

셔터 버튼은 임시(momentary) 푸시버튼이면 아무거나 사용 가능합니다. LED는 준비 완료, 로딩 등 상태 표시용으로 사용합니다.

**GPIO 연결:**
- **셔터 버튼**: GPIO20 (핀 38)에 연결
- **LED**: GPIO16 (핀 36)에 연결

**부품 목록:**
  - [LED가 내장된 푸시버튼](https://www.adafruit.com/search?q=16mm%20Panel%20Mount%20Momentary%20Pushbutton): 촉감(클릭감)은 애매하지만, LED 내에 저항이 포함되어 있어 편리합니다.
  - 버튼을 Pi에 쉽게 연결하기 위한 [퀵 커넥트 와이어 2개](https://www.adafruit.com/product/1152)
  - 별도 LED 사용 시: 330Ω 저항이 필요합니다

### 7. Miscellaneous equipment
  - 니퍼 & 와이어 스트리퍼
  - 납땜 인두 및 소모품
  - 점퍼 케이블

## 소프트웨어 개요
현재 코드는 Google Gemini API를 사용해 사진을 시로 변환합니다. 또한 [Adafruit의 Thermal Printer 파이썬 라이브러리](https://github.com/adafruit/Python-Thermal-Printer)의 드라이버를 사용합니다.

### 왜 Google Gemini API인가?

이 프로젝트는 원래 OpenAI의 GPT-4 Vision API를 사용했지만, **비용 및 결제 문제**로 인해 Google Gemini API로 전환했습니다.

**OpenAI API의 문제점:**
- ❌ **신용카드 등록 필수**: API 사용을 위해 무조건 결제 수단 등록 필요
- ❌ **자동 결제 위험**: 무료 크레딧 소진 후 자동으로 유료 전환되어 요금 청구
- ❌ **비용 발생**: 무료 크레딧($5-18) 소진 후 사용할 때마다 비용 발생
- ❌ **2회 API 호출 필요**: 이미지 분석(1회) + 시 생성(2회) = 비용 2배

**Google Gemini API의 장점:**
- ✅ **신용카드 불필요**: API 키만으로 바로 사용 가능
- ✅ **완전 무료**: 월 1,500회 요청까지 무료, 자동 결제 없음
- ✅ **효율성**: 이미지 분석과 시 생성을 **하나의 API 호출**로 처리
- ✅ **멀티모달**: 이미지와 텍스트를 동시에 처리 가능
- ✅ **빠른 속도**: 최신 Gemini 2.5 Flash 모델 사용

**사용 중인 모델: `models/gemini-2.5-flash`**

Google Gemini는 여러 모델을 제공하며, 이 프로젝트에서는 속도와 품질의 균형이 좋은 `gemini-2.5-flash`를 사용합니다:

| 모델 | 특징 | 적합성 |
|------|------|--------|
| gemini-2.5-pro | 최고 품질, 느림 | 시 품질 최우선 시 |
| **gemini-2.5-flash** | **빠름 + 좋은 품질** | **권장 (현재 사용 중)** |
| gemini-2.5-flash-lite | 매우 빠름, 기본 품질 | 빠른 테스트용 |
| gemini-2.0-flash | 이전 세대 | - |

다른 모델로 변경하려면 `main.py` 파일의 이 줄을 수정하세요:
```python
model = genai.GenerativeModel('models/gemini-2.5-flash')
```

### API 키 발급

[Google AI Studio](https://makersuite.google.com/app/apikey)에서 **신용카드 등록 없이** 무료로 API 키를 발급받을 수 있습니다:
1. Google 계정으로 로그인
2. "Create API Key" 클릭
3. "Create API key in new project" 선택
4. 생성된 키를 복사하여 `.env` 파일에 저장

**무료 사용 한도:**
- 분당 15회 요청
- 일일 1,500회 요청
- 월 1백만 토큰
- **한도 초과 시**: 자동 결제 없음, API 호출만 실패

일반적인 사용으로는 충분한 한도입니다!

### 작동 방식

현재 Pi에서 실행되는 `main.py` 스크립트는 다음을 수행합니다:
1. 셔터 버튼을 누르면 사진을 촬영합니다
2. 촬영한 사진과 시 생성 프롬프트를 Google Gemini API로 보냅니다
3. Gemini가 이미지를 분석하고 **직접 시를 생성**합니다 (한 번의 API 호출로 완료!)
4. 생성된 시를 열전사(영수증) 프린터로 출력합니다

**이전 방식 (OpenAI) vs 현재 방식 (Gemini):**
- OpenAI: 이미지 → 캡션 생성 (API 호출 1) → 캡션 → 시 생성 (API 호출 2) = 2회 호출, 유료, 카드 등록 필수
- Gemini: 이미지 → 시 생성 (API 호출 1) = 1회 호출, 무료, 카드 등록 불필요!


---

# 하드웨어 조립 가이드

## 하드웨어 연결 개요
다음 튜토리얼을 참고해 구성했습니다:
- [Raspberry Pi와 열전사 프린터로 즉석 카메라 만들기](https://learn.adafruit.com/instant-camera-using-raspberry-pi-and-thermal-printer)
- [Raspberry Pi와 CUPS로 네트워크 열전사 프린터 구성](https://learn.adafruit.com/networked-thermal-printer-using-cups-and-raspberry-pi)

### 1. 카메라 모듈 연결
1. **Raspberry Pi의 전원을 끕니다** (매우 중요!)
2. **카메라 커넥터 열기**: 
   - Pi Zero 2 W의 카메라 포트(CSI 포트) 옆 검은색 플라스틱 칼라를 부드럽게 위로 당깁니다.
   - 핀셋을 사용하면 더 안전합니다.
3. **카메라 케이블 삽입**:
   - Pi Zero 2용 짧은 카메라 케이블을 준비합니다.
   - 파란색 면이 HDMI 포트 쪽을 향하도록 케이블을 삽입합니다.
   - 칼라를 다시 아래로 눌러 고정합니다.
4. **카메라 모듈 연결**: 케이블의 반대편을 카메라 모듈에 연결합니다.

⚠️ **정전기 주의**: 카메라 모듈은 정전기에 매우 민감합니다. 사용하지 않을 때는 반드시 정전기 차폐 봉투에 보관하세요.

### 2. 프린터 하드웨어 연결
열전사 프린터를 Raspberry Pi에 연결합니다:

| 프린터 핀 | Pi GPIO 핀 | 물리적 핀 번호 |
|---------|-----------|-------------|
| GND     | GND       | 6, 9, 14, 20, 25, 30, 34, 39 중 아무거나 |
| RX      | TX (GPIO 14) | 핀 8 |
| TX      | RX (GPIO 15) | 핀 10 |

**추가 GPIO 연결:**
- **셔터 버튼**: GPIO20 (핀 38)
- **LED**: GPIO16 (핀 36)

**전원 연결**:
- 프린터의 DC 전원 커넥터에 5V 전원 어댑터를 연결합니다.
- 프린터와 Pi는 **별도의 전원**을 사용해야 합니다.

자세한 배선도는 [이 튜토리얼](https://learn.adafruit.com/networked-thermal-printer-using-cups-and-raspberry-pi/connect-and-configure-printer)을 참고하세요.

### 3. 버튼 및 LED 연결

**GPIO 핀 배치:**

| 구성요소 | GPIO 핀 | 물리적 핀 번호 | 연결 방법 |
|---------|--------|-------------|----------|
| 셔터 버튼 | GPIO20 | 핀 38 | 버튼 한쪽을 GPIO20에, 다른 쪽을 GND에 연결 |
| LED | GPIO16 | 핀 36 | LED 양극(+)을 GPIO16에, 음극(-)을 GND에 연결 (저항 필요시 추가) |

**연결 시 주의사항:**
- 셔터 버튼: 내부 풀업 저항을 사용하므로 별도 저항이 불필요합니다.
- LED: LED가 내장된 푸시버튼을 사용하는 경우 내장 저항이 있어 별도 저항이 불필요할 수 있습니다. 일반 LED 사용 시 330Ω 저항을 직렬로 연결하세요.

자세한 핀 배치는 [Raspberry Pi GPIO 핀아웃](https://pinout.xyz/)을 참고하세요.

### 4. 전원 회로 구성
[TODO] 정리 및 단계별 설명 추가

<img width="1217" alt="image" src="./pics/dca36686.png">

---

# 소프트웨어 설치 및 설정

하드웨어 조립을 완료했다면, 이제 Raspberry Pi에 소프트웨어를 설치하고 설정해야 합니다.

**📘 자세한 소프트웨어 설정 가이드는 [RASPBERRY_PI_SETUP.md](RASPBERRY_PI_SETUP.md)를 참고하세요.**

다음 내용을 포함합니다:
- Raspberry Pi OS 설치 및 초기 설정
- SSH를 통한 헤드리스 접속
- 카메라 및 프린터 드라이버 설치
- Python 패키지 설치
- OpenAI API 키 설정
- 부팅 시 자동 실행 설정
- Wi-Fi 네트워크 관리

---

# 추가 기능

## 이동 중 Wi‑Fi 네트워크 변경
이 카메라는 동작을 위해 Wi‑Fi가 필요합니다. 이동 중 새 Wi‑Fi에 손쉽게 연결하려면 플러그 앤드 플레이 코드가 포함된 [이 간단한 튜토리얼](https://www.raspberrypi.com/tutorials/host-a-hotel-wifi-hotspot/)을 따라 하세요.

위 튜토리얼을 진행하려면 microUSB 포트에 두 번째 Wi‑Fi 어댑터를 꽂아야 합니다. Linux/Raspberry Pi에서 곧바로 인식되는 플러그 앤드 플레이 어댑터를 추천합니다.

작동이 확인된 Wi‑Fi 어댑터 예시:
- [Pi Hut(영국)](https://thepihut.com/products/usb-wifi-adapter-for-the-raspberry-pi)
- [LOTEKOO, Amazon](https://www.amazon.com/dp/B06Y2HKT75)
- [Canakit, Amazon](https://www.amazon.com/dp/B00GFAN498)

MicroUSB→USB 어댑터:
- [Amazon](https://www.amazon.com/Ksmile%C2%AE-Female-Adapter-SamSung-tablets/dp/B01C6032G0)
- [초슬림, Adafruit](https://www.adafruit.com/product/2910)
