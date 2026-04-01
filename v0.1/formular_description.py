import streamlit as st

def display_formula_guide(analyze_count=100):
    """
    Streamlit 화면에 크레이지 분석 엔진 v2.2의 공식 및 수치 해석 섹션을 출력합니다.
    """
    st.divider()
    st.subheader("📝 크레이지 분석 리포트 공식 가이드 (v2.2)")
    
    # --- [상단] 주요 지표 (양적 분석 & 에너지) ---
    col_top1, col_top2 = st.columns(2)
    
    with col_top1:
        st.info("#### 📊 최근 출현 지표 (Quantity)")
        st.latex(r"Rate = \frac{Count_{range}}{Range} \times 100")
        st.markdown(f"""
        * **출현수:** 최근 **{analyze_count}회** 중 해당 번호가 당첨된 횟수
        * **출현율:** 분석 범위 내 실제 등장 확률 (%)
        * **해석:** 최근 흐름에서 번호가 얼마나 활발히 움직이는지 체급을 측정합니다.
        """)

    with col_top2:
        st.warning("#### ⚡ 반등 임계점 (Rebound Index)")
        st.latex(r"Rebound = \frac{Skip_{curr} (현재스킵)}{Skip_{avg} (평균주기)}")
        st.markdown("""
        * **1.0 미만:** 에너지 축적 단계 (기다림 필요)
        * **1.0 ~ 1.5:** **반등 임박!** 통계적 출현 시점에 도달한 최적 구간 🔥
        * **1.5 이상:** 과냉각 상태. 장기 미출수로 전환될 가능성 주의
        """)

    # --- [중단] 에너지 및 기세 지수 ---
    col_mid1, col_mid2 = st.columns(2)
    
    with col_mid1:
        st.success("#### 🔋 에너지 지수 (Energy Index)")
        st.latex(r"Energy = \frac{Skip_{last} (직전스킵)}{Skip_{avg} (평균주기)}")
        st.markdown("""
        * **해석:** 지난번 당첨 시 얼마나 응축되었다 터졌는지 측정합니다.
        * 에너지가 높았던 번호는 이번 회차에도 강한 반동을 일으킬 잠재력이 높습니다.
        """)

    with col_mid2:
        st.info("#### 🏃‍♂️ 연속 지수 (Streak Score)")
        st.latex(r"S_{streak} = \frac{(Max - Curr)}{Max} \times 100")
        st.markdown("""
        * **해석:** 역대 최대 연속 기록(Max) 대비 현재의 폭발력을 수치화합니다.
        * 한번 터진 번호가 몰아치는 힘을 반영합니다.
        """)

    st.divider()

    # --- [하단] 최종 통합 점수 공식 (가중치 수정본) ---
    st.success("#### 🏆 [v2.2] 최종 통합 크레이지 점수 (Total Score)")
    
    # 통합 점수 공식 (LaTeX) - 수정된 가중치 반영
    st.latex(r"Total = (S_{rebound} \times 0.3) + (S_{streak} \times 0.25) + (S_{energy} \times 0.25) + (S_{rhythm} \times 0.2) + Bonus_{rate}")
    
    col_info1, col_info2 = st.columns(2)
    
    with col_info1:
        st.markdown("""
        **📊 핵심 4대 가중치 (Main Weights)**
        1. **반등(30%):** 현재 미출현 기간의 통계적 적정성
        2. **기세(25%):** 연속 출현 및 최대 폭발력 기록 반영
        3. **에너지(25%):** 직전 응축 에너지가 주는 반동 효과
        4. **리듬(20%):** 주기 데이터의 표준편차($\sigma$) 기반 규칙성
        """)
        
    with col_info2:
        st.markdown("""
        **⚖️ 특수 조정 로직 (Adjustments)**
        * **출현율 보너스:** 평균 출현율(13.3%) 대비 성적에 따른 $\pm$ 조정
        * **이월수 필터:** 방금 나온 번호(스킵 0)는 **기세에 따라 40~70% 감점**
        * **박자 싱크:** 현재 스킵이 평균 주기에 근접하면 **'정박자'** 판정
        """)

    # --- [상세] 리듬 및 박자 설명 ---
    with st.expander("🥁 리듬(Rhythm) 및 박자 해석 상세보기"):
        c1, c2, c3 = st.columns(3)
        with c1:
            st.warning("#### 🥁 정박자 (On-Beat)")
            st.latex(r"Sync \le 0.5")
            st.write("자신의 선호 주기에 정확히 도달한 상태.")
        with c2:
            st.info("#### 🌀 리듬 점수")
            st.latex(r"100 - (\sigma \times 10)")
            st.write("높을수록 규칙적인 '모범생' 번호.")
        with c3:
            st.error("#### 🔥 반등 지수")
            st.latex(r"Rebound \ge 1.0")
            st.write("평균적으로 쉴 만큼 쉬었음을 의미.")
            
    st.divider()

    # 하단: 색상별 전략 가이드
    st.subheader("💡 데이터 기반 전략 가이드")
    c1, c2, c3 = st.columns(3)

    with c1:
        st.warning("#### 🟡 노란색 (주기 회귀)")
        st.latex(r"|Skip_{last} - Skip_{avg}| \le 1")
        st.markdown("**평균 주기 도달:** 번호가 자신의 원래 리듬을 찾고 반등을 준비하는 타이밍")
            
    with c2:
        st.error("#### 🔴 빨간색 (에너지 과포화)")
        st.latex(r"Skip_{last} > Skip_{avg}")
        st.markdown("**평균 초과 미출현:** 평소보다 오래 침묵하여 에너지가 과응축된 고확률 상태")
            
    with c3:
        st.info("#### 🔵 파란색 (흐름 일시중지)")
        st.latex(r"Streak_{curr} = 0")
        st.markdown("**미출현 상태:** 최근 연속 당첨 흐름이 끊겨 다시 에너지를 모으는 중")

    # 하단 분석 팁
    st.info(f"💡 **분석 팁:** **17번**처럼 '출현율'은 낮아도 '에너지 지수'가 **1.0** 이상이면서***최종 점수**가 높다면, 통계적 확률이 극대화된 **A급 후보**로 분류합니다.")
            
    st.divider()
    with st.expander("🥁 리듬(Rhythm) 분석이란?"):
        st.write("""
            번호마다 고유한 출현 주기가 있습니다. **리듬 점수**는 이 주기가 얼마나 일정한지를 측정합니다.
            * **정박자:** 현재 미출현 기간이 자신의 평균 주기와 표준편차 범위 내에 들어온 상태입니다. (당첨 확률 급증)
            * **엇박자:** 평소 리듬보다 너무 빠르거나 늦게 나타나고 있는 상태입니다.
            * **리듬 점수 80점 이상:** 기계처럼 정확한 주기로 나오는 '효자 번호'입니다.""")
            
        st.latex(r"Rhythm\ Score = 100 - (StdDev(Skips) \times 10)")

        st.divider()

        # --- 리듬 및 박자 상세 설명 ---
        st.subheader("🥁 리듬(Rhythm) 및 박자 해석")
        c1, c2, c3 = st.columns(3)

        with c1:
            st.warning("#### 🥁 정박자 (On-Beat)")
            st.latex(r"Sync \le 0.5")
            st.markdown("자신이 선호하는 출현 주기에 정확히 도달한 상태. **당첨 임박 신호**")
            
        with c2:
            st.info("#### 🌀 리듬 점수 (Rhythm)")
            st.latex(r"100 - (\sigma \times 10)")
            st.markdown("점수가 높을수록(80+) 주기가 일정한 '모범생' 번호, 낮을수록 '폭주형'")
            
        with c3:
            st.error("#### 🔥 에너지 임계점")
            st.latex(r"Energy \ge 1.0")
            st.markdown("평균적으로 쉴 만큼 쉬었음을 의미. 에너지가 꽉 찬 상태")
            
    st.caption(f"※ 모든 분석은 실시간 업데이트되는 {analyze_count}회 데이터를 기반으로 계산됩니다.")
    st.divider()
