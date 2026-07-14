#*************************************************************************
# Adafruit 감열 프린터용 파이썬 라이브러리입니다.
# 제품 정보: http://www.adafruit.com/products/597
# 이 프린터는 TTL 시리얼 통신을 사용하며, 2개의 핀이 필요합니다.
# 중요: 3.3V 시스템(예: Raspberry Pi)에서는 RX 핀
# (프린터의 TX, 초록색 선)에 10K 저항을 사용하거나 아예 연결하지 마세요.
#
# Adafruit는 이 오픈소스 코드를 제공하기 위해 시간과 자원을 투자합니다.
# Adafruit 제품을 구매하여 Adafruit와 오픈소스 하드웨어를 지원해 주세요.
#
# Adafruit Industries를 위해 Limor Fried/Ladyada가 작성했습니다.
# Phil Burgess가 Adafruit Industries용으로 파이썬 포팅을 했습니다.
# MIT 라이선스이며, 재배포 시 위의 모든 문구를 포함해야 합니다.
#*************************************************************************

# 이것은 Arduino용 Adafruit_Thermal 라이브러리를 거의 1:1로
# 직접 파이썬으로 옮긴 버전입니다. 모든 메서드는 Arduino 라이브러리와
# 동일한 이름 규칙을 사용하며, 필요한 경우에만 매개변수 동작에 약간의
# 차이가 있습니다. 덕분에 기존 Adafruit_Thermal 기반 프린터 프로젝트를
# Raspberry Pi, BeagleBone 등으로 옮기기 쉬워집니다. 예시는 printertest.py를
# 참고하세요.
#
# 큰 변화 중 하나는 printImage() 함수가 추가되었다는 점입니다.
# 이 함수는 Python Imaging Library와 연결되어 다양한 그래픽 기능을
# 활용할 수 있게 해줍니다.
#
# 할 일:
# - 표준 ConfigParser 라이브러리를 사용해 감열 프린터 보정 설정을
#   라이브러리 내부가 아닌 전역 설정 파일에 둘 수 있음.
# - 올바른 파이썬 라이브러리 설치 절차를 적용하기.
# - 오류 처리를 더 정확히 하기. 현재는 일부가 그대로 통과함.
# - 전반에 걸쳐 독스트링 추가하기.

from serial import Serial
import time
import sys
import math

