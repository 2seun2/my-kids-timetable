import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os
import time
from io import BytesIO

# ---------------------------------------------------------
# 1. 기본 설정 및 색상 프리셋
# ---------------------------------------------------------
st.set_page_config(page_title="우리 아이 맞춤 시간표", layout="wide")

# 예쁜 파스텔톤 색상 목록 (이름 -> 코드 변환용)
COLOR_MAP = {
    '파스텔 블루': '#5D9CEC',
    '민트': '#48CFAD',
    '개나리색': '#FFCE54',
    '연보라': '#AC92EC',
    '살구색': '#FB6E52',
    '그레이': '#AAB2BD',
    '벚꽃핑크': '#ED5565',
    '잔디색': '#A0D468',
    '하늘색': '#4FC1E9',
    '진한남색': '#3B4758'
}

TEXT_COLOR_MAP = {
    '흰색': 'white',
    '검정': 'black'
}

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

# ---------------------------------------------------------
# 2. 데이터 처리 및 오류 검사 함수
# ---------------------------------------------------------
def validate_and_process_data(df):
    """ 
    데이터를 검사하고, 오류가 있으면 에러 메시지를 반환합니다. 
    정상 데이터는 그래프용으로 변환합니다.
    """
    expanded_data = []
    error_messages = []
    day_order = {'월': 0, '화': 1, '수': 2, '목': 3, '금': 4}
    
    for index, row in df.iterrows():
        # 필수 입력값 확인
        activity = str(row.get('활동명', '')).strip()
        days_str = str(row.get('요일', '')).strip()
        start_str = str(row.get('시작시간', '')).strip()
        end_str = str(row.get('종료시간', '')).strip()
        color_name = str(row.get('배경색', '그레이'))
        text_color_name = str(row.get('글자색', '흰색'))

        # 빈 줄은 무시
        if not activity and not days_str and not start_str:
            continue
            
        # 1. 누락된 항목 검사
        if not activity or not days_str or not start_str or not end_str:
            error_messages.append(f"{index+1}번째 줄: 모든 칸(활동명, 요일, 시간)을 채워주세요.")
            continue

        # 2. 시간 형식 검사 (HH:MM)
        try:
            if ':' not in start_str or ':' not in end_str:
                raise ValueError("콜론(:) 없음")
                
            s_h, s_m = map(int, start_str.split(':'))
            e_h, e_m = map(int, end_str.split(':'))
            
            # 3. 시간 논리 검사 (0~23시, 종료가 시작보다 늦어야 함)
            if not (0 <= s_h <= 23) or not (0 <= s_m <= 59) or \
               not (0 <= e_h <= 23) or not (0 <= e_m <= 59):
                error_messages.append(f"{index+1}번째 줄: 시간은 00:00 ~ 23:59 사이여야 합니다.")
                continue
                
            start_float = s_h + (s_m / 60)
            end_float = e_h + (e_m / 60)
            
            if end_float <= start_float:
                error_messages.append(f"{index+1}번째 줄: 끝나는 시간이 시작 시간보다 빨라요! ({activity})")
                continue

        except ValueError:
            error_messages.append(f"{index+1}번째 줄: 시간 형식이 잘못되었습니다. '14:00'처럼 써주세요. ({activity})")
            continue

        # 4. 요일 분리 및 데이터 생성
        days = days_str.split(',')
        for day in days:
            day = day.strip()
            if day in day_order:
                expanded_data.append({
                    '요일': day,
                    '요일인덱스': day_order[day],
                    '활동명': activity,
                    '시작': start_float,
                    '소요시간': end_float - start_float,
                    '배경색': COLOR_MAP.get(color_name, '#CCCCCC'),
                    '글자색': TEXT_COLOR_MAP.get(text_color_name, 'white'),
                    '시간텍스트': f"{start_str}~{end_str}"
                })
            else:
                # 요일 오타는 경고만 하고 넘어감 (그래프엔 표시 안 됨)
                pass
                
    return pd.DataFrame(expanded_data), error_messages

