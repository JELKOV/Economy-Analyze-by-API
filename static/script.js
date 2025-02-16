// 문서가 로드되면 실행
$(document).ready(function () {
    let allCountries = {}; // 모든 국가 데이터를 저장할 객체
    let groupSelections = { All: false, G20: false, G7: false, BRICS: false }; // 그룹별 선택 상태 저장

    // 주요 국가 그룹 (G20, G7, BRICS) 국가 코드 정의
    let g20 = ["ARG", "AUS", "BRA", "CAN", "CHN", "FRA", "DEU", "IND", "IDN", "ITA", "JPN", "MEX", "RUS", "SAU", "ZAF", "KOR", "TUR", "GBR", "USA", "EU"];
    let g7 = ["CAN", "FRA", "DEU", "ITA", "JPN", "GBR", "USA"];
    let brics = ["BRA", "RUS", "IND", "CHN", "ZAF"];

    // 경제 지표 목록 불러오기
    function loadIndicators() {
        $.getJSON("/list-indicators", function(data) {  // 서버에서 경제 지표 목록을 가져옴
            let indicatorSelect = $("#indicator");
            indicatorSelect.empty().append(new Option("경제 지표 선택", "")); // 기존 데이터 초기화 및 기본 옵션 추가

            // 가져온 데이터를 select 옵션으로 추가
            $.each(data, function (key, value) {
                indicatorSelect.append(new Option(value, key));
            });
        });

        // 지표 선택 시 해당 지표에서 데이터를 제공하는 국가 목록 조회
        $("#indicator").change(function () {
            let selectedIndicator = $(this).val();
            if (selectedIndicator) {
                // 국가 목록 갱신
                loadAvailableCountries(selectedIndicator);
            }
        });
    }

    // 선택된 국가 목록을 UI에 업데이트하는 함수
    function updateSelectedCountriesList() {
        // 선택된 국가 목록 가져오기
        let selectedCountries = $("#countries").val() || [];
        let countryList = $("#selectedCountriesList");

        // 기존 목록 초기화
        countryList.empty();

        if (selectedCountries.length === 0) {
            // 입력 필드 초기화
            $("#selectedCountries").val("");
            return;
        }

        // 선택된 국가 목록을 화면에 표시
        $("#selectedCountries").val(selectedCountries.join(", "));

        selectedCountries.forEach(code => {
            // 국가 코드에서 이름 가져오기
            let countryName = allCountries[code] || code;
            let listItem = `<li class="list-group-item d-flex justify-content-between align-items-center">
                                ${countryName}
                                <button class="btn btn-sm btn-danger remove-country" data-code="${code}">❌</button>
                            </li>`;
            countryList.append(listItem);
        });

        // 국가 개별 제거 버튼 이벤트
        $(".remove-country").click(function () {
            let countryCode = $(this).data("code");
            let currentSelection = new Set($("#countries").val() || []);
            currentSelection.delete(countryCode);

            $("#countries").val([...currentSelection]).trigger("change");
            updateSelectedCountriesList();
        });
    }

    // 선택한 경제 지표를 제공하는 국가 목록 불러오기
    function loadAvailableCountries(indicator) {
         // 기존 국가 목록 초기화
        $("#countries").empty();
        // 로딩 화면 표시
        $("#loading-countries").fadeIn();
        // 메시지 표시
        $("#loading-message").text("국가 목록을 불러오는 중...");

        let startYear = $("#startYear").val();
        let endYear = $("#endYear").val();

        $.getJSON(`/available-countries?indicator=${indicator}&startYear=${startYear}&endYear=${endYear}`, function(data) {
            // 로딩 화면 숨기기
            $("#loading-countries").fadeOut();

            // 데이터가 없을 경우
            if (data.error) {
                Swal.fire({
                    icon: "warning",
                    title: "📌 데이터 없음",
                    text: "해당 지표와 연도 범위에 대한 데이터를 제공하는 국가가 없습니다.",
                });
                return;
            }

            // 사용 가능한 국가 목록 저장
            allCountries = data;

            // 사용 가능한 국가 개수
            let countryCount = Object.keys(allCountries).length;

            $.each(allCountries, function (key, value) {
                $("#countries").append(new Option(value, key));
            });

            // Select2 초기화 및 검색 기능 추가
            $("#countries").select2({
                placeholder: "국가 선택 (다중 가능)",
                allowClear: true,
                width: "100%",
                matcher: function (params, data) {
                    if ($.trim(params.term) === '') {
                        return data;
                    }
                    if (data.text.toLowerCase().indexOf(params.term.toLowerCase()) === 0) {
                        return data; // 첫 글자부터 일치하는 경우만 반환
                    }
                    return null;
                }
            }).on("change", updateSelectedCountriesList);
            //  국가 목록 로드 완료 알림
            Swal.fire({
                icon: "success",
                title: "✅ 국가 목록 불러오기 완료!",
                text: `${indicator} 지표에서 ${countryCount}개의 국가 데이터를 제공합니다.`,
                timer: 3000
            });

            // 화면에 국가 개수 표시
            $("#country-count").text(`📌 ${countryCount}개 국가 데이터를 제공합니다.`);
        })
        // 서버 요청 실패 시
        .fail(function() {
            $("#loading-countries").fadeOut();
            Swal.fire({
                icon: "error",
                title: "🚨 오류 발생",
                text: "국가 데이터를 불러오는 중 문제가 발생했습니다.",
            });
        });
    }

    // G20, G7, BRICS 등의 그룹 선택 기능
    function selectGroup(group, groupKey) {
        // 국가 선택 드롭다운 요소 가져오기
        let countrySelect = $("#countries");
        // 사용 가능한 국가만 필터링
        let validCountries = group.filter(code => allCountries.hasOwnProperty(code));


         // 선택하려는 그룹에 해당하는 국가가 없을 경우 경고 메시지 표시
        if (validCountries.length === 0) {
            Swal.fire({
                icon: "warning",
                title: "⚠️ 선택 불가",
                text: `현재 선택한 지표에 대한 ${groupKey} 국가 데이터가 없습니다.`,
                confirmButtonText: "확인"
            });
            return;
        }

        // 현재 선택된 국가 목록을 Set으로 변환 (중복 제거)
        let currentSelection = new Set(countrySelect.val() || []);
        // 선택하려는 그룹의 국가들을 추가
        validCountries.forEach(code => currentSelection.add(code));

        // 선택된 국가 목록 업데이트 및 UI 반영
        countrySelect.val([...currentSelection]).trigger("change");
        // 선택된 상태로 버튼 업데이트
        toggleButtons(groupKey, true);
        // UI에 반영하여 선택된 국가 목록 표시
        updateSelectedCountriesList();
    }

    // 특정 그룹 (전체, G20, G7, BRICS) 해제 기능
    function deselectGroup(group, groupKey) {
        // 국가 선택 드롭다운 요소 가져오기
        let countrySelect = $("#countries");
        // 현재 선택된 국가 목록을 Set으로 변환 (중복 제거)
        let currentSelection = new Set(countrySelect.val() || []);

        // 선택 해제할 국가 그룹의 국가들을 제거
        group.forEach(code => currentSelection.delete(code));

        // 변경된 국가 목록을 UI에 반영
        countrySelect.val([...currentSelection]).trigger("change");
        // 선택 해제 상태로 버튼 업데이트
        toggleButtons(groupKey, false);
        // UI 업데이트하여 반영
        updateSelectedCountriesList();
    }

    // 버튼 상태 변경 (선택 → 해제, 해제 → 선택)
    function toggleButtons(groupKey, isSelected) {
        if (isSelected) {
            // 선택 버튼 숨기기
            $(`#select${groupKey}`).hide();
            // 해제 버튼 표시
            $(`#deselect${groupKey}`).show();
        } else {
            // 선택 버튼 다시 표시
            $(`#select${groupKey}`).show();
            // 해제 버튼 숨기기
            $(`#deselect${groupKey}`).hide();
        }
        // 해당 그룹의 선택 상태를 업데이트
        groupSelections[groupKey] = isSelected;
    }

    // 전체 국가 선택 버튼 이벤트 추가
    $("#selectAll").click(function (e) {
        e.preventDefault(); // 기본 이벤트 (페이지 이동) 방지
        // 모든 국가 선택
        selectGroup(Object.keys(allCountries), "All");
    });
    $("#deselectAll").click(function (e) {
        e.preventDefault(); // 기본 이벤트 방지
        // 모든 국가 해제
        deselectGroup(Object.keys(allCountries), "All");
    });

    // G20 그룹 선택 및 해제 버튼 이벤트 추가
    $("#selectG20").click(function (e) {
        e.preventDefault();
        // G20 국가 선택
        selectGroup(g20, "G20");
    });
    $("#deselectG20").click(function (e) {
        e.preventDefault();
        // G20 국가 해제
        deselectGroup(g20, "G20");
    });

    // G7 그룹 선택 및 해제 버튼 이벤트 추가
    $("#selectG7").click(function (e) {
        e.preventDefault();
        // G7 국가 선택
        selectGroup(g7, "G7");
    });
    $("#deselectG7").click(function (e) {
        e.preventDefault();
        // G7 국가 해제
        deselectGroup(g7, "G7");
    });

    // BRICS 그룹 선택 및 해제 버튼 이벤트 추가
    $("#selectBRICS").click(function (e) {
        e.preventDefault();
        // BRICS 국가 선택
        selectGroup(brics, "BRICS");
    });
    $("#deselectBRICS").click(function (e) {
        e.preventDefault();
        // BRICS 국가 해제
        deselectGroup(brics, "BRICS");
    });


    // IMF 데이터 요청 및 그래프 업데이트 함수
    function fetchData() {
        // 사용자가 선택한 경제 지표, 국가, 연도 값을 가져옴

        // 선택한 경제 지표 값
        let indicator = $("#indicator").val();
        // 선택한 국가 목록 (배열 형태)
        let countries = $("#countries").val();
        // 조회 시작 연도
        let startYear = parseInt($("#startYear").val());
        // 조회 종료 연도
        let endYear = parseInt($("#endYear").val());


        // 유효성 검사 (필수 입력값 확인)

        // 경제 지표가 선택되지 않은 경우
        if (!indicator) {
            Swal.fire({
                icon: "warning",
                title: "📌 선택 필요",
                text: "경제 지표를 선택하세요.",
                confirmButtonText: "확인"
            });
            return;
        }
        // 최소 한 개의 국가가 선택되지 않은 경우
        if (!countries || countries.length === 0) {
            Swal.fire({
                icon: "warning",
                title: "📌 선택 필요",
                text: "최소 한 개 이상의 국가를 선택하세요.",
                confirmButtonText: "확인"
            });
            return;
        }
        // 시작 연도가 종료 연도보다 큰 경우 오류 처리
        if (startYear > endYear) {
            Swal.fire({
                icon: "error",
                title: "⚠️ 입력 오류",
                text: "시작 연도가 종료 연도보다 클 수 없습니다.",
                confirmButtonText: "확인"
            });
            return;
        }

        // startYear부터 endYear까지 모든 연도를 배열로 생성
        let selectedYears = [];
        for (let year = startYear; year <= endYear; year++) {
            selectedYears.push(year);
        }

        // API 요청 URL 생성
        let apiUrl = `/get-data?indicator=${indicator}&countries=${countries.join(',')}&years=${selectedYears.join(',')}`;
        let plotUrl = `/plot-data?indicator=${indicator}&countries=${countries.join(',')}&years=${selectedYears.join(',')}`;

        // 데이터 요청 전, 로딩 UI 표시

        // 로딩 표시 활성화
        $("#loading").fadeIn();
        // 기존 그래프 숨김
        $("#gdpPlot").hide();
        // 기존 데이터 숨김
        $("#jsonData").hide();
        // 오류 메시지 숨기기
        $("#alert-box").hide();

        // IMF 데이터 API 요청 (비동기 요청)
        fetch(apiUrl)
            // 응답을 JSON으로 변환
            .then(response => response.json())
            // 데이터 로드 완료
            .then(data => {
                // 로딩 화면 숨기기
                $("#loading").fadeOut();
                // 그래프 표시
                $("#gdpPlot").fadeIn();
                // JSON 데이터 표시
                $("#jsonData").fadeIn();

                // 오류 발생 시 처리
                if (data.error) {
                    Swal.fire({
                        icon: "error",
                        title: "❌ 데이터 없음",
                        text: "해당 조건의 데이터를 불러올 수 없습니다.",
                        confirmButtonText: "확인"
                    });

                    // 오류 메시지 표시
                    $("#jsonData").text("❌ 데이터를 불러올 수 없습니다.");
                    // 오류 이미지 표시
                    $("#gdpPlot").attr("src", "{{ url_for('static', filename='no-data.png') }}").hide();
                    // 오류 박스 표시
                    $("#alert-box").fadeIn().text("⚠️ 해당 조건의 데이터가 없습니다.");
                } else {
                    // 정상 데이터 수신 시 처리
                    Swal.fire({
                        icon: "success",
                        title: "✅ 데이터 로드 완료",
                        text: "경제 데이터를 성공적으로 불러왔습니다.",
                        confirmButtonText: "확인"
                    });
                    $("#jsonData").text(JSON.stringify(data, null, 2));
                    $("#gdpPlot").attr("src", plotUrl);
                }
            })
            // 네트워크 또는 서버 오류 발생 시
            .catch(error => {
                // 오류 로그 출력
                console.error("Error fetching data:", error);
                // 로딩 숨기기
                $("#loading").fadeOut();
                Swal.fire({
                    icon: "error",
                    title: "🚨 요청 실패",
                    text: "데이터 요청 중 오류가 발생했습니다.",
                    confirmButtonText: "확인"
                });
                $("#alert-box").fadeIn().text("🚨 데이터 요청 중 오류가 발생했습니다.");
            });
    }

    // 연도 슬라이더 값 업데이트 함수
    function updateYearLabel() {
        // 현재 선택된 시작 연도 값 가져오기
        let startYear = $("#startYear").val();
        // 현재 선택된 종료 연도 값 가져오기
        let endYear = $("#endYear").val();
        // UI에 반영
        $("#yearLabel").text(`${startYear} ~ ${endYear}`);
    }

    // 슬라이더 값 변경 이벤트
    $("#startYear, #endYear").on("input", function () {
        // 시작 연도 값
        let startYear = parseInt($("#startYear").val());
        // 종료 연도 값
        let endYear = parseInt($("#endYear").val());

        // 시작 연도가 종료 연도보다 크다면 자동 조정
        if (startYear > endYear) {
            // 종료 연도를 시작 연도로 맞춤
            $("#endYear").val(startYear);
        }

        // UI 반영을 위한 딜레이 적용
        setTimeout(() => updateYearLabel(), 100);
    });

    // 초기 데이터 로드

    // IMF 경제 지표 목록 불러오기
    loadIndicators();
    // 초기 연도 범위 표시
    updateYearLabel();

    // "조회" 버튼 이벤트 등록
    $("#fetchDataBtn").click(function (e) {
        e.preventDefault();
        fetchData();
    });
});