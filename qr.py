import qrcode

def generate_qr(url, filename="qrcode.png"):
    # QR 코드 객체 생성
    qr = qrcode.QRCode(
        version=1,  # QR 코드 크기 (1~40)
        error_correction=qrcode.constants.ERROR_CORRECT_L,  # 오류 수정 수준
        box_size=10,  # 각 박스(픽셀) 크기
        border=4,  # 테두리 크기
    )
    
    # 데이터 추가
    qr.add_data(url)
    qr.make(fit=True)

    # 이미지 생성
    img = qr.make_image(fill_color="black", back_color="white")
    
    # 이미지 저장
    img.save(filename)
    print(f"QR 코드가 {filename} 으로 저장되었습니다.")

# 사용 예
url = input("URL을 입력하세요: ")
generate_qr(url)
