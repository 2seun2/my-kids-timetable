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
    plt.rcParams['axes.unicode_minus'] = False 

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
    
    # 그래프 정렬
    df = df.sort_values(by='Start_Float', ascending=True)
    df = df.reset_index(drop=True)
    df_reversed = df.iloc[::-1]

    # 캔버스 생성
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # 막대 그래프 그리기
    # 색상 컬럼이 유효한지 확인하고 없으면 기본색 사용
    colors = df_reversed['색상'].tolist()
    
    bars = ax.barh(df_reversed.index, df_reversed['Duration'], left=df_reversed['Start_Float'], 
                   color=colors, edgecolor='white', height=0.6)

    # 텍스트 추가
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
    if not df.empty:
        start_min = df['Start_Float'].min()
        end_max = df['End_Float'].max()
        ax.set_xlim(start_min - 0.5, end_max + 0.5)
    
    ax.set_xlabel("시간 (Time)", fontsize=10)
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
st.title("🕒 우리 아이 하루 생활계획표")
st.caption("활동 내용을 수정하면 아래 그래프가 자동으로 바뀝니다.")

tab1, tab2 = st.tabs(["첫째 아이", "둘째 아이"])

# 색상 팔레트 (사용자가 복사해서 쓸 수 있게 텍스트로 표시)
color_map = {
    '공부(파랑)': '#5D9CEC',
    '운동(민트)': '#48CFAD',
    '식사(노랑)': '#FFCE54',
    '놀이(보라)': '#AC92EC',
    '수면(회색)': '#AAB2BD',
    '학원(주황)': '#FB6E52',
}

def render_tab(key_suffix, default_name, default_data):
    col1, col2 = st.columns([1, 2])
    
    with col1:
        name = st.text_input("아이 이름", value=default_name, key=f"name_{key_suffix}")
        
        # 색상 가이드 버튼 보여주기
        st.markdown("##### 🎨 색상표 (아래 코드를 복사해서 표에 넣으세요)")
        st.code(
            "파랑: #5D9CEC  |  민트: #48CFAD\n"
            "노랑: #FFCE54  |  보라: #AC92EC\n"
            "회색: #AAB2BD  |  주황: #FB6E52"
        )
        
        df = pd.DataFrame(default_data)
        
        # [수정된 부분] SelectColumn 제거 -> 오류 원인 완전 제거
        edited_df = st.data_editor(
            df,
            column_config={
                "활동명": st.column_config.TextColumn("활동 내용", required=True),
                "시작시간": st.column_config.TimeColumn("시작", format="HH:mm", step=60*30, required=True),
                "종료시간": st.column_config.TimeColumn("끝", format="HH:mm", step=60*30, required=True),
                "색상": st.column_config.TextColumn("색상 코드", help="#으로 시작하는 색상코드 입력", required=True)
            },
            num_rows="dynamic",
            use_container_width=True,
            key=f"editor_{key_suffix}"
        )

    with col2:
        st.write("### 미리보기")
        plot_df = edited_df.copy()
        
        if not plot_df.empty:
            try:
                plot_df['시작시간'] = plot_df['시작시간'].astype(str)
                plot_df['종료시간'] = plot_df['종료시간'].astype(str)
                
                fig = create_gantt_chart(name, plot_df)
                st.pyplot(fig)
                
                buf = BytesIO()
                fig.savefig(buf, format="png", bbox_inches='tight', dpi=300)
                st.download_button(
                    label=f"💾 {name} 계획표 다운로드",
                    data=buf.getvalue(),
                    file_name=f"{name}_timeline.png",
                    mime="image/png"
                )
            except Exception as e:
                st.warning(f"데이터를 확인해주세요. (오류: {e})")

# 초기 데이터
data_1 = {
    "활동명": ["기상", "학교 수업", "점심", "학원", "게임", "저녁"],
    "시작시간": ["07:30", "09:00", "12:00", "14:00", "16:00", "18:00"],
    "종료시간": ["08:30", "12:00", "13:00", "16:00", "18:00", "19:00"],
    "색상": ['#AAB2BD', '#5D9CEC', '#FFCE54', '#FB6E52', '#AC92EC', '#FFCE54']
}

data_2 = {
    "활동명": ["기상", "유치원", "태권도", "놀이터", "간식", "취침"],
    "시작시간": ["08:00", "09:30", "14:00", "15:30", "16:30", "21:00"],
    "종료시간": ["09:00", "13:30", "15:00", "16:30", "17:00", "07:00"],
    "색상": ['#AAB2BD', '#5D9CEC', '#48CFAD', '#AC92EC', '#FFCE54', '#AAB2BD']
}

with tab1:
    render_tab("child1", "첫째(하민)", data_1)

with tab2:
    render_tab("child2", "둘째(하율)", data_2)
