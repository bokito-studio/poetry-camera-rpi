
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
            chars_per_line = int(width / avg_char_width)
            print(f"📏 폰트 크기: {font_size}px, 평균 글자폭: {avg_char_width:.1f}px, 한 줄 글자수: {chars_per_line}자")
            return max(chars_per_line, 10)  # 최소 10글자 보장
        else:
            return 15  # 기본값
            
    except Exception as e:
        print(f"⚠️  글자수 계산 실패: {e} - 기본값 15 사용")
        return 15

