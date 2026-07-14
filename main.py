# picamera2 예제 capture_jpeg.py를 기반으로 함
#!/usr/bin/python3

# 프리뷰 모드가 실행 중인 상태에서 JPEG를 캡처합니다.
# 파일로 캡처하면 반환값은 해당 이미지의 메타데이터입니다.

import time, requests, signal, os, base64, random, glob

from picamera2 import Picamera2, Preview
from gpiozero import LED, Button
from Adafruit_Thermal import *
from wraptext import *
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai
from PIL import Image, ImageDraw, ImageFont

# python-escpos를 우선 시도하고, 실패하면 Adafruit_Thermal 사용
try:
    from escpos.printer import Serial
    printer = Serial('/dev/serial0', baudrate=19200, timeout=5)
    USE_ESCPOS = True
    # ASCII 문자 출력을 위한 코드페이지 설정
    try:
        printer.charcode(code='USA')  # 또는 'CP437' 사용
    except:
        pass  # 코드페이지 설정 실패해도 계속 진행
    print("✅ python-escpos로 프린터 연결 성공")
except ImportError:
    print("❌ python-escpos가 설치되지 않음. Adafruit_Thermal로 대체 시도...")
    # 프린터 초기화
    baud_rate = 19200 # 대부분의 감열 프린터는 19200 보드레이트를 사용
    printer = Adafruit_Thermal('/dev/serial0', baud_rate, timeout=5)
    USE_ESCPOS = False
    print("⚠️  Adafruit_Thermal 사용 (이미지 출력 제한적)")
except Exception as e:
    print(f"❌ 프린터 연결 실패: {e}")
    # 일단 계속 진행, 프린터 없이도 동작하도록
    printer = None
    USE_ESCPOS = False

# .env에서 API 키 불러오기
load_dotenv()
genai.configure(api_key=os.environ['GOOGLE_API_KEY'])

# 카메라 초기화
picam2 = Picamera2()
# 카메라 시작
picam2.start()
time.sleep(2) # 처음 몇 프레임의 품질이 낮을 수 있어 예열 시간을 둠

# 버튼 초기화 (bounce_time 추가로 버튼 바운싱 방지)
shutter_button = Button(16, bounce_time=0.1) # 셔터 버튼 GPIO16, 100ms 바운스 타임
# power_button = Button(26, hold_time = 2) # 파워 버튼 미지정 - 주석 처리
led = LED(26) # LED GPIO26

# 실행 중 플래그 (중복 실행 방지)
is_processing = False

# 시작 시 한 번만 폰트 선택
SELECTED_FONT_PATH = None

def calculate_chars_per_line(font_size=48, width=384):
    """
    선택된 폰트로 한 줄에 들어갈 수 있는 글자수를 계산
    Args:
        font_size: 폰트 크기 (기본값: 48)
        width: 이미지 너비 (기본값: 384픽셀)
    Returns:
        한 줄에 들어갈 수 있는 글자수 (빈칸 포함)
    """
    global SELECTED_FONT_PATH
    
    try:
        if SELECTED_FONT_PATH:
            font = ImageFont.truetype(SELECTED_FONT_PATH, font_size)
        else:
            font = ImageFont.load_default()
        
        # 한글 대표 문자들로 평균 글자폭 계산
        test_chars = "가나다라마바사아자차카타파하 일이삼사오육칠팔구십"
        
        total_width = 0
        char_count = 0
        
        for char in test_chars:
            try:
                bbox = font.getbbox(char)
                char_width = bbox[2] - bbox[0]
                total_width += char_width
                char_count += 1
            except:
                # 이전 버전 PIL 호환성
                try:
                    char_width, _ = font.getsize(char)
                    total_width += char_width
                    char_count += 1
                except:
                    # 기본값 사용
                    total_width += 20
                    char_count += 1
        
        if char_count > 0:
            avg_char_width = total_width / char_count
            # 좌우 여백(20px) + 볼드효과(2px)를 고려한 실제 사용 가능 폭
            usable_width = width - 20 - 2  # 362픽셀
            chars_per_line = int(usable_width / avg_char_width)
            print(f"📏 폰트 크기: {font_size}px, 평균 글자폭: {avg_char_width:.1f}px, 한 줄 글자수: {chars_per_line}자")
            return max(chars_per_line, 8)  # 최소 8글자 보장
        else:
            return 12  # 기본값
            
    except Exception as e:
        print(f"⚠️  글자수 계산 실패: {e} - 기본값 12 사용")
        return 12

