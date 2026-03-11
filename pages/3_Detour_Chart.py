import streamlit as st
import mariadb
import pandas as pd

conn_params = {
  "user": "root",
  "password": "1234",
  "host": "192.168.0.201",
  "database" : "db_to_air",
  "port" : int(3306)
}

@st.cache_data
def get_data():
    """데이터베이스에서 공항 데이터를 가져옵니다."""
    try:
        conn = mariadb.connect(**conn_params)
        cursor = conn.cursor()
        query= '''
        select 
        d.`년도`, 
        d.`월`, 
        d.`일`, 
        d.`요일`, 
        d.`항공사코드`,
        d.`항공편번호`,
        d.`출발공항코드`,
        d.`도착지공항코드`,
        d.`비행거리`
        FROM `항공우회분석` AS d
        
        ORDER BY d.`년도`,d.`월`
        '''
        cursor.execute(query)
        data = cursor.fetchall()
        df = pd.DataFrame(data, columns=['년도', '월', '일', '요일','항공사코드','항공편번호','출발공항코드','도착지공항코드','비행거리'])
        cursor.close()
        conn.close()

        df['년도'] = pd.to_numeric(df['년도'], errors='coerce')
        df['비행거리'] = pd.to_numeric(df['비행거리'], errors='coerce')
        return df

    except mariadb.Error as e:
        st.error(f"데이터베이스 연결 오류:{e}")
        st.info("왼쪽 사이드바의 'DB 연결 정보'를 올바르게 입력했는지 확인하세요.")
        return pd.DataFrame()


st.set_page_config(layout="wide")

st.title("항공사별 우회 분석")

df = get_data()
if not df.empty:
    df['년도'] = pd.to_numeric(df['년도'], errors='coerce')
    df['비행거리'] = pd.to_numeric(df['비행거리'], errors='coerce')
    df['월'] = pd.to_numeric(df['월'], errors='coerce')
    # 숫자가 아닌 값이 들어있던 행은 삭제
    df = df.dropna(subset=['비행거리', '월'])
if df is not None and not df.empty:
    st.success("데이터베이스 연결 및 데이터 로드 성공")
    options = ["전체"] + sorted(df['항공사코드'].unique().tolist())
    selected_airline = st.selectbox(
        label="항공사를 선택하세요",
        options=options,
        index=0
    )
    year_options = sorted(df['년도'].unique().tolist())
    selected_year = st.selectbox("분석할 년도를 선택하세요", options=year_options)
    year_df = df[df['년도'] == selected_year]
    airline_options = ["전체"] + sorted(year_df['항공사코드'].unique().tolist())
    
    st.header(f" '{selected_airline}' 항공사별 우회 데이터")
    
    chart_df = year_df if selected_airline == '전체' else year_df[year_df['항공사코드'] == selected_airline]
    detour_count = chart_df.groupby('월').size().reset_index(name='우회횟수')

    
    detour_data = chart_df.groupby('월').size()
    st.bar_chart(detour_data, use_container_width=True)
    # detour = chart_df.set_index('월').groupby('월')['비행거리'].mean()
else:
    st.warning("데이터를 불러오지 못했습니다")