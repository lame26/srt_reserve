"""
SRT 간편예매 자동화 스크립트

[사전 준비]
1. Android Studio AVD 실행 (emulator-5554)
2. SRT 앱에서 간편예매 화면 열기
   - 출발: 동탄 / 도착: 울산(통도사)
   - 출발일시: 2026년 2월 22일(일) 13시 이후
   - 좌석옵션: 일반/기본  /  객실등급: 일반실
3. 그 상태로 이 스크립트 실행

[실행]
  C:\\Python314\\python.exe D:\\srt\\srt_quick_reserve.py
"""

import os
import sys
import time
from urllib import error, parse, request

try:
    import uiautomator2 as u2
except ImportError:
    print("pip install uiautomator2")
    sys.exit(1)


DEVICE_ADDR = "emulator-5554"
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")


def send_telegram(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = parse.urlencode({"chat_id": TELEGRAM_CHAT_ID, "text": message}).encode("utf-8")

    try:
        req = request.Request(url, data=payload, method="POST")
        req.add_header("Content-Type", "application/x-www-form-urlencoded")
        with request.urlopen(req, timeout=5):
            pass
    except (error.URLError, TimeoutError) as e:
        print(f"텔레그램 전송 실패({e})")


def is_waiting_queue_screen(d):
    return (
        d(text="접속대기 중입니다.").exists(timeout=1)
        or d(textContains="나의 대기순서").exists(timeout=1)
        or d(textContains="잠시만 기다리시면").exists(timeout=1)
    )


def main():
    print("디바이스 연결 중...")
    d = u2.connect(DEVICE_ADDR)
    print(f"연결 완료: {d.info.get('productName', DEVICE_ADDR)}")
    print()
    print("간편예매 화면이 열려 있는지 확인하세요.")
    print("(출발: 동탄 / 도착: 울산 / 2026.02.22 13시이후 / 일반실)")
    input("준비되면 Enter...")
    print()

    send_telegram("[SRT] 예약 시도 시작")

    attempt = 0
    while True:
        attempt += 1
        print(f"[{attempt}회] 열차 예약하기 클릭...", end=" ", flush=True)

        try:
            if is_waiting_queue_screen(d):
                print("접속대기 화면 감지. 잠시 후 재시도...")
                time.sleep(3)
                continue

            # 열차 예약하기 버튼 클릭 (content-desc 기준)
            btn = d(description="열차 예약하기")
            if not btn.exists(timeout=5):
                if is_waiting_queue_screen(d):
                    print("접속대기 화면 감지. 잠시 후 재시도...")
                else:
                    print("버튼 미발견. 간편예매 화면인지 확인하세요.")
                time.sleep(3)
                continue

            btn.click()
            time.sleep(1)  # 팝업 뜨는 시간 대기

            # 잔여석없음 팝업이면 확인 누르고 즉시 재시도
            if d(text="잔여석없음").exists(timeout=4):
                print("잔여석없음.")
                d(text="확인").click()

            # 간편예매 화면 그대로면 → 뭔가 다른 상황 (재시도)
            elif d(description="열차 예약하기").exists(timeout=2):
                print("화면 유지 중, 재시도...")

            else:
                # 화면이 바뀌었다 → 예매 성공!
                print()
                print("=" * 40)
                print("🎉 예매 성공 가능성!")
                print("에뮬레이터를 확인하고 빠르게 결제하세요!")
                print("=" * 40)
                send_telegram("[SRT] 예약 성공 가능성 감지! 앱에서 결제를 진행하세요.")
                input("완료 후 Enter를 눌러 종료...")
                break

        except Exception as e:
            if is_waiting_queue_screen(d):
                print("접속대기 화면에서 대기 중...")
                time.sleep(3)
                continue

            print(f"오류({e})")


if __name__ == "__main__":
    main()
