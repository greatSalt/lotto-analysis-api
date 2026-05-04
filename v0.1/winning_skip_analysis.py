import pandas as pd
import plotly.express as px

#당첨번호 주기(Skip) 분석 및 시각화 로직
def analyze_winning_skip_distribution(history_df, target_rounds=10):
    """
    history_df: 전체 당첨 번호 데이터 (회차, 번호1~6 포함)
    target_rounds: 분석할 최근 회차 범위 (사용자 입력값)
    """
    skip_data = []
    
    # 최근 n회차의 당첨 번호들만 순회
    recent_rounds = history_df.head(target_rounds)
    
    for idx, row in recent_rounds.iterrows():
        round_num = row['round']
        winning_nums = [row['n1'], row['n2'], row['n3'], row['n4'], row['n5'], row['n6']]
        
        for num in winning_nums:
            # 해당 번호가 이 회차(idx) 이전에는 언제 나왔는지 찾기
            prev_appearances = history_df.iloc[idx+1:]
            last_idx = prev_appearances[(prev_appearances['n1'] == num) | 
                                        (prev_appearances['n2'] == num) | 
                                        (prev_appearances['n3'] == num) | 
                                        (prev_appearances['n4'] == num) | 
                                        (prev_appearances['n5'] == num) | 
                                        (prev_appearances['n6'] == num)].index
            
            if not last_idx.empty:
                skip_val = last_idx[0] - idx - 1 # 주기 계산
            else:
                skip_val = target_rounds+10 # 아주 오래된 미출현수
                
            skip_data.append({"회차": round_num, "번호": num, "주기": skip_val})
            
    analysis_results = pd.DataFrame(skip_data)
    
    # 주기별 출현 빈도 계산 (0, 1, 2, 3...)
    skip_counts = analysis_results['주기'].value_counts().sort_index().reset_index()
    skip_counts.columns = ['주기', '출현빈도']
    
    # 확률(가중치) 계산: 해당 주기의 빈도 / 전체 번호 수
    total_nums = len(analysis_results)
    skip_counts['확률'] = (skip_counts['출현빈도'] / total_nums).round(4)
    
    return analysis_results, skip_counts