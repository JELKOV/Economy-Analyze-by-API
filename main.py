from flask import Flask, jsonify, render_template, request, send_file
import requests
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import time
from flask_caching import Cache


# Flask 애플리케이션 초기화
app = Flask(__name__)

# IMF API 기본 URL
IMF_API_BASE = "https://www.imf.org/external/datamapper/api/v1"

# Flask Caching 설정 (1시간 동안 캐시 유지)
cache = Cache(app, config={'CACHE_TYPE': 'simple', 'CACHE_DEFAULT_TIMEOUT': 3600})


# IMF API에서 데이터를 가져오는 함수 (국가 목록을 50개 이하로 나눠 요청)
def fetch_imf_data(indicator, countries, years, max_retries=3):
    """
    IMF DataMapper API에서 특정 경제 지표 데이터를 가져오는 함수
    :param indicator: 경제 지표 ID (예: NGDP_RPCH)
    :param countries: 조회할 국가 코드 리스트 (예: "USA,CHN,KOR")
    :param years: 조회할 연도 리스트 (예: "2010,2024")
    :param max_retries: API 요청 실패 시 재시도 횟수 (기본값: 3)
    :return: Pandas DataFrame 또는 None (실패 시)
    """
    all_records = [] # 모든 데이터 저장 리스트
    country_list = countries.split(",") # 국가 코드를 리스트로 변환
    chunk_size = 50  # IMF API 요청 시 국가를 50개 이하 단위로 나누기 (API 제한 대비)
    # 국가 목록을 50개씩 잘라서 요청 (IMF API 요청 제한을 고려)
    for i in range(0, len(country_list), chunk_size):
        country_chunk = ",".join(country_list[i:i+chunk_size]) # 50개씩 묶어서 요청
        api_url = f"{IMF_API_BASE}/{indicator}/{country_chunk}?periods={years}" # 요청 URL 생성
        print(f"🔍 [DEBUG] API 요청 URL: {api_url}")  # 디버깅 로그 출력

        # 최대 재시도 횟수만큼 반복 (네트워크 오류 대비)
        for attempt in range(max_retries):
            try:
                response = requests.get(api_url, timeout=10) # API 요청 (10초 제한)
                response.raise_for_status() # HTTP 오류 발생 시 예외 처리
                data = response.json() # JSON 형식으로 변환

                # 지표 데이터 추출
                values = data.get("values", {}).get(indicator, {})
                if not values:
                    print(f"⚠️ [WARNING] {indicator}에 대한 데이터가 없음!")
                    continue
                # 데이터를 리스트에 저장
                for country, year_data in values.items():
                    for year, value in year_data.items():
                        all_records.append({"Year": int(year), "Country": country, "Value": value})
                break  # 성공하면 반복 중지

            except requests.exceptions.Timeout:
                print(f"⏳ IMF API 요청 시간이 초과됨. ({attempt + 1}/{max_retries} 재시도 중...)")
            except requests.exceptions.RequestException as e:
                print(f"❌ [ERROR] IMF API 요청 실패: {e}")
                continue

        time.sleep(1)  # 1초 대기 후 다음 요청

    df = pd.DataFrame(all_records) # 데이터프레임 변환

    # 올바른 국가만 남기기
    df = df[df["Country"].isin(country_list)]
    return df if not df.empty else None # 데이터가 없으면 None 반환

# IMF 경제 지표 목록 가져오기 API
@app.route('/list-indicators', methods=['GET'])
def list_indicators():
    """
    IMF 경제 지표 목록을 가져오는 API 엔드포인트
    - IMF에서 제공하는 경제 지표 코드와 설명을 반환
    """
    # IMF API에서 지표 목록 조회
    response = requests.get(f"{IMF_API_BASE}/indicators")

    # IMF API 요청이 실패하면 에러 메시지를 반환
    if response.status_code != 200:
        return jsonify({"error": "지표 목록을 가져오는 데 실패했습니다."}), 500

    # JSON 변환
    data = response.json()
    print(f"indicators 리스트: {data}")

    """
    code: 경제 지표 코드 (NGDP_RPCH, PPPGDP, LUR 등)
    details["label"]: 경제 지표의 한글 설명 (Real GDP Growth (%), GDP, current prices (PPP), Unemployment Rate (%))
    if details["label"]: 라벨이 존재하는 경우만 포함 (빈 값이 있는 경우 제외)
    """
    # 유효한 지표만 추출
    indicators = {code: details["label"] for code, details in data["indicators"].items() if details["label"]}

    # JSON 응답 반환
    return jsonify(indicators)

