#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
한글 출력 테스트용 스크립트 (이미지 방식)
텍스트를 이미지로 렌더링한 후 프린터로 출력합니다.
"""

from PIL import Image, ImageDraw, ImageFont
import io
import os
import random
import glob

# Adafruit_Thermal 대신 python-escpos 사용 (한글 이미지 출력 지원)
try:
    from escpos.printer import Serial
    printer = Serial('/dev/serial0', baudrate=19200, timeout=5)
    print("✅ python-escpos로 프린터 연결 성공")
except ImportError:
    print("❌ python-escpos가 설치되지 않음. Adafruit_Thermal로 대체 시도...")
    from Adafruit_Thermal import *
    printer = Adafruit_Thermal('/dev/serial0', 19200, timeout=5)
    print("⚠️  Adafruit_Thermal 사용 (이미지 출력 제한적)")
except Exception as e:
    print(f"❌ 프린터 연결 실패: {e}")
    exit(1)

import time

def create_korean_text_image(text, font_path, font_size=48, width=384):
    """
    한글 텍스트를 이미지로 변환
    Args:
        text: 출력할 한글 텍스트
        font_path: 사용할 폰트 파일 경로
        font_size: 폰트 크기 (기본값: 48 - 2배 크기)
        width: 이미지 너비 (프린터 너비에 맞춤)
    Returns:
        PIL Image 객체
    """
    # 폰트 로드
    try:
        font = ImageFont.truetype(font_path, font_size)
        print(f"✅ 폰트 로드: {os.path.basename(font_path)}")
    except Exception as e:
        print(f"⚠️  폰트 로드 실패: {font_path} - {e}")
        font = ImageFont.load_default()

    # 텍스트 크기 계산
    # PIL 9.0+에서는 bbox를 사용하고, 이전 버전은 textsize를 사용
    try:
        bbox = font.getbbox(text)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
    except AttributeError:
        # 이전 버전 PIL 호환성
        try:
            text_width, text_height = font.getsize(text)
        except:
            # 기본 폰트로 대체
            text_width, text_height = 100, 20
    
    # 이미지 생성 (흰 배경)
    height = max(text_height + 20, 40)  # 최소 높이 보장
    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)
    
    # 텍스트를 이미지 중앙에 그리기 (볼드 효과를 위해 여러 번 그리기)
    x = max((width - text_width) // 2, 0)
    y = max((height - text_height) // 2, 0)
    
    # 볼드 효과: 1픽셀씩 이동하며 여러 번 그리기
    for dx in range(2):
        for dy in range(2):
            draw.text((x + dx, y + dy), text, font=font, fill='black')
    
    # 1비트 흑백으로 변환 (프린터용)
    img = img.convert('1')
    
    return img

def print_korean_text_with_font(font_path, font_display_name):
    """특정 폰트로 한글 텍스트를 이미지로 변환하여 출력"""
    try:
        # 폰트 이름을 텍스트로 변환하여 출력
        img = create_korean_text_image(font_display_name, font_path)
        
        # python-escpos 사용 시
        if hasattr(printer, 'image'):
            printer.image(img)
            print(f"✅ 이미지로 출력: {font_display_name}")
        # Adafruit_Thermal 사용 시 (제한적)
        elif hasattr(printer, 'printImage'):
            printer.printImage(img, LaaT=True)
            print(f"✅ 이미지로 출력: {font_display_name}")
        else:
            # 일반 텍스트로 출력 (한글 깨짐)
            printer.println(font_display_name)
            print(f"⚠️  텍스트로 출력 (한글 깨질 수 있음): {font_display_name}")
            
    except Exception as e:
        print(f"❌ 출력 실패: {font_display_name} - {e}")

def get_all_fonts():
    """모든 폰트 파일을 순서대로 가져오기"""
    font_base_path = './fonts/clova-all/'
    all_fonts = []
    
    # 모든 폰트 폴더 찾기
    font_folders = [f for f in os.listdir(font_base_path) if os.path.isdir(os.path.join(font_base_path, f))]
    font_folders.sort()  # 폴더명으로 정렬
    
    for folder in font_folders:
        font_folder_path = os.path.join(font_base_path, folder)
        
        # 폰트 파일 찾기 (ttf, otf 확장자)
        font_files = []
        for ext in ['*.ttf', '*.otf', '*.TTF', '*.OTF']:
            font_files.extend(glob.glob(os.path.join(font_folder_path, ext)))
        
        for font_file in sorted(font_files):  # 파일명으로 정렬
            # 파일명에서 확장자 제거하여 폰트 표시명 생성
            font_display_name = os.path.splitext(os.path.basename(font_file))[0]
            all_fonts.append((font_file, font_display_name))
    
    return all_fonts

# 프린터 초기화 대기
time.sleep(2)

print("한글 이미지 출력 테스트 시작...")
print("모든 폰트를 순서대로 출력합니다...")

try:
    # 모든 폰트 가져오기
    all_fonts = get_all_fonts()
    
    if not all_fonts:
        print("❌ 폰트를 찾을 수 없습니다.")
        exit(1)
    
    print(f"총 {len(all_fonts)}개의 폰트를 발견했습니다.")
    
    # 헤더 출력
    if hasattr(printer, 'set'):
        printer.set(align='center')
    else:
        printer.justify('C')
    
    # 첫 번째 폰트로 헤더 출력
    if all_fonts:
        first_font_path, _ = all_fonts[0]
        header_img = create_korean_text_image("=== 한글 폰트 테스트 ===", first_font_path)
        if hasattr(printer, 'image'):
            printer.image(header_img)
        print("✅ 헤더 출력 완료")
    
    # 좌측 정렬로 변경
    if hasattr(printer, 'set'):
        printer.set(align='left')
    else:
        printer.justify('L')
    
    # 모든 폰트를 순서대로 출력
    for i, (font_path, font_display_name) in enumerate(all_fonts):
        print(f"[{i+1}/{len(all_fonts)}] 출력 중: {font_display_name}")
        print_korean_text_with_font(font_path, font_display_name)
        
        # 프린터 과부하 방지를 위한 약간의 지연
        time.sleep(0.5)
    
    # 푸터 출력
    if hasattr(printer, 'set'):
        printer.set(align='center')
    else:
        printer.justify('C')
    
    if all_fonts:
        last_font_path, _ = all_fonts[-1]
        footer_img = create_korean_text_image("=== 테스트 완료 ===", last_font_path)
        if hasattr(printer, 'image'):
            printer.image(footer_img)
        print("✅ 푸터 출력 완료")
    
    # 용지 여백
    if hasattr(printer, 'ln'):
        printer.ln(3)
    else:
        printer.println('\n\n\n')
    
    print("✅ 한글 폰트 테스트 완료!")
    print(f"총 {len(all_fonts)}개의 폰트가 출력되었습니다.")
    
except Exception as e:
    print(f"❌ 오류 발생: {e}")
    
finally:
    # 프린터 연결 종료
    if hasattr(printer, 'close'):
        printer.close()
    print("프린터 연결 종료")
