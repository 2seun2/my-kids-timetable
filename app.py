import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os
from io import BytesIO

# ---------------------------------------------------------
# 1. 기본 설정
# ---------------------------------------------------------
st.set_page_config(page_title="우리 아이 주간 시간표", layout="wide")

@st.cache_resource
def install_font_and_configure():
    # 한글 폰트 설정 (나눔고딕)
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
# 2. 데이터 처리 함수 (안전장치 강화)
# ---------------------------------------------------------
def process_weekly_data_from_df(df):
    expanded_data = []
    day_order = {'월': 0, '화': 1, '수': 2, '목': 3, '금': 4, '토': 5, '일': 6}
    
    # 데이터프레임 순회
    for index, row in df.iterrows():
        # 데이터가 None이거나 비어있으면 무시 (오류 방지)
        if pd.isna(row['요일']) or pd.isna(row['시작시간']) or pd.isna(row['종료시간']):
            continue
        if str(row['요일']).strip() == "" or str(row['시작시간']).strip() == "":
            continue
            
        days = str(row['요일']).split(',')
        
        for day in days:
            day = day.strip()
            if day in day_order:
                try:
                    # 시간 포맷 처리 (혹시 모를 공백 제거)
                    s_str = str(row['시작시간']).strip()
                    e_str = str(row['종료시간']).strip()
                    
                    if ':' not in s_str or ':' not in e_str:
                        continue
                        
                    s_h, s_m = map(int, s_str.split(':'))
                    e_h, e_m = map(int, e_str.split(':'))
                    
                    start_float = s_h + (s_m / 60)
                    end_float = e_h + (e_m / 60)
                    
                    # 색상값이 없으면 기본 회색 적용
                    color_val = str(row['색상']).strip()
                    if not color_val.startswith('#'):
                        color_val = '#CCCCCC'

                    expanded_data.append({
                        '요일': day,
                        '요일인덱스': day_order[day],
                        '활동명': str(row['활동명']),
                        '시작': start_float,
                        '소요시간': end_float - start_float,
                        '색상': color_val,
                        '시간텍스트': f"{s_str}~{e_str}"
                    })
                except:
                    continue 
    
    return pd.DataFrame(expanded_data)

def draw_weekly_timetable(child_name, df):
    fig, ax = plt.subplots(figsize=(12, 7))
    days_labels = ['월', '화', '수', '목', '금', '토', '일']
    
    if not df.empty:
        bars = ax.barh(df['요일인덱스'], df['소요시간'], left=df['시작'], 
                       color=df['색상'], edgecolor='white', height=0.7)

        for i, bar in enumerate(bars):
            row = df.iloc[i]
            # 글자 크기 조정
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_y() + 0.45, 
                    str(row['활동명']), 
                    ha='center', va='center', color='white', weight='bold', fontsize=11)
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_y() + 0.25, 
                    row['시간텍스트'], 
                    ha='center', va='center', color='white', fontsize=8)

    ax.set_yticks(range(7))
    ax.set_yticklabels(days_labels, fontsize=12, weight='bold')
    ax.invert_yaxis()
    ax.set_xlim(8, 22)
    ax.set_xticks(range(8, 23))
    ax.set_xlabel("시간 (Time)", fontsize=10)
    ax.grid(axis='x', linestyle='--', alpha=0.5)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)

    plt.title(f"📅 {child_name}의 주간 계획표", fontsize=20, weight='bold', pad=20)
    return fig

# ---------------------------------------------------------
# 3. 초기 데이터 (세션 상태)
# ---------------------------------------------------------
# 처음 실행될 때만 데이터를 생성합니다.
if 'data_1' not in st.session_state:
    st.session_state.data_1 = pd.DataFrame([
        {'활동명': '학교', '요일': '월,화,수,목,금', '시작시간': '09:00', '종료시간': '13:00', '색상': '#5D9CEC'},
        {'활동명': '학원', '요일': '월,수,금', '시작시간': '14:00', '종료시간': '16:00', '색상': '#FB6E52'},
    ])

if 'data_2' not in st.session_state:
    st.session_state.data_2 = pd.DataFrame([
        {'활동명': '유치원', '요일': '월,화,수,목,금', '시작시간': '09:30', '종료시간': '13:30', '색상': '#FFCE54'},
        {'활동명': '태권도', '요일': '화,목', '시작시간': '16:00', '종료시간': '17:00', '색상': '#48CFAD'},
    ])

# ---------------------------------------------------------
# 4. 화면 UI
# ---------------------------------------------------------
st.title("📅 우리 아이 주간 학업 시간표 (입력 수정 가능)")
st.caption("표의 맨 아래 빈 칸을 클릭하면 새로운 일정을 추가할 수 있습니다.")

tab1, tab2 = st.tabs(["첫째 아이", "둘째 아이"])

def render_tab(key_suffix, child_name, data_key):
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader(f"📝 {child_name} 일정 편집")
        st.markdown("""
        - **요일**: `월,수,금` (쉼표로 구분)
        - **시간**: `14:00` (반드시 : 포함)
        - **색상**: `#` 색상코드
        """)
        
        # [핵심 수정] 모든 컬럼을 '텍스트'로 강제 지정하여 입력 오류 방지
        edited_df = st.data_editor(
            st.session_state[data_key],
            column_config={
                "활동명": st.column_config.TextColumn("활동명", required=True),
                "요일": st.column_config.TextColumn("요일 (예: 월,수)", required=True),
                "시작시간": st.column_config.TextColumn("시작 (예: 14:00)", required=True),
                "종료시간": st.column_config.TextColumn("종료 (예: 15:00)", required=True),
                "색상": st.column_config.TextColumn("색상코드", default="#CCCCCC"),
            },
            num_rows="dynamic", # 행 추가 허용
            use_container_width=True,
            key=f"editor_{key_suffix}"
        )
        
        # 수정된 데이터 저장
        st.session_state[data_key] = edited_df

    with col2:
        st.subheader("📊 시간표 미리보기")
        
        if not edited_df.empty:
            # 안전하게 문자열로 변환 후 처리
            safe_df = edited_df.astype(str)
            plot_df = process_weekly_data_from_df(safe_df)
            
            if not plot_df.empty:
                try:
                    fig = draw_weekly_timetable(child
