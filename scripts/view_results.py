#!/usr/bin/env python3
"""
결과 요약 뷰어 - JSON 파싱 없이 읽기 쉬운 형태로 출력
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any


def format_percentage(value: float) -> str:
    """퍼센트 형식으로 포맷"""
    return f"{value * 100:.1f}%"


def format_number(value: float, precision: int = 3) -> str:
    """숫자 포맷"""
    return f"{value:.{precision}f}"


def get_winner_emoji(winner: str) -> str:
    """승자 이모지"""
    if winner == "TreeRAG":
        return "🌳 TreeRAG"
    elif winner == "FlatRAG":
        return "📄 FlatRAG"
    elif winner == "BM25":
        return "🔍 BM25"
    return "🤝 무승부"


def print_header(text: str):
    """헤더 출력"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def print_subheader(text: str):
    """서브헤더 출력"""
    print(f"\n📊 {text}")
    print("-" * 70)


def view_comparison_results(results_path: Path):
    """비교 결과 요약 출력"""
    
    if not results_path.exists():
        print(f"❌ 파일을 찾을 수 없습니다: {results_path}")
        return
    
    with open(results_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print_header("🎯 벤치마크 결과 요약")
    
    # 시스템 정보
    systems = data.get("systems", {})
    primary = systems.get("primary", "System A")
    baseline = systems.get("baseline", "System B")
    
    print(f"\n비교 시스템:")
    print(f"  🟢 주요 시스템: {primary}")
    print(f"  🔵 기준 시스템: {baseline}")
    
    # 전체 요약
    summary = data.get("summary", {})
    print_subheader("전체 승패")
    print(f"  {primary} 승리:  {summary.get(f'{primary}_wins', 0)}개 메트릭")
    print(f"  {baseline} 승리:  {summary.get(f'{baseline}_wins', 0)}개 메트릭")
    print(f"  무승부:         {summary.get('ties', 0)}개 메트릭")
    print(f"  전체 비교:      {summary.get('total_comparisons', 0)}개 메트릭")
    
    # 상세 비교
    comparisons = data.get("comparisons", {})
    
    print_subheader("검색 성능 (Retrieval Metrics)")
    retrieval_metrics = ["P@1", "P@3", "P@5", "P@10", "NDCG@1", "NDCG@3", "NDCG@5", "NDCG@10", "MRR"]
    
    for metric in retrieval_metrics:
        if metric in comparisons:
            comp = comparisons[metric]
            winner = comp.get("winner")
            primary_val = comp.get(f"{primary}_mean", 0)
            baseline_val = comp.get(f"{baseline}_mean", 0)
            p_value = comp.get("p_value", 1.0)
            effect_size = comp.get("effect_size", 0)
            
            # 통계적 유의성
            sig_marker = "✓" if p_value < 0.05 else "✗"
            
            # 효과 크기 해석
            effect_interp = comp.get("effect_interpretation", "negligible")
            
            winner_emoji = get_winner_emoji(winner) if winner else "🤝 무승부"
            
            print(f"\n  {metric:10s}  {winner_emoji}")
            print(f"    {primary:10s}: {format_percentage(primary_val):>6s}")
            print(f"    {baseline:10s}: {format_percentage(baseline_val):>6s}")
            print(f"    차이: {format_percentage(abs(primary_val - baseline_val)):>6s}  |  p-value: {p_value:.4f} {sig_marker}  |  효과: {effect_interp}")
    
    print_subheader("효율성 (Efficiency Metrics)")
    efficiency_metrics = ["Latency (ms)", "Tokens", "Nodes Visited"]
    
    for metric in efficiency_metrics:
        if metric in comparisons:
            comp = comparisons[metric]
            winner = comp.get("winner")
            primary_val = comp.get(f"{primary}_mean", 0)
            baseline_val = comp.get(f"{baseline}_mean", 0)
            p_value = comp.get("p_value", 1.0)
            
            sig_marker = "✓" if p_value < 0.05 else "✗"
            winner_emoji = get_winner_emoji(winner) if winner else "🤝 무승부"
            
            print(f"\n  {metric:15s}  {winner_emoji}")
            print(f"    {primary:10s}: {format_number(primary_val):>8s}")
            print(f"    {baseline:10s}: {format_number(baseline_val):>8s}")
            print(f"    차이: {format_number(abs(primary_val - baseline_val)):>8s}  |  p-value: {p_value:.4f} {sig_marker}")
    
    print_subheader("신뢰도 (Fidelity Metrics)")
    fidelity_metrics = ["Groundedness", "Hallucination Rate", "Citation Accuracy"]
    
    for metric in fidelity_metrics:
        if metric in comparisons:
            comp = comparisons[metric]
            winner = comp.get("winner")
            primary_val = comp.get(f"{primary}_mean", 0)
            baseline_val = comp.get(f"{baseline}_mean", 0)
            p_value = comp.get("p_value", 1.0)
            
            sig_marker = "✓" if p_value < 0.05 else "✗"
            winner_emoji = get_winner_emoji(winner) if winner else "🤝 무승부"
            
            print(f"\n  {metric:20s}  {winner_emoji}")
            print(f"    {primary:10s}: {format_percentage(primary_val):>6s}")
            print(f"    {baseline:10s}: {format_percentage(baseline_val):>6s}")
            print(f"    차이: {format_percentage(abs(primary_val - baseline_val)):>6s}  |  p-value: {p_value:.4f} {sig_marker}")
    
    # 결론
    print_header("📝 결론")
    
    if summary.get(f'{primary}_wins', 0) > summary.get(f'{baseline}_wins', 0):
        print(f"\n  🎉 {primary}가 {baseline}보다 우수합니다!")
    elif summary.get(f'{primary}_wins', 0) < summary.get(f'{baseline}_wins', 0):
        print(f"\n  ⚠️  {baseline}가 {primary}보다 우수합니다.")
    else:
        print(f"\n  🤝 {primary}와 {baseline}가 비슷한 성능을 보입니다.")
    
    print("\n  💡 통계적 유의성 (p-value < 0.05)이 있는 차이만 의미 있습니다.")
    print("\n" + "=" * 70 + "\n")


def view_evaluation_report(report_path: Path):
    """전체 평가 결과 요약"""
    
    if not report_path.exists():
        print(f"❌ 파일을 찾을 수 없습니다: {report_path}")
        return
    
    with open(report_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print_header("📊 전체 평가 결과")
    
    experiment = data.get("experiment", "Unknown")
    timestamp = data.get("timestamp", "Unknown")
    systems = data.get("systems", {})
    
    print(f"\n실험명: {experiment}")
    print(f"실행 시간: {timestamp}")
    print(f"평가 시스템: {', '.join(systems.keys())}")
    
    for system_name, system_data in systems.items():
        print_subheader(f"시스템: {system_name}")
        
        retrieval = system_data.get("retrieval_metrics", {})
        if retrieval:
            print("\n  검색 성능:")
            for metric, value in retrieval.items():
                if isinstance(value, dict):
                    for k, v in value.items():
                        print(f"    {metric}@{k}: {format_percentage(v)}")
                elif isinstance(value, (int, float)):
                    print(f"    {metric}: {format_percentage(value)}")
        
        efficiency = system_data.get("efficiency_metrics", {})
        if efficiency:
            print("\n  효율성:")
            avg_latency = efficiency.get("avg_latency_ms", 0)
            avg_tokens = efficiency.get("avg_tokens", 0)
            print(f"    평균 지연시간: {avg_latency:.2f}ms")
            print(f"    평균 토큰: {avg_tokens:.0f}")
        
        fidelity = system_data.get("fidelity_metrics", {})
        if fidelity:
            print("\n  신뢰도:")
            groundedness = fidelity.get("avg_groundedness", 0)
            print(f"    평균 근거성: {format_percentage(groundedness)}")
    
    print("\n" + "=" * 70 + "\n")


def main():
    """메인 함수"""
    
    if len(sys.argv) > 1:
        results_path = Path(sys.argv[1])
    else:
        # 기본 경로 찾기
        default_comparison = Path("benchmarks/results/default/treerag_vs_flatrag/comparison_report.json")
        default_evaluation = Path("benchmarks/results/default/evaluation_report.json")
        
        if default_comparison.exists():
            results_path = default_comparison
        elif default_evaluation.exists():
            results_path = default_evaluation
        else:
            print("❌ 결과 파일을 찾을 수 없습니다.")
            print("\n사용법:")
            print("  python scripts/view_results.py [결과_파일_경로]")
            print("\n예시:")
            print("  python scripts/view_results.py benchmarks/results/default/treerag_vs_flatrag/comparison_report.json")
            return
    
    # 파일 타입에 따라 다른 뷰어 호출
    if "comparison" in results_path.name:
        view_comparison_results(results_path)
    elif "evaluation" in results_path.name:
        view_evaluation_report(results_path)
    else:
        print(f"⚠️  알 수 없는 결과 파일 형식: {results_path.name}")
        print("comparison_report.json 또는 evaluation_report.json 파일을 사용하세요.")


if __name__ == "__main__":
    main()
