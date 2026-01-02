import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import koreanize_matplotlib  # 한글 폰트 자동 설정
from io import BytesIO

# 페이지 설정
st.set_page_config(page_title="아이 학업 시간표 만들기", layout="wide")
st.title("🎨 우리 아이 학업 시간표 생성기")
st.markdown("요일과 과목을 입력하면 **예쁜 이미지**로 만들어 드려요!")

# ---------------------------------------------------------
# 함수: 시간표 이미지 생성
# ---------------------------------------------------------
def create_schedule_image(child_name, df, color_theme):
    # 그림 생성
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # 축 숨기기
    ax.axis('tight')
    ax.axis('off')
    
    # 테이블 그리기
    table = ax.table(cellText=df.values,
                     colLabels=df.columns,
                     rowLabels=df.index,
                     cellLoc='center',
                     loc='center')

    # 스타일 설정
    table.auto_set_font_size(False)
    table.set_fontsize(13)
    table.scale(1.2, 2.5)

    # 테마 색상 설정
    colors = {
        'Blue (하늘색)': '#87CEFA',
        'Yellow (노란색)': '#FFD700',
        'Pink (분홍색)': '#FFB6C1',
        'Green (연두색)': '#98FB98'
    }
    header_color = colors.get(color_theme, '#87CEFA')
    row_colors = ['#f9f9f9', '#ffffff']

    # 셀 꾸미기
    for (row, col), cell in table.get_celld().items():
        cell.set_edgecolor('white')
        cell.set_linewidth(2)
        
        if row == 0 or col == -1:
            cell.set_text_props(weight='bold', color='black', fontsize=14)
            cell.set_facecolor(header_color)
        else:
            cell.set_facecolor(row_colors[row % 2])

    plt.title(f"★ {child_name}의 주간 시간표 ★", fontsize=20, weight='bold', pad=20)
    return fig

# ---------------------------------------------------------
# 메인 화면 구성
# ---------------------------------------------------------

# 탭으로 아이 구분
tab1, tab2 = st.tabs(["첫째 아이", "둘째 아이"])

# --- [첫째 아이 탭] ---
with tab1:
    st.header("첫째 시간표 설정")
    col1, col2 = st.columns([1, 3])
    
    with col1:
        name_1 = st.text_input("이름 입력", value="첫째(하민)", key="name1")
        theme_1 = st.selectbox("테마 색상", ["Blue (하늘색)", "Yellow (노란색)", "Pink (분홍색)", "Green (연두색)"], key="theme1")

    with col2:
        st.info("👇 아래 표를 더블 클릭해서 내용을 수정하세요!")
        # 초기 데이터
        data_1 = {
            '월': ['국어', '수학', '영어', '과학', '체육'],
            '화': ['수학', '영어', '사회', '미술', '동아리'],
            '수': ['영어', '국어', '음악', '수학', '자습'],
            '목': ['과학', '체육', '역사', '도덕', '컴퓨터'],
            '금': ['사회', '미술', '국어', '영어', '학급회의']
        }
        index_1 = ['1교시', '2교시', '3교시', '4교시', '5교시']
        df_1 = pd.DataFrame(data_1, index=index_1)
        
        # 데이터 에디터 (사용자가 직접 수정 가능)
        edited_df_1 = st.data_editor(df_1, use_container_width=True, num_rows="dynamic", key="editor1")

    # 이미지 생성 버튼
    if st.button("📸 첫째 시간표 이미지 만들기", key="btn1"):
        fig = create_schedule_image(name_1, edited_df_1, theme_1)
        st.pyplot(fig)
        
        # 다운로드 버튼
        buf = BytesIO()
        fig.savefig(buf, format="png", bbox_inches='tight', dpi=300)
        st.download_button(
            label="💾 이미지로 저장하기",
            data=buf.getvalue(),
            file_name=f"{name_1}_시간표.png",
            mime="image/png"
        )

# --- [둘째 아이 탭] ---
with tab2:
    st.header("둘째 시간표 설정")
    col1, col2 = st.columns([1, 3])
    
    with col1:
        name_2 = st.text_input("이름 입력", value="둘째(하율)", key="name2")
        theme_2 = st.selectbox("테마 색상", ["Yellow (노란색)", "Blue (하늘색)", "Pink (분홍색)", "Green (연두색)"], key="theme2")

    with col2:
        st.info("👇 아래 표를 더블 클릭해서 내용을 수정하세요!")
        # 초기 데이터
        data_2 = {
            '월': ['피아노', '태권도', '간식', '숙제', '자유'],
            '화': ['미술', '태권도', '독서', '숙제', 'TV'],
            '수': ['피아노', '수영', '간식', '영어', '자유'],
            '목': ['미술', '태권도', '독서', '수학', '블록'],
            '금': ['키즈카페', '태권도', '영화', '파티', '취침']
        }
        index_2 = ['13:00', '14:00', '15:00', '16:00', '17:00']
        df_2 = pd.DataFrame(data_2, index=index_2)
        
        # 데이터 에디터
        edited_df_2 = st.data_editor(df_2, use_container_width=True, num_rows="dynamic", key="editor2")

    # 이미지 생성 버튼
    if st.button("📸 둘째 시간표 이미지 만들기", key="btn2"):
        fig = create_schedule_image(name_2, edited_df_2, theme_2)
        st.pyplot(fig)
        
        # 다운로드 버튼
        buf = BytesIO()
        fig.savefig(buf, format="png", bbox_inches='tight', dpi=300)
        st.download_button(
            label="💾 이미지로 저장하기",
            data=buf.getvalue(),
            file_name=f"{name_2}_시간표.png",
            mime="image/png"
        )