# 프롬프트 설정
# 시스템 프롬프트: AI 시인의 스타일과 제약사항을 정의 (한국어 시)
system_prompt = """당신은 한국어 시를 쓰는 시인입니다. 우아하고 감정적으로 영향력 있는 한국어 시를 전문으로 합니다.
미묘함을 사용하고 현대적인 구어체 스타일로 작성합니다.
일상적인 한국어를 사용하되, 문학적인 기교를 사용합니다.
시는 문학적이면서도 공감하고 이해하기 쉬워야 합니다.
친밀하고 개인적인 진실에 집중하며, '진실', '시간', '침묵', '인생', '사랑', '평화', '전쟁', '증오', '행복' 같은 추상적이고 큰 단어를 직접적으로 사용하지 않습니다.
대신 구체적이고 명확한 언어를 사용하여 그러한 아이디어를 말하지 않고 보여줘야 합니다.
섬세하고 아름다운 한국어 시를 만드는 방법에 대해 신중하게 생각하세요.
이것은 매우 중요하며, 지나치게 서투르거나 진부한 시는 피해야 합니다."""

# 시 형식: 8줄 자유시 (한국어)
poem_format = "8줄 자유시 (한국어)"


#############################
# 핵심 사진-시 변환 함수
#############################
def take_photo_and_print_poem():
  global is_processing
  
  # 이미 실행 중이면 무시 (중복 실행 방지)
  if is_processing:
    print("⚠️  이미 처리 중입니다. 완료될 때까지 기다려주세요.")
    return
  
  is_processing = True
  print("📸 사진 촬영 및 시 생성 시작...")
  
  try:
    # 백그라운드에서 LED 점멸 시작
    led.blink()

    # 저장 디렉터리가 존재하도록 보장
    image_path = '/home/pashiran/CamTest/images/image.jpg'
    os.makedirs(os.path.dirname(image_path), exist_ok=True)

    # 사진을 촬영하고 저장합니다
    metadata = picam2.capture_file(image_path)

    # 디버깅용: 메타데이터 출력
    #print(metadata)

    # 카메라 종료는 프로그램 마지막에만 가능해서 주석 처리
    # picam2.close()

    # 디버깅용: 이미지 저장 완료 표시
    print('----- SUCCESS: image saved locally')

    #########################
    # Google Gemini API로 이미지를 분석하고 시를 생성
    #########################

    # 이미지 불러오기
    img = Image.open(image_path)

    # Gemini 모델 생성(속도와 품질 균형을 위해 gemini-2.5-flash 사용)
    model = genai.GenerativeModel('models/gemini-2.5-flash')

    # 한 줄에 들어갈 글자수 계산
    chars_per_line = calculate_chars_per_line()
    
    # Gemini용 프롬프트 생성 (이미지 분석과 한국어 시 생성을 통합)
    prompt = f"""{system_prompt}

제공된 이미지를 기반으로 다음 형식으로 한국어 시를 작성하세요: {poem_format}

중요한 제약사항:
1. 첫 줄에 전체 주제를 관통하는 1-2단어 이내의 간결한 제목을 배치하세요
2. 제목 다음 줄을 비우고 본문을 시작하세요
3. 각 줄은 공백 포함 최대 {chars_per_line}글자를 넘지 않게 작성하세요. 공백은 반(1/2)글자로 계산합니다. 
4. 전체적으로 3연 구조를 따르며, 각 연 사이에 빈 줄을 넣어 명확히 구분하세요
5. 이미지의 중앙에 보이는 주제에 집중하고, 제일 중요한 요소를 중심으로 시를 전개하세요

시는 이미지에서 보이는 세부 사항을 자연스럽게 하나의 주제로 통합해야 합니다.
이미지에 대한 참조는 미묘하면서도 명확해야 합니다.
이미지의 구체적인 아이디어와 세부 사항을 사용하여 독특하고 우아한 한국어 시에 집중하세요.
어휘를 단순하게 유지하고 절제된 관점을 사용해야 합니다.
분위기, 대기, 사물, 색상 및 흥미로운 세부 사항에 집중하세요.

출력 형식 예시:
제목

첫 번째 연의 첫 줄
첫 번째 연의 둘째 줄

두 번째 연의 첫 줄
두 번째 연의 둘째 줄

세 번째 연의 첫 줄
세 번째 연의 둘째 줄

한국어 시만 응답하고 다른 것은 응답하지 마세요."""

    # 이미지로부터 시 생성
    print('⏳ AI가 시를 생성하고 있습니다...')
    try:
      response = model.generate_content([prompt, img])
      poem = response.text
      
      print('--------POEM BELOW-------')
      print(poem)
      print('------------------')
      print('✅ 시 생성 완료! 이제 프린터로 출력합니다...')
      
    # API 응답을 받은 뒤 전체 출력 시작
      print_header()
      
    # 헤더와 시 사이 구분선
      print_separator()
      
      # 시 출력
      print_poem(poem)
      
    # 시와 푸터 사이 구분선
      print_separator()
      
      # 푸터 출력
      print_footer()
      
    except Exception as e:
      print(f'❌ 시 생성 실패: {e}')
      if printer and hasattr(printer, 'println'):
        printer.println('Error: Could not generate poem')
    
    led.off()
    
    # 이미지 파일 삭제 (저장 공간 절약 및 개인정보 보호)
    try:
      os.remove(image_path)
      print(f'----- SUCCESS: image deleted from {image_path}')
    except Exception as e:
      print(f'----- WARNING: Could not delete image: {e}')
  
  except Exception as e:
    # 전체 프로세스에서 발생한 예외 처리
    print(f'❌ 처리 중 오류 발생: {e}')
    led.off()
  finally:
    # 처리 완료 후 플래그 해제 및 대기 상태로 복귀
    is_processing = False
    led.on()  # 대기 상태 LED 다시 켜기
    print("✅ 처리 완료 - 다음 촬영 대기 중...\n")
    print("💡 LED 켜짐 - 셔터 버튼 대기 중...")

  return


