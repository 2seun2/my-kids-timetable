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
    # 폰트 설치 및 설정
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
# 2. 데이터 처리 및 시각화 함수
# ---------------------------------------------------------
def process_weekly_data_from_df(df):
    """
    편집된 데이터프레임을 받아 그래프용 데이터로 변환
    """
    expanded_data = []
    day_order = {'월': 0, '화': 1, '수': 2, '목': 3, '금': 4, '토': 5, '일': 6}
    
    # 데이터프레임의 각 줄을 반복
    for index, row in df.iterrows():
        # 필수 값이 비어있으면 건너뜀
        if not row['요일'] or not row['시작시간'] or not row['종료시간']:
            continue
            
        # "월,수,금" 같은 텍스트를 콤마로 분리
        days = str(row['요일']).split(',')
        
        for day in days:
            day = day.strip()
            if day in day_order:
                try:
                    # 시간 변환 (14:30 -> 14.5)
                    s_h, s_m = map(int, str(row['시작시간']).split(':'))
                    e_h, e_m = map(int, str(row['종료시간']).split(':'))
                    
                    start_float = s_h + (s_m / 60)
                    end_float = e_h + (e_m / 60)
                    
                    expanded_data.append({
                        '요일': day,
                        '요일인덱스': day_order[day],
                        '활동명': row['활동명'],
                        '시작': start_float,
                        '소요시간': end_float - start_float,
                        '색상': row['색상'] if row['색상'] else '#CCCCCC',
                        '시간텍스트': f"{row['시작시간']}~{row['종료시간']}"
                    })
                except:
                    continue # 시간 형식이 틀리면 무시
    
    return pd.DataFrame(expanded_data)

def draw_weekly_timetable(child_name, df):
    fig, ax = plt.subplots(figsize=(12, 7))
    days_labels = ['월', '화', '수', '목', '금', '토', '일']
    
    if not df.empty:
        # 막대 그래프 그리기
        bars = ax.barh(df['요일인덱스'], df['소요시간'], left=df['시작'], 
                       color=df['색상'], edgecolor='white', height=0.7)

        # 텍스트 추가
        for i, bar in enumerate(bars):
            row = df.iloc[i]
            # 활동명
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_y() + 0.45, 
                    str(row['활동명']), 
                    ha='center', va='center', color='white', weight='bold', fontsize=11)
            # 시간
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_y() + 0.25, 
                    row['시간텍스트'], 
                    ha='center', va='center', color='white', fontsize=8)

    # 그래프 꾸미기
    ax.set_yticks(range(7))
    ax.set_yticklabels(days_labels, fontsize=12, weight='bold')
    ax.invert_yaxis()
    ax.set_xlim(8, 22) # 오전 8시 ~ 오후 10시
    ax.set_xlabel("시간 (Time)", fontsize=10)
    ax.set_xticks(range(8, 23))
    ax.grid(axis='x', linestyle='--', alpha=0.5)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)

    plt.title(f"📅 {child_name}의 주간 계획표", fontsize=20, weight='bold', pad=20)
    return fig

# ---------------------------------------------------------
# 3. 초기 데이터 설정 (세션 상태 사용)
# ---------------------------------------------------------
if 'data_1' not in st.session_state:
    st.session_state.data_1 = pd.DataFrame([
        {'활동명': '학교', '요일': '월,화,수,목,금', '시작시간': '09:00', '종료시간': '13:00', '색상': '#5D9CEC'},
        {'활동명': '태권도', '요일': '월,수,금', '시작시간': '14:00', '종료시간': '15:00', '색상': '#48CFAD'},
    ])

if 'data_2' not in st.session_state:
    st.session_state.data_2 = pd.DataFrame([
        {'활동명': '유치원', '요일': '월,화,수,목,금', '시작시간': '09:30', '종료시간': '13:30', '색상': '#FFCE54'},
        {'활동명': '미술', '요일': '화,목', '시작시간': '15:00', '종료시간': '16:30', '색상': '#AC92EC'},
    ])

# ---------------------------------------------------------
# 4. 화면 구성
# ---------------------------------------------------------
st.title("📅 우리 아이 주간 학업 시간표 (직접 편집)")
st.caption("아래 표를 엑셀처럼 클릭해서 내용을 수정하거나, 맨 아래 행을 클릭해 내용을 추가하세요.")

tab1, tab2 = st.tabs(["첫째 아이", "둘째 아이"])

def render_tab(key_suffix, child_name, data_key):
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader(f"📝 {child_name} 일정 편집")
        st.markdown("""
        - **요일:** `월,수,금` 처럼 쉼표로 구분
        - **시간:** `14:00` (24시간제)
        - **색상:** `#`으로 시작하는 코드
        """)
        
        # 데이터 에디터 (여기서 직접 수정 가능!)
        edited_df = st.data_editor(
            st.session_state[data_key],
            num_rows="dynamic", # 행 추가/삭제 가능
            use_container_width=True,
            key=f"editor_{key_suffix}"
        )
        
        # 수정된 내용을 세션에 저장 (새로고침해도 유지되도록 하려면 별도 DB 필요하지만, 여기선 앱 사용 중 유지)
        st.session_state[data_key] = edited_df

    with col2:
        st.subheader("📊 시간표 미리보기")
        
        # 그래프 그리기
        if not edited_df.empty:
            try:
                # 데이터 변환
                plot_df = process_weekly_data_from_df(edited_df)
                
                if not plot_df.empty:
                    fig = draw_weekly_timetable(child_name, plot_df)
                    st.pyplot(fig)
                    
                    buf = BytesIO()
                    fig.savefig(buf, format="png", bbox_inches='tight', dpi=300)
                    st.download_button(
                        label=f"💾 {child_name} 시간표 저장",
                        data=buf.getvalue(),
                        file_name=f"{child_name}_timetable.png",
                        mime="image/png"
                    )
                else:
                    st.info("표시할 데이터가 없습니다. 요일과 시간을 확인해주세요.")
            except Exception as e:
                st.error(f"오류가 발생했습니다. 입력 형식을 확인해주세요.\n(예: 시간은 14:00 형태여야 합니다)")

with tab1:
    render_tab("child1", "첫째(하민)", 'data_1')

with tab2:
    render_tab("child2", "둘째(하율)", 'data_2')
