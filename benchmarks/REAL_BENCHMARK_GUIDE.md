# 🚀 실제 문서로 벤치마크 실행하기

이 가이드는 **실제 TreeRAG 시스템**을 사용하여 벤치마크를 실행하는 방법을 설명합니다.

---

## 📋 사전 준비

### 1. 실제 문서 준비

TreeRAG에 이미 업로드되어 인덱싱된 문서가 필요합니다.

```bash
# 현재 인덱싱된 문서 확인
ls data/indices/
```

**출력 예시:**
```
2025학년도 교육과정 반도체공학과_index.json
생체의공학개론_보고서_index.json
웹:파이썬 프로그래밍 프로젝트 #6 보고서_index.json
```

### 2. TreeRAG 서버 실행

```bash
# 백엔드 서버 시작
python main.py

# 또는 uvicorn으로 시작
uvicorn main:app --reload --port 8000
```

서버가 실행되면 `http://localhost:8000`에서 API 사용 가능합니다.

### 3. API 연결 테스트

```bash
curl http://localhost:8000/health
```

---

## 📝 질문 데이터셋 작성

### 형식

`benchmarks/datasets/my_benchmark_questions.json` 파일을 작성합니다:

```json
{
  "version": "1.0",
  "description": "내 벤치마크 질문",
  "n_questions": 3,
  "questions": [
    {
      "question_id": "q001",
      "question": "실제 질문 내용",
      "document_id": "문서명 (인덱스 파일명에서 _index.json 제외)",
      "relevant_sections": ["정답 섹션 ID들"],
      "expected_answer": "기대되는 답변",
      "domain": "academic",
      "difficulty": "medium"
    }
  ]
}
```

### 예제 (실제 문서 기반)

```json
{
  "version": "1.0",
  "n_questions": 3,
  "questions": [
    {
      "question_id": "real_001",
      "question": "2025학년도 반도체공학과 필수 과목은?",
      "document_id": "2025학년도 교육과정 반도체공학과",
      "relevant_sections": ["sec_required_courses"],
      "expected_answer": "반도체공학과 필수 과목 목록",
      "domain": "academic",
      "difficulty": "easy"
    },
    {
      "question_id": "real_002",
      "question": "생체의공학 보고서의 실험 방법은?",
      "document_id": "생체의공학개론_보고서",
      "relevant_sections": ["methodology", "experiments"],
      "expected_answer": "실험 설계 및 방법론",
      "domain": "academic",
      "difficulty": "medium"
    }
  ]
}
```

**💡 팁:** `relevant_sections`는 정확한 섹션 ID를 모르면 빈 배열 `[]`로 두고, 나중에 TreeRAG 응답을 보고 수정할 수 있습니다.

---

## 🎯 벤치마크 실행

### 방법 1: 실제 API 평가 (권장)

```bash
# 기본 실행
python benchmarks/run_real_evaluation.py

# 사용자 정의 설정
python benchmarks/run_real_evaluation.py \
  --questions benchmarks/datasets/my_benchmark_questions.json \
  --api-url http://localhost:8000 \
  --experiment my_real_test \
  --output benchmarks/results
```

### 방법 2: 실제 + 기준선 비교

실제 TreeRAG와 시뮬레이션 기준선을 비교하려면:

```bash
# 1단계: 실제 TreeRAG 평가
python benchmarks/run_real_evaluation.py \
  --experiment comparison_test

# 2단계: 결과를 기준선과 비교 (수동)
python scripts/compare_with_baseline.py \
  --treerag benchmarks/results/comparison_test/treerag_results.json \
  --baseline benchmarks/results/flatrag_baseline.json
```

---

## 📊 결과 확인

### 터미널에서 바로 보기

```bash
# 가장 최근 결과 자동 로드
python scripts/view_results.py

# 특정 결과 파일 지정
python scripts/view_results.py benchmarks/results/my_real_test/evaluation_report.json
```

### 결과 파일 위치

```
benchmarks/results/my_real_test/
├── evaluation_report.json    # 전체 결과 데이터
└── treerag_results.json       # TreeRAG 상세 결과
```

### 예상 출력

```
======================================================================
  📊 전체 평가 결과
======================================================================

실험명: my_real_test
실행 시간: 2026-02-14 15:30:00
평가 시스템: TreeRAG (Real)

📊 시스템: TreeRAG (Real)
----------------------------------------------------------------------

  검색 성능:
    P@1: 100.0%
    P@3: 85.2%
    P@5: 78.3%
    NDCG@5: 0.892
    MRR: 0.950

  효율성:
    평균 지연시간: 2450.32ms
    평균 토큰: 1250

  신뢰도:
    평균 근거성: 92.5%
```

---

## 🔧 문제 해결

### 1. API 연결 실패

```bash
# 서버 상태 확인
curl http://localhost:8000/health

# 로그 확인
tail -f logs/treerag.log
```

### 2. 문서를 찾을 수 없음

```bash
# 인덱싱된 문서 목록 확인
ls -la data/indices/

# 문서 재업로드 및 인덱싱
# (프론트엔드 또는 API를 통해)
```

### 3. 질문 데이터셋 오류

```bash
# JSON 유효성 검사
python -m json.tool benchmarks/datasets/my_benchmark_questions.json
```

---

## 📈 고급 사용

### A. 배치 평가 (여러 실험)

```bash
#!/bin/bash
# run_all_benchmarks.sh

experiments=("test1" "test2" "test3")

for exp in "${experiments[@]}"; do
  echo "Running $exp..."
  python benchmarks/run_real_evaluation.py \
    --experiment "$exp" \
    --questions "benchmarks/datasets/${exp}_questions.json"
done

echo "✅ 모든 실험 완료"
```

### B. 통계 분석

```bash
# 여러 실험 결과 비교
python scripts/analyze_experiments.py \
  benchmarks/results/test1 \
  benchmarks/results/test2 \
  benchmarks/results/test3
```

### C. 시각화

```bash
# 그래프 생성 (matplotlib 필요)
python scripts/plot_results.py benchmarks/results/my_real_test/evaluation_report.json
```

---

## ✅ 체크리스트

실행 전 확인사항:

- [ ] TreeRAG 서버 실행 중 (`http://localhost:8000`)
- [ ] 문서가 인덱싱되어 있음 (`data/indices/` 확인)
- [ ] 질문 데이터셋 작성 완료
- [ ] `document_id`가 실제 파일명과 일치
- [ ] Python 패키지 설치 (`aiohttp`, `requests`)

---

## 📚 참고

- **기본 벤치마크 (시뮬레이션)**: `benchmarks/run_evaluation.py`
- **실제 시스템 벤치마크**: `benchmarks/run_real_evaluation.py`
- **결과 뷰어**: `scripts/view_results.py`
- **API 문서**: `http://localhost:8000/docs`

---

**Happy Benchmarking! 🚀**