#######################
# 이 함수는 Gemini API 사용 시 더 이상 필요하지 않음
# (참고용으로만 남겨두며 실제로는 사용하지 않음)
#######################
def generate_prompt(image_description):
    # Gemini 사용 시 이 함수는 더 이상 권장되지 않음
    # Gemini는 한 번의 호출로 이미지 분석과 시 생성을 모두 처리함
  pass



###########################
# 한글 텍스트 이미지 함수
###########################

def get_random_korean_font():
    """랜덤하게 한글 폰트를 선택"""
    font_base_path = './fonts/clova-all/'
    
    try:
        # 모든 폰트 폴더 찾기
        font_folders = [f for f in os.listdir(font_base_path) if os.path.isdir(os.path.join(font_base_path, f))]
        
        if not font_folders:
            print("❌ fonts/clova-all/ 폴더에서 폰트를 찾을 수 없습니다.")
            return None
        
        # 랜덤하게 폰트 폴더 선택
        selected_font_folder = random.choice(font_folders)
        font_folder_path = os.path.join(font_base_path, selected_font_folder)
        
        # 폰트 파일 찾기 (ttf, otf 확장자)
        font_files = []
        for ext in ['*.ttf', '*.otf', '*.TTF', '*.OTF']:
            font_files.extend(glob.glob(os.path.join(font_folder_path, ext)))
        
        if font_files:
            # 랜덤하게 폰트 파일 선택
            selected_font_file = random.choice(font_files)
            print(f"✅ 랜덤 폰트 선택: {selected_font_folder} - {os.path.basename(selected_font_file)}")
            return selected_font_file
        else:
            print(f"⚠️  {selected_font_folder}에서 폰트 파일을 찾을 수 없습니다.")
            return None
            
    except Exception as e:
        print(f"❌ 폰트 선택 실패: {e}")
        return None