class Adafruit_Thermal(Serial):

	resumeTime      =   0.0
	byteTime        =   0.0
	dotPrintTime    =   0.0
	dotFeedTime     =   0.0
	prevByte        =  '\n'
	column          =     0
	maxColumn       =    32
	charHeight      =    24
	lineSpacing     =     8
	barcodeHeight   =    50
	printMode       =     0
	defaultHeatTime =   120
	firmwareVersion =   268
	writeToStdout   = False

	def __init__(self, *args, **kwargs):
		# 새로운 동작: 매개변수가 없으면 출력은 stdout으로 기록되며
		# 'lp -o raw'로 파이프할 수 있습니다
		# (이전 동작은 기본 포트와 보드레이트를 사용하는 방식이었음).
		baudrate = 19200
		if len(args) == 0:
			self.writeToStdout = True
		if len(args) == 1:
			# 포트만 전달되면 기본 보드레이트를 사용합니다.
			args = [ args[0], baudrate ]
		elif len(args) == 2:
			# 둘 다 전달되면 해당 값을 사용합니다.
			baudrate = args[1]

		# 펌웨어는 기본적으로 2.68 버전이라고 가정합니다.
		# 'firmware=X' 인수로 덮어쓸 수 있으며,
		# X는 메이저 버전 * 100 + 마이너 버전입니다
		# (예: 2.64 버전은 "firmware=264").
		self.firmwareVersion = kwargs.get('firmware', 268)

		if self.writeToStdout is False:
			# 프린터에 1바이트를 전송하는 데 걸리는 시간을 계산합니다.
			# 유휴, 시작, 정지 비트를 고려해 8비트가 아닌 11비트를 사용합니다.
			# 유휴 시간은 불필요할 수도 있지만, 여기서는 안전 쪽으로 잡습니다.
			self.byteTime = 11.0 / float(baudrate)

			Serial.__init__(self, *args, **kwargs)

			# 이 메서드의 나머지 부분은 이전에는 begin()에 있었습니다.

			# 프린터는 전원이 들어오자마자 바로 데이터를 받을 수 없습니다.
			# 콜드 부팅과 초기화에 잠시 시간이 필요합니다.
			# 데이터를 받기 전 최소 0.5초 정도의 기동 시간을 둡니다.
			self.timeoutSet(0.5)

			self.wake()
			self.reset()

			# 매뉴얼 23페이지의 출력 설정 설명:
			# ESC 7 n1 n2 n3 설정 제어 매개변수 명령
			# 10진수: 27 55 n1 n2 n3
			# 최대 가열 도트 수, 가열 시간, 가열 간격
			# n1 = 0-255 최대 가열 도트 수, 단위(8도트), 기본값: 7(64도트)
			# n2 = 3-255 가열 시간, 단위(10us), 기본값: 80(800us)
			# n3 = 0-255 가열 간격, 단위(10us), 기본값: 2(20us)
			# 최대 가열 도트 수가 많을수록 인쇄 시 순간 전류 소모가 커지고
			# 인쇄 속도도 빨라집니다.
			# 최대 가열 도트 수는 8*(n1+1)입니다. 가열 시간이 길수록
			# 농도는 진해지지만 인쇄 속도는 느려집니다.
			# 가열 시간이 너무 짧으면 빈 페이지가 나올 수 있습니다.
			# 가열 간격이 길수록 더 선명하지만 인쇄 속도는 느려집니다.

			heatTime = kwargs.get('heattime', self.defaultHeatTime)
			self.writeBytes(
			  27,       # Esc
			  55,       # 7 (print settings)
			  11,       # Heat dots
			  heatTime, # Lib default
			  40)       # Heat interval

			# 매뉴얼 23페이지의 인쇄 농도 설명:
			# DC2 # n 인쇄 농도 설정
			# 10진수: 18 35 n
			# n의 D4..D0 비트는 인쇄 농도를 설정하는 데 사용됩니다.
			# 농도는 50% + 5% * n(D4-D0)입니다.
			# n의 D7..D5 비트는 인쇄 중단 시간을 설정하는 데 사용됩니다.
			# 중단 시간은 n(D7-D5)*250us입니다.
			# (기본값은 문서화되어 있지 않아 확실하지 않음)

			printDensity   = 10 # 100%
			printBreakTime =  2 # 500 uS

			self.writeBytes(
			  18, # DC2
			  35, # Print density
			  (printBreakTime << 5) | printDensity)
			self.dotPrintTime = 0.03
			self.dotFeedTime  = 0.0021
		else:
			self.reset() # 일부 변수를 초기화함

	# 프린터와 컴퓨터 사이에는 흐름 제어가 없으므로,
	# 프린터 버퍼가 넘치지 않도록 특별히 주의해야 합니다.
	# 시리얼 출력은 시리얼 속도와 장치의 인쇄/급지 속도 추정치에 따라
	# 제한됩니다. 이 장치는 움직이는 부품의 물리적 한계 때문에 비교적 느립니다.
	# 프린터에 작업을 보낸 뒤(예: 비트맵 인쇄)에는 일정 시간 동안 다른
	# 프린터 작업을 중단시키는 타임아웃을 설정합니다.
	# 이는 단순 지연을 쓰는 것보다 보통 더 효율적이며, 프린터가 실제 작업을
	# 마치는 동안 호출 측 코드가 다른 일(예: 이미지 수신 또는 디코딩)을
	# 계속할 수 있게 해줍니다.

	# 방금 보낸 작업의 예상 완료 시간을 설정합니다.
	def timeoutSet(self, x):
		self.resumeTime = time.time() + x

	# 필요하면 이전 작업이 끝날 때까지 기다립니다.
	def timeoutWait(self):
		if self.writeToStdout is False:
			while (time.time() - self.resumeTime) < 0: pass

	# 프린터 성능은 전원 전압, 종이 두께, 심지어 운까지 포함한 여러 변수에 따라
	# 달라질 수 있습니다. 이 메서드는 인쇄와 급지 시 종이가 세로 1도트 이동하는
	# 데 걸리는 시간(마이크로초 단위)을 설정합니다.
	# 예를 들어 기본 초기화 상태에서는 일반 크기 텍스트 높이가 24도트이고
	# 줄 간격이 32도트이므로, 한 줄을 출력하는 데 걸리는 시간은 대략
	# 24 * 인쇄 시간 + 8 * 급지 시간입니다.
	# 기본 인쇄/급지 시간은 임의의 테스트 기기를 기준으로 하지만,
	# 앞서 말했듯 실제 환경은 많은 요인의 영향을 받습니다.
	# 이 값을 조정해 과도한 지연이나 프린터 버퍼 초과를 피할 수 있습니다.
	def setTimes(self, p, f):
		# Arduino 라이브러리와의 호환성을 위해
		# 단위는 마이크로초를 사용합니다
		self.dotPrintTime = p / 1000000.0
		self.dotFeedTime  = f / 1000000.0

	# 원시 바이트 쓰기 메서드
	def writeBytes(self, *args):
		if self.writeToStdout:
			for arg in args:
				sys.stdout.write(bytes([arg]))
		else:
			for arg in args:
				self.timeoutWait()
				self.timeoutSet(len(args) * self.byteTime)
				super(Adafruit_Thermal, self).write(bytes([arg]))

	# write() 메서드를 재정의해 용지 급지를 추적합니다.
	def write(self, *data):
		for i in range(len(data)):
			c = data[i]
			if self.writeToStdout:
				sys.stdout.write(c)
				continue
			if c != 0x13:
				self.timeoutWait()
				super(Adafruit_Thermal, self).write(c)
				d = self.byteTime
				if ((c == '\n') or
				    (self.column == self.maxColumn)):
					# 줄바꿈 또는 자동 개행
					if self.prevByte == '\n':
						# 빈 줄 급지
						d += ((self.charHeight +
						       self.lineSpacing) *
						      self.dotFeedTime)
					else:
						# 텍스트 줄
						d += ((self.charHeight *
						       self.dotPrintTime) +
						      (self.lineSpacing *
						       self.dotFeedTime))
						self.column = 0
						# 다음 처리 단계에서는
						# 줄바꿈으로 간주
						c = '\n'
				else:
					self.column += 1
				self.timeoutSet(d)
				self.prevByte = c

	# 이 메서드의 대부분은 __init__으로 옮겨졌지만,
	# Arduino 코드에서 직접 포팅되는 오래된 코드와의
	# 호환성을 위해 여기 남겨둡니다.
	def begin(self, heatTime=defaultHeatTime):
		self.writeBytes(
		  27,       # Esc
		  55,       # 7 (print settings)
		  11,       # Heat dots
		  heatTime,
		  40)       # Heat interval

	def reset(self):
		self.writeBytes(27, 64) # Esc @ = 초기화 명령
		self.prevByte      = '\n' # 이전 줄이 빈 줄이었다고 가정
		self.column        =  0
		self.maxColumn     = 32
		self.charHeight    = 24
		self.lineSpacing   =  6
		self.barcodeHeight = 50
		if self.firmwareVersion >= 264:
			# 최신 프린터에서 탭 위치를 설정
			self.writeBytes(27, 68)         # 탭 위치 설정
			self.writeBytes( 4,  8, 12, 16) # 4칸마다,
			self.writeBytes(20, 24, 28,  0) # 0은 목록의 끝

	# 텍스트 서식 관련 매개변수를 초기화합니다.
	def setDefault(self):
		self.online()
		self.justify('L')
		self.inverseOff()
		self.doubleHeightOff()
		self.setLineHeight(30)
		self.boldOff()
		self.underlineOff()
		self.setBarcodeHeight(50)
		self.setSize('s')
		self.setCharset()
		self.setCodePage()

	def test(self):
		self.write("Hello world!".encode('cp437', 'ignore'))
		self.feed(2)

	def testPage(self):
		self.writeBytes(18, 84)
		self.timeoutSet(
		  self.dotPrintTime * 24 * 26 +
		  self.dotFeedTime * (6 * 26 + 30))

	def setBarcodeHeight(self, val=50):
		if val < 1: val = 1
		self.barcodeHeight = val
		self.writeBytes(29, 104, val)

	UPC_A   =  0
	UPC_E   =  1
	EAN13   =  2
	EAN8    =  3
	CODE39  =  4
	I25     =  5
	CODEBAR =  6
	CODE93  =  7
	CODE128 =  8
	CODE11  =  9
	MSI     = 10
	ITF     = 11
	CODABAR = 12

	def printBarcode(self, text, type):

		newDict = { # firmwareVersion >= 264용 UPC 코드와 값
			self.UPC_A   : 65,
			self.UPC_E   : 66,
			self.EAN13   : 67,
			self.EAN8    : 68,
			self.CODE39  : 69,
			self.ITF     : 70,
			self.CODABAR : 71,
			self.CODE93  : 72,
			self.CODE128 : 73,
			self.I25     : -1, # 새 펌웨어에서는 지원하지 않음
			self.CODEBAR : -1,
			self.CODE11  : -1,
			self.MSI     : -1
		}
		oldDict = { # firmwareVersion < 264용 UPC 코드와 값
			self.UPC_A   :  0,
			self.UPC_E   :  1,
			self.EAN13   :  2,
			self.EAN8    :  3,
			self.CODE39  :  4,
			self.I25     :  5,
			self.CODEBAR :  6,
			self.CODE93  :  7,
			self.CODE128 :  8,
			self.CODE11  :  9,
			self.MSI     : 10,
			self.ITF     : -1, # 구형 펌웨어에서는 지원하지 않음
			self.CODABAR : -1
		}

		if self.firmwareVersion >= 264:
			n = newDict[type]
		else:
			n = oldDict[type]
		if n == -1: return
		self.feed(1) # 최신 펌웨어는 이것이 필요할 수 있음
		self.writeBytes(
		  29,  72, 2, # 바코드 아래에 라벨 출력
		  29, 119, 3, # 바코드 너비
		  29, 107, n) # 바코드 종류
		self.timeoutWait()
		self.timeoutSet((self.barcodeHeight + 40) * self.dotPrintTime)
		# 문자열 출력
		if self.firmwareVersion >= 264:
			# 최신 펌웨어: 길이 바이트 + NUL 없는 문자열 기록
			n = len(text)
			if n > 255: n = 255
			if self.writeToStdout:
				sys.stdout.write((chr(n)).encode('cp437', 'ignore'))
				for i in range(n):
					sys.stdout.write(text[i].encode('utf-8', 'ignore'))
			else:
				super(Adafruit_Thermal, self).write((chr(n)).encode('utf-8', 'ignore'))
				for i in range(n):
					super(Adafruit_Thermal,
					  self).write(text[i].encode('utf-8', 'ignore'))
		else:
			# 구형 펌웨어: 문자열 + NUL 기록
			if self.writeToStdout:
				sys.stdout.write(text.encode('utf-8', 'ignore'))
			else:
				super(Adafruit_Thermal, self).write(text.encode('utf-8', 'ignore'))
		self.prevByte = '\n'

	# === 문자 관련 명령 ===

	INVERSE_MASK       = (1 << 1) # 2.6.8 펌웨어에는 없음(inverseOn() 참고)
	UPDOWN_MASK        = (1 << 2)
	BOLD_MASK          = (1 << 3)
	DOUBLE_HEIGHT_MASK = (1 << 4)
	DOUBLE_WIDTH_MASK  = (1 << 5)
	STRIKE_MASK        = (1 << 6)

	def setPrintMode(self, mask):
		self.printMode |= mask
		self.writePrintMode()
		if self.printMode & self.DOUBLE_HEIGHT_MASK:
			self.charHeight = 48
		else:
			self.charHeight = 24
		if self.printMode & self.DOUBLE_WIDTH_MASK:
			self.maxColumn  = 16
		else:
			self.maxColumn  = 32

	def unsetPrintMode(self, mask):
		self.printMode &= ~mask
		self.writePrintMode()
		if self.printMode & self.DOUBLE_HEIGHT_MASK:
			self.charHeight = 48
		else:
			self.charHeight = 24
		if self.printMode & self.DOUBLE_WIDTH_MASK:
			self.maxColumn  = 16
		else:
			self.maxColumn  = 32

	def writePrintMode(self):
		self.writeBytes(27, 33, self.printMode)

	def normal(self):
		self.printMode = 0
		self.writePrintMode()

	def inverseOn(self):
		if self.firmwareVersion >= 268:
			self.writeBytes(29, 66, 1)
		else:
			self.setPrintMode(self.INVERSE_MASK)

	def inverseOff(self):
		if self.firmwareVersion >= 268:
			self.writeBytes(29, 66, 0)
		else:
			self.unsetPrintMode(self.INVERSE_MASK)

	def upsideDownOn(self):
		self.setPrintMode(self.UPDOWN_MASK)

	def upsideDownOff(self):
		self.unsetPrintMode(self.UPDOWN_MASK)

	def doubleHeightOn(self):
		self.setPrintMode(self.DOUBLE_HEIGHT_MASK)

	def doubleHeightOff(self):
		self.unsetPrintMode(self.DOUBLE_HEIGHT_MASK)

	def doubleWidthOn(self):
		self.setPrintMode(self.DOUBLE_WIDTH_MASK)

	def doubleWidthOff(self):
		self.unsetPrintMode(self.DOUBLE_WIDTH_MASK)

	def strikeOn(self):
		self.setPrintMode(self.STRIKE_MASK)

	def strikeOff(self):
		self.unsetPrintMode(self.STRIKE_MASK)

	def boldOn(self):
		self.setPrintMode(self.BOLD_MASK)

	def boldOff(self):
		self.unsetPrintMode(self.BOLD_MASK)

	def justify(self, value):
		c = value.upper()
		if   c == 'C':
			pos = 1
		elif c == 'R':
			pos = 2
		else:
			pos = 0
		self.writeBytes(0x1B, 0x61, pos)

	# 지정한 줄 수만큼 급지합니다.
	def feed(self, x=1):
		if self.firmwareVersion >= 264:
			self.writeBytes(27, 100, x)
			self.timeoutSet(self.dotFeedTime * self.charHeight)
			self.prevByte = '\n'
			self.column   =    0

		else:
			# 데이터시트에는 27, 100, <x> 바이트 전송으로 동작한다고 되어 있지만
			# 실제로는 그보다 훨씬 많이 급지됩니다. 그래서 수동으로 처리합니다:
			while x > 0:
				self.write('\n'.encode('cp437', 'ignore'))
				x -= 1

	# 지정한 개수만큼 개별 픽셀 행을 급지합니다.
	def feedRows(self, rows):
		self.writeBytes(27, 74, rows)
		self.timeoutSet(rows * dotFeedTime)
		self.prevByte = '\n'
		self.column = 0

	def flush(self):
		self.writeBytes(12) # ASCII FF

	def setSize(self, value):
		c = value.upper()
		if c == 'L':   # Large: 가로/세로 2배
			size            = 0x11
			self.charHeight = 48
			self.maxColumn  = 16
		elif c == 'M': # Medium: 세로 2배
			size            = 0x01
			self.charHeight = 48
			self.maxColumn  = 32
		else:          # Small: 기본 가로/세로 크기
			size            = 0x00
			self.charHeight = 24
			self.maxColumn  = 32

		self.writeBytes(29, 33, size)
		prevByte = '\n' # 크기 설정 시 줄바꿈이 추가됨

	# 두께가 다른 밑줄을 만들 수 있습니다:
	# 0 - 밑줄 없음
	# 1 - 일반 밑줄
	# 2 - 두꺼운 밑줄
	def underlineOn(self, weight=1):
		if weight > 2: weight = 2
		self.writeBytes(27, 45, weight)

	def underlineOff(self):
		self.writeBytes(27, 45, 0)

	def printBitmap(self, w, h, bitmap, LaaT=False):
		rowBytes = math.floor((w + 7) / 8)  # 다음 바이트 경계까지 올림
		if rowBytes >= 48:
			rowBytesClipped = 48  # 최대 너비 384픽셀
		else:
			rowBytesClipped = rowBytes

		# LaaT(line-at-a-time)가 True면 비트맵을
		# 청크 단위가 아니라 스캔라인 단위로 출력합니다.
		# 큰 이미지에서는 급지 틈이 없어 더 깔끔하게 인쇄되는 경향이 있지만,
		# 하나의 청크에 들어갈 정도로 작은 이미지에는 반대 효과가 날 수 있으니
		# 주의해서 사용하세요.
		if LaaT: maxChunkHeight = 1
		else:    maxChunkHeight = 255

		i = 0
		for rowStart in range(0, h, maxChunkHeight):
			chunkHeight = h - rowStart
			if chunkHeight > maxChunkHeight:
				chunkHeight = maxChunkHeight

			# 여기서 타임아웃 대기가 발생합니다
			self.writeBytes(18, 42, chunkHeight, rowBytesClipped)

			for y in range(chunkHeight):
				for x in range(rowBytesClipped):
					if self.writeToStdout:
						sys.stdout.write(bytes([bitmap[i]]))
					else:
						super(Adafruit_Thermal,
						  self).write(bytes([bitmap[i]]))
					i += 1
				i += rowBytes - rowBytesClipped
			self.timeoutSet(chunkHeight * self.dotPrintTime)

		self.prevByte = '\n'

	# 이미지를 출력합니다. Python Imaging Library가 필요합니다.
	# 이 기능은 파이썬 포트 전용이며 Arduino 라이브러리에는 없습니다.
	# 필요하면 이미지를 최대 384픽셀 너비로 잘라내고,
	# 확산 디더링을 사용한 1비트 이미지로 변환합니다.
	# 다른 동작(크기 조절, 흑백 임계값 등)이 필요하면,
	# 이 함수에 전달하기 전에 Imaging Library에서 미리 처리하세요.
	def printImage(self, image_file, LaaT=False):
		from PIL import Image
		image = Image.open(image_file)
		if image.mode != '1':
			image = image.convert('1')

		width  = image.size[0]
		height = image.size[1]
		if width > 384:
			width = 384
		rowBytes = math.floor((width + 7) / 8)
		bitmap   = bytearray(rowBytes * height)
		pixels   = image.load()

		for y in range(height):
			n = y * rowBytes
			x = 0
			for b in range(rowBytes):
				sum = 0
				bit = 128
				while bit > 0:
					if x >= width: break
					if pixels[x, y] == 0:
						sum |= bit
					x    += 1
					bit >>= 1
				bitmap[n + b] = sum

		self.printBitmap(width, height, bitmap, LaaT)

	# 프린터를 오프라인 상태로 전환합니다.
	# 이후의 출력 명령은 'online'이 호출될 때까지 무시됩니다.
	def offline(self):
		self.writeBytes(27, 61, 0)

	# 프린터를 온라인 상태로 전환합니다. 이후 출력 명령이 처리됩니다.
	def online(self):
		self.writeBytes(27, 61, 1)

	# 프린터를 즉시 저전력 상태로 전환합니다.
	def sleep(self):
		self.sleepAfter(1) # 0은 "절전 안 함"을 의미하므로 사용할 수 없음

	# 지정한 초가 지난 뒤 프린터를 저전력 상태로 전환합니다.
	def sleepAfter(self, seconds):
		if self.firmwareVersion >= 264:
			self.writeBytes(27, 56, seconds & 0xFF, seconds >> 8)
		else:
			self.writeBytes(27, 56, seconds)

	def wake(self):
		self.timeoutSet(0)
		self.writeBytes(255)
		if self.firmwareVersion >= 264:
			time.sleep(0.05)            # 50밀리초
			self.writeBytes(27, 118, 0) # 절전 해제(중요!)
		else:
			for i in range(10):
				self.writeBytes(27)
				self.timeoutSet(0.1)

	# 빈 메서드이며, Arduino에서 포팅된 기존 코드와의
	# 호환성을 위해 포함되어 있습니다.
	def listen(self):
		pass

	# 프린터의 자체 보고 기능을 사용해 용지 상태를 확인합니다.
	# 다만 데이터시트와 완전히 일치하지는 않습니다.
	# 용지가 있으면 True, 없으면 False를 반환합니다.
	def hasPaper(self):
		if self.firmwareVersion >= 264:
			self.writeBytes(27, 118, 0)
		else:
			self.writeBytes(29, 114, 0)
		# 응답의 2번 비트가 용지 상태로 보입니다
		stat = ord(self.read(1)) & 0b00000100
		# 비트가 설정되어 있지 않으면 용지가 있는 것으로 판단
		return stat == 0

	def setLineHeight(self, val=32):
		if val < 24: val = 24
		self.lineSpacing = val - 24

		# 프린터는 줄 높이를 설정할 때 현재 텍스트 높이를 고려하지 않으므로,
		# 이것은 줄 높이보다는 줄 간격 설정에 가깝습니다.
		# 기본 줄 간격은 32이며
		# (문자 높이 24, 줄 간격 8)입니다.
		self.writeBytes(27, 51, val)

	CHARSET_USA          =  0
	CHARSET_FRANCE       =  1
	CHARSET_GERMANY      =  2
	CHARSET_UK           =  3
	CHARSET_DENMARK1     =  4
	CHARSET_SWEDEN       =  5
	CHARSET_ITALY        =  6
	CHARSET_SPAIN1       =  7
	CHARSET_JAPAN        =  8
	CHARSET_NORWAY       =  9
	CHARSET_DENMARK2     = 10
	CHARSET_SPAIN2       = 11
	CHARSET_LATINAMERICA = 12
	CHARSET_KOREA        = 13
	CHARSET_SLOVENIA     = 14
	CHARSET_CROATIA      = 14
	CHARSET_CHINA        = 15

	# ASCII 0x23-0x7E 범위의 일부 문자를 변경합니다. 데이터시트를 참고하세요.
	def setCharset(self, val=0):
		if val > 15: val = 15
		self.writeBytes(27, 82, val)

	CODEPAGE_CP437       =  0 # 미국, 표준 유럽
	CODEPAGE_KATAKANA    =  1
	CODEPAGE_CP850       =  2 # 다국어
	CODEPAGE_CP860       =  3 # 포르투갈어
	CODEPAGE_CP863       =  4 # 캐나다 프랑스어
	CODEPAGE_CP865       =  5 # 북유럽권
	CODEPAGE_WCP1251     =  6 # 키릴 문자
	CODEPAGE_CP866       =  7 # 키릴 문자 2
	CODEPAGE_MIK         =  8 # 키릴/불가리아어
	CODEPAGE_CP755       =  9 # 동유럽, 라트비아어 2
	CODEPAGE_IRAN        = 10
	CODEPAGE_CP862       = 15 # 히브리어
	CODEPAGE_WCP1252     = 16 # 라틴 1
	CODEPAGE_WCP1253     = 17 # 그리스어
	CODEPAGE_CP852       = 18 # 라틴 2
	CODEPAGE_CP858       = 19 # 다국어 라틴 1 + 유로
	CODEPAGE_IRAN2       = 20
	CODEPAGE_LATVIAN     = 21
	CODEPAGE_CP864       = 22 # 아랍어
	CODEPAGE_ISO_8859_1  = 23 # 서유럽
	CODEPAGE_CP737       = 24 # 그리스어
	CODEPAGE_WCP1257     = 25 # 발트어권
	CODEPAGE_THAI        = 26
	CODEPAGE_CP720       = 27 # 아랍어
	CODEPAGE_CP855       = 28
	CODEPAGE_CP857       = 29 # 터키어
	CODEPAGE_WCP1250     = 30 # 중부 유럽
	CODEPAGE_CP775       = 31
	CODEPAGE_WCP1254     = 32 # 터키어
	CODEPAGE_WCP1255     = 33 # 히브리어
	CODEPAGE_WCP1256     = 34 # 아랍어
	CODEPAGE_WCP1258     = 35 # 베트남어
	CODEPAGE_ISO_8859_2  = 36 # 라틴 2
	CODEPAGE_ISO_8859_3  = 37 # 라틴 3
	CODEPAGE_ISO_8859_4  = 38 # 발트어권
	CODEPAGE_ISO_8859_5  = 39 # 키릴 문자
	CODEPAGE_ISO_8859_6  = 40 # 아랍어
	CODEPAGE_ISO_8859_7  = 41 # 그리스어
	CODEPAGE_ISO_8859_8  = 42 # 히브리어
	CODEPAGE_ISO_8859_9  = 43 # 터키어
	CODEPAGE_ISO_8859_15 = 44 # 라틴 3
	CODEPAGE_THAI2       = 45
	CODEPAGE_CP856       = 46
	CODEPAGE_CP874       = 47

	# 상위 ASCII 값 0x80-0xFF에 대한 대체 기호를 선택합니다.
	def setCodePage(self, val=0):
		if val > 47: val = 47
		self.writeBytes(27, 116, val)

	# Arduino 라이브러리와의 동등성을 위해 가져온 코드이며,
	# 모든 프린터에서 동작하지 않을 수 있습니다
	def tab(self):
		self.writeBytes(9)
		self.column = (self.column + 4) & 0xFC

	# Arduino 라이브러리와의 동등성을 위해 가져온 코드이며,
	# 모든 프린터에서 동작하지 않을 수 있습니다
	def setCharSpacing(self, spacing):
		self.writeBytes(27, 32, spacing)

	# Python 3.0 이전 스타일의 print() 오버로딩은 다소 어색하지만,
	# Arduino 라이브러리용 기존 코드와 더 직접적인 호환성을 제공하기 위해 둡니다.
	def print(self, *args, **kwargs):
		for arg in args:
			self.write((str(arg)).encode('cp437', 'ignore'))

	# Arduino 코드와의 호환성을 위해 제공
	def println(self, *args, **kwargs):
		for arg in args:
			self.write((str(arg)).encode('cp437', 'ignore'))
		self.write('\n'.encode('cp437', 'ignore'))