# 특정 지표에 대해 데이터를 제공하는 국가 목록 가져오기
@app.route('/available-countries', methods=['GET'])
# 캐싱 적용 (1시간 유지)
@cache.cached(timeout=3600, query_string=True)
def get_available_countries():
    """
    선택한 indicator(경제 지표)에 대해 실제 데이터를 제공하는 국가 목록 조회 (캐싱 적용)
    - 특정 지표에 대해 데이터를 제공하는 국가 목록을 IMF API에서 확인 후 반환
    """
    # 사용자 요청에서 지표 값 가져오기
    indicator = request.args.get('indicator')
    # 기본 조회 시작 연도
    start_year = request.args.get('startYear', '2010')  # 기본값 2010
    # 기본 조회 종료 연도
    end_year = request.args.get('endYear', '2024')  # 기본값 2024

    # 지표 값이 없으면 오류 반환
    if not indicator:
        return jsonify({"error": "지표를 제공해야 합니다."}), 400

    # 조회 연도 범위 설정
    years = ",".join(str(year) for year in range(int(start_year), int(end_year) + 1))

    # 국가 목록 조회
    all_countries_response = requests.get(f"{IMF_API_BASE}/countries")
    if all_countries_response.status_code != 200:
        return jsonify({"error": "국가 목록을 가져오는 데 실패했습니다."}), 500

    # 응답 데이터에서 국가 목록 가져오기
    all_countries = all_countries_response.json().get("countries", {})

    # 특정 지표에서 데이터를 제공하는 국가 조회
    df = fetch_imf_data(indicator, ",".join(all_countries.keys()), years)

    # 데이터가 없으면 404 반환
    if df is None or df.empty:
        return jsonify({"error": "해당 지표에 대해 데이터를 제공하는 국가가 없습니다."}), 404

    # 실제 데이터를 제공하는 국가만 필터링
    available_countries = df["Country"].unique().tolist()
    filtered_countries = {code: all_countries[code]["label"] for code in available_countries if code in all_countries}

    print(f"✅ [DEBUG] {indicator}에 대해 데이터를 제공하는 국가 개수: {len(filtered_countries)}")

    # JSON 응답 반환
    return jsonify(filtered_countries)


# IMF 데이터 조회 API
@app.route('/get-data', methods=['GET'])
def get_data():
    """
    특정 국가 및 경제 지표 데이터를 조회하는 API 엔드포인트
    - IMF DataMapper API에서 데이터를 가져온 후 JSON 응답 반환
    """
    indicator = request.args.get('indicator', 'NGDP_RPCH')  # 기본값: GDP 성장률
    countries = request.args.get('countries', 'USA,CHN')  # 기본값: 미국, 중국
    print(f"🛠 [DEBUG] 요청된 국가 목록: {countries}")  # 요청된 국가 확인
    years = request.args.get('years', '2010,2024')  # 기본 조회 연도

    df = fetch_imf_data(indicator, countries, years)

    # 데이터 가져오기
    if df is not None:
        print(f"📌 [DEBUG] 데이터 미리보기:\n{df.head()}")
        return df.to_json(orient='records', date_format='iso')

    return jsonify({"error": "데이터를 가져오는 데 실패했습니다."}), 500


