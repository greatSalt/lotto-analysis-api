import pandas as pd

def get_cold_analysis(df):
    if df.empty:
        return pd.DataFrame()

    # 과거순 정렬
    df_sorted = df.sort_values(by='round', ascending=True)
    latest_round = df_sorted['round'].max()
    results = []

    for num in range(1, 46):
        # 해당 번호가 나온 회차들
        appearances = []
        for row in df_sorted.itertuples():
            if num in [row.n1, row.n2, row.n3, row.n4, row.n5, row.n6]:
                appearances.append(row.round)
        
        # 1. 현재 미출현 기간 (현재 기준 얼마나 안 나왔나)
        last_round = appearances[-1] if appearances else df_sorted['round'].min() - 1
        current_gap = latest_round - last_appearance if appearances else len(df_sorted)
        
        # 2. 역대 미출현 기간 기록 (간격 분석)
        gaps = []
        if appearances:
            # 첫 회차부터 첫 당첨까지의 간격
            gaps.append(appearances[0] - df_sorted['round'].min())
            # 당첨 사이의 간격
            for i in range(1, len(appearances)):
                gaps.append(appearances[i] - appearances[i-1] - 1)
        
        max_gap_record = max(gaps) if gaps else current_gap
        
        # 3. 콜드 지수 (임계점 접근도)
        # 역대 최대 미출현 기간 대비 현재 얼마나 안 나왔는가
        cold_index = (current_gap / max_gap_record * 100) if max_gap_record > 0 else 0
        
        results.append({
            "번호": num,
            "현재미출현": current_gap,
            "역대최대미출현": max_gap_record,
            "콜드지수": round(min(cold_index, 100.0), 1) # 100% 상한선
        })

    return pd.DataFrame(results)
