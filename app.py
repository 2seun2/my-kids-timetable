import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os
from io import BytesIO

# 1. 페이지 설정
st.set_page_config(page_title="우리 아이 하루 계획표", layout="wide")

# 2. 폰트 설정 (나눔고딕 강제 설치)
@st.cache_resource
def install_font_and_configure():
    font_file = "NanumGothic.ttf"
    if not os.path.exists(font_file):
        import urllib.request
        url = "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Regular.ttf"
        urllib.request.urlretrieve(url, font_file)
    fm.fontManager.addfont(font_file)
    plt.rc('font', family='NanumGothic')
    plt.rcParams['axes.unicode_minus'] = False 

install_font_and_configure()

# 3. 데이터 처리 함수
def time_to_float(time_str):
    try:
        # 입력된 값이 문자열인지 확인하고 처리
        time_str = str(time_str).strip()
        if ':' in time_str:
            h, m = map(int, time_str.split(':'))
            return h + (m / 60)
        else:
            return 0.0
    except:
        return 0.0

def create_gantt_chart(child_name, df):
    # 데이터 복사 및 전처리
    plot_df = df.copy()
    plot_df['Start_Float'] = plot_df['시작시간'].apply(time_to_float)
    plot_df['End_Float'] = plot_df['종료시간'].apply(time_to_float)
    plot_df['Duration'] = plot_df['End_Float'] - plot_df['Start_Float']
    
    # 시간 순서 정렬
    plot_df = plot_df.sort_values(by='Start_Float', ascending=True)
    plot_df = plot_df.reset_index(drop=True)
    df_reversed = plot_df.iloc[::-1]

    # 그래프 그리기
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # 색상 처리 (오류 방지를 위해 기본값 설정)
    colors = []
    for c in df_reversed['색상코드']:
        try:
            if str(c).startswith('#'):
                colors.append(c)
            else:
                colors.append('#cccccc') # 색상 코드가 이상하면 회색
        except:
            colors.append('#cccccc')

    bars = ax.barh(df_reversed.index, df_reversed['Duration'], left=df_reversed['Start_Float'], 
                   color=colors, edgecolor='white', height=0.6)

    # 텍스트 추가
    for i, bar in enumerate(bars):
        row = df_reversed.iloc[i]
        
        # 활동명
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_y() + bar.get_height()/2 + 0.1, 
                str(row['활동명']), 
                ha='center', va='center', color='white', weight='bold', fontsize=12)
        
        # 시간 표시
        time_text = f"{row['시작시간']}~{row['종료시간']}"
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_y() + bar.get_height()/2 - 0.15, 
                time_text, 
                ha='center', va='center', color='white', fontsize=9)

    # 축 설정
    if not plot_df.empty:
        start_min = plot_df['Start_Float'].min()
        end_max = plot_df['End_Float'].max()
        ax.set_xlim(start_min - 0.5, end_max + 0.5)
    
    ax.set_xlabel("시간 (Time)", fontsize=10)
    ax.set_yticks([])
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.grid(axis='x', linestyle='--', alpha=0.5)

    plt.title(f"★ {child_name}의 하루 흐름 ★", fontsize=20, weight='bold', pad=20)
    return fig

# 4. 화면 구성
st.title("🕒 우리 아이 하루 생활계획표")
st.caption("⚠️ 시간은 반드시 **14:00** 형식으로, 색상은 **#코드** 형식으로 입력해주세요.")

tab1, tab2 = st.tabs(["첫째 아이", "둘째 아이"])

def render_tab(key_suffix, default_name, default_data):
    col1, col2 = st.columns([1, 2])
    
    with col1:
        name = st.text_input("아이 이름", value=default_name, key=f"name_{key_suffix}")
        
        st.markdown("""
        **색상 코드표:**
        - 파랑: `#5D9CEC` | 민트: `#48CFAD`
        - 노랑: `#FFCE54` | 보라: `#AC92EC`
        - 회색: `#AAB2BD` | 주황: `#FB6E52`
        """)
        
        # 데이터프레임 생성
        df = pd.DataFrame(default_data)
        
        # [핵심 수정] column_config를 삭제하여 오류 원인 제거
        # 그냥 엑셀처럼 텍스트로 입력받습니다.
        edited_df = st.data_editor(
            df,
            num_rows="dynamic",
            use_container_width=True,
            key=f"editor_{key_suffix}"
        )

    with col2:
        st.write("### 📸 미리보기")
        
        # 버튼 없이 즉시 반응하도록 처리
        if not edited_df.empty:
            try:
                fig = create_gantt_chart(name, edited_df)
                st.pyplot(fig)
                
                buf = BytesIO()
                fig.savefig(buf, format="png", bbox_inches='tight', dpi=300)
                st.download_button(
                    label="💾 이미지 저장하기",
                    data=buf.getvalue(),
                    file_name=f"{name}_timetable.png",
                    mime="image/png"
                )
            except Exception as e:
                st.error(f"입력 형식을 확인해주세요. (시간은 13:00 처럼 콜론(:)이 있어야 합니다)")

# 초기 데이터 (모두 문자열로 처리)
data_1 = {
    "활동명": ["기상", "학교", "학원", "게임", "저녁"],
    "시작시간": ["07:30", "09:00", "14:00", "16:00", "18:00"],
    "종료시간": ["08:30", "12:00", "16:00", "18:00", "19:00"],
    "색상코드": ['#AAB2BD', '#5D9CEC', '#FB6E52', '#AC92EC', '#FFCE54']
}

data_2 = {
    "활동명": ["기상", "유치원", "태권도", "놀이터", "취침"],
    "시작시간": ["08:00", "09:30", "14:00", "15:30", "21:00"],
    "종료시간": ["09:00", "13:30", "15:00", "16:30", "07:00"],
    "색상코드": ['#AAB2BD', '#5D9CEC', '#48CFAD', '#FFCE54', '#AAB2BD']
}

with tab1:
    render_tab("child1", "첫째(하민)", data_1)

with tab2:
    render_tab("child2", "둘째(하율)", data_2)
