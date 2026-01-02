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
# 2. 데이터 처리 함수
# ---------------------------------------------------------
def process_weekly_data_from_df(df):
    expanded_data = []
    day_order = {'월': 0, '화': 1, '수': 2, '목': 3, '금': 4, '토': 5, '일': 6}
    
    # 데이터프레임 순회
    for index, row in df.iterrows():
        # 데이터 유효성 검사 (문자열로 변환하여 안전하게 처리)
        if pd.isna(row.get('요일')) or pd.isna(row.get('시작시간')) or pd.isna(row.get('종료시간')):
            continue
            
        days_str = str(row.get('요일', '')).strip()
        start_str = str(row.get('시작시간', '')).strip()
        end_str = str(row.get('종료시간', '')).strip()
        activity_str = str(row.get('활동명', '')).strip()

        if not days_str or not start_str or not end_str or not activity_str:
            continue
        
        if ':' not in start_str or ':' not in end_str:
             continue

        days = days_str.split(',')
        
        for day in days:
            day = day.strip()
            if day in day_order:
                try:
                    s_h, s_m = map(int, start_str.split(':'))
                    e_h, e_m = map(int, end_str.split(':'))
                    
                    start_float = s_h + (s_m / 60)
                    end_float = e_h + (e_m / 60)
                    
                    # 색상 처리
                    color_val = str(row.get('색상', '')).strip()
                    if not color_val.startswith('#'):
                        color_val = '#CCCCCC'

                    expanded_data.append({
                        '요일': day,
                        '요일인덱스': day_order[day],
                        '활동명': activity_str,
                        '시작': start_float,
                        '소요시간': end_float - start_float,
                        '색상': color_val,
                        '시간텍스트': f"{start_str}~{end_str}"
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
st.title("📅 우리 아이 주간 학업 시간표 (입력 후 버튼 클릭)")
st.markdown("👉 **왼쪽 표**에서 내용을 수정하고 추가한 뒤, 아래 **[🔄 일정 적용 및 이미지 업데이트] 버튼**을 눌러주세요.")

tab1, tab2 = st.tabs(["첫째 아이", "둘째 아이"])

def render_tab(key_suffix, child_name, data_key):
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader(f"📝 {child_name} 일정 편집")
        st.info("💡 표의 맨 아래 빈 줄을 클릭하면 새 항목을 추가할 수 있습니다.")
        
        # 데이터 에디터 (모든 컬럼 텍스트 모드)
        # 주의: 여기서는 임시 변수(temp_df)에 담아둡니다.
        temp_df = st.data_editor(
            st.session_state[data_key], # 현재 저장된 데이터를 보여줌
            column_config={
                "활동명": st.column_config.TextColumn("활동명", required=True),
                "요일": st.column_config.TextColumn("요일 (예: 월,수)", required=True),
                "시작시간": st.column_config.TextColumn("시작 (예: 14:00)", required=True),
                "종료시간": st.column_config.TextColumn("종료 (예: 15:00)", required=True),
                "색상": st.column_config.TextColumn("색상코드 (예: #CCCCCC)"),
            },
            num_rows="dynamic",
            use_container_width=True,
            key=f"editor_{key_suffix}"
        )
        
        st.markdown("""
        <small>색상 예시: 파랑(#5D9CEC), 민트(#48CFAD), 노랑(#FFCE54), 보라(#AC92EC), 주황(#FB6E52)</small>
        """, unsafe_allow_html=True)

        # [핵심] 업데이트 버튼
        # 이 버튼을 눌러야 temp_df가 실제 session_state에 저장되고 그래프가 그려집니다.
        if st.button("🔄 일정 적용 및 이미지 업데이트", key=f"btn_{key_suffix}", use_container_width=True, type="primary"):
            st.session_state[data_key] = temp_df
            st.rerun() # 화면 새로고침

    with col2:
        st.subheader("📊 시간표 미리보기")
        
        # [핵심] 그래프는 항상 '저장된(버튼으로 확정된) 데이터'를 사용합니다.
        confirmed_df = st.session_state[data_key]
        
        if not confirmed_df.empty:
            # 안전하게 문자열로 변환 후 처리
            safe_df = confirmed_df.astype(str)
            plot_df = process_weekly_data_from_df(safe_df)
            
            if not plot_df.empty:
                try:
                    fig = draw_weekly_timetable(child_name, plot_df)
                    st.pyplot(fig)
                    
                    buf = BytesIO()
                    fig.savefig(buf, format="png", bbox_inches='tight', dpi=300)
                    st.download_button(
                        label="💾 이미지 파일로 저장하기",
                        data=buf.getvalue(),
                        file_name=f"{child_name}_timetable.png",
                        mime="image/png",
                        use_container_width=True
                    )
                except Exception as e:
                    st.error(f"그래프 생성 중 오류가 발생했습니다. 입력 데이터를 확인해주세요.")
            else:
                st.warning("표시할 데이터가 없습니다. 왼쪽 표에 일정을 입력하고 버튼을 눌러주세요.")
        else:
             st.warning("데이터가 비어있습니다. 일정을 추가해주세요.")

with tab1:
    render_tab("child1", "첫째(하민)", 'data_1')

with tab2:
    render_tab("child2", "둘째(하율)", 'data_2')