def create_korean_text_image(text, font_size=48, width=384):
    """
    한글 텍스트를 볼드 이미지로 변환
    Args:
        text: 출력할 한글 텍스트
        font_size: 폰트 크기 (기본값: 48)
        width: 이미지 너비 (프린터 너비에 맞춤)
    Returns:
        PIL Image 객체
    """
    global SELECTED_FONT_PATH
    
    # 폰트 로드 (전역 변수 사용)
    try:
        if SELECTED_FONT_PATH:
            font = ImageFont.truetype(SELECTED_FONT_PATH, font_size)
        else:
            font = ImageFont.load_default()
            print("⚠️  기본 폰트 사용")
    except Exception as e:
        print(f"⚠️  폰트 로드 실패: {e} - 기본 폰트 사용")
        font = ImageFont.load_default()

    # 텍스트 크기 계산
    try:
        bbox = font.getbbox(text)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        # bbox는 (left, top, right, bottom) 형태로, top은 음수일 수 있음
        bbox_top = bbox[1]
        bbox_bottom = bbox[3]
    except AttributeError:
        # 이전 버전 PIL 호환성
        try:
            text_width, text_height = font.getsize(text)
            bbox_top = 0
            bbox_bottom = text_height
        except:
            text_width, text_height = 100, 20
            bbox_top = 0
            bbox_bottom = 20
    
    # 이미지 생성 (흰 배경)
    # 글자 크기에 비례하여 상하 여백 확보 (폰트 크기의 40% 여백)
    vertical_margin = int(font_size * 0.4)
    # 실제 글자의 전체 높이 (상단 여백 포함)
    total_text_height = bbox_bottom - bbox_top
    # 볼드 효과(2픽셀) + 상하 여백을 고려한 총 높이
    height = max(total_text_height + vertical_margin * 2 + 4, 40)  # 최소 높이 보장
    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)
    
    # 텍스트를 왼쪽 정렬 (좌우 여백 10픽셀씩 확보)
    x_margin = 10
    # bbox_top이 음수인 경우를 고려하여 y 위치 조정
    y = vertical_margin - bbox_top + 2  # 상단 여백 + bbox 오프셋 보정 + 볼드 효과 여유
    
    # 볼드 효과: 1픽셀씩 이동하며 여러 번 그리기
    for dx in range(2):
        for dy in range(2):
            draw.text((x_margin + dx, y + dy), text, font=font, fill='black')
    
    # 1비트 흑백으로 변환 (프린터용)
    img = img.convert('1')
    
    return img

def print_korean_text(text, font_size=48):
    """한글 텍스트를 이미지로 변환하여 프린터로 출력
    Args:
        text: 출력할 한글 텍스트
        font_size: 폰트 크기 (기본값: 48, 제목은 53)
    """
    if not printer:
        print(f"❌ 프린터가 연결되지 않음: {text}")
        return
        
    try:
        # 텍스트를 이미지로 변환 (font_size 파라미터 전달)
        img = create_korean_text_image(text, font_size=font_size)
        
        # python-escpos 사용 시
        if USE_ESCPOS and hasattr(printer, 'image'):
            printer.image(img)
            print(f"✅ 한글 이미지로 출력: {text}")
        # Adafruit_Thermal 사용 시 (제한적)
        elif hasattr(printer, 'printImage'):
            printer.printImage(img, LaaT=True)
            print(f"✅ 한글 이미지로 출력: {text}")
        else:
            # 일반 텍스트로 출력 (한글 깨짐)
            if hasattr(printer, 'println'):
                printer.println(text)
            print(f"⚠️  텍스트로 출력 (한글 깨질 수 있음): {text}")
            
    except Exception as e:
        print(f"❌ 한글 출력 실패: {text} - {e}")

###########################
# 영수증 프린터 함수
###########################

def print_separator():
    """아스키 구분선 출력"""
    if not printer:
        return
        
    try:
        # 중앙 정렬
        if USE_ESCPOS and hasattr(printer, 'set'):
            printer.set(align='center')
        elif hasattr(printer, 'justify'):
            printer.justify('C')
        
        # 아스키 구분선 출력 (escpos와 Adafruit 방식 구분)
        if USE_ESCPOS and hasattr(printer, 'text'):
            # python-escpos는 text() 사용 (자동 개행 없음)
            printer.text('\n')
            printer.text("`'. .'`'. .'`'. .'`'. .'`'. .'`\n")
            printer.text("   `     `     `     `     `   \n")
            printer.text('\n')
        elif hasattr(printer, 'println'):
            # Adafruit_Thermal은 println() 사용
            printer.println('\n')
            printer.println("`'. .'`'. .'`'. .'`'. .'`'. .'`")
            printer.println("   `     `     `     `     `   ")
            printer.println('\n')
        
        print("✅ 구분선 출력 완료")
        
    except Exception as e:
        print(f"❌ 구분선 출력 실패: {e}")