# IMF 데이터 시각화 API
@app.route('/plot-data', methods=['GET'])
def plot_data():
    """
    IMF 데이터 시각화 API
    - 선택된 경제 지표, 국가, 연도에 대한 데이터를 다양한 차트로 시각화하여 PNG 이미지로 반환
    """
    # 사용자가 요청한 경제 지표 (기본값: 'NGDPD' → 명목 GDP)
    indicator = request.args.get('indicator', 'NGDPD')
    # 사용자가 요청한 국가 목록 (기본값: 'USA,CHN' → 미국, 중국)
    countries = request.args.get('countries', 'USA,CHN')
    # 사용자가 요청한 연도 범위 (기본값: '2010,2024')
    years = request.args.get('years', '2010,2024')
    # 기본값은 Line Chart
    chart_type = request.args.get('type', 'line')
    print(chart_type)

    # IMF API에서 해당 지표, 국가, 연도에 대한 데이터를 가져옴
    df = fetch_imf_data(indicator, countries, years)

    # 데이터가 없을 경우 500 에러 반환
    if df is None or df.empty:
        return jsonify({"error": "데이터를 가져오는 데 실패했습니다."}), 500

    # 그래프 생성 시작
    plt.figure(figsize=(10, 5)) # 그래프 크기 설정 (가로 10인치, 세로 5인치)

    if chart_type == "bar":
        # 막대 그래프
        sns.barplot(x="Year", y="Value", hue="Country", data=df)
        plt.title(f"IMF Data ({indicator}) - Bar Chart")
    elif chart_type == "pie":
        # 원형 그래프
        latest_year = df["Year"].max()
        df_latest = df[df["Year"] == latest_year]
        plt.pie(df_latest["Value"], labels=df_latest["Country"], autopct="%1.1f%%", startangle=140)
        plt.title(f"IMF Data ({indicator}) - {latest_year}년 기준 Pie Chart")
    elif chart_type == "heatmap":
        # 히트맵 (연도별 경제 지표 변화)
        pivot_df = df.pivot(index="Country", columns="Year", values="Value")
        sns.heatmap(pivot_df, annot=True, cmap="coolwarm", fmt=".1f")
        plt.title(f"IMF Data ({indicator}) - Heatmap")
    else:
        # 기본 선 그래프 (Line Chart)
        for country in countries.split(","): # 입력받은 국가 목록을 ','로 분할하여 리스트로 변환
            country_df = df[df["Country"] == country] # 특정 국가에 대한 데이터 필터링

            # 해당 국가의 데이터가 없을 경우 경고 메시지 출력 후 건너뜀
            if country_df.empty:
                print(f"⚠️ [WARNING] {country}에 대한 데이터가 없음!")
                continue
            # 연도를 x축, 경제 지표 값을 y축으로 설정하여 라인 그래프 그리기
            plt.plot(
                country_df["Year"], # x축: 연도
                country_df["Value"], # y축: 경제 지표 값
                marker="o", # 데이터 포인트를 동그라미로 표시
                linestyle="-", # 선 스타일: 실선(-)
                label=country # 범례에 국가명 표시
            )

        # 그래프에 레이블 추가
        plt.xlabel("Year") # x축 라벨 설정
        plt.ylabel("Value") # y축 라벨 설정
        plt.title(f"IMF Data ({indicator})") # 그래프 제목 설정
        plt.legend() # 국가별 범례 추가

    # 배경에 격자 무늬 추가하여 가독성 향상
    plt.grid(True)
    # 생성된 그래프를 static 폴더 내 plot.png 파일로 저장
    plot_path = os.path.join("static", "plot.png")
    # 그래프를 PNG 이미지로 저장
    plt.savefig(plot_path)
    # 메모리 절약을 위해 그래프 닫기
    plt.close()

    # 저장된 이미지를 사용자에게 반환 (MIME 타입: image/png)
    return send_file(plot_path, mimetype="image/png")


# 기본 웹 UI 제공
@app.route('/')
def home():
    """
    웹 UI (index.html) 제공
    """
    return render_template("index.html")


if __name__ == '__main__':
    os.makedirs("static", exist_ok=True)  # static 폴더 생성 (없으면 자동 생성)
    app.run(debug=True)