# ---------------------------------------------------------
# 3. 그래프 그리기
# ---------------------------------------------------------
def draw_timetable(name1, icon1, df1, name2, icon2, df2, style_opts):
    fig, ax = plt.subplots(figsize=(14, 10))
    days_labels = ['월', '화', '수', '목', '금']
    y_min, y_max = 8, 22
    
    # 스타일
    font_weight = style_opts['font_weight']
    
    # 배경
    ax.grid(axis='y', linestyle='--', alpha=0.3, zorder=0)
    for x in range(len(days_labels) - 1):
        ax.axvline(x + 0.5, color='gray', linestyle='-', linewidth=1, alpha=0.3)
    
    bar_width = 0.4
    
    def plot_bars(df, offset):
        if df.empty: return
        x_positions = df['요일인덱스'] + offset
        
        bars = ax.bar(x=x_positions, height=df['소요시간'], bottom=df['시작'], 
                      color=df['배경색'], edgecolor='white', width=bar_width, zorder=3, alpha=0.95)
        
        for i, bar in enumerate(bars):
            row = df.iloc[i]
            # 글자색 적용
            txt_color = row['글자색']
            
            # 활동명
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_y() + bar.get_height()/2 + 0.1, 
                    str(row['활동명']), ha='center', va='center', color=txt_color, 
                    weight=font_weight, fontsize=style_opts['bar_text_size'])
            # 시간
            if row['소요시간'] >= 0.5:
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_y() + bar.get_height()/2 - 0.2, 
                        row['시간텍스트'], ha='center', va='center', color=txt_color, 
                        fontsize=style_opts['time_text_size'], alpha=0.8)

    plot_bars(df1, -0.21)
    plot_bars(df2, 0.21)

    # 축 설정
    ax.set_xticks(range(5))
    ax.set_xticklabels(days_labels, fontsize=style_opts['axis_size'], weight=font_weight)
    
    # 범례
    legend_text = f"◀ {icon1} {name1} (왼쪽)   |   {icon2} {name2} (오른쪽) ▶"
    ax.text(0, y_min - 0.6, legend_text, fontsize=style_opts['axis_size'], weight='bold', 
            color='#333333', ha='left',
            bbox=dict(facecolor='#f0f2f6', edgecolor='none', boxstyle='round,pad=0.5'))

    ax.set_ylim(y_max, y_min)
    ax.set_yticks(range(y_min, y_max + 1))
    ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False); ax.spines['left'].set_visible(False)

    plt.suptitle(f"{icon1} {icon2} 우리 아이 주간 시간표", fontsize=style_opts['title_size'], weight='bold', y=0.98)
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    return fig

# ---------------------------------------------------------
# 4. 초기 데이터 (색상 이름으로 저장)
# ---------------------------------------------------------
if 'data_1' not in st.session_state:
    st.session_state.data_1 = pd.DataFrame([
        {'활동명': '학교', '요일': '월,화,수,목,금', '시작시간': '09:00', '종료시간': '13:00', '배경색': '파스텔 블루', '글자색': '흰색'},
        {'활동명': '학원', '요일': '월,수,금', '시작시간': '14:00', '종료시간': '16:00', '배경색': '살구색', '글자색': '흰색'},
    ])

if 'data_2' not in st.session_state:
    st.session_state.data_2 = pd.DataFrame([
        {'활동명': '유치원', '요일': '월,화,수,목,금', '시작시간': '09:30', '종료시간': '13:30', '배경색': '개나리색', '글자색': '검정'},
        {'활동명': '태권도', '요일': '화,목', '시작시간': '15:00', '종료시간': '16:00', '배경색': '연보라', '글자색': '흰색'},
    ])

# ---------------------------------------------------------
# 5. UI 구성
# ---------------------------------------------------------
st.title("🎨 우리 아이 시간표 만들기 (오류 체크 & 색상 선택)")

