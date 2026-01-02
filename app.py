import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os
from io import BytesIO

# ---------------------------------------------------------
# 1. 기본 설정 (페이지 및 폰트)
# ---------------------------------------------------------
st.set_page_config(page_title="우리 아이 주간 시간표", layout="wide")

@st.cache_resource
def install_font_and_configure():
    # 폰트 깨짐 방지를 위한 나눔고딕 설치
    font_file = "NanumGothic.ttf"
    if not os.path.exists(font_file):
        import urllib.request
        url = "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Regular.ttf"
        urllib.request.urlretrieve(url, font_file)
    fm.fontManager.addfont(font_file)
    plt.rc('font', family='NanumGothic')
    plt.rcParams['axes.unicode_minus'] = False 

install_font_and_configure()

# ---------------------------------------------------------
# 2. 핵심 로직: 데이터를 일주일치로 뻥튀기 해주는 함수
# ---------------------------------------------------------
def process_weekly_data(schedule_list):
    """
    사용자가 입력한 '반복 규칙'을 풀어서 '그릴 수 있는 데이터'로 변환합니다.
    예: "월,수 14:00" -> 월요일 데이터 1개, 수요일 데이터 1개 생성
    """
    expanded_data = []
    
    # 요일 순서 정의 (그래프 Y축 배치용)
    day_order = {'월': 0, '화': 1, '수': 2, '목': 3, '금': 4, '토': 5, '일': 6}
    
    for item in schedule_list:
        # "월,수,금" 처럼 콤마로 된 요일을 분리
        days = item['days'].split(',')
        
        for day in days:
            day = day.strip() # 공백 제거
            if day in day_order:
                # 시간 변환 (09:30 -> 9.5)
                start_h, start_m = map(int, item['start'].split(':'))
                end_h, end_m = map(int, item['end'].split(':'))
                
                start_float = start_h + (start_m / 60)
                end_float = end_h + (end_m / 60)
                
                expanded_data.append({
                    '요일': day,
                    '요일인덱스': day_order[day], # Y축 위치
                    '활동명': item['title'],
                    '시작': start_float,
                    '소요시간': end_float - start_float,
                    '색상': item['color'],
                    '시간텍스트': f"{item['start']}~{item['end']}"
                })
    
    return pd.DataFrame(expanded_data)

def draw_weekly_timetable(child_name, df):
    # 캔버스 생성
    fig, ax = plt.subplots(figsize=(12, 7))
    
    # Y축을 요일로 설정 (월요일이 위로 가도록 invert)
    days_labels = ['월', '화', '수', '목', '금', '토', '일']
    
    # 데이터가 있을 때만 그림
    if not df.empty:
        # 막대 그래프 그리기 (Y축: 요일인덱스, X축: 시간)
        # 0.8은 막대 두께
        bars = ax.barh(df['요일인덱스'], df['소요시간'], left=df['시작'], 
                       color=df['색상'], edgecolor='white', height=0.7)

        # 막대 안에 글자 쓰기
        for i, bar in enumerate(bars):
            row = df.iloc[i]
            # 활동명 (굵게)
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_y() + 0.45, 
                    str(row['활동명']), 
                    ha='center', va='center', color='white', weight='bold', fontsize=11)
            # 시간 (작게)
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_y() + 0.25, 
                    row['시간텍스트'], 
                    ha='center', va='center', color='white', fontsize=8)

    # 그래프 꾸미기
    ax.set_yticks(range(7))
    ax.set_yticklabels(days_labels, fontsize=12, weight='bold')
    ax.invert_yaxis() # 월요일을 맨 위로
    
    # X축 시간 설정 (오전 8시 ~ 오후 10시)
    ax.set_xlim(8, 22) 
    ax.set_xlabel("시간 (Time)", fontsize=10)
    ax.set_xticks(range(8, 23)) # 1시간 단위 눈금
    
    # 격자 무늬
    ax.grid(axis='x', linestyle='--', alpha=0.5)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)

    plt.title(f"📅 {child_name}의 주간 계획표", fontsize=20, weight='bold', pad=20)
    return fig

# ---------------------------------------------------------
# 3. 사용자 데이터 입력 구간 (여기만 고치면 됩니다!)
# ---------------------------------------------------------
# 색상표: 
# 파랑(#5D9CEC), 민트(#48CFAD), 노랑(#FFCE54), 보라(#AC92EC), 회색(#AAB2BD), 주황(#FB6E52)

# ▶ 첫째 아이 시간표 데이터
schedule_data_1 = [
    # {'title': '활동이름', 'days': '반복요일', 'start': '시작', 'end': '종료', 'color': '색상코드'},
    {'title': '학교수업', 'days': '월,화,수,목,금', 'start': '09:00', 'end': '13:00', 'color': '#5D9CEC'},
    {'title': '수학학원', 'days': '월,수,금', 'start': '14:00', 'end': '16:00', 'color': '#FB6E52'},
    {'title': '태권도',   'days': '화,목',   'start': '15:00', 'end': '16:00', 'color': '#48CFAD'},
    {'title': '가족식사', 'days': '토,일',     'start': '18:00', 'end': '19:30', 'color': '#FFCE54'},
    {'title': '학습지',   'days': '월,화,목',   'start': '19:00', 'end': '20:00', 'color': '#AC92EC'},
]

# ▶ 둘째 아이 시간표 데이터
schedule_data_2 = [
    {'title': '유치원',   'days': '월,화,수,목,금', 'start': '09:30', 'end': '14:00', 'color': '#FFCE54'},
    {'title': '미술놀이', 'days': '월,수',     'start': '15:00', 'end': '16:30', 'color': '#AC92EC'},
    {'title': '태권도',   'days': '화,목,금',   'start': '16:00', 'end': '17:00', 'color': '#48CFAD'},
    {'title': '놀이터',   'days': '금',       'start': '17:00', 'end': '18:30', 'color': '#5D9CEC'},
    {'title': '자유시간', 'days': '토,일',     'start': '10:00', 'end': '12:00', 'color': '#AAB2BD'},
]


# ---------------------------------------------------------
# 4. 화면 표시 (수정 불필요)
# ---------------------------------------------------------
st.title("📅 우리 아이 주간 학업 시간표")
st.markdown("코드에 입력된 데이터를 바탕으로 **일주일 전체 흐름**을 보여줍니다.")

tab1, tab2 = st.tabs(["첫째 아이", "둘째 아이"])

def render_schedule(name, data_list):
    # 1. 데이터를 표 형식으로 변환
    df = process_weekly_data(data_list)
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        st.write(f"### 📋 {name} 스케줄 목록")
        # 사용자가 보기 편하게 리스트 출력
        for item in data_list:
            st.text(f"• {item['title']} ({item['days']})\n  {item['start']}~{item['end']}")
            
    with col2:
        # 2. 그래프 그리기
        try:
            fig = draw_weekly_timetable(name, df)
            st.pyplot(fig)
            
            # 다운로드 버튼
            buf = BytesIO()
            fig.savefig(buf, format="png", bbox_inches='tight', dpi=300)
            st.download_button(
                label=f"💾 {name} 주간 시간표 저장",
                data=buf.getvalue(),
                file_name=f"{name}_weekly_plan.png",
                mime="image/png"
            )
        except Exception as e:
            st.error(f"오류가 발생했습니다: {e}")

with tab1:
    render_schedule("첫째(하민)", schedule_data_1)

with tab2:
    render_schedule("둘째(하율)", schedule_data_2)
