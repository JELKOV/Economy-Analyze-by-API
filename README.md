# 📊 IMF 경제 데이터 분석 프로젝트

## 🌍 프로젝트 개요
**IMF 경제 데이터 분석 프로젝트**는 국제 통화 기금(IMF)에서 제공하는 경제 데이터를 시각화하고 분석하는 웹 애플리케이션입니다. Flask 기반의 백엔드와 HTML, JavaScript, CSS로 구성된 프론트엔드로, 사용자가 선택한 경제 지표, 국가, 연도 범위에 대한 데이터를 검색하고 다양한 그래프 형태로 시각화할 수 있도록 구현되었습니다.

## 🚀 주요 기능
- **IMF API 연동**: IMF에서 제공하는 경제 데이터를 실시간으로 가져오기
- **국가 및 지표 선택**: 사용자가 원하는 국가 및 경제 지표 선택 가능
- **연도 범위 설정**: 슬라이더를 이용해 조회할 연도 범위 설정
- **다양한 그래프 지원**: Line Chart, Bar Chart, Pie Chart, Heatmap 제공
- **데이터 캐싱**: IMF API 요청을 캐싱하여 성능 최적화
- **반응형 UI**: 모바일과 데스크톱 환경 모두에서 편리하게 사용 가능
- **모던한 디자인**: Select2, Bootstrap, SweetAlert2 적용으로 UI 개선

## 🏗 프로젝트 구조
```
IMF-Data-Visualization/
├── static/
│   ├── loading-spinner.gif
│   ├── plot.png
│   ├── no-data.png
│   ├── script.js  # 클라이언트 측 기능 담당
│   ├── styles.css # UI 스타일링
├── templates/
│   ├── index.html # 메인 페이지
├── main.py        # Flask 백엔드 애플리케이션
├── requirements.txt # 프로젝트 의존성 목록
├── README.md      # 프로젝트 설명서
```

## 🛠 기술 스택
- **Backend**: Python (Flask)
- **Frontend**: HTML, CSS, JavaScript (jQuery, Bootstrap, Select2, SweetAlert2)
- **Data Handling**: Pandas, Matplotlib, Seaborn
- **API**: IMF DataMapper API
- **Caching**: Flask-Caching

## 🔍 사용 방법
### 1️⃣ 프로젝트 실행
```bash
# 가상 환경 생성 및 활성화 (선택 사항)
python -m venv venv
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate    # Windows

# 필수 패키지 설치
pip install -r requirements.txt

# 서버 실행
python main.py
```

### 2️⃣ 웹 인터페이스 사용
1. 웹 브라우저에서 `http://127.0.0.1:5000/` 접속
2. 경제 지표 선택
3. 국가 선택 (다중 선택 가능)
4. 연도 범위 설정
5. 그래프 타입 선택
6. 데이터 조회 버튼 클릭 후 분석 결과 확인

## 📡 API 사용법
### 1️⃣ IMF 데이터 조회 API
```http
GET /get-data?indicator={지표코드}&countries={국가코드}&years={연도범위}
```
- **지표코드**: IMF에서 제공하는 경제 지표 코드 (예: `NGDP_RPCH` - 실질 GDP 성장률)
- **국가코드**: IMF 코드로 된 국가 리스트 (예: `USA,CHN,KOR`)
- **연도범위**: 조회할 연도 범위 (예: `2010,2025`)

**응답 예시:**
```json
[
    {"Year": 2020, "Country": "USA", "Value": 2.3},
    {"Year": 2020, "Country": "KOR", "Value": 3.1}
]
```

### 2️⃣ IMF 데이터 시각화 API
```http
GET /plot-data?indicator={지표코드}&countries={국가코드}&years={연도범위}&type={차트타입}
```
- **차트타입**: `line`, `bar`, `pie`, `heatmap` 중 선택 가능

예시:
```http
GET /plot-data?indicator=NGDP_RPCH&countries=USA,KOR&years=2010,2025&type=bar
```

## 📌 코드 설명
### **1️⃣ main.py (Flask 백엔드)**
- **Flask 서버 실행**: `@app.route('/')` → index.html 렌더링
- **IMF 데이터 가져오기**: `fetch_imf_data()` 함수에서 API 요청 후 Pandas DataFrame으로 변환
- **데이터 시각화**: `plot-data` 엔드포인트에서 Matplotlib + Seaborn 활용해 그래프 생성
- **캐싱 적용**: `Flask-Caching`을 활용해 1시간 동안 요청 결과 저장

### **2️⃣ index.html (프론트엔드)**
- **Select2 활용**: 국가 및 지표 검색 기능 추가
- **SweetAlert2 적용**: 알림 메시지를 더 깔끔하게 표시
- **Bootstrap 디자인**: 반응형 UI 적용
- **jQuery 이벤트 처리**: 버튼 클릭 시 데이터 요청 후 그래프 업데이트

### **3️⃣ script.js (클라이언트 로직)**
- **국가 및 지표 목록 로드** (`loadIndicators()`, `loadAvailableCountries()`)
- **차트 요청 및 데이터 표시** (`fetchData()`)
- **UI 이벤트 처리** (`selectGroup()`, `deselectGroup()`, `updateYearLabel()`)

## 📊 지표 설명
| 지표 코드 | 설명 |
|-----------|------------------------------------------------|
| NGDPD | 명목 GDP (단위: 백만 달러) |
| NGDP_RPCH | 실질 GDP 성장률 (%) |
| LUR | 실업률 (%) |
| BCA | 경상수지 잔액 (단위: 백만 달러) |


## 📄 프로젝트 제작자
**👤 JELKOV**
- Email: ajh4234@gmail.com
- GitHub: [github.com/jelkov](https://github.com/jelkov)
- Portfolio: [포트폴리오 사이트](https://jelkov.github.io/Portfolio-New-Version/)


---
📝 본 프로젝트는 IMF 경제 데이터를 효과적으로 분석하고 시각화할 수 있도록 설계되었으며, 누구나 자유롭게 사용할 수 있습니다! 🚀

