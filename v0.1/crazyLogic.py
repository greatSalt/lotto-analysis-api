import pandas as pd
import numpy as np

def get_crazy_analysis(df):
    if df.empty:
        return pd.DataFrame()

    df_sorted = df.sort_values(by='round', ascending=True)
    results = []

    for num in range(1, 46):
        appearances_bool = []
        for row in df_sorted.itertuples():
            win_nums = [row.n1, row.n2, row.n3, row.n4, row.n5, row.n6]
            appearances_bool.append(num in win_nums)
        
        # --- [A] 양적 지표 추출 (복구) ---
        count_in_range = sum(appearances_bool) 
        total_range = len(appearances_bool)
        occurrence_rate = (count_in_range / total_range) * 100 if total_range > 0 else 0

        # --- [B] 스킵 및 연속 데이터 추출 ---
        skips, streaks = [], []
        temp_skip, temp_streak = 0, 0
        
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

        # --- [C] 핵심 지표 계산 ---
        current_skip = temp_skip  
        avg_skip = sum(skips) / len(skips) if skips else 1.0
        last_skip = skips[-1] if skips else avg_skip
        max_streak = max(streaks) if streaks else 1
        
        curr_streak = 0
        for app in reversed(appearances_bool):
            if app: curr_streak += 1
            else: break

        # --- [D] 지수 정의 ---
        rebound_index = current_skip / avg_skip if avg_skip > 0 else 0
        energy_index = last_skip / avg_skip if avg_skip > 0 else 0
        is_critical = rebound_index >= 1.0

        # --- [E] 리듬 및 변동성 ---
        if len(skips) >= 3:
            rhythm_std = np.std(skips)
            rhythm_score = max(0, min(100, 100 - (rhythm_std * 10)))
            sync_val = abs(current_skip - avg_skip) / (rhythm_std + 0.1)
            rhythm_status = "정박자" if sync_val <= 0.5 else "엇박자"
        else:
            rhythm_std, rhythm_score, rhythm_status = 0, 50, "데이터부족"

        # --- [F] 가중치 기반 통합 점수 설계 ---
        # 1. 반등 점수 (30%): 현재 타이밍
        rebound_part = min(100, rebound_index * 75) if rebound_index <= 1.5 else max(0, 100 - (rebound_index * 10))
        # 2. 기세 점수 (25%): 연속 폭발력
        streak_part = min(100, (curr_streak / max_streak * 100) if curr_streak > 0 else (max_streak * 10))
        # 3. 에너지 점수 (25%): 직전 응축도
        energy_part = min(100, energy_index * 70)
        # 4. 리듬 점수 (20%): 규칙성
        rhythm_part = rhythm_score

        # 통합 점수 산출
        total_score = (rebound_part * 0.3) + (streak_part * 0.25) + (energy_part * 0.25) + (rhythm_part * 0.2)
        
        # 보너스: 출현율 가산점 (기본 체급 반영)
        total_score += (occurrence_rate - 13.3) * 0.5

        # 이월수 보정
        if current_skip == 0:
            total_score *= 0.7 if curr_streak < max_streak else 0.4

        total_score = max(0, min(100, total_score))

        # --- [G] 최종 결과 데이터 구성 (모든 컬럼 포함) ---
        results.append({
            "번호": num,
            "출현수": count_in_range,
            "출현율": round(occurrence_rate, 1),
            "현재연속": curr_streak,
            "최대연속": max_streak,
            "연속점수": round(streak_part, 1),
            "탄성점수": round(bridge_score, 1),
            "반등지수": round(rebound_index, 2),
            "에너지지수": round(energy_index, 2),
            "평균스킵": round(avg_skip, 1),
            "직전스킵": last_skip,
            "현재스킵": current_skip,
            "변동성": round(rhythm_std, 2),        # 표준편차(Sigma) - 리듬점수의 근거
            "리듬점수": round(rhythm_score, 1),     # 규칙성
            "박자상태": rhythm_status,
            "임계점": "🔥반등임박" if is_critical else "⏳에너지충전",
            "통합크레이지점수": round(total_score, 1)
        })

    return pd.DataFrame(results)
