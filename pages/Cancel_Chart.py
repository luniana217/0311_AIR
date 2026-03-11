import streamlit as st
import mariadb
import pandas as pd
import numpy as np

# 데이터베이스 연결 정보
conn_params = {
    "user": "root",
    "password": "1234",
    "host": "192.168.0.201",
    "database" : "db_to_air",
    "port" : int(3306)
}

def process_delay_bins(df):
    """지연 시간을 구간별로 나누는 함수"""
    conditions = [
        (df['출발지연시간'] > 0) & (df['출발지연시간'] <= 30),
        (df['출발지연시간'] > 30) & (df['출발지연시간'] < 180),
        (df['출발지연시간'] >= 180)
    ]
    choices = ['30분 이하', '3시간 미만', '3시간 이상']
    
    # 지연되지 않은 데이터는 '정상'으로 표시
    df['지연구간'] = np.select(conditions, choices, default='정상')
    return df

@st.cache_data
def get_data():
    try:
        conn = mariadb.connect(**conn_params)
        cursor = conn.cursor()
        query = '''
        SELECT 
            `년도`, `월`, `일`, `요일`, 
            `항공사코드`, `항공편번호`, 
            `출발공항코드`, `도착지공항코드`,
            `예정출발시간`,`출발지연시간`,
            `출발지연시간`,  `도착지연시간`,
            
        FROM `항공지연분석` 
        WHERE `년도` = {selected_year}
        ORDER BY `년도`, `월`
        '''
        cursor.execute(query)
        data = cursor.fetchall()
        
        df = pd.DataFrame(data, columns=[
            '년도', '월', '일', '요일', '항공사코드', '항공편번호', 
            '출발공항코드', '도착지공항코드', '출발지연시간', '도착지연시간', '비행거리'
        ])
        
        cursor.close()
        conn.close()

        # 데이터 타입 변환
        for col in ['년도', '월', '출발지연시간']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return df.dropna(subset=['출발지연시간'])

    except mariadb.Error as e:
        st.error(f"데이터베이스 연결 오류: {e}")
        return pd.DataFrame()


st.set_page_config(layout="wide")
st.title(" 항공사별 지연 시간 구간 분석")

selected_year = st.selectbox("분석할 년도를 선택하세요", options=[1987, 1988, 1989])

df = get_data(selected_year)



if not df.empty:
    st.success(f"{selected_year}년 데이터 로드 성공")
    # 지연구간 데이터 생성
    df = process_delay_bins(df)
    # 1. 필터링 UI
    airline_options = ["전체"] + sorted(df['항공사코드'].unique().tolist())
    airport_options = ["전체"] + sorted(df['공항코드'].unique().tolist())
    selected_airline = st.selectbox("항공사를 선택하세요", options=airline_options)
    selected_airport = st.selectbox("공항을 선택하세요", options=airport_options)
    
    chart_df = df if selected_airline == '전체' else df[df['항공사코드'] == selected_airline]
    delay_only_df = chart_df[chart_df['지연구간'] 1= '정상']
    
if not delay_only_df.empty:
    delay_stats = delay_only_df.groupby(['월','지연구간']).size().unstack(fill_value=0)
    all_months = pd.Index(range(1,13),name='월')
    delay_stats = delay_stats.reindex(all_months, fill_value=0)
    sort_order = ['30분 이하', '3시간 미만', '3시간 이상']
    available_cols = [ c for c in sort_order if c in delay_stats.columns]
    delay_stats = delay_stats[available_cols]

    st.header(f" {selected_year}년 '{selected_airline}' 지연 규모별 분포")
    st.line_chart(delay_stats, use_container_width=True)
else:
    st.info("해당 항공사의 지연 데이터가 없습니다")
  