def print_poem(poem):
    """시를 한글 이미지로 변환하여 출력"""
    if not printer:
        print("❌ 프린터가 연결되지 않음")
        return
        
    try:
        # 시를 줄별로 분할
        lines = poem.strip().split('\n')
        
        if not lines:
            print("⚠️  출력할 시가 없습니다")
            return
        
        # 좌측 정렬
        if USE_ESCPOS and hasattr(printer, 'set'):
            printer.set(align='left')
        elif hasattr(printer, 'justify'):
            printer.justify('L')
        
        # 첫 번째 줄을 제목으로 처리 (10% 더 크게 = 48 * 1.1 = 53)
        title = lines[0].strip()
        if title:
            print(f"📌 제목 출력: {title}")
            print_korean_text(title, font_size=53)
            time.sleep(0.2)
            
            # 제목과 본문 사이 한 줄 띄우기 (feed 사용)
            if hasattr(printer, 'feed'):
                printer.feed(1)  # 1줄 공급
            elif USE_ESCPOS and hasattr(printer, 'text'):
                printer.text('\n\n')  # 2개 줄바꿈으로 확실히 띄우기
            elif hasattr(printer, 'println'):
                printer.println('\n')  # 빈 줄 출력
            print("  (제목과 본문 사이 빈 줄 추가)")
        
        # 나머지 줄들을 본문으로 처리 (연 구분)
        # 빈 줄을 기준으로 연을 구분하고, 각 연 사이에 줄바꿈 추가
        stanza_lines = []
        current_stanza = []
        
        for i in range(1, len(lines)):
            line = lines[i].strip()
            
            if line:  # 빈 줄이 아닌 경우
                current_stanza.append(line)
            else:  # 빈 줄인 경우 (연 구분)
                if current_stanza:
                    stanza_lines.append(current_stanza)
                    current_stanza = []
        
        # 마지막 연 추가
        if current_stanza:
            stanza_lines.append(current_stanza)
        
        # 각 연을 출력하되, 연 사이에 빈 줄 추가
        for stanza_idx, stanza in enumerate(stanza_lines):
            for line in stanza:
                print_korean_text(line)
                time.sleep(0.2)  # 프린터 과부하 방지
            
            # 연 사이에 빈 줄 추가 (마지막 연 제외)
            if stanza_idx < len(stanza_lines) - 1:
                if hasattr(printer, 'feed'):
                    printer.feed(1)  # 1줄 공급
                elif USE_ESCPOS and hasattr(printer, 'text'):
                    printer.text('\n\n')  # 2개 줄바꿈으로 확실히 띄우기
                elif hasattr(printer, 'println'):
                    printer.println('\n')  # 빈 줄 출력
                print(f"  (연 {stanza_idx + 1} 완료, 빈 줄 추가)")
        
        print("✅ 시 출력 완료")
        
    except Exception as e:
        print(f"❌ 시 출력 실패: {e}")
        # 백업: 기존 텍스트 방식으로 출력
        try:
            if hasattr(printer, 'println'):
                printable_poem = wrap_text(poem, 32)
                printer.justify('L')
                printer.println(printable_poem)
                print("⚠️  백업 텍스트 방식으로 출력됨")
        except Exception as e2:
            print(f"❌ 백업 출력도 실패: {e2}")


# 날짜/시간 헤더 출력
def print_header():
    """헤더 출력 (날짜/시간)"""
    if not printer:
        print("❌ 프린터가 연결되지 않음")
        return
        
    try:
        # 현재 날짜와 시간을 가져와 출력과 파일명에 사용
        now = datetime.now()

        # 중앙 정렬
        if USE_ESCPOS and hasattr(printer, 'set'):
            printer.set(align='center')
        elif hasattr(printer, 'justify'):
            printer.justify('C')
        
        # 줄바꿈
        if USE_ESCPOS and hasattr(printer, 'text'):
            printer.text('\n')
        elif hasattr(printer, 'ln'):
            printer.ln()
        elif hasattr(printer, 'println'):
            printer.println('\n')

        # 출력용 날짜/시간 형식 지정
        date_string = now.strftime('%Y년 %m월 %d일')
        time_string = now.strftime('%H:%M')
        
        # 날짜와 시간을 한글 이미지로 출력
        print_korean_text(date_string)
        print_korean_text(time_string)

        # 시각적 간격 조정
        if USE_ESCPOS and hasattr(printer, 'text'):
            printer.text('\n')
        elif hasattr(printer, 'setLineHeight'):
            printer.setLineHeight(56)
            printer.println()
            printer.setLineHeight()
        elif hasattr(printer, 'ln'):
            printer.ln()
        elif hasattr(printer, 'println'):
            printer.println()
        
        print("✅ 헤더 출력 완료")
        
    except Exception as e:
        print(f"❌ 헤더 출력 실패: {e}")


