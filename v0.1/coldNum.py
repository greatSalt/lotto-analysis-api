import pandas as pd

def get_cold_analysis(df):
    if df.empty:
        return pd.DataFrame()

    # 과거순 정렬
    df_sorted = df.sort_values(by='round', ascending=True)
    latest_round = int(df_sorted['round'].max())
    results = []

    for num in range(1, 46):
        # 해당 번호가 나온 회차들 추출
        appearances = []
        for row in df_sorted.itertuples():
            win_nums = [row.n1, row.n2, row.n3, row.n4, row.n5, row.n6]
            if num in win_nums:
                appearances.append(int(row.round))
        
        # 1. 현재 미출현 기간 계산
        if appearances:
            last_round = appearances[-1]
            current_gap = latest_round - last_round
        else:
            # 한 번도 안 나왔다면 전체 데이터 개수를 미출현 기간으로 간주
            current_gap = len(df_sorted)
        
        # 2. 역대 미출현 기간(Gaps) 분석
        gaps = []
        if appearances:
            # 데이터 시작점부터 첫 당첨까지의 간격
            gaps.append(appearances[0] - int(df_sorted['round'].min()))
            # 당첨 사이의 간격들
            for i in range(1, len(appearances)):
                gaps.append(appearances[i] - appearances[i-1] - 1)
        
        # 현재 안 나오고 있는 기간도 하나의 gap 기록으로 포함
        max_gap_record = max(max(gaps) if gaps else 0, current_gap)
        
        # 3. 콜드 지수 (임계점 접근도)
        # 과거 최대 기록 대비 현재 얼마나 도달했는가
        if max_gap_record > 0:
            cold_index = (current_gap / max_gap_record * 100)
        else:
            cold_index = 0.0
            
        results.append({
            "번호": num,
            "현재미출현": current_gap,
            "역대최대미출현": max_gap_record,
            "콜드지수": round(min(cold_index, 100.0), 1)
        })

    return pd.DataFrame(results)
