# 'text'는 줄바꿈할 입력 문자열입니다
# 'line_length'는 한 줄당 최대 글자 수입니다
def wrap_text(text, line_length):
  # 입력 텍스트를 개별 줄로 분리합니다
  lines = text.split('\n')
  wrapped_text = ''

  for line in lines:
    # 현재 줄을 단어 목록으로 나눕니다
    words = line.split()
    current_line = ''

    for word in words:

      # 현재 줄 길이와 다음 단어 길이의 합이 최대 줄 길이 이내인지 확인합니다
      if len(current_line) + len(word) <= line_length:

        # 조건을 만족하면 현재 줄에 단어를 계속 추가합니다
        current_line += word + ' '

      else:

        # 현재 줄을 마무리해서 결과 문자열에 추가합니다
        # 다음 줄 들여쓰기를 위해 공백도 함께 넣습니다
        wrapped_text += current_line.strip() + '\n   '

        # 새 현재 줄을 시작합니다
        current_line = word + ' '

    # 마지막 줄을 결과 문자열에 추가합니다
    wrapped_text += current_line.strip() + '\n'

  return wrapped_text