# 사이드바 설정
with st.sidebar:
    st.header("설정 패널")
    s_title_size = st.slider("제목 크기", 15, 40, 24)
    s_bar_text_size = st.slider("내용 글자 크기", 5, 20, 10)
    st.markdown("---")
    col_s1, col_s2 = st.columns(2)
    with col_s1: icon1 = st.selectbox("첫째 아이콘", ["🐶", "👦", "🐰"], index=1)
    with col_s2: name1 = st.text_input("첫째 이름", value="하민")
    col_s3, col_s4 = st.columns(2)
    with col_s3: icon2 = st.selectbox("둘째 아이콘", ["🐥", "👧", "🐹"], index=1)
    with col_s4: name2 = st.text_input("둘째 이름", value="하율")

style_opts = {
    'title_size': s_title_size, 'axis_size': 14, 
    'bar_text_size': s_bar_text_size, 'time_text_size': 8, 'font_weight': 'bold'
}

# --- 메인 입력 탭 ---
tab1, tab2 = st.tabs([f"{icon1} {name1} 일정", f"{icon2} {name2} 일정"])

def render_editor(key_suffix, data_key):
    # [핵심] 색상을 드롭다운으로 선택할 수 있도록 설정
    edited_df = st.data_editor(
        st.session_state[data_key],
        column_config={
            "활동명": st.column_config.TextColumn("활동명", required=True),
            "요일": st.column_config.TextColumn("요일 (예: 월,수)", required=True),
            "시작시간": st.column_config.TextColumn("시작 (HH:MM)", required=True),
            "종료시간": st.column_config.TextColumn("종료 (HH:MM)", required=True),
            "배경색": st.column_config.SelectboxColumn("배경색", options=list(COLOR_MAP.keys()), required=True),
            "글자색": st.column_config.SelectboxColumn("글자색", options=list(TEXT_COLOR_MAP.keys()), required=True),
        },
        num_rows="dynamic",
        use_container_width=True,
        key=f"editor_{key_suffix}"
    )
    return edited_df

with tab1:
    st.info("💡 팁: '배경색' 열을 클릭하면 예쁜 색상 목록이 나옵니다.")
    df1_input = render_editor("child1", "data_1")

with tab2:
    st.info("💡 팁: '배경색' 열을 클릭하면 예쁜 색상 목록이 나옵니다.")
    df2_input = render_editor("child2", "data_2")

# --- 실행 버튼 및 결과 ---
st.divider()

if st.button("🔄 시간표 업데이트 및 오류 확인", type="primary", use_container_width=True):
    # 1. 로딩 표시 (새로고침 느낌)
    with st.spinner('시간표를 꼼꼼하게 확인하고 있어요...'):
        time.sleep(0.8) # 로딩 효과를 위해 살짝 멈춤
        
        # 2. 데이터 세션 저장
        st.session_state.data_1 = df1_input
        st.session_state.data_2 = df2_input
        
        # 3. 데이터 검사 및 변환
        df1_final, err1 = validate_and_process_data(df1_input)
        df2_final, err2 = validate_and_process_data(df2_input)
        
        # 4. 오류 메시지 출력
        if err1 or err2:
            st.error("앗! 입력값에 문제가 있어요. 아래 내용을 확인해주세요.")
            col_err1, col_err2 = st.columns(2)
            with col_err1:
                if err1:
                    st.warning(f"**[{name1}] 오류 목록**")
                    for e in err1: st.write(f"- {e}")
            with col_err2:
                if err2:
                    st.warning(f"**[{name2}] 오류 목록**")
                    for e in err2: st.write(f"- {e}")
        else:
            st.success("✅ 모든 데이터가 정상입니다! 시간표를 생성했습니다.")

        # 5. 그래프 그리기 (오류가 있어도 가능한 부분은 그리기)
        try:
            fig = draw_timetable(name1, icon1, df1_final, name2, icon2, df2_final, style_opts)
            st.pyplot(fig)
            
            # 다운로드 버튼
            buf = BytesIO()
            fig.savefig(buf, format="png", bbox_inches='tight', dpi=300)
            st.download_button(
                label="🖼️ 완성된 이미지 다운로드",
                data=buf.getvalue(),
                file_name="timetable_final.png",
                mime="image/png"
            )
        except Exception as e:
            st.error(f"그래프 생성 중 알 수 없는 오류가 발생했습니다: {e}")
