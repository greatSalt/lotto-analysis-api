import pandas as pd
import numpy as np

def get_crazy_analysis(df):
    if df.empty:
        return pd.DataFrame()

#------------------------------------------------------------------------------------------
    #df_sorted = df.sort_values(by='round', ascending=True
    df['round'] = pd.to_numeric(df['round'])    #mycode
    df_sorted = df.sort_values(by='round', ascending=True).reset_index(drop=True)   #mycode
    results = []
#------------------------------------------------------------------------------------------

    for num in range(1, 46):
#------------------------------------------------------------------------------------------        
        '''appearances_bool = []
        for row in df_sorted.itertuples():
            win_nums = [row.n1, row.n2, row.n3, row.n4, row.n5, row.n6]
            appearances_bool.append(num in win_nums)'''
        # 기존 루프 방식을 대체하는 최적화 코드
        # 1. n1~n6 컬럼에서 현재 번호(num)와 일치하는 값이 있는지 불리언 시리즈 생성
        # .eq(num)은 전체 요소와 num을 비교하고, .any(axis=1)은 행 방향으로 하나라도 True가 있는지 확인합니다.
        appearances_series = df_sorted[['n1', 'n2', 'n3', 'n4', 'n5', 'n6']].eq(num).any(axis=1)    #mycode: 
        appearances_bool = appearances_series.tolist()  #mycode: 분석에 사용할 리스트로 변환
#------------------------------------------------------------------------------------------
        
        # --- [A] 양적 지표 추출 ---
        '''count_in_range = sum(appearances_bool)   #True(1)와 False(0)로 이루어진 리스트에서 True의 개수만 합산하여 해당 번호의 총 출현 횟수를 구합니다. 
        total_range = len(appearances_bool) #분석 대상이 된 전체 회차 수를 구합니다.
        occurrence_rate = (count_in_range / total_range) * 100 if total_range > 0 else 0'''
        
        # 판다스 시리즈(appearances_series)를 사용할 경우
        count_in_range = appearances_series.sum()   #mycode: 출현 빈도:True(1)와 False(0)로 이루어진 리스트에서 True의 개수만 합산하여 해당 번호의 총 출현 횟수를 구합니다.
        occurrence_rate = appearances_series.mean() * 100   #mycode: 출현 확률:mean()을 취하면 자동으로 (합계 / 개수)가 계산되어 출현 확률이 나옵니다. 

        # 기대치보다 많이 나오는 번호인지 확인
        is_hot_number = occurrence_rate > 13.33 #my code:로또의 수학적 기대 출현율은 약 13.33\% (6 / 45 \times 100)
#------------------------------------------------------------------------------------------

        # --- [B] 스킵 및 연속 데이터 추출 ---
        skips, streaks = [], [] #얼마나 쉬었다 나왔나(skips)"**와 **"얼마나 연달아 나왔나(streaks)
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
#------------------------------------------------------------------------------------------

        # --- [C] 핵심 지표 계산 ---
        current_skip = temp_skip    #마지막 당첨 이후 현재까지 몇 회차를 쉬고 있는지 나타냅니다.  
        
        #avg_skip = sum(skips) / len(skips) if skips else 1.0    #이 번호가 가진 **'고유의 주기'**
        # 출현 기록(skips)이 있을 때만 평균을 구하고, 없으면 0으로 정의
        if skips:
            avg_skip = sum(skips) / len(skips)
        else:
            # 한 번도 안 나왔거나, 단 한 번만 나와서 '간격(skip)' 데이터가 형성되지 않은 경우
            avg_skip = 0.0
            
        last_skip = skips[-1] if skips else avg_skip    #직전 휴식 기간
        
        #max_streak = max(streaks) if streaks else 1    #최대연속출현횟수
        # streaks 리스트가 비어있을 때, 실제로 출현한 적이 있는지(count_in_range) 확인
        if streaks:
            max_streak = max(streaks)   #최대연속출현횟수
        else:
            # 한 번도 안 나왔으면 0, 한 번이라도 나왔지만 연타가 없었으면 1
            max_streak = 1 if count_in_range > 0 else 0

        curr_streak = 0 #현재 연속 출현 횟수
        for app in reversed(appearances_bool):
            if app: curr_streak += 1
            else: break