# 푸터 출력
def print_footer():
    """푸터 출력"""
    if not printer:
        print("❌ 프린터가 연결되지 않음")
        return
        
    try:
        # 중앙 정렬
        if USE_ESCPOS and hasattr(printer, 'set'):
            printer.set(align='center')
        elif hasattr(printer, 'justify'):
            printer.justify('C')

        # AI 안내 메시지를 한글 이미지로 출력
        print_korean_text("이 시는 AI가 작성했습니다")
        
        if USE_ESCPOS and hasattr(printer, 'text'):
            printer.text('\n')
        elif hasattr(printer, 'println'):
            printer.println()
        
        # 웹사이트 정보는 영문 텍스트로 출력
        if USE_ESCPOS and hasattr(printer, 'text'):
            printer.text('Explore the archives at\n')
            printer.text('poetry.camera\n')
        elif hasattr(printer, 'println'):
            printer.println('Explore the archives at')
            printer.println('poetry.camera')
        
        # 종이를 밀어내서 여백 확보 (2배 증가)
        # 약 3cm 여백 = 약 24줄 (열 프린터 해상도 8dots/mm 기준)
        if hasattr(printer, 'feed'):
            printer.feed(50)  # escpos 방식: 24줄 공급 (약 3cm)
        elif hasattr(printer, 'println'):
            # Adafruit 방식: 24줄 공급
            printer.println('\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n')
        
        print("✅ 푸터 출력 완료")
        
    except Exception as e:
        print(f"❌ 푸터 출력 실패: {e}")


##############
# 전원 버튼
##############
def shutdown():
  print('shutdown button held for 2s')
  print('shutting down now')
  led.off()
  os.system('sudo shutdown -h now')

################################
# Raspberry Pi 디버깅용:
# Ctrl+C로 스크립트를 안전하게 종료합니다
# (그렇지 않으면 Pi 전체가 종료될 수 있음)
#################################
def handle_keyboard_interrupt(sig, frame):
  print('Ctrl+C received, stopping script')
  led.off()

    # Pi가 비정상 종료되지 않도록 RPi 포럼에서 찾은 우회 방법
  os.kill(os.getpid(), signal.SIGUSR1)

signal.signal(signal.SIGINT, handle_keyboard_interrupt)


#################
# 버튼 핸들러
#################
def handle_pressed():
  """셔터 버튼이 눌렸을 때 실행"""
  print("🔘 버튼 눌림 감지!")
  take_photo_and_print_poem()

def handle_held():
  """파워 버튼이 길게 눌렸을 때 실행"""
  print("button held!")
  shutdown()


################################
# 버튼 입력 이벤트 대기
################################

# 프로그램 시작 시 폰트 선택 (한 번만)
print("🎨 프로그램 시작 - 폰트 선택 중...")
SELECTED_FONT_PATH = get_random_korean_font()
if SELECTED_FONT_PATH:
    font_name = os.path.basename(os.path.dirname(SELECTED_FONT_PATH))
    print(f"✅ 선택된 폰트: {font_name}")
    
    # 글자수 미리 계산해서 확인
    chars_per_line = calculate_chars_per_line()
    print(f"📝 한 줄 최대 글자수: {chars_per_line}자 (공백 포함)")
else:
    print("⚠️  기본 폰트를 사용합니다")
    chars_per_line = calculate_chars_per_line()
    print(f"📝 한 줄 최대 글자수: {chars_per_line}자 (공백 포함)")

# 버튼 이벤트 핸들러 등록 (한 번만!)
shutter_button.when_pressed = handle_pressed
# power_button.when_held = shutdown  # 파워 버튼 미지정으로 주석 처리

# 대기 상태임을 표시 (LED 켜기)
led.on()
print("💡 LED 켜짐 - 셔터 버튼 대기 중...")

signal.pause()