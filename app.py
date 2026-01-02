import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os
from io import BytesIO

# ---------------------------------------------------------
# 페이지 설정
# ---------------------------------------------------------
st.set_page_config(page_title="우리 아이 하루 계획표", layout="wide")

# ---------------------------------------------------------
# 폰트 설정 (서버에 폰트가 없을 경우 자동 설치)
# ---------------------------------------------------------
@st.cache_resource
def install_font_and_configure():
    # 1. 폰트 파일 다운로드 (나눔고딕)
    font_file = "NanumGothic.ttf"
    if not os.path.exists(font_file):
        import urllib.request
        url = "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Regular.ttf"
        urllib.request.urlretrieve(url, font_file)
        
    # 2. 폰트 등록
    fm.fontManager.addfont(font_file)
    plt.rc('font', family='NanumGothic')
    plt.rcParams['axes.unicode_minus'] = False # 마이너스 기호 깨짐 방지

# 폰트 실행
install_font_and_configure()

# ---------------------------------------------------------
# 그래프 및 데이터 처리 로직
# ---------------------------------------------------------
def time_to_float(time_str):
    try:
        h, m = map(int, str(time_str).split(':'))
        return h + (m / 60)
    except:
        return 0.0

def create_gantt_chart(child_name, df):
    # 데이터 전처리
    df['Start_Float'] = df['시작시간'].apply(time_to_float)
    df['End_Float'] = df['종료시간'].apply(time_to_float)
    df['Duration'] = df['End_Float'] - df['Start_Float']
    
    # 그래프 정렬 (시간순)
    df = df.sort_values(by='Start_Float', ascending=True)
    df = df.reset_index(drop=True)
    df_reversed = df.iloc[::-1] # 그래프는 밑에서부터 그려지므로 뒤집기

    # 캔버스 생성
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # 막대 그래프 그리기
    bars = ax.barh(df_reversed.index, df_reversed['Duration'], left=df_reversed['Start_Float'], 
                   color=df_reversed['색상'], edgecolor='white', height=0.6)

    # 막대 안에 글자 넣기
    for i, bar in enumerate(bars):
        row = df_reversed.iloc[i]
        
        # 활동명
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_y() + bar.get_height()/2 + 0.1, 
                str(row['활동명']), 
                ha='center', va='center', color='white', weight='bold', fontsize=12)
        
        # 시간 텍스트
        time_text = f"{row['시작시간']} ~ {row['종료시간']}"
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_y() + bar.get_height()/2 - 0.15, 
                time_text, 
                ha='center', va='center', color='white', fontsize=9)

    # 축 설정
    start_min = df['Start_Float'].min()
    end_max = df['End_Float'].max()
    ax.set_xlim(start_min - 0.5, end_max + 0.5)
    ax.set_xlabel("시간 (Time)", fontsize=10)
    
    # 불필요한 테두리 제거
    ax.set_yticks([])
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.grid(axis='x', linestyle='--', alpha=0.5)

    plt.title(f"★ {child_name}의 하루 흐름 ★", fontsize=20, weight='bold', pad=20)
    return fig

# ---------------------------------------------------------
# 메인 UI 구성
# ---------------------------------------------------------
st.title("🕒 우리 아이 하루 생활계획표 (막대그래프형)")
st.caption("새로고침을 해도 오류가 난다면, 우측 상단 메뉴 -> Clear Cache를 눌러보세요.")

tab1, tab2 = st.tabs(["첫째 아이", "둘째 아이"])

# 색상 팔레트 정의
color_options = {
    '공부/학교 (파랑)': '#5D9CEC',
    '운동/활동 (민트)': '#48CFAD',
    '식사/휴식 (노랑)': '#FFCE54',
    '취미/놀이 (보라)': '#AC92EC',
    '수면/준비 (회색)': '#AAB2BD',
    '학원/레슨 (주황)': '#FB6E52',
}

def render_tab(key_suffix, default_name, default_data):
    col1, col2 = st.columns([1, 2])
    
    with col1:
        name = st.text_input("아이 이름", value=default_name, key=f"name_{key_suffix}")
        
        df = pd.DataFrame(default_data)
        
        # 데이터 에디터 (여기가 오류의 원인이었음 -> 버전업으로 해결)
        edited_df = st.data_editor(
            df,
            column_config={
                "활동명": st.column_config.TextColumn("활동 내용", required=True),
                "시작시간": st.column_config.TimeColumn("시작", format="HH:mm", step=60*30, required=True),
                "종료시간": st.column_config.TimeColumn("끝", format="HH:mm", step=60*30, required=True),
                "색상": st.column_config.SelectColumn("색상", options=list(color_options.values()), required=True)
            },
            num_rows="dynamic",
            use_container_width=True,
            key=f"editor_{key_suffix}"
        )
        
        # 색상 가이드
        st.markdown("###### 🎨 색상 가이드")
        for label, color in color_options.items():
            st.markdown(f"<span style='color:{color}'>■</span> {label}", unsafe_allow_html=True)

    with col2:
        st.write("###
