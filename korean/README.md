# 한글 써멀 프린터 출력 모듈

써멀 프린터에서 한글을 출력하기 위한 이미지 기반 렌더링 모듈입니다.

## 문제점

기존 `Adafruit_Thermal.py` 라이브러리는:
- CP437 인코딩만 지원 (한글 미지원)
- `CHARSET_KOREA`는 일부 특수문자만 한국식으로 변경
- UTF-8, EUC-KR, CP949 같은 한글 코드페이지 미지원

## 해결 방법

한글 텍스트를 PIL(Pillow) 라이브러리로 비트맵 이미지로 변환한 후, 프린터의 `printImage()` 메소드로 출력합니다.

## 필수 요구사항

### 1. Pillow 라이브러리 설치
```bash
pip install Pillow
```

### 2. 한글 폰트 설치 (라즈베리파이)
```bash
sudo apt-get update
sudo apt-get install fonts-nanum fonts-nanum-coding
```

설치 가능한 한글 폰트:
- **NanumGothic**: 나눔고딕 (기본)
- **NanumMyeongjo**: 나눔명조
- **NanumBarunGothic**: 나눔바른고딕
- **NanumSquare**: 나눔스퀘어

폰트 경로:
- `/usr/share/fonts/truetype/nanum/NanumGothic.ttf`
- `/usr/share/fonts/truetype/nanum/NanumMyeongjo.ttf`
- `/usr/share/fonts/truetype/nanum/NanumBarunGothic.ttf`

## 사용 방법

### 테스트 실행

```bash
cd korean
python test_korean_print.py
```

### 기본 사용 예제

```python
from korean.test_korean_print import print_korean_text, print_korean_poem

# 한 줄 텍스트 출력
print_korean_text('안녕하세요', font_size=24)

# 여러 줄 시 출력
poem = [
    '바람이 불어오는 곳',
    '',
    '하늘을 보며',
    '구름 사이로'
]
print_korean_poem(poem)
```

## 주요 함수

### `create_korean_text_image(text, font_size=24, font_path)`
한글 텍스트를 PIL Image 객체로 변환합니다.

**매개변수:**
- `text`: 출력할 한글 텍스트
- `font_size`: 폰트 크기 (기본값: 24)
- `font_path`: 폰트 파일 경로 (기본값: NanumGothic)

**반환값:**
- PIL Image 객체 (1-bit 흑백 비트맵, 384px 너비)

### `print_korean_text(text, font_size=24)`
한글 텍스트를 써멀 프린터로 바로 출력합니다.

**매개변수:**
- `text`: 출력할 한글 텍스트
- `font_size`: 폰트 크기 (기본값: 24)

### `print_korean_poem(poem_lines)`
여러 줄의 시를 출력합니다.

**매개변수:**
- `poem_lines`: 시의 각 줄을 담은 리스트

## 폰트 크기 권장사항

- **제목**: 26-32
- **본문**: 20-24
- **소제목**: 18-22

써멀 프린터의 너비는 384픽셀(48mm)이므로, 한 줄에 들어가는 글자 수:
- 24pt: 약 12-14자
- 20pt: 약 14-16자
- 18pt: 약 16-18자

## 성능 고려사항

이미지 변환 방식은 텍스트를 직접 출력하는 것보다 느립니다:
- 각 줄마다 이미지 생성 및 변환 필요
- 프린터로 전송되는 데이터량 증가

하지만 한글 출력을 위해서는 현재 유일한 방법입니다.

## 문제 해결

### 폰트를 찾을 수 없음
```
IOError: cannot open resource
```

**해결:**
```bash
# 설치된 폰트 확인
fc-list :lang=ko

# 폰트 재설치
sudo apt-get install --reinstall fonts-nanum
```

### 프린터 연결 오류
```
SerialException: [Errno 2] No such file or directory: '/dev/serial0'
```

**해결:**
1. 라즈베리파이 시리얼 포트 활성화 확인
2. `/boot/config.txt`에서 `enable_uart=1` 설정
3. 재부팅 후 `/dev/serial0` 존재 확인

### 이미지가 깨져서 출력됨

**해결:**
- `printImage()` 메소드의 `LaaT=True` 매개변수 확인
- 프린터 전원 및 용지 상태 확인
- 폰트 크기를 줄여서 테스트

## 메인 프로젝트 통합

`main.py`에서 한글 시를 출력하려면:

```python
# main.py 상단에 추가
from korean.test_korean_print import print_korean_poem

# print_poem() 함수 수정
def print_poem(poem):
    # 한글이 포함된 경우 이미지 기반 출력
    poem_lines = poem.split('\n')
    print_korean_poem(poem_lines)
```

## 라이선스

메인 프로젝트와 동일한 라이선스를 따릅니다.
