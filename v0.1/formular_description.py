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
        st.info("#### 🏃‍♂️ 기세 지수 (Streak Score)")
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
            
    st.caption(f"※ 모든 분석은 실시간 업데이트되는 {analyze_count}회 데이터를 기반으로 계산됩니다.")
    st.divider()
