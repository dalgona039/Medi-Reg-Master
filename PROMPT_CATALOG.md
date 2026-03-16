# TreeRAG Prompt Catalog

이 문서는 코드베이스에서 `Config.CLIENT.models.generate_content(...)`로 실제 전달되는 프롬프트를 정리한 목록입니다.

## 1) Document Routing Prompt

- Files:
  - `src/api/routes.py`
  - `src/services/document_router_service.py`

```text
당신은 문서 라우터입니다.
사용자의 질문을 분석하여, 어떤 규제 문서를 참조해야 하는지 선택하세요.

### 사용 가능한 문서:
{context}

### 사용자 질문:
{question}

### 규칙:
1. 질문과 가장 관련 있는 문서를 선택하세요.
2. 여러 문서가 관련되어 있다면 모두 선택하세요.
3. 반드시 위 목록에 있는 문서명만 사용하세요.
4. 응답 형식: JSON 배열로만 답하세요. 설명 없이 문서명만.

예시: ["2025학년도_교육과정_전자공학과", "교육과정_가이드라인"]

### 선택된 문서 (JSON 배열):
```

---

## 2) Node Relevance Evaluation Prompt

- File:
  - `src/core/tree_traversal.py`

```text
당신은 문서 탐색 전문가입니다.
사용자의 질문에 답하기 위해, 아래 섹션이 관련이 있는지 판단하세요.

### 컨텍스트 (문서 경로):
{context}

### 평가 대상 섹션:
- 제목: {node_title}
- 요약: {node_summary}
- 페이지: {node_page_ref}

### 사용자 질문:
{query}

### 판단 기준:
1. 이 섹션이 질문에 직접 답할 수 있는가?
2. 이 섹션의 하위 항목에 답이 있을 가능성이 높은가?
3. 키워드나 개념이 겹치는가?

답변 형식 (JSON):
{
  "relevant": true 또는 false,
  "confidence": 0.0부터 1.0 사이의 수치,
  "reason": "1-2문장 설명"
}

JSON만 출력하세요:
```

---

## 3) Child Branch Selection Prompt

- File:
  - `src/core/tree_traversal.py`

```text
당신은 문서 탐색 전문가입니다.
다음 하위 섹션들 중에서, 사용자 질문에 답하기 위해 우선적으로 탐색해야 할 {max_branches}개를 선택하세요.

### 상위 컨텍스트:
{parent_context}

### 하위 섹션 목록:
{children_summaries_json}

### 사용자 질문:
{query}

### 선택 기준:
- 질문과의 직접적 관련성
- 답변에 필요한 정보가 있을 가능성
- 우선순위 (중요도 높은 순)

답변 형식 (JSON):
{
  "selected_indices": [0, 3, 5],
  "reason": "선택 이유 1-2문장"
}

최대 {max_branches}개의 인덱스를 선택하세요. JSON만 출력:
```

---

## 4) Index Creation Prompt

- File:
  - `src/core/indexer.py`

```text
You are a Legal & Regulatory Expert AI.
Your task is to convert the provided regulatory document text into a structured JSON tree.

### Structure Requirements:
- Root: Document Title
- Children: Chapters -> Sections -> Articles
- Each node MUST have: "id", "title", "summary", "page_ref" (e.g., "12-15").

### Text to Analyze:
Title: {doc_title}
Content:
{full_text}
```

---

## 5) Domain Classification Prompt

- File:
  - `src/core/domain_benchmark.py`

```text
Classify the following document into one of these domains:
- medical: Healthcare, clinical, biomedical
- legal: Laws, regulations, contracts
- technical: Software, hardware, engineering
- academic: Research papers, education
- financial: Finance, accounting, investment
- regulatory: Standards, compliance, certification
- general: None of the above

Document Title: {title}
Document Excerpt: {text_excerpt}

Respond in JSON format:
{
  "domain": "<domain_name>",
  "confidence": <0.0-1.0>,
  "reasoning": "<brief explanation>"
}

JSON only:
```

---

## 6) Answer Evaluation Prompt

- File:
  - `src/core/domain_benchmark.py`

```text
Evaluate if the actual answer correctly addresses the question compared to the expected answer.

Question: {question}

Expected Answer: {expected}

Actual Answer: {actual_excerpt}

Evaluate on these criteria:
1. Factual correctness: Does the actual answer contain correct information?
2. Completeness: Does it cover the key points of the expected answer?
3. Relevance: Is the information relevant to the question?

Respond in JSON format:
{
  "is_correct": true/false,
  "partial_score": <0.0-1.0>,
  "explanation": "<brief explanation>"
}

JSON only:
```

---

## 7) Benchmark Question Generation Prompt

- File:
  - `src/core/domain_benchmark.py`

```text
Generate 5 benchmark questions for evaluating a RAG system on this {domain} document.

Document Structure:
{tree_structure}

For each question, provide:
1. A question that requires finding specific information
2. The expected answer (based on the document structure)
3. Difficulty level (easy/medium/hard)
4. Whether it requires multi-section reasoning

JSON format:
{
  "questions": [
    {
      "question": "...",
      "expected_answer": "...",
      "difficulty": "easy|medium|hard",
      "requires_reasoning": true/false,
      "expected_sections": ["section_title_1", "section_title_2"]
    }
  ]
}

JSON only:
```

