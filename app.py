import streamlit as st
import requests
from bs4 import BeautifulSoup
import yfinance as yf
from datetime import datetime
import json
import os
import datetime

# -------------------------------------------------------------
# 0. 데이터 영구 저장용 파일 및 함수 제어
# -------------------------------------------------------------
SCHEDULE_FILE = "schedule_data.json"
LEAVE_FILE = "leave_data.json"
CALENDAR_FILE = "calendar_schedule.json"

def load_data(file_path):
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_data(file_path, data):
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception:
        pass

# -------------------------------------------------------------
# 1. Streamlit 페이지 설정 (가로 모드)
# -------------------------------------------------------------
st.set_page_config(
    page_title="🌊 낄낄낄",
    layout="wide"
)

# -------------------------------------------------------------
# 2. 파란 오션뷰 & 잔파도 애니메이션 및 컴포넌트 디자인 CSS
# -------------------------------------------------------------
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(180deg, #0284c7 0%, #0369a1 40%, #075985 70%, #0c4a6e 100%) !important;
        background-attachment: fixed !important;
    }
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 7rem !important;
        max-width: 1400px !important;
    }
    .stApp::after {
        content: "";
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        height: 90px;
        background: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1440 320"><path fill="rgba(255,255,255,0.18)" d="M0,224L48,213.3C96,203,192,181,288,181.3C384,181,480,203,576,224C672,245,768,267,864,256C960,245,1056,203,1152,186.7C1248,171,1344,181,1392,186.7L1440,192L1440,320L1392,320C1344,320,1248,320,1152,320C1056,320,960,320,864,320C768,320,672,320,576,320C480,320,384,320,288,320C192,320,96,320,48,320L0,320Z"></path></svg>') repeat-x;
        background-size: 1440px 90px;
        animation: waveAnim 12s linear infinite;
        pointer-events: none;
        z-index: 10;
    }
    @keyframes waveAnim {
        0% { background-position-x: 0; }
        100% { background-position-x: 1440px; }
    }
    .main-title {
        text-align: center;
        color: #ffffff !important;
        font-size: 32px;
        font-weight: 800;
        margin-bottom: 30px;
        text-shadow: 0 4px 12px rgba(2, 132, 199, 0.5);
    }
    .ocean-card {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 20px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 12px 30px rgba(7, 89, 133, 0.25);
        backdrop-filter: blur(10px);
        border: 2px solid #bae6fd;
    }
    .news-item {
        padding: 6px 0;
        border-bottom: 1px solid #f0f9ff;
        font-size: 13px;
        color: #0f172a;
    }
    .news-item:last-child { border-bottom: none; }
    .news-num {
        font-weight: 700;
        color: #0284c7;
        background: #e0f2fe;
        padding: 2px 6px;
        border-radius: 6px;
        margin-right: 6px;
        font-size: 11px;
    }
    a.card-link {
        color: #0f172a !important;
        text-decoration: none;
        transition: all 0.2s;
    }
    a.card-link:hover {
        color: #0284c7 !important;
        font-weight: 600;
    }
    .stock-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 8px 0;
        border-bottom: 1px solid #f0f9ff;
    }
    .stock-row:last-child { border-bottom: none; }
    .stock-name { font-weight: 700; color: #0f172a; font-size: 13px; }
    .stock-val { font-weight: 700; color: #0369a1; font-size: 14px; }
    .stock-up {
        font-weight: 700;
        color: #e11d48;
        background: #ffe4e6;
        padding: 2px 8px;
        border-radius: 20px;
        font-size: 12px;
        border: 1px solid #fecdd3;
    }
    .weather-box {
        display: flex;
        flex-direction: column;
        gap: 5px;
        background: linear-gradient(135deg, #e0f2fe 0%, #bae6fd 100%);
        padding: 12px 15px;
        border-radius: 14px;
    }
    .weather-date { font-size: 13px; font-weight: 700; color: #0369a1; }
    .weather-info { font-size: 15px; font-weight: 800; color: #0f172a; }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# 3. 데이터 수집 로직 (캐싱 적용)
# -------------------------------------------------------------
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

@st.cache_data(ttl=600)
def fetch_weather():
    weather_link = "https://search.naver.com/search.naver?query=부산날씨"
    weather_temp, weather_status = "수집 중", "맑음"
    try:
        res_w = requests.get(weather_link, headers=headers, timeout=3)
        soup_w = BeautifulSoup(res_w.text, "html.parser")
        temp_tag = soup_w.select_one(".temperature_text")
        status_tag = soup_w.select_one(".weather.before_slash") or soup_w.select_one(".txt_weather")
        if temp_tag: weather_temp = temp_tag.get_text().replace("현재 온도", "").strip()
        if status_tag: weather_status = status_tag.get_text().strip()
    except Exception:
        weather_temp = "정보 없음"
    return weather_link, weather_temp, weather_status

@st.cache_data(ttl=600)
def fetch_news(site_url, site_tag):
    news_list = []
    try:
        res_news = requests.get(site_url, headers=headers, timeout=3)
        res_news.encoding = 'utf-8'
        soup_news = BeautifulSoup(res_news.text, "html.parser")
        titles = soup_news.select(site_tag)
        count, seen = 0, set()
        for t in titles:
            txt = t.get_text().strip()
            link = site_url
            if t.name == 'a' and t.has_attr('href'): link = t['href']
            elif t.find_parent('a') and t.find_parent('a').has_attr('href'): link = t.find_parent('a')['href']
            if link.startswith('/'): link = site_url.rstrip('/') + link
            
            if len(txt) > 8 and txt not in seen:
                seen.add(txt)
                count += 1
                news_list.append({"txt": txt, "link": link})
                if count == 5: break
    except Exception:
        pass
    return news_list

@st.cache_data(ttl=300)
def fetch_market_data():
    stock_data, exchange_rates, kr_gainers, us_gainers = [], [], [], []
    try:
        stock_url = "https://finance.naver.com/sise/"
        res = requests.get(stock_url, headers=headers, timeout=3)
        res.encoding = 'euc-kr'
        soup_stock = BeautifulSoup(res.text, "html.parser")
        kospi = soup_stock.select_one("#KOSPI_now").get_text().strip()
        kosdaq = soup_stock.select_one("#KOSDAQ_now").get_text().strip()
        stock_data.append({"name": "코스피 (KOSPI)", "val": kospi, "link": "https://finance.naver.com/sise/sise_index.naver?code=KOSPI"})
        stock_data.append({"name": "코스닥 (KOSDAQ)", "val": kosdaq, "link": "https://finance.naver.com/sise/sise_index.naver?code=KOSDAQ"})
    except Exception:
        stock_data.append({"name": "국내 증시", "val": "수집 실패", "link": "#"})

    try:
        dow_val = round(yf.Ticker("^DJI").fast_info['lastPrice'], 2)
        nasdaq_val = round(yf.Ticker("^IXIC").fast_info['lastPrice'], 2)
        usd_val = round(yf.Ticker("KRW=X").fast_info['lastPrice'], 2)
        jpy_val = round(yf.Ticker("JPYKRW=X").fast_info['lastPrice'] * 100, 2)

        stock_data.append({"name": "다우 산업 (DOW)", "val": f"{dow_val:,.2f}", "link": "https://finance.yahoo.com/quote/^DJI"})
        stock_data.append({"name": "나스닥 종합 (NASDAQ)", "val": f"{nasdaq_val:,.2f}", "link": "https://finance.yahoo.com/quote/^IXIC"})

        exchange_rates.append({"name": "원/달러 (USD)", "val": f"{usd_val:,.2f} 원", "link": "https://finance.naver.com/marketindex/exchangeDetail.naver?marketindexCd=FX_USDKRW"})
        exchange_rates.append({"name": "원/100엔 (JPY)", "val": f"{jpy_val:,.2f} 원", "link": "https://finance.naver.com/marketindex/exchangeDetail.naver?marketindexCd=FX_JPYKRW"})
    except Exception:
        exchange_rates.append({"name": "환율 정보", "val": "수집 실패", "link": "#"})

    try:
        res_rise = requests.get("https://finance.naver.com/sise/sise_rise.naver", headers=headers, timeout=3)
        res_rise.encoding = 'euc-kr'
        soup_rise = BeautifulSoup(res_rise.text, "html.parser")
        for row in soup_rise.select("table.type_2 tr"):
            title_tag = row.select_one("a.tltle")
            tah_spans = row.select("td.number span.tah")
            if title_tag and tah_spans:
                rate_text = tah_spans[-1].get_text().strip()
                if not rate_text.startswith(("-", "+")): rate_text = "+" + rate_text
                kr_gainers.append({"name": title_tag.get_text().strip(), "rate": rate_text, "link": "https://finance.naver.com" + title_tag['href']})
                if len(kr_gainers) == 5: break
    except Exception:
        kr_gainers = [{"name": "수집 오류", "rate": "-", "link": "#"}]

    try:
        temp_us = []
        for sym in ["AAPL", "NVDA", "TSLA", "MSFT", "AMZN", "GOOGL", "AMD", "META"]:
            info = yf.Ticker(sym).fast_info
            pct = ((info['lastPrice'] - info['previousClose']) / info['previousClose']) * 100
            temp_us.append({"name": sym, "rate": pct, "link": f"https://yahoo.com/quote/{sym}"})
        temp_us.sort(key=lambda x: x["rate"], reverse=True)
        for item in temp_us[:5]:
            rate_str = f"+{item['rate']:.2f}%" if item['rate'] > 0 else f"{item['rate']:.2f}%"
            us_gainers.append({"name": item["name"], "rate": rate_str, "link": item["link"]})
    except Exception:
        us_gainers = [{"name": "수집 오류", "rate": "-", "link": "#"}]

    return stock_data, exchange_rates, kr_gainers, us_gainers

weather_link, weather_temp, weather_status = fetch_weather()
stock_data, exchange_rates, kr_gainers, us_gainers = fetch_market_data()

now = datetime.datetime.now()
days = ["월", "화", "수", "목", "금", "토", "일"]
date_str = f"{now.year}년 {now.month}월 {now.day}일 ({days[now.weekday()]})"

sites = [
    {"name": "YTN 뉴스", "url": "https://www.ytn.co.kr/", "tag": ".title"},
    {"name": "SBS 뉴스", "url": "https://news.sbs.co.kr/news/newsMain.do", "tag": "strong.sub"},
    {"name": "KBS 뉴스", "url": "https://news.kbs.co.kr/news/pc/main/main.html", "tag": ".title, .news_title, div.box_content, p.title"}
]

# -------------------------------------------------------------
# 4. Streamlit 화면 레이아웃 출력 (3열 구조)
# -------------------------------------------------------------
st.markdown('<div class="main-title">🌊 낄낄낄 </div>', unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

# =============================================================
# [1열] 날씨 및 뉴스 영역
# =============================================================
with col1:
    weather_html = f"""
    <div class="ocean-card">
        <h3 style="color: #0284c7; font-size: 16px; font-weight: 700; border-bottom: 2px dashed #bae6fd; padding-bottom: 8px; margin-top: 0; margin-bottom: 12px;"><a href="{weather_link}" target="_blank" style="color:#0284c7; text-decoration:none;">🌤️ 부산 날씨 & 날짜 🔗</a></h3>
        <a href="{weather_link}" target="_blank" style="text-decoration:none;">
            <div class="weather-box">
                <div class="weather-date">📅 {date_str}</div>
                <div class="weather-info">⚓ 부산 {weather_temp} ({weather_status})</div>
            </div>
        </a>
    </div>
    """
    st.markdown(weather_html, unsafe_allow_html=True)

    for site in sites:
        news_list = fetch_news(site["url"], site["tag"])
        news_html = f'<div class="ocean-card"><h3 style="color: #0284c7; font-size: 16px; font-weight: 700; border-bottom: 2px dashed #bae6fd; padding-bottom: 8px; margin-top: 0; margin-bottom: 12px;">⚓ <a href="{site["url"]}" target="_blank" style="color:#0284c7; text-decoration:none;">{site["name"]} 🔗</a></h3>'
        if news_list:
            for idx, item in enumerate(news_list, 1):
                news_html += f'<div class="news-item"><span class="news-num">{idx}</span><a href="{item["link"]}" target="_blank" class="card-link">{item["txt"]}</a></div>'
        else:
            news_html += '<div class="news-item">뉴스를 불러올 수 없습니다.</div>'
        news_html += '</div>'
        st.markdown(news_html, unsafe_allow_html=True)

# =============================================================
# [2열] 환율 및 증시 영역
# =============================================================
with col2:
    ex_html = '<div class="ocean-card"><h3 style="color:#0d9488 !important; font-size: 16px; font-weight: 700; border-bottom: 2px dashed #bae6fd; padding-bottom: 8px; margin-top: 0; margin-bottom: 12px;">💱 실시간 주요 환율</h3>'
    for ex in exchange_rates:
        ex_html += f"""
        <div class="stock-row">
            <a href="{ex['link']}" target="_blank" class="stock-name" style="text-decoration:none;">{ex['name']}</a>
            <a href="{ex['link']}" target="_blank" class="stock-val" style="color:#0d9488; text-decoration:none;">{ex['val']}</a>
        </div>"""
    ex_html += '</div>'
    st.markdown(ex_html, unsafe_allow_html=True)

    idx_html = '<div class="ocean-card"><h3 style="color: #0284c7; font-size: 16px; font-weight: 700; border-bottom: 2px dashed #bae6fd; padding-bottom: 8px; margin-top: 0; margin-bottom: 12px;">📊 실시간 주요 지수</h3>'
    for idx in stock_data:
        idx_html += f"""
        <div class="stock-row">
            <a href="{idx['link']}" target="_blank" class="stock-name" style="text-decoration:none;">{idx['name']}</a>
            <span class="stock-val">{idx['val']}</span>
        </div>"""
    idx_html += '</div>'
    st.markdown(idx_html, unsafe_allow_html=True)

    kr_html = '<div class="ocean-card"><h3 style="color:#e11d48 !important; font-size: 16px; font-weight: 700; border-bottom: 2px dashed #bae6fd; padding-bottom: 8px; margin-top: 0; margin-bottom: 12px;">🔥 국내 급등 종목 Top 5</h3>'
    for item in kr_gainers:
        kr_html += f"""
        <div class="stock-row">
            <a href="{item['link']}" target="_blank" class="stock-name" style="text-decoration:none;">{item['name']}</a>
            <span class="stock-up">{item['rate']}</span>
        </div>"""
    kr_html += '</div>'
    st.markdown(kr_html, unsafe_allow_html=True)

    us_html = '<div class="ocean-card"><h3 style="color: #0284c7; font-size: 16px; font-weight: 700; border-bottom: 2px dashed #bae6fd; padding-bottom: 8px; margin-top: 0; margin-bottom: 12px;">🚀 미국 주요 종목 상승 Top 5</h3>'
    for item in us_gainers:
        us_html += f"""
        <div class="stock-row">
            <a href="{item['link']}" target="_blank" class="stock-name" style="text-decoration:none;">{item['name']}</a>
            <span class="stock-up">{item['rate']}</span>
        </div>"""
    us_html += '</div>'
    st.markdown(us_html, unsafe_allow_html=True)

# =============================================================
# [3열] 스케줄 및 연차 기간 지정 관리 영역
# =============================================================
with col3:
    if "schedule_list" not in st.session_state:
        st.session_state.schedule_list = load_data(SCHEDULE_FILE)
    if "leave_list" not in st.session_state:
        st.session_state.leave_list = load_data(LEAVE_FILE)

    # 🔗 삭제 동작 처리 (HTML 링크 방식)
    if "del_task" in st.query_params:
        try:
            st.session_state.schedule_list.pop(int(st.query_params["del_task"]))
            save_data(SCHEDULE_FILE, st.session_state.schedule_list)
        except:
            pass
        st.query_params.clear()
        st.rerun()
        
    if "del_leave" in st.query_params:
        try:
            st.session_state.leave_list.pop(int(st.query_params["del_leave"]))
            save_data(LEAVE_FILE, st.session_state.leave_list)
        except:
            pass
        st.query_params.clear()
        st.rerun()

    # 1. 📅 준엔지니어링 스케줄 관리 카드 (기간 선택형)
    st.markdown('<div style="background: rgba(255, 255, 255, 0.95); border-radius: 20px; padding: 20px; margin-bottom: 20px; box-shadow: 0 12px 30px rgba(7, 89, 133, 0.25); backdrop-filter: blur(10px); border: 2px solid #bae6fd;"><h3 style="color: #0284c7; font-size: 16px; font-weight: 700; border-bottom: 2px dashed #bae6fd; padding-bottom: 8px; margin-top: 0; margin-bottom: 12px;">📅 준엔지니어링 스케줄 관리</h3>', unsafe_allow_html=True)
    
    # 날짜 범위 선택 (튜플 형태로 반환됨: (시작일, 종료일) 혹은 단일 선택 시 처리)
    task_dates = st.date_input("스케줄 날짜 기간 선택", value=(datetime.date.today(), datetime.date.today()), key="task_date_range")
    new_task = st.text_input("일정 내용 입력", placeholder="예: 북구 하수관로 조사", key="task_input_box")

    if st.button("스케줄 추가", key="btn_add_task", use_container_width=True):
        if new_task.strip():
            # 날짜 범위가 정상적으로 지정되었는지 확인
            if isinstance(task_dates, tuple) and len(task_dates) == 2:
                start_d, end_d = task_dates
                if start_d and end_d:
                    date_str = f"{start_d} ~ {end_d}" if start_d != end_d else f"{start_d}"
                else:
                    date_str = str(start_d) if start_d else str(datetime.date.today())
            else:
                date_str = str(task_dates)

            entry = {"date": date_str, "content": new_task.strip()}
            st.session_state.schedule_list.append(entry)
            # 날짜순 정렬
            st.session_state.schedule_list = sorted(st.session_state.schedule_list, key=lambda x: x["date"])
            save_data(SCHEDULE_FILE, st.session_state.schedule_list)
            st.rerun()

    st.markdown("<div style='margin-bottom: 12px;'></div>", unsafe_allow_html=True)

    task_html = ""
    if not st.session_state.schedule_list:
        task_html = '<div style="font-size:13px; color:#64748b; text-align: center; padding: 10px;">등록된 일정이 없습니다.</div>'
    else:
        for idx, item in enumerate(st.session_state.schedule_list):
            # 딕셔너리 구조(기간+내용)인지 문자열 형태인지 호환 처리
            if isinstance(item, dict):
                d_part = item.get("date", "")
                c_part = item.get("content", "")
                display_text = f"[{d_part}] {c_part}"
            else:
                display_text = str(item)

            task_html += f'<div style="display: flex; justify-content: space-between; align-items: center; padding: 10px 8px; border-bottom: 1px solid #f1f5f9;"><span style="font-size: 14px; color: #0f172a; font-weight: 600; word-break: break-all; margin-right: 10px;">• {display_text}</span><a href="?del_task={idx}" target="_self" style="background: #fee2e2; color: #ef4444; border-radius: 6px; padding: 4px 10px; font-size: 12px; font-weight: bold; text-decoration: none; border: 1px solid #fca5a5; white-space: nowrap;">✕ 삭제</a></div>'

    st.markdown(f'<div style="background: #ffffff; border-radius: 12px; border: 1px solid #cbd5e1; padding: 4px 12px; max-height: 250px; overflow-y: auto;">{task_html}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


    # 2. 🏖️ 인원 연차 사용 현황 카드 (기간 선택형)
    st.markdown('<div style="background: rgba(255, 255, 255, 0.95); border-radius: 20px; padding: 20px; margin-bottom: 20px; box-shadow: 0 12px 30px rgba(7, 89, 133, 0.25); backdrop-filter: blur(10px); border: 2px solid #bae6fd;"><h3 style="color: #0d9488 !important; font-size: 16px; font-weight: 700; border-bottom: 2px dashed #bae6fd; padding-bottom: 8px; margin-top: 0; margin-bottom: 12px;">🏖️ 인원 연차 사용 현황</h3>', unsafe_allow_html=True)
    
    leave_dates = st.date_input("연차 날짜 기간 선택", value=(datetime.date.today(), datetime.date.today()), key="leave_date_range")
    new_leave_name = st.text_input("직원 이름 및 내용", placeholder="예: 홍길동 휴가", key="leave_input_box")

    if st.button("연차 추가", key="btn_add_leave", use_container_width=True):
        if new_leave_name.strip():
            if isinstance(leave_dates, tuple) and len(leave_dates) == 2:
                start_l, end_l = leave_dates
                if start_l and end_l:
                    date_str = f"{start_l} ~ {end_l}" if start_l != end_l else f"{start_l}"
                else:
                    date_str = str(start_l) if start_l else str(datetime.date.today())
            else:
                date_str = str(leave_dates)

            entry = {"date": date_str, "content": new_leave_name.strip()}
            st.session_state.leave_list.append(entry)
            st.session_state.leave_list = sorted(st.session_state.leave_list, key=lambda x: x["date"])
            save_data(LEAVE_FILE, st.session_state.leave_list)
            st.rerun()

    st.markdown("<div style='margin-bottom: 12px;'></div>", unsafe_allow_html=True)

    leave_html = ""
    if not st.session_state.leave_list:
        leave_html = '<div style="font-size:13px; color:#64748b; text-align: center; padding: 10px;">등록된 연차 내역이 없습니다.</div>'
    else:
        for idx, item in enumerate(st.session_state.leave_list):
            if isinstance(item, dict):
                d_part = item.get("date", "")
                c_part = item.get("content", "")
                display_text = f"[{d_part}] {c_part}"
            else:
                display_text = str(item)

            leave_html += f'<div style="display: flex; justify-content: space-between; align-items: center; padding: 10px 8px; border-bottom: 1px solid #f1f5f9;"><span style="font-size: 14px; color: #0f172a; font-weight: 600; word-break: break-all; margin-right: 10px;">• {display_text}</span><a href="?del_leave={idx}" target="_self" style="background: #fee2e2; color: #ef4444; border-radius: 6px; padding: 4px 10px; font-size: 12px; font-weight: bold; text-decoration: none; border: 1px solid #fca5a5; white-space: nowrap;">✕ 삭제</a></div>'

    st.markdown(f'<div style="background: #ffffff; border-radius: 12px; border: 1px solid #cbd5e1; padding: 4px 12px; max-height: 250px; overflow-y: auto;">{leave_html}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
