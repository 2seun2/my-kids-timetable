import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os

# 페이지 설정
st.set_page_config(page_title="우리 아이 하루 계획표", layout="wide")

# ---------------------------------------------------------
# [수정된 부분] 폰트 자동 설치 함수 (오류 해결 핵심)
# ---------------------------------------------------------
@st.cache_resource
def install_font():
    # 리눅스(Streamlit Cloud) 환경 등에서 한글 폰트가 없을 경우
    # 구글 폰트(나눔고딕)를 다운로드하여 적용합니다.
    font_file = "NanumGothic.ttf"
    
    if not os.path.exists(font_file):
        # 폰트 파일이 없으면 다운로드 (curl 명령어 사용)
        import urllib.request
        url = "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Regular.ttf"
        urllib.request.urlretrieve(url, font_file)
        
    # 폰트 매니저에 추가
    fm.fontManager.addfont(font_file)
    plt.rc('font', family='NanumGothic')

# 폰트 적용 실행
install_font()
plt.rcParams['axes.unicode_minus'] = False # 마이너스 기호 깨짐 방지

# ---------------------------------------------------------
# 기존 로직 유지
# ---------------------------------------------------------
from io import BytesIO

st.title("🕒 우리 아이 하루 생활계획표 (막대그래프형)")
st.markdown("시작 시간과 끝나는 시간을 입력하면 **시간의 길이를 시각화**해서 보여줍니다.")

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
    
    # 그래프 순서를 시간 순서대로 정렬
    df = df.sort_values(by='Start_Float', ascending=True)
    df = df.reset_index(drop=True)
    df_reversed = df.iloc[::-1]

    # 그림 생성
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # 막대 그래프 그리기
    bars = ax.barh(df_reversed.index, df_reversed['Duration'], left=df_reversed['Start_Float'], 
                   color=df_reversed['색상'], edgecolor='white', height=0.6)

    # 텍스트 추가
    for i, bar in enumerate(bars):
        row = df_reversed.iloc[i]
        
        # 활동명
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_y() + bar.get_height()/2 + 0.1, 
                str(row['활동명']), 
                ha='center', va='center', color='white', weight='bold', fontsize=12)
        
        # 시간 범위
        time_text = f"{row['시작시간']} ~ {row['종료시간']}"
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_y() + bar.get_height()/2 - 0.15, 
                time_text, 
                ha='center', va='center', color='white', fontsize=9)

    ax.set_xlim(df['Start_Float'].min() - 0.5, df['End_Float'].max() + 0.5)
    ax.set_xlabel("시간 (Time)", fontsize=10)
    
    ax.set_yticks([])
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.grid(axis='x', linestyle='--', alpha=0.5)

    plt.title(f"★ {child_name}의 하루 흐름 ★", fontsize=20, weight='bold', pad=20)
    return fig

# ---------------------------------------------------------
# 메인 화면 구성
# ---------------------------------------------------------

tab1, tab2 = st.tabs(["첫째 아이", "둘째 아이"])

color_options = {
    '공부/학교': '#5D9CEC',
    '운동/활동': '#48CFAD',
    '식사/휴식': '#FFCE54',
    '취미/놀이': '#AC92EC',
    '수면/준비': '#AAB2BD',
    '학원/레슨': '#FB6E52',
}

def render_tab(key_suffix, default_name, default_data):
    col1, col2 = st.columns([1, 2])
    
    with col1:
        name = st.text_input("아이 이름", value=default_name, key=f"name_{key_suffix}")
        
        df = pd.DataFrame(default_data)
        
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

        st.markdown("###### 🎨 색상 가이드")
        for label, color in color_options.items():
            st.markdown(f"<span style='color:{color}'>■</span> {label}", unsafe_allow_html=True)

    with col2:
        plot_df = edited_df.copy()
        
        try:
            if not plot_df.empty:
                plot_df['시작시간'] = plot_df['시작시간'].astype(str)
                plot_df['종료시간'] = plot_df['종료시간'].astype(str)
                
                fig = create_gantt_chart(name, plot_df)
                st.pyplot(fig)
                
                buf = BytesIO()
                fig.savefig(buf, format="png", bbox_inches='tight', dpi=300)
                st.download_button(
                    label=f"💾 {name} 계획표 저장하기",
                    data=buf.getvalue(),
                    file_name=f"{name}_timeline.png",
                    mime="image/png"
                )
        except Exception as e:
            st.error(f"시간 형식을 확인해주세요! (오류: {e})")

# 데이터
data_1 = {
    "활동명": ["기상 및 아침", "학교 수업", "점심 시간", "수학 학원", "자유 시간", "저녁 식사", "숙제"],
    "시작시간": ["07:30", "09:00", "12:00", "14:00", "16:00", "18:00", "19:00"],
    "종료시간": ["08:30", "12:00", "13:00", "16:00", "18:00", "19:00", "21:00"],
    "색상": [color_options['수면/준비'], color_options['공부/학교'], color_options['식사/휴식'], 
           color_options['학원/레슨'], color_options['취미/놀이'], color_options['식사/휴식'], color_options['공부/학교']]
}

data_2 = {
    "활동명": ["일어나기", "유치원 등원", "태권도", "놀이터", "간식", "학습지", "꿈나라"],
    "시작시간": ["08:00", "09:30", "14:00", "15:30", "16:30", "17:00", "21:00"],
    "종료시간": ["09:00", "13:30", "15:00", "16:30", "17:00", "18:00", "07:00"],
    "색상": [color_options['수면/준비'], color_options['공부/학교'], color_options['운동/활동'], 
           color_options['취미/놀이'], color_options['식사/휴식'], color_options['공부/학교'], color_options['수면/준비']]
}

with tab1:
    render_tab("child1", "첫째(하민)", data_1)

with tab2:
    render_tab("child2", "둘째(하율)", data_2)