#------------------------------------------------------------------------------------------

        # --- [D] 지수 정의 ---
        rebound_index = current_skip / avg_skip if avg_skip > 0 else 0  #반등 지수: 이 번호가 평소 쉬는 시간(avg)보다 현재 얼마나 더 많이 쉬고 있는가를 나타냅니다. 이 수치가 1.2~1.5를 넘어간다면, 고무줄을 당길 대로 당긴 상태처럼 **강력한 반등(Rebound)**이 임박했음을 뜻합니다.
        energy_index = last_skip / avg_skip if avg_skip > 0 else 0  #에너지 지수: "직전에 터졌을 때 얼마나 에너지를 비축하고 터졌는가?"를 나타냅니다. 직전 휴식기(last_skip)가 평소보다 길었다면, 그 번호는 현재 **'잔여 에너지'**가 남아있을 확률이 높다고 보는 관점입니다. 이는 이월수나 연속 출현을 예측할 때 매우 중요한 보조 지표가 됩니다.
        is_critical = rebound_index >= 1.0  #임계점 도달 여부: "평균 이상으로 쉬었는가?"라는 단순하지만 강력한 **이진 판독(Boolean)**입니다. 이 값이 True가 되는 순간, 엔진은 해당 번호를 **'언제든 튀어나올 수 있는 활성 상태'**로 간주합니다.
#------------------------------------------------------------------------------------------

        # --- [E] 리듬 및 변동성 ---
        if len(skips) >= 3: #최소 3번의 휴식기 데이터가 있어야 '패턴'이라는 것을 논할 수 있다는 통계적 최소 기준입니다. 데이터가 부족할 때(else) rhythm_score를 50점(중간값)으로 주고 "데이터부족" 상태를 명시한 것은 매우 합리적인 폴백(Fallback) 전략입니다.
            rhythm_std = np.std(skips)  #표준편차: 스킵 주기가 얼마나 일정한지 측정합니다.
            rhythm_score = max(0, min(100, 100 - (rhythm_std * 10)))    #100 - (rhythm_std * 10) 식을 통해, 주기가 일정할수록(표준편차가 작을수록) 100점에 가까운 고득점을 줍니다. 즉, 예측 가능한 번호에 높은 점수를 부여하는 방식입니다.
            
            #sync_val = abs(current_skip - avg_skip) / (rhythm_std + 0.1)    
            if rhythm_std > 0:
                sync_val = abs(current_skip - avg_skip) / rhythm_std    #동기화 지수: 현재 쉬고 있는 기간(current_skip)이 평소 리듬(avg_skip)과 얼마나 일치하는지를 표준편차 단위로 측정합니다. #표준편차 계산에 현재스킵은 포함되지 않는다.
            else:
                # 표준편차가 0일 때: 현재스킵이 평균과 같으면 0(정박), 다르면 큰 값(엇박) 부여
                sync_val = 0 if current_skip == avg_skip else 9.9 

            rhythm_status = "정박자" if sync_val <= 0.5 else "엇박자"   #현재 상태가 평소 리듬의 오차 범위(0.5 시그마) 내에 있다면 "정박자", 아니면 **"엇박자"**로 규정합니다.
        else:
            rhythm_std, rhythm_score, rhythm_status = 0, 50, "데이터부족"
#------------------------------------------------------------------------------------------

        # --- [F] 탄성 점수(Bridge Score) 계산 (최근 10회 리듬) ---
        recent_10 = appearances_bool[-10:]
        indices = [i for i, val in enumerate(recent_10) if val]
        
        if len(indices) >= 2:
            # 최근 출현 간격(Gap)들의 평균 계산
            gaps = [indices[i] - indices[i-1] - 1 for i in range(1, len(indices))]
            avg_gap = sum(gaps) / len(gaps)
            # 1.0(매회 출현에 가까운 리듬)과의 차이를 점수화
            elasticity = max(0, 100 - (abs(1.0 - avg_gap) * 40))
            bridge_score = min(100, elasticity)
        else:
            # 데이터가 부족할 경우 출현 횟수에 비례하여 기본 점수 부여
            bridge_score = min(100, sum(recent_10) * 20)
#------------------------------------------------------------------------------------------

                # --- [G] 각 지표별 세부 점수 산출 ---
        
        # 1. 반등 점수 (30%): 현재 타이밍 (rebound_index 기반)
        # 1.0~1.5 구간에서 피크를 찍고, 그 이상(과냉각)일 경우 완만하게 하락
        rebound_part = min(100, rebound_index * 75) if rebound_index <= 1.5 else max(0, 100 - (rebound_index * 10))

#------------------------------------------------------------------------------------------        
        # 2. 기세 점수 (25%): 연속 폭발력 (streak_part)
        # 현재 연속 중이면 비율로 계산, 미출현 중이면 최대 연속 기록의 잠재력 반영
        #streak_part = min(100, (curr_streak / max_streak * 100) if curr_streak > 0 else (max_streak * 10))
