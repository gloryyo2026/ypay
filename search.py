import streamlit as st
import requests
import pandas as pd

# 페이지 설정
st.set_page_config(
    page_title="용인 와이페이 가맹점 조회",
    page_icon="💳",
    layout="wide"
)

# API 설정
API_URL = "https://apis.data.go.kr/4050000/ypay/getYpay"
API_KEY = "2bdb968b4fc49a9424355c554e3912113decf421c74fb27b55a3efc6015de814"

# 용인시 지역 목록 (구/읍 -> 동/면 단위)
YONGIN_REGIONS = {
    "처인구": [
        "김량장동", "남사읍", "원삼면", "백암면", "양지면", 
        "포곡읍", "모현읍", "역북동", "마평동", "유방동",
        "유림동", "삼가동", "고림동", "운학동", "호계동"
    ],
    "기흥구": [
        "구갈동", "상갈동", "하갈동", "공세동", "보정동",
        "신갈동", "영덕동", "중동", "서천동", "동백동",
        "지곡동", "마북동", "청덕동"
    ],
    "수지구": [
        "풍덕천동", "신봉동", "죽전동", "동천동", "상현동",
        "성복동", "고기동"
    ],
    "포곡읍": [
        "전체포곡읍"
    ]
}

def get_ypay_data(service_key, page_no=1, num_of_rows=1000, fld=None, aflt_nm=None):
    """API를 호출하여 가맹점 데이터를 가져오는 함수"""
    params = {
        'serviceKey': service_key,
        'pageNo': page_no,
        'numOfRows': num_of_rows
    }
    
    if fld:
        params['fld'] = fld
    if aflt_nm:
        params['aflt_nm'] = aflt_nm
    
    try:
        response = requests.get(API_URL, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('resultCode') == 0:
                return data
            else:
                st.error(f"API 오류: {data.get('resultMsg', '알 수 없는 오류')}")
                return None
        else:
            st.error(f"HTTP 오류: {response.status_code}")
            return None
            
    except requests.exceptions.Timeout:
        st.error("요청 시간이 초과되었습니다. 다시 시도해주세요.")
        return None
    except Exception as e:
        st.error(f"오류 발생: {str(e)}")
        return None

def check_merchant_exists(service_key, merchant_name):
    """특정 식당이 가맹점인지 확인"""
    data = get_ypay_data(service_key, aflt_nm=merchant_name)
    
    if data and 'items' in data:
        return data['items'], data.get('totalCount', 0)
    return [], 0

def get_merchants_by_region(service_key, region):
    """특정 지역의 가맹점 목록 조회"""
    all_items = []
    page = 1
    
    with st.spinner(f'{region} 지역의 가맹점을 검색 중입니다...'):
        while True:
            data = get_ypay_data(service_key, page_no=page, num_of_rows=1000)
            
            if data and 'items' in data:
                filtered_items = [
                    item for item in data['items'] 
                    if region in item.get('addr', '')
                ]
                all_items.extend(filtered_items)
                
                total_count = data.get('totalCount', 0)
                current_count = page * 1000
                
                if current_count >= total_count:
                    break
                    
                page += 1
            else:
                break
    
    return all_items

# 메인 UI
st.title("💳 용인시 와이페이카드 가맹점 조회 서비스")
st.markdown("---")

# API 키 설정 (코드에 직접 포함)
service_key = API_KEY

# 사이드바
with st.sidebar:
    st.header("⚙️ 설정")
    st.success("✅ API 키가 설정되었습니다")
    
    st.markdown("---")
    st.markdown("""
    ### 📌 사용 방법
    1. 원하는 기능을 선택하세요
    2. 조회 버튼을 클릭하세요
    
    ### ℹ️ 안내
    - 데이터 출처: 공공데이터포털
    - 데이터는 연 2회 갱신됩니다
    """)

# 탭 생성
tab1, tab2 = st.tabs(["🔍 가맹점 확인", "📍 지역별 조회"])

# 탭 1: 가맹점 확인
with tab1:
    st.header("가맹점 확인")
    st.write("식당명을 입력하여 와이페이 가맹점인지 확인할 수 있습니다.")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        merchant_input = st.text_input(
            "식당명 입력",
            placeholder="예: 맛있는집",
            key="merchant_name"
        )
    with col2:
        st.write("")
        st.write("")
        search_btn = st.button("🔍 조회", key="search_merchant", use_container_width=True)
    
    if search_btn and merchant_input:
        items, total_count = check_merchant_exists(service_key, merchant_input)
        
        if total_count > 0:
            st.success(f"✅ '{merchant_input}'로 검색된 가맹점이 {total_count}개 있습니다.")
            
            df = pd.DataFrame(items)
            
            column_mapping = {
                'no': '번호',
                'fld': '분야',
                'subcls': '소분류',
                'aflt_nm': '가맹점명',
                'zip': '우편번호',
                'addr': '주소'
            }
            df = df.rename(columns=column_mapping)
            
            display_columns = ['가맹점명', '분야', '소분류', '주소', '우편번호']
            df_display = df[display_columns]
            
            st.dataframe(df_display, use_container_width=True, hide_index=True)
            
            csv = df_display.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📥 CSV 다운로드",
                data=csv,
                file_name=f"ypay_가맹점_{merchant_input}.csv",
                mime="text/csv"
            )
        else:
            st.error(f"❌ '{merchant_input}'로 검색된 가맹점이 없습니다.")
    
    elif search_btn and not merchant_input:
        st.warning("⚠️ 식당명을 입력해주세요.")

