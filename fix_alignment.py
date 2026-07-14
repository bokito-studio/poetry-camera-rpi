with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. x = max 를 x_margin = 10 으로 변경
content = content.replace("    x = max((width - text_width) // 2, 0)", "    x_margin = 10")

# 2. draw.text의 x를 x_margin으로 변경
content = content.replace("draw.text((x + dx, y + dy), text, font=font, fill='black')", 
                         "draw.text((x_margin + dx, y + dy), text, font=font, fill='black')")

# 3. 글자수 계산에 여백 고려
content = content.replace("            chars_per_line = int(width / avg_char_width)",
                         "            usable_width = width - 22\n            chars_per_line = int(usable_width / avg_char_width)")

# 4. 기본값 변경
content = content.replace("return max(chars_per_line, 10)", "return max(chars_per_line, 8)")
content = content.replace("return 15  # 기본값", "return 12  # 기본값", 1)
content = content.replace("기본값 15 사용", "기본값 12 사용")
content = content.replace("        return 15\n", "        return 12\n", 1)

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("수정 완료!")
