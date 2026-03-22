import pandas as pd
import numpy as np

def get_crazy_analysis(df):
    if df.empty:
        return pd.DataFrame()

    # 회차 기준 오름차순 정렬
    df_sorted = df.sort_values(by='round', ascending=True)
    results = []

    for num in range(1, 46):
        appearances_bool = []
        for row in df_sorted.itertuples():
            win_nums = [row.n1, row.n2, row.n3, row.n4, row.n5, row.n6]
            appearances_bool.append(num in win_nums)
        
        # --- [A] 분석 범위 내 양적 지표 ---
        count_in_range = sum(appearances_bool) 
        total_range = len(appearances_bool)
        occurrence_rate = (count_in_range / total_range) * 100 if total_range > 0 else 0

        # --- [B] 스킵(미출현) 및 연속 데이터 추출 ---
        skips = []
        streaks = []
        temp_skip = 0
        temp_streak = 0
        
        for app in appearances_bool:
            if app:
                if temp_skip > 0: skips.append(temp_skip)
                temp_skip = 0
                temp_streak += 1
            else:
                if temp_streak > 0: streaks.append(temp_streak)
                temp_streak = 0
                temp_skip += 1
        
        if temp_streak > 0: streaks.append(temp_streak)
        
        # --- [C] 주기 및 에너지 지표 계산 ---
        current_skip = temp_skip  
        avg_skip = sum(skips) / len(skips) if skips else 1.0
        last_skip = skips[-1] if skips else 0
        max_streak = max(streaks) if streaks else 1
        
        curr_streak = 0
        for app in reversed(appearances_bool):
            if app: curr_streak += 1
            else: break

        energy_index = current_skip / avg_skip if avg_skip > 0 else 0
        is_critical = energy_index >= 1.0

        # --- [D] 리듬(Rhythm) 분석 로직 추가 ---
        if len(skips) >= 3:
            # 1. 리듬 변동성 (표준편차)
            rhythm_std = np.std(skips)
            # 2. 리듬 점수 (변동성이 작을수록 고점)
            rhythm_score = max(0, min(100, 100 - (rhythm_std * 10)))
            # 3. 박자 싱크로율 (현재 박자가 평균에 도달했는지)
            sync_val = abs(current_skip - avg_skip) / (rhythm_std + 0.1)
            rhythm_status = "정박자" if sync_val <= 0.5 else "엇박자"
            if current_skip == 0: rhythm_status = "연주중"
        else:
            rhythm_std = 0
            rhythm_score = 50
            rhythm_status = "부족"

        # --- [E] 최종 통합 점수 산출 (가중치 조정) ---
        # 1. 기세 점수 (30%)
        streak_score = max(0, min(100, ((max_streak - curr_streak) / max_streak) * 100))
        
        # 2. 탄성 점수 (20%): 최근 10회 리듬
        recent_10 = appearances_bool[-10:]
        indices = [i for i, val in enumerate(recent_10) if val]
        if len(indices) >= 2:
            gaps = [indices[i] - indices[i-1] - 1 for i in range(1, len(indices))]
            avg_gap = sum(gaps) / len(gaps)
            elasticity = max(0, 100 - (abs(1.0 - avg_gap) * 40))
            bridge_score = min(100, elasticity)
        else:
            bridge_score = min(100, sum(recent_10) * 20)

        # 3. 에너지 점수 (30%): 에너지 지수 반영
        energy_score = min(100, energy_index * 70) 

        # 4. 리듬 점수 반영 (20%): 규칙성 가점
        final_rhythm_part = rhythm_score * 0.2

        # 5. 출현율 보너스 (Bonus)
        rate_bonus = (occurrence_rate - 13.3) * 0.5

        # 통합 점수 계산
        total_score = (streak_score * 0.3) + (bridge_score * 0.2) + (energy_score * 0.3) + final_rhythm_part + rate_bonus
        
        # 방금 나온 번호는 순위 방어 (감점 로직)
        if current_skip == 0:
            total_score *= 0.5

        total_score = max(0, min(100, total_score))

        # --- [F] 결과 수집 ---
        results.append({
            "번호": num,
            "출현수": count_in_range,
            "출현율": round(occurrence_rate, 1),
            "현재연속": curr_streak,
            "최대연속": max_streak,
            "연속점수": round(streak_score, 1),
            "징검다리점수": round(bridge_score, 1),
            "평균스킵": round(avg_skip, 1),
            "직전스킵": last_skip,
            "현재스킵": current_skip,
            "에너지지수": round(energy_index, 2),
            "리듬점수": round(rhythm_score, 1),
            "변동성": round(rhythm_std, 2),
            "박자상태": rhythm_status,
            "임계점": "🔥도달" if is_critical else "⏳충전",
            "통합크레이지점수": round(total_score, 1)
        })

    return pd.DataFrame(results)