---

## 8) Batch Relevance Scoring Prompt

- File:
  - `src/core/beam_search.py`

```text
당신은 문서 검색 관련성 평가 전문가입니다.
사용자 질문에 대해 각 섹션의 관련성 점수(0.0~1.0)를 평가하세요.

### 사용자 질문:
{query}

### 평가 대상 섹션들:
{nodes_text}

### 평가 기준:
- 1.0: 질문에 직접 답변 가능
- 0.7-0.9: 매우 관련성 높음
- 0.4-0.6: 어느 정도 관련 있음
- 0.1-0.3: 약간 관련 있음
- 0.0: 전혀 관련 없음

### 응답 형식 (JSON):
{
  "scores": [
    {"index": 0, "score": 0.8, "reason": "이유"},
    {"index": 1, "score": 0.3, "reason": "이유"}
  ]
}

JSON만 출력하세요:
```

---

## 9) Section Relationship Inference Prompt

- File:
  - `src/core/reasoning_graph.py`

```text
Analyze the semantic relationship between two document sections.

Section A:
- Title: {title_a}
- Summary: {summary_a}

Section B:
- Title: {title_b}
- Summary: {summary_b}

Determine if there is a reasoning relationship between these sections.

Possible relationship types:
- cause_effect: A causes or leads to B
- support: A provides evidence/justification for B
- contrast: A contrasts or contradicts B
- elaboration: B elaborates or expands on A
- temporal: A precedes B in time/sequence
- reference: A references concepts in B
- definition: A defines terms used in B
- example: B is an example of concepts in A
- none: No significant relationship

Respond in JSON format:
{
  "relationship": "<type or 'none'>",
  "confidence": <0.0-1.0>,
  "direction": "a_to_b" or "b_to_a" or "bidirectional",
  "description": "<brief explanation>"
}

JSON only:
```

---

## 10) Seed Node Selection Prompt

- File:
  - `src/core/reasoning_graph.py`

```text
Given a query, identify the most relevant document sections.

Query: {query}

Available sections:
{formatted_nodes}

Return the IDs of the top {top_k} most relevant sections with relevance scores.

JSON format:
{
  "relevant_sections": [
    {"id": "<node_id>", "score": <0.0-1.0>, "reason": "<brief reason>"}
  ]
}

JSON only:
```

---

## 11) Final Answer Generation Prompt (Main Prompt)

- File:
  - `src/core/reasoner.py`

이 프롬프트는 아래를 조합해 최종 생성됩니다.

- `DOMAIN_PROMPTS[domain_template]`
- `LANGUAGE_INSTRUCTIONS[language]`
- 단계별 작성 지침
- (멀티 문서일 때) 비교 분석 지시문
- `context_str`
- `user_question`

```text
{domain_prompt}

{language_instruction}

### 📋 답변 작성 단계 (반드시 순서대로):

**STEP 1: 질문 핵심 파악**
- 질문에서 요구하는 핵심 정보가 무엇인지 명확히 파악

**STEP 2: 인덱스에서 정확한 정보 검색**
- 제공된 인덱스 JSON에서 질문과 관련된 섹션 찾기

**STEP 3: 핵심 답변 먼저 작성 (1-2문장)**
- 질문에 대한 직접적인 답변을 먼저 명확하게 제시
- 반드시 페이지 참조 포함: [문서명, p.페이지]

**STEP 4: 상세 설명 추가 (필요시)**
- 핵심 답변 이후 추가 맥락이나 상세 정보 제공

**STEP 5: 참조 페이지 요약**
- 답변 마지막에 📚 **참조 페이지** 형식으로 모든 출처 나열

### ⚠️ 중요 규칙:
1. 인덱스에 없는 정보는 절대 추측하지 마세요
2. 페이지 번호 필수
3. 간결하고 정확하게
4. 숫자/이름은 정확히
5. 질문 범위 밖 문장 금지
6. 마무리 문장 제한
{comparison_prompt_if_multi_doc}

### 답변 템플릿:
[핵심 답변 1-2문장 + 페이지 참조]
[상세 설명 (필요시) + 페이지 참조]

📚 **참조 페이지**: [문서명, p.X], [문서명, p.Y-Z]

### 컨텍스트:
{context_str}

### 질문:
{user_question}

### 답변 (위 규칙을 철저히 따라 작성):
```

### 11-1) Domain Prompt Blocks

- File:
  - `src/core/reasoner.py`

도메인별 시스템 프롬프트: `general`, `medical`, `legal`, `financial`, `academic`

### 11-2) Language Instruction Blocks

- File:
  - `src/core/reasoner.py`

언어 지시문:
- `ko`: 모든 답변은 한국어
- `en`: 영어만 사용
- `ja`: 일본어만 사용

---

## 12) API Health Check Prompt

- File:
  - `main.py`

```text
ping
```

---

## 13) (Tests) Real API Smoke Prompt

- File:
  - `tests/test_integration_real_api.py`

```text
Say 'ok' if you can hear me.
```

---

## Scope Notes

- 포함: 실제 `generate_content` 호출에 전달되는 프롬프트
- 제외: 단순 문자열 상수, mock 응답, API 미호출 문자열
- 테스트 프롬프트는 마지막 섹션에 별도 분리
