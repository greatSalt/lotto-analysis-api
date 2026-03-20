import gspread
import csv
import os
from oauth2client.service_account import ServiceAccountCredentials

def sync_data():
    # 1. 경로 및 설정
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    # 경로가 './key/...'인지 다시 한번 확인하세요!
    creds_file = './key/lotto-project-489404-a267ebd6b49d.json' 
    
    if not os.path.exists(creds_file):
        print(f"❌ 파일 없음: {creds_file}")
        return

    try:
        # 2. 인증 및 연결
        creds = ServiceAccountCredentials.from_json_keyfile_name(creds_file, scope)
        client = gspread.authorize(creds)

        # 3. 시트 열기 및 데이터 읽기
        # 시트 이름 '로또당첨데이터'가 구글 시트 제목과 정확히 일치해야 합니다!
        spreadsheet = client.open("Lotto_db")
        sheet = spreadsheet.get_worksheet(0) # 첫 번째 탭 강제 지정
        
        data = sheet.get_all_values() 

        # 4. CSV 저장
        if data:
            with open('lotto_data.csv', 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerows(data)
            print("✅ [성공] 구글 시트 동기화 완료!")
            print(f"📊 총 {len(data)}줄의 데이터를 가져왔습니다.")
        else:
            print("❓ 시트에 데이터가 없습니다.")

    except gspread.exceptions.SpreadsheetNotFound:
        print("❌ 에러: '로또당첨데이터'라는 이름의 시트를 찾을 수 없습니다.")
    except Exception as e:
        # Response [200]이 찍히는 범인을 잡기 위한 상세 출력
        print(f"❌ 상세 에러 발생: {type(e).__name__} - {e}")

if __name__ == "__main__":
    sync_data()
