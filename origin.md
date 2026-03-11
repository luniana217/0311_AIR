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
    conditions = [
        (df['출발지연시간'] > 0) & (df['출발지연시간'] <= 30),
        (df['출발지연시간'] > 30) & (df['출발지연시간'] < 180),
        (df['출발지연시간'] >= 180)
    ]

@st.cache_data
def get_data():
    try:
        conn = mariadb.connect(**conn_params)
        cursor = conn.cursor()
        # 이미지의 컬럼 순서와 이름을 반영한 쿼리
        query = '''
        SELECT 
            `년도`, `월`, `일`, `요일`, 
            `항공사코드`, `항공편번호`, 
            `출발공항코드`, `도착지공항코드`,
            `출발지연시간`,
            `도착지연시간`,
            `비행거리`
        FROM `항공지연분석`
        ORDER BY `년도`, `월`
        LIMIT 5 
        '''
        cursor.execute(query)
        data = cursor.fetchall()
        # 컬럼명 리스트 업데이트
        df = pd.DataFrame(data, columns=['년도', '월', '일', '요일', '항공사코드', '항공편번호', 
            '출발공항코드', '도착지공항코드', '출발지연시간', '도착지연시간', '비행거리'])
        cursor.close()
        conn.close()

        for col in ['년도', '월', '출발지연시간']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return df.dropna(subset=['출발지연시간'])

        # 데이터 타입 변환
    except mariadb.Error as e:
        st.error(f"데이터베이스 연결 오류: {e}")
        return pd.DataFrame()
    return df
        
       
    
# ... (상단 데이터 로드 부분 생략)

st.set_page_config(layout="wide")
st.title(" 항공사별 지연 시간 구간 분석")

if not df.empty:
    st.success("데이터베이스 연결 및 데이터 로드 성공")
    
    # 1. 필터링 UI
    year_options = sorted(df['년도'].unique().tolist())
    selected_year = st.selectbox("분석할 년도를 선택하세요", options=year_options)
    
    year_df = df[df['년도'] == selected_year]
    
    airline_options = ["전체"] + sorted(year_df['항공사코드'].unique().tolist())
    selected_airline = st.selectbox("항공사를 선택하세요", options=airline_options)

    # 2. 데이터 필터링
    chart_df = year_df if selected_airline == '전체' else year_df[year_df['항공사코드'] == selected_airline]

    # 3. 지연율 계산 (월별)
    # 월별 전체 운항 횟수와 지연 횟수 집계
    delay_stats = chart_df.groupby('월').agg(
        전체운항 = ('항공편번호', 'count'),
        지연횟수 = ('is_delayed', 'sum')
    )
    # 지연율(%) 계산
    delay_stats['지연율'] = (delay_stats['지연횟수'] / delay_stats['전체운항']) * 100

    # 4. 시각화
    st.header(f" {selected_year}년 '{selected_airline}' 항공사 지연율 분석 (%)")
    
    # 바 차트로 지연율 표시
    st.bar_chart(delay_stats['지연율'], use_container_width=True)

    # 상세 데이터 표 (선택사항)
    with st.expander("상세 지연 통계 보기"):
        st.table(delay_stats)