# 탭 2: 지역별 조회
with tab2:
    st.header("지역별 가맹점 조회")
    st.write("용인시의 특정 지역을 선택하여 해당 지역의 가맹점 목록을 확인할 수 있습니다.")
    
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        selected_gu = st.selectbox(
            "구/읍 선택",
            options=list(YONGIN_REGIONS.keys()),
            key="gu_select"
        )
    with col2:
        selected_dong = st.selectbox(
            "동/면 선택",
            options=YONGIN_REGIONS[selected_gu],
            key="dong_select"
        )
    with col3:
        st.write("")
        st.write("")
        region_search_btn = st.button("🔍 조회", key="search_region", use_container_width=True)
    
    if region_search_btn:
        if selected_dong == "전체포곡읍":
            search_region = "포곡읍"
        else:
            search_region = selected_dong
            
        items = get_merchants_by_region(service_key, search_region)
        
        if items:
            st.success(f"✅ {selected_gu} {selected_dong} 지역의 가맹점 {len(items)}개를 찾았습니다.")
            
            df = pd.DataFrame(items)
            
            column_mapping = {
                'no': '번호',
                'fld': '분야',
                'subcls': '소분류',
                'aflt_nm': '가맹점명',
                'zip': '우편번호',
                'addr': '주소'
            }
            df = df.rename(columns=column_mapping)
            
            st.subheader("📊 분야별 통계")
            fld_counts = df['분야'].value_counts()
            col1, col2 = st.columns(2)
            
            with col1:
                st.bar_chart(fld_counts)
            
            with col2:
                for fld, count in fld_counts.items():
                    st.metric(label=fld, value=f"{count}개")
            
            st.markdown("---")
            
            st.subheader("🔍 분야별 필터링")
            selected_fld = st.multiselect(
                "분야 선택 (다중 선택 가능)",
                options=['전체'] + list(df['분야'].unique()),
                default=['전체']
            )
            
            if '전체' not in selected_fld and selected_fld:
                df_filtered = df[df['분야'].isin(selected_fld)]
            else:
                df_filtered = df
            
            display_columns = ['가맹점명', '분야', '소분류', '주소', '우편번호']
            df_display = df_filtered[display_columns]
            
            st.write(f"**총 {len(df_filtered)}개의 가맹점**")
            st.dataframe(df_display, use_container_width=True, hide_index=True)
            
            csv = df_display.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📥 CSV 다운로드",
                data=csv,
                file_name=f"ypay_가맹점_{selected_gu}_{selected_dong}.csv",
                mime="text/csv"
            )
        else:
            st.error(f"❌ {selected_gu} {selected_dong} 지역의 가맹점을 찾을 수 없습니다.")

# 푸터
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray; font-size: 0.9em;'>
    <p>📊 데이터 출처: 공공데이터포털 - 용인시 와이페이카드 가맹점 정보</p>
    <p>💡 데이터 갱신 주기: 연 2회</p>
</div>
""", unsafe_allow_html=True)