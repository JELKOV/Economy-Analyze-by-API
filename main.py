from flask import Flask, jsonify, render_template, request, send_file
import requests
import pandas as pd
import matplotlib.pyplot as plt
import os
import time

app = Flask(__name__)

# 🌍 IMF API 기본 URL
IMF_API_BASE = "https://www.imf.org/external/datamapper/api/v1"

# 📌 IMF API에서 경제 데이터를 가져오는 함수
def fetch_imf_data(indicator, countries, years, max_retries=3):
    """
    IMF DataMapper API에서 경제 데이터를 가져오는 함수
    :param indicator: 경제 지표 ID (예: NGDP_RPCH)
    :param countries: 조회할 국가 코드 리스트 (예: USA,CHN,KOR)
    :param years: 조회할 연도 리스트 (예: 2010,2024)
    :return: Pandas DataFrame 또는 None (실패 시)
    """
    api_url = f"{IMF_API_BASE}/{indicator}/{countries}?periods={years}"
    print(f"🔍 [DEBUG] API 요청 URL: {api_url}")  # 디버깅용

    for attempt in range(max_retries):  # 최대 3번 재시도
        try:
            response = requests.get(api_url, timeout=10)
            response.raise_for_status()  # HTTP 오류 발생 시 예외 처리

            data = response.json()

            # 응답 데이터 확인
            if not data:
                print("⚠️ [WARNING] IMF API 응답이 비어 있음!")
                return None

            df = pd.DataFrame(data)
            if df.empty:
                print("⚠️ [WARNING] 데이터가 없음!")
                return None

            return df

        except requests.exceptions.Timeout:
            print(f"⏳ IMF API 요청 시간이 초과됨. ({attempt + 1}/{max_retries} 재시도 중...)")
        except requests.exceptions.RequestException as e:
            print(f"❌ [ERROR] IMF API 요청 실패: {e}")
            return None

        time.sleep(2)  # 2초 대기 후 재시도

    print("🚨 [ERROR] IMF API 재시도 후에도 실패!")
    return None


# 📌 경제 지표 리스트 가져오기
@app.route('/list-indicators', methods=['GET'])
def list_indicators():
    """
    IMF 경제 지표 목록을 가져오는 API 엔드포인트
    :return: JSON (지표 코드 - 지표명 매핑)
    """
    response = requests.get(f"{IMF_API_BASE}/indicators")
    if response.status_code != 200:
        return jsonify({"error": "지표 목록을 가져오는 데 실패했습니다."}), 500

    data = response.json()
    indicators = {code: details["label"] for code, details in data["indicators"].items() if details["label"]}

    return jsonify(indicators)


# 📌 국가 리스트 가져오기
@app.route('/list-countries', methods=['GET'])
def list_countries():
    """
    IMF에서 제공하는 국가 리스트를 가져오는 API 엔드포인트
    :return: JSON (국가 코드 - 국가명 매핑)
    """
    response = requests.get(f"{IMF_API_BASE}/countries")
    if response.status_code != 200:
        return jsonify({"error": "국가 목록을 가져오는 데 실패했습니다."}), 500

    data = response.json()
    countries = {code: details["label"] for code, details in data["countries"].items() if details["label"]}

    return jsonify(countries)


# 📌 IMF 데이터 조회 API
@app.route('/get-data', methods=['GET'])
def get_data():
    """
    IMF API에서 특정 국가 및 경제 지표 데이터를 조회하는 API 엔드포인트
    :return: JSON 데이터 또는 오류 메시지
    """
    indicator = request.args.get('indicator', 'NGDP_RPCH')  # 기본값: GDP 성장률
    countries = request.args.get('countries', 'USA,CHN')  # 기본값: 미국, 중국
    years = request.args.get('years', '2010,2024')  # 기본 조회 연도

    df = fetch_imf_data(indicator, countries, years)

    if df is not None:
        return df.to_json(orient='records', date_format='iso')

    return jsonify({"error": "데이터를 가져오는 데 실패했습니다."}), 500


# 📌 IMF 데이터 시각화 API
@app.route('/plot-data', methods=['GET'])
def plot_data():
    """
    IMF 경제 데이터를 그래프로 시각화하는 API 엔드포인트
    :return: PNG 이미지 (플롯)
    """
    indicator = request.args.get('indicator', 'NGDP_RPCH')
    countries = request.args.get('countries', 'USA,CHN')
    years = request.args.get('years', '2010,2024')

    df = fetch_imf_data(indicator, countries, years)

    if df is None:
        return jsonify({"error": "데이터를 가져오는 데 실패했습니다."}), 500

    # 📊 그래프 그리기
    plt.figure(figsize=(10, 5))
    for country in countries.split(","):
        country_df = df[df["Country"] == country]
        if country_df.empty:
            print(f"⚠️ [WARNING] {country}에 대한 데이터가 없음!")
            continue
        plt.plot(country_df["Year"], country_df["Value"], marker="o", linestyle="-", label=country)

    plt.xlabel("Year")
    plt.ylabel("Value")
    plt.title(f"IMF Data ({indicator})")
    plt.legend()
    plt.grid(True)

    plot_path = os.path.join("static", "plot.png")
    plt.savefig(plot_path)
    plt.close()

    return send_file(plot_path, mimetype="image/png")


# 📌 기본 웹 UI 제공
@app.route('/')
def home():
    """
    웹 UI (index.html) 제공
    """
    return render_template("index.html")


if __name__ == '__main__':
    os.makedirs("static", exist_ok=True)  # static 폴더 생성 (없으면 자동 생성)
    app.run(debug=True)