#----------------------mycode--------------------------------------------------------------        
        # 2. 기세 점수 (25%): 엄격한 연속성 판정
        # 현재 연속 중(curr_streak > 0)일 때만 점수를 부여하며, 
        # 현재연속이 최대연속과 같아지면(임계점) 오히려 에너지가 고갈된 것으로 간주하거나 
        # 또는 현재연속이 0이면 기대치를 0으로 처리.
        
        if curr_streak > 0 and max_streak > 0:
            # 현재 연타 중일 때만 점수 산출
            if curr_streak >= max_streak:
                # 현재 기세가 역대 최고치에 도달했다면, 곧 꺾일 것으로 보고 0점 처리 (사용자 의도 반영)
                streak_part = 0
            else:
                # 아직 역대 기록에 미치지 못했다면 그 비율만큼 점수 부여
                streak_part = (curr_streak / max_streak) * 100
        else:
            # 현재 안 나오고 있거나(curr_streak=0), 역대 연타 기록이 1 이하(max_streak<=1)이면 0점
            streak_part = 0
        
        streak_part = min(100, streak_part)
#------------------------------------------------------------------------------------------
        
        # 3. 에너지 점수 (25%): 직전 응축도 (energy_index 기반)
        energy_part = min(100, energy_index * 70)
        
        # 4. 탄성 점수 (10%): 최근 10회 리듬 (bridge_score)
        # (앞서 선언된 bridge_score 변수 사용)
        bridge_final_part = bridge_score

        # 5. 리듬 점수 (10%): 전체 주기의 규칙성 (rhythm_score)
        # (앞서 선언된 rhythm_score 변수 사용)
        #rhythm_final_part = rhythm_score
        rhythm_final_part = min(100, (1 - sync_val)*100) + rhythm_score
        
        # --- [F] 최종 통합 점수 산출 (V2.2 가중치 모델) ---
        # 반등(30%) + 기세(50%) + 에너지(10%) + 탄성(5%) + 리듬(5%) = 100%
        total_score = (
            #(rebound_part * 0.30) + 
            #(streak_part * 0.50) + 
            #(energy_part * 0.10) + 
            #(bridge_final_part * 0.05) + 
            #(rhythm_final_part * 0.05)
            rhythm_final_part
        )
        
        # --- [G] 추가 보정 및 필터링 ---
        # 1. 출현율 보너스: 평균치(13.3%) 대비 체급 가산점
        #total_score += (occurrence_rate - 13.3) * 0.5   #로또의 수학적 기대치인 **13.3%**를 기준으로, 이보다 자주 나오는 '효자 번호'에는 가산점을, 덜 나오는 '비인기 번호'에는 감산점을 줍니다.

#----------------------mycode--------------------------------------------------------------
        # 2. 이월수(연속출현) 보정 로직
        # 현재 스킵이 0(방금 당첨)인 경우, 기세가 최대치에 못 미치면 패널티 적용
        '''if current_skip == 0:
            total_score *= 0.7 if curr_streak < max_streak else 0.4'''

        # --- [G-2] 이월수(Iteration) 전략 모듈 재설계 ---
#----------------------mycode--------------------------------------------------------------
        '''if current_skip == 0:
            # 1. 기세가 남아있는 경우 (현재연속 < 최대연속)
            if curr_streak < max_streak:
                # 패널티가 아니라, 기세 유지 점수를 부여 (1.0 ~ 1.2배)
                # 최대연속에 가까워질수록 신중하게 접근하기 위해 점진적 가중치 적용
                momentum_factor = 1.0 + (1.0 - (curr_streak / max_streak)) * 0.2
                total_score *= momentum_factor
                
            # 2. 기세가 임계점에 도달한 경우 (현재연속 == 최대연속)
            elif curr_streak == max_streak:
                # 자신의 역대 최고 기록과 타동률 -> 다음은 꺾일 확률 매우 높음
                total_score *= 0.5
                
            # 3. 기세를 초과한 경우 (현재연속 > 최대연속) - '미친 기세'
            else:
                # 역대 기록을 깼다면 통계적 범주를 벗어난 것이므로 강제 하락 처리
                total_score *= 0.3'''
#----------------------mycode--------------------------------------------------------------

        # 최종 점수 범위 제한 (0~200)
        total_score = max(0, min(200, total_score))
        
        # --- [G] 최종 결과 데이터 구성 (모든 컬럼 포함) ---
        results.append({
            "번호": num,
            "통합크레이지점수": round(total_score, 1),
            "동기화지수": round(sync_val, 2),
            "변동성": round(rhythm_std, 2),        # 표준편차(Sigma) - 리듬점수의 근거
            "박자상태": rhythm_status,
            "평균스킵": round(avg_skip, 1),
            "현재스킵": current_skip,
            "리듬점수": round(rhythm_score, 1),     # 규칙성
            "출현수": count_in_range,
            "출현율": round(occurrence_rate, 1),
            "출현기대치": "hot" if is_hot_number else "cold", 
            "현재연속": curr_streak,
            "최대연속": max_streak,
            "연속점수": round(streak_part, 1),
            "탄성점수": round(bridge_score, 1),
            "반등지수": round(rebound_index, 2),
            "에너지지수": round(energy_index, 2),
            "직전스킵": last_skip,
            "임계점": "🔥반등임박" if is_critical else "⏳에너지충전" 
        })

    return pd.DataFrame(results)
