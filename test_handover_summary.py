#!/usr/bin/env python3
"""
OpenAI GPT-4 인수인계 명료화 기능 종합 테스트
- 직접 요청 방식 테스트
- 프로토콜 래퍼 방식 테스트
- 다양한 인수인계 상황별 테스트
"""

import socket
import struct
import json
import time
from typing import Dict, Any, Optional

class HandoverSummaryTester:
    def __init__(self, host: str = "localhost", port: int = 6004):
        self.host = host
        self.port = port
        self.test_results = []
    
    def send_request_with_timing(self, request_data: Dict[str, Any]) -> tuple[Optional[Dict[str, Any]], float]:
        """서버에 요청을 보내고 응답 시간을 측정합니다."""
        start_time = time.time()
        
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(30)  # OpenAI 응답 대기시간 고려
                sock.connect((self.host, self.port))
                
                json_data = json.dumps(request_data, ensure_ascii=False)
                json_bytes = json_data.encode('utf-8')
                
                total_size = len(json_bytes)
                header = struct.pack('<II', total_size, total_size)
                
                sock.send(header + json_bytes)
                
                response_header = sock.recv(8)
                if len(response_header) < 8:
                    return None, time.time() - start_time
                
                total_size, json_size = struct.unpack('<II', response_header)
                
                response_data = b""
                while len(response_data) < json_size:
                    chunk = sock.recv(json_size - len(response_data))
                    if not chunk:
                        break
                    response_data += chunk
                
                response_time = time.time() - start_time
                return json.loads(response_data.decode('utf-8')), response_time
                
        except Exception as e:
            response_time = time.time() - start_time
            print(f"❌ 요청 실패 ({response_time:.2f}초): {e}")
            return None, response_time
    
    def test_direct_request(self, input_text: str, test_name: str) -> Dict[str, Any]:
        """직접 요청 방식 테스트"""
        print(f"🧪 [직접 요청] {test_name}")
        
        request = {
            "task": "summarize_handover",
            "input_text": input_text
        }
        
        response, response_time = self.send_request_with_timing(request)
        
        result = {
            "test_name": test_name,
            "request_type": "direct",
            "response_time": round(response_time, 2),
            "success": False,
            "input_length": len(input_text),
            "output_length": 0,
            "summary_quality": 0
        }
        
        if response and response.get("status") == "success":
            result["success"] = True
            summary = response.get("result", "")
            result["output_length"] = len(summary)
            result["summary_quality"] = self.evaluate_summary_quality(input_text, summary)
            
            print(f"   ✅ 성공 | 시간: {response_time:.2f}초 | 품질: {result['summary_quality']}/10")
            print(f"   📝 요약: {summary[:100]}...")
        else:
            print(f"   ❌ 실패 | 시간: {response_time:.2f}초")
            if response:
                result["error"] = response.get("status", "Unknown error")
        
        return result
    
    def test_protocol_wrapper(self, input_text: str, test_name: str) -> Dict[str, Any]:
        """프로토콜 래퍼 방식 테스트"""
        print(f"🧪 [프로토콜 래퍼] {test_name}")
        
        request = {
            "protocol": "py_req_handover_summary",
            "data": {
                "task": "summarize_handover",
                "input_text": input_text
            }
        }
        
        response, response_time = self.send_request_with_timing(request)
        
        result = {
            "test_name": test_name,
            "request_type": "protocol_wrapper",
            "response_time": round(response_time, 2),
            "success": False,
            "input_length": len(input_text),
            "output_length": 0,
            "summary_quality": 0
        }
        
        if response and response.get("protocol") == "res_handover_summary" and response.get("resp") == "success":
            result["success"] = True
            summary = response.get("data", {}).get("result", "")
            result["output_length"] = len(summary)
            result["summary_quality"] = self.evaluate_summary_quality(input_text, summary)
            
            print(f"   ✅ 성공 | 시간: {response_time:.2f}초 | 품질: {result['summary_quality']}/10")
            print(f"   📝 요약: {summary[:100]}...")
        else:
            print(f"   ❌ 실패 | 시간: {response_time:.2f}초")
            if response:
                result["error"] = response.get("resp", "Unknown error")
        
        return result
    
    def evaluate_summary_quality(self, original: str, summary: str) -> int:
        """요약 품질을 0-10점으로 평가합니다."""
        score = 5  # 기본 점수
        
        # 길이 적절성 (원문의 20-50%)
        length_ratio = len(summary) / len(original)
        if 0.2 <= length_ratio <= 0.5:
            score += 2
        elif 0.1 <= length_ratio <= 0.7:
            score += 1
        
        # 구조화 여부 (불릿포인트, 섹션 등)
        if any(marker in summary for marker in ['•', '-', '1.', '2.', '**', '##']):
            score += 2
        
        # 핵심 키워드 보존 (환자, 상태, 처치 등)
        key_terms = ['환자', '상태', '처치', '투약', '모니터링', '주의사항', '검사', '수술']
        preserved_terms = sum(1 for term in key_terms if term in original and term in summary)
        score += min(preserved_terms, 2)
        
        # 빈 요약 또는 너무 짧은 요약 감점
        if len(summary.strip()) < 50:
            score -= 3
        
        return max(0, min(10, score))
    
    def run_comprehensive_tests(self):
        """종합 테스트 실행"""
        print("🚀 OpenAI GPT-4 인수인계 명료화 기능 종합 테스트")
        print("=" * 70)
        
        # 테스트 시나리오
        test_scenarios = [
            {
                "name": "일반적인 인수인계",
                "text": """
                환자 301호 김할머니(75세)는 당뇨병성 신증으로 입원하신 분입니다. 
                현재 혈당 조절이 잘 안되고 있으며 아침 공복혈당이 180mg/dl로 측정되었습니다.
                인슐린 주사를 하루 3회 맞고 계시고, 식사 조절도 함께 하고 있습니다.
                소변량이 많아 탈수 위험이 있어 수액 주입 중이며, 혈압도 불안정하여 
                매 4시간마다 활력징후 체크 필요합니다. 가족 면회 시 교육도 필요한 상황입니다.
                """
            },
            {
                "name": "응급상황 인수인계", 
                "text": """
                응급실에서 올라온 202호 박환자(45세) 급성심근경색 의심 환자입니다.
                흉통 호소하며 EKG상 ST elevation 확인되었고 cardiac enzyme 상승 소견입니다.
                응급 심도자술 예정이며 현재 산소포화도 92%로 O2 4L/min 적용 중입니다.
                Aspirin, Plavix 투여 완료했고 Heparin drip 진행 중입니다.
                혈압 90/60으로 낮아 dopamine 0.5mcg/kg/min으로 시작했습니다.
                보호자는 부인으로 수술 동의서 작성 완료된 상태입니다.
                """
            },
            {
                "name": "수술 후 관리",
                "text": """
                오늘 오전 복강경 담낭절제술 받은 105호 이환자(52세)입니다.
                수술은 성공적으로 끝났고 회복실에서 안정된 상태로 병실로 올라왔습니다.
                현재 의식은 명료하지만 수술 부위 통증 호소하고 있어 PCA 연결되어 있습니다.
                배액관이 2개 삽입되어 있고 하루 배액량 체크 필요합니다.
                금식 상태이며 내일 가스배출 확인 후 식사 시작 예정입니다.
                항생제는 Cefazolin 8시간마다 투여하고 있고 활력징후는 안정적입니다.
                """
            },
            {
                "name": "소아환자 인수인계",
                "text": """
                301호 김아기(생후 8개월) 기관지폐렴으로 입원한 환아입니다.
                발열, 기침, 호흡곤란 증상이 있어 항생제 치료 중입니다.
                현재 체온 38.5도이며 해열제 투여 후 경과 관찰 중입니다.
                수유는 평소의 70% 정도 섭취하고 있고 보채는 증상이 있습니다.
                산소포화도 94%로 O2 2L/min 비강캐뉼러로 적용 중입니다.
                어머니가 24시간 보호자로 상주하고 있으며 모유수유 중입니다.
                """
            },
            {
                "name": "복잡한 다중질환",
                "text": """
                502호 최할아버지(82세)는 고혈압, 당뇨병, 심부전, 치매를 앓고 계시는 분입니다.
                이번에는 폐렴으로 입원하셨고 현재 항생제 치료 3일째입니다.
                혈당 조절을 위해 인슐린을 사용하고 있고 심부전으로 이뇨제를 복용 중입니다.
                치매로 인해 의사소통이 어렵고 가끔 불안해하시는 증상이 있습니다.
                낙상 위험이 높아 침대 안전바를 올려놓았고 보호자 상주가 필요한 상태입니다.
                복용하는 약물이 많아 상호작용 주의가 필요하고 신기능 모니터링도 중요합니다.
                """
            }
        ]
        
        print(f"📋 테스트 시나리오: {len(test_scenarios)}개")
        print(f"🔄 테스트 방식: 직접 요청 + 프로토콜 래퍼 (총 {len(test_scenarios) * 2}개)")
        print("=" * 70)
        
        total_tests = 0
        successful_tests = 0
        
        for scenario in test_scenarios:
            print(f"\n🎯 시나리오: {scenario['name']}")
            print("-" * 50)
            
            # 직접 요청 방식 테스트
            result1 = self.test_direct_request(scenario["text"].strip(), scenario["name"])
            self.test_results.append(result1)
            total_tests += 1
            if result1["success"]:
                successful_tests += 1
            
            time.sleep(1)  # OpenAI API 호출 간격
            
            # 프로토콜 래퍼 방식 테스트
            result2 = self.test_protocol_wrapper(scenario["text"].strip(), scenario["name"])
            self.test_results.append(result2)
            total_tests += 1
            if result2["success"]:
                successful_tests += 1
            
            time.sleep(1)  # 다음 테스트와의 간격
        
        # 결과 분석
        self.analyze_results(total_tests, successful_tests)
    
    def analyze_results(self, total_tests: int, successful_tests: int):
        """테스트 결과 분석 및 리포트"""
        print(f"\n" + "=" * 70)
        print("📊 인수인계 명료화 기능 테스트 결과 분석")
        print("=" * 70)
        
        success_rate = (successful_tests / total_tests) * 100
        print(f"✅ 전체 성공률: {success_rate:.1f}% ({successful_tests}/{total_tests})")
        
        # 방식별 성공률
        direct_results = [r for r in self.test_results if r["request_type"] == "direct"]
        wrapper_results = [r for r in self.test_results if r["request_type"] == "protocol_wrapper"]
        
        direct_success = len([r for r in direct_results if r["success"]])
        wrapper_success = len([r for r in wrapper_results if r["success"]])
        
        print(f"🔗 직접 요청 방식: {direct_success}/{len(direct_results)} ({(direct_success/len(direct_results)*100):.1f}%)")
        print(f"🔄 프로토콜 래퍼 방식: {wrapper_success}/{len(wrapper_results)} ({(wrapper_success/len(wrapper_results)*100):.1f}%)")
        
        # 성능 분석
        successful_results = [r for r in self.test_results if r["success"]]
        if successful_results:
            response_times = [r["response_time"] for r in successful_results]
            avg_time = sum(response_times) / len(response_times)
            min_time = min(response_times)
            max_time = max(response_times)
            
            print(f"\n⏱️ 응답 시간 분석:")
            print(f"  • 평균: {avg_time:.2f}초")
            print(f"  • 최소: {min_time:.2f}초")
            print(f"  • 최대: {max_time:.2f}초")
            
            # 품질 분석
            quality_scores = [r["summary_quality"] for r in successful_results]
            avg_quality = sum(quality_scores) / len(quality_scores)
            
            print(f"\n📝 요약 품질 분석:")
            print(f"  • 평균 품질: {avg_quality:.1f}/10점")
            print(f"  • 우수 요약 (8점 이상): {len([q for q in quality_scores if q >= 8])}개")
            print(f"  • 양호 요약 (6점 이상): {len([q for q in quality_scores if q >= 6])}개")
            
            # 압축률 분석
            compression_ratios = [r["output_length"] / r["input_length"] for r in successful_results if r["input_length"] > 0]
            if compression_ratios:
                avg_compression = sum(compression_ratios) / len(compression_ratios)
                print(f"  • 평균 압축률: {avg_compression:.1%} (원문 대비)")
        
        # 상세 결과 테이블
        print(f"\n📋 상세 결과 테이블:")
        print("시나리오           | 방식   | 시간(초) | 성공 | 품질 | 압축률")
        print("-" * 65)
        
        for result in self.test_results:
            name = result["test_name"][:15].ljust(15)
            req_type = "직접" if result["request_type"] == "direct" else "래퍼"
            time_str = f"{result['response_time']:6.2f}"
            success = "✅" if result["success"] else "❌"
            quality = f"{result['summary_quality']:4}/10" if result["success"] else "  -"
            
            if result["success"] and result["input_length"] > 0:
                compression = f"{(result['output_length'] / result['input_length']):.1%}"
            else:
                compression = "  -"
            
            print(f"{name} | {req_type} | {time_str} | {success} | {quality} | {compression}")
        
        print(f"\n🎉 OpenAI GPT-4 인수인계 명료화 기능 테스트 완료")
        if success_rate >= 80:
            print("🏆 우수한 성능! 실무 적용 준비 완료")
        elif success_rate >= 60:
            print("⚡ 양호한 성능! 일부 개선 후 적용 가능")
        else:
            print("⚠️ 성능 개선 필요")

if __name__ == "__main__":
    tester = HandoverSummaryTester()
    tester.run_comprehensive_tests()