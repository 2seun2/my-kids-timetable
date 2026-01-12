import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os
import time
from io import BytesIO

# ---------------------------------------------------------
# 1. 기본 설정 및 색상 프리셋 (여기에 색을 추가할 수 있어요)
# ---------------------------------------------------------
st.set_page_config(page_title="우리 아이 맞춤 시간표", layout="wide")

# 사용자가 선택할 배경색 목록 (이름 : 실제색상코드)
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
    '진한남색': '#3B4758',
    '초콜릿색': '#5D4037'
}

# 글자색 목록
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
# 2. 유틸리티 함수 (CSV 변환, 데이터 처리)
# ---------------------------------------------------------
def convert_df_to_csv(df):
    return df.to_csv(index=False).encode('utf-8-sig')

def validate_and_process_data(df):
    """ 데이터 검사 및 그래프용 변환 """
    expanded_data = []
    error_messages = []
    day_order = {'월': 0, '화': 1, '수': 2, '목': 3, '금': 4}
    
    for index, row in df.iterrows():
        # 데이터 가져오기 (없으면 기본값)
        activity = str(row.get('활동명', '')).strip()
        days_str = str(row.get('요일', '')).strip()
        start_str = str(row.get('시작시간', '')).strip()
        end_str = str(row.get('종료시간', '')).strip()
        
        # [수정] 사용자가 선택한 색상 이름 가져오기
        color_name = str(row.get('배경색', '그레이'))
        text_color_name = str(row.get('글자색', '흰색'))

        # 빈 줄 무시
        if not activity and not days_str and not start_str:
            continue
            
        # 필수 입력 확인
        if not activity or not days_str or not start_str or not end_str:
            error_messages.append(f"{index+1}번째 줄: 내용을 모두 채워주세요.")
            continue

        try:
            if ':' not in start_str or ':' not in end_str:
                raise ValueError("콜론(:) 없음")
                
            s_h, s_m = map(int, start_str.split(':'))
            e_h, e_m = map(int, end_str.split(':'))
            
            if not (0 <= s_h <= 23) or not (0 <= s_m <= 59) or \
               not (0 <= e_h <= 23) or not (0 <= e_m <= 59):
                error_messages.append(f"{index+1}번째 줄: 시간은 00:00~23:59 사이여야 합니다.")
                continue
                
            start_float = s_h + (s_m / 60)
            end_float = e_h + (e_m / 60)
            
            if end_float <= start_float:
                error_messages.append(f"{index+1}번째 줄: 종료 시간이 시작 시간보다 빨라요! ({activity})")
                continue

        except ValueError:
            error_messages.append(f"{index+1}번째 줄: 시간 형식 오류 (예: 14:00)")
            continue

        days = days_str.split(',')
        for day in days:
            day = day.strip()
            if day in day_order:
                # [수정] 이름으로 된 색상을 실제 코드로 변환해서 저장
                expanded_data.append({
                    '요일': day,
                    '요일인덱스': day_order[day],
                    '활동명': activity,
                    '시작': start_float,
                    '소요시간': end_float - start_float,
                    '배경색': COLOR_MAP.get(color_name, '#CCCCCC'), # 이름 -> #코드 변환
                    '글자색': TEXT_COLOR_MAP.get(text_color_name, 'white'), # 이름 -> 영어코드 변환
                    '시간텍스트': f"{start_str}~{end_str}"
                })
                
    return pd.DataFrame(expanded_data), error_messages

# ---------------------------------------------------------
# 3. 그래프 그리기 함수
# ---------------------------------------------------------
def draw_timetable(name1, icon1, df1, name2, icon2, df2, style_opts):
    fig, ax = plt.subplots(figsize=(14, 10))
    days_labels = ['월', '화', '수', '목', '금']
    y_min, y_max = 8, 22
    
    font_weight = style_opts['font_weight']
    
    # 배경 설정
    ax.grid(axis='y', linestyle='--', alpha=0.3, zorder=0)
    for x in range(len(days_labels) - 1):
        ax.axvline(x + 0.5, color='gray', linestyle='-', linewidth=1, alpha=0.3)
    
    bar_width = 0.4
    
    def plot_bars(df, offset):
        if df.empty: return
        x_positions = df['요일인덱스'] + offset
        
        # 배경색 적용
        bars = ax.bar(x=x_positions, height=df['소요시간'], bottom=df['시작'], 
                      color=df['배경색'], edgecolor='white', width=bar_width, zorder=3, alpha=0.95)
        
        for i, bar in enumerate(bars):
            row = df.iloc[i]
            # [수정] 글자색 적용 (사용자가 선택한 색)
            txt_color = row['글자색']
            
            # 활동명
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_y() + bar.get_height()/2 + 0.1, 
                    str(row['활동명']), ha='center', va='center', color=txt_color, 
                    weight=font_weight, fontsize=style_opts['bar_text_size'])
            
            # 시간 텍스트
            if row['소요시간'] >= 0.5:
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_y() + bar.get_height()/2 - 0.2, 
                        row['시간텍스트'], ha='center', va='center', color=txt_color, 
                        fontsize=style_opts['time_text_size'], alpha=0.8)

    plot_bars(df1, -0.21)
    plot_bars(df2, 0.21)

    # 축 설정
    ax.set_xticks(range(5))
    ax.set_xticklabels(days_labels, fontsize=style_opts['axis_size'], weight=font_weight)
    
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
# 4. 초기 데이터 (색상 이름으로 설정)
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

st.title("🎨 우리 아이 시간표 (색상 선택 + 저장)")

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
tab1, tab2 = st.tabs([f"{icon1} {name1} 일정 관리", f"{icon2} {name2} 일정 관리"])

def render_manager(key_suffix, data_key, child_name):
    col_edit, col_file = st.columns([4, 1])
    
    with col_file:
        st.write("📂 **불러오기**")
        uploaded_file = st.file_uploader("", type=['csv'], key=f"load_{key_suffix}")
        if uploaded_file is not None:
            try:
                df = pd.read_csv(uploaded_file)
                st.session_state[data_key] = df
                st.success("로드 완료!")
            except:
                st.error("오류 발생")

    with col_edit:
        st.subheader(f"📝 {child_name} 일정 편집")
        # [핵심] 배경색, 글자색을 '선택 상자'로 변경
        edited_df = st.data_editor(
            st.session_state[data_key],
            column_config={
                "활동명": st.column_config.TextColumn("활동명", required=True),
                "요일": st.column_config.TextColumn("요일 (예: 월,수)", required=True),
                "시작시간": st.column_config.TextColumn("시작 (HH:MM)", required=True),
                "종료시간": st.column_config.TextColumn("종료 (HH:MM)", required=True),
                "배경색": st.column_config.SelectboxColumn(
                    "배경색", 
                    options=list(COLOR_MAP.keys()), # 색상 이름 목록 보여주기
                    required=True
                ),
                "글자색": st.column_config.SelectboxColumn(
                    "글자색", 
                    options=list(TEXT_COLOR_MAP.keys()), # 흰색/검정 목록 보여주기
                    required=True
                ),
            },
            num_rows="dynamic",
            use_container_width=True,
            key=f"editor_{key_suffix}"
        )
        
        csv_data = convert_df_to_csv(edited_df)
        st.download_button(
            label=f"💾 {child_name} 데이터 저장 (CSV)",
            data=csv_data,
            file_name=f"{child_name}_timetable.csv",
            mime='text/csv',
            key=f"save_{key_suffix}"
        )
    
    return edited_df

with tab1:
    df1_input = render_manager("child1", "data_1", name1)

with tab2:
    df2_input = render_manager("child2", "data_2", name2)

# --- 실행 버튼 및 결과 ---
st.divider()

if st.button("🔄 시간표 업데이트 및 오류 확인", type="primary", use_container_width=True):
    with st.spinner('시간표를 생성하고 있어요...'):
        time.sleep(0.5) 
        
        st.session_state.data_1 = df1_input
        st.session_state.data_2 = df2_input
        
        df1_final, err1 = validate_and_process_data(df1_input)
        df2_final, err2 = validate_and_process_data(df2_input)
        
        if err1 or err2:
            st.error("입력값에 오류가 있습니다.")
            c1, c2 = st.columns(2)
            with c1:
                if err1: 
                    st.warning(f"{name1} 오류:")
                    for e in err1: st.write(f"- {e}")
            with c2:
                if err2: 
                    st.warning(f"{name2} 오류:")
                    for e in err2: st.write(f"- {e}")
        else:
            st.success("✅ 오류 없이 완벽합니다!")

        try:
            fig = draw_timetable(name1, icon1, df1_final, name2, icon2, df2_final, style_opts)
            st.pyplot(fig)
            
            buf = BytesIO()
            fig.savefig(buf, format="png", bbox_inches='tight', dpi=300)
            st.download_button(
                label="🖼️ 시간표 이미지 다운로드",
                data=buf.getvalue(),
                file_name="timetable_final.png",
                mime="image/png"
            )
        except Exception as e:
            st.error(f"오류 발생: {e}")
