"""
웹 검색 기능 모듈
RAG 시스템에 웹 검색 기능을 추가하여 최신 정보를 활용할 수 있도록 함
"""
import requests
import json
import logging
import time
from typing import List, Dict, Optional, Tuple
from urllib.parse import quote_plus
import re

logger = logging.getLogger(__name__)

class WebSearchEngine:
    """웹 검색 엔진 클래스"""
    
    def __init__(self, api_key: str = None, search_engine: str = "google"):
        """
        Args:
            api_key: 검색 API 키 (Google Custom Search API 등)
            search_engine: 사용할 검색 엔진 ("google", "bing", "duckduckgo")
        """
        self.api_key = api_key
        self.search_engine = search_engine
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def search(self, query: str, num_results: int = 5, lang: str = "ko") -> List[Dict]:
        """
        웹 검색 실행
        
        Args:
            query: 검색 쿼리
            num_results: 반환할 결과 수
            lang: 검색 언어
            
        Returns:
            검색 결과 리스트
        """
        try:
            if self.search_engine == "google":
                return self._search_google(query, num_results, lang)
            elif self.search_engine == "bing":
                return self._search_bing(query, num_results, lang)
            elif self.search_engine == "duckduckgo":
                return self._search_duckduckgo(query, num_results, lang)
            else:
                logger.warning(f"지원하지 않는 검색 엔진: {self.search_engine}")
                return []
        except Exception as e:
            logger.error(f"웹 검색 오류: {e}")
            return []
    
    def _search_google(self, query: str, num_results: int, lang: str) -> List[Dict]:
        """Google Custom Search API 사용"""
        if not self.api_key:
            logger.warning("Google API 키가 설정되지 않음")
            return self._search_google_web(query, num_results)
        
        try:
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                'key': self.api_key,
                'cx': 'YOUR_SEARCH_ENGINE_ID',  # Custom Search Engine ID 필요
                'q': query,
                'num': min(num_results, 10),
                'lr': f'lang_{lang}',
                'safe': 'medium'
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            for item in data.get('items', []):
                results.append({
                    'title': item.get('title', ''),
                    'url': item.get('link', ''),
                    'snippet': item.get('snippet', ''),
                    'source': 'Google'
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Google API 검색 오류: {e}")
            return self._search_google_web(query, num_results)
    
    def _search_google_web(self, query: str, num_results: int) -> List[Dict]:
        """Google 웹 검색 (API 없이)"""
        try:
            # Google 검색 URL
            search_url = f"https://www.google.com/search?q={quote_plus(query)}&num={num_results}"
            
            response = self.session.get(search_url, timeout=10)
            response.raise_for_status()
            
            # 간단한 HTML 파싱 (실제로는 BeautifulSoup 등 사용 권장)
            results = self._parse_google_results(response.text, num_results)
            return results
            
        except Exception as e:
            logger.error(f"Google 웹 검색 오류: {e}")
            return []
    
    def _search_bing(self, query: str, num_results: int, lang: str) -> List[Dict]:
        """Bing 검색"""
        try:
            # Bing 검색 URL
            search_url = f"https://www.bing.com/search?q={quote_plus(query)}&count={num_results}"
            
            response = self.session.get(search_url, timeout=10)
            response.raise_for_status()
            
            results = self._parse_bing_results(response.text, num_results)
            return results
            
        except Exception as e:
            logger.error(f"Bing 검색 오류: {e}")
            return []
    
    def _search_duckduckgo(self, query: str, num_results: int, lang: str) -> List[Dict]:
        """DuckDuckGo 검색"""
        try:
            # DuckDuckGo 검색 URL
            search_url = f"https://duckduckgo.com/html/?q={quote_plus(query)}"
            
            response = self.session.get(search_url, timeout=10)
            response.raise_for_status()
            
            results = self._parse_duckduckgo_results(response.text, num_results)
            return results
            
        except Exception as e:
            logger.error(f"DuckDuckGo 검색 오류: {e}")
            return []
    
    def _parse_google_results(self, html: str, num_results: int) -> List[Dict]:
        """Google 검색 결과 파싱"""
        results = []
        # 간단한 정규식으로 파싱 (실제로는 BeautifulSoup 사용 권장)
        title_pattern = r'<h3[^>]*>([^<]+)</h3>'
        url_pattern = r'href="([^"]+)"'
        
        titles = re.findall(title_pattern, html)
        urls = re.findall(url_pattern, html)
        
        for i in range(min(len(titles), len(urls), num_results)):
            if 'google.com' not in urls[i]:  # Google 내부 링크 제외
                results.append({
                    'title': titles[i],
                    'url': urls[i],
                    'snippet': '',
                    'source': 'Google'
                })
        
        return results
    
    def _parse_bing_results(self, html: str, num_results: int) -> List[Dict]:
        """Bing 검색 결과 파싱"""
        results = []
        # Bing 결과 파싱 로직
        return results
    
    def _parse_duckduckgo_results(self, html: str, num_results: int) -> List[Dict]:
        """DuckDuckGo 검색 결과 파싱"""
        results = []
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')
            
            # DuckDuckGo 검색 결과 선택자
            result_links = soup.find_all('a', class_='result__a')
            
            for i, link in enumerate(result_links[:num_results]):
                title = link.get_text(strip=True)
                url = link.get('href', '')
                
                # 상대 URL을 절대 URL로 변환
                if url.startswith('/'):
                    url = 'https://duckduckgo.com' + url
                
                # snippet 찾기
                snippet = ''
                parent = link.parent
                if parent:
                    snippet_elem = parent.find('a', class_='result__snippet')
                    if snippet_elem:
                        snippet = snippet_elem.get_text(strip=True)
                
                if title and url:
                    results.append({
                        'title': title,
                        'url': url,
                        'snippet': snippet,
                        'source': 'DuckDuckGo'
                    })
            
        except Exception as e:
            logger.error(f"DuckDuckGo 결과 파싱 오류: {e}")
            # 간단한 정규식으로 대체
            import re
            title_pattern = r'<a[^>]*class="result__a"[^>]*>([^<]+)</a>'
            url_pattern = r'href="([^"]+)"'
            
            titles = re.findall(title_pattern, html)
            urls = re.findall(url_pattern, html)
            
            for i in range(min(len(titles), len(urls), num_results)):
                if titles[i] and urls[i]:
                    results.append({
                        'title': titles[i],
                        'url': urls[i],
                        'snippet': '',
                        'source': 'DuckDuckGo'
                    })
        
        return results

class WebSearchRetriever:
    """웹 검색 결과를 RAG 시스템에 통합하는 클래스"""
    
    def __init__(self, web_search_engine: WebSearchEngine, max_results: int = 3):
        """
        Args:
            web_search_engine: 웹 검색 엔진
            max_results: 최대 검색 결과 수
        """
        self.web_search_engine = web_search_engine
        self.max_results = max_results
    
    def should_use_web_search(self, question: str) -> bool:
        """
        웹 검색이 필요한지 판단
        
        Args:
            question: 사용자 질문
            
        Returns:
            웹 검색 필요 여부
        """
        # 최신 정보가 필요한 키워드들
        web_keywords = [
            # 시간 관련
            "최신", "현재", "오늘", "어제", "이번 주", "이번 달", "올해",
            "뉴스", "시사", "정책", "법령", "규정", "변경", "개정",
            "실시간", "라이브", "현재 상황", "최근", "최신 동향",
            # 교통 관련 최신 정보
            "교통사고", "사고", "충돌", "안전", "위험", "다발", "구간",
            "버스", "지하철", "택시", "자전거", "도로", "신호등",
            "교통정책", "교통법", "교통규정", "교통안전",
            # 일반적인 최신 정보 요청
            "어떻게", "어디서", "언제", "왜", "무엇을", "누가",
            "알려주세요", "알려줘", "도와주세요", "도와줘"
        ]
        
        question_lower = question.lower()
        
        # 웹 검색이 필요한 키워드가 있는지 확인
        for keyword in web_keywords:
            if keyword in question_lower:
                return True
        
        # 시간 관련 표현이 있는지 확인
        time_patterns = [
            r'\d{4}년', r'\d{1,2}월', r'\d{1,2}일',
            r'최근', r'최신', r'현재', r'오늘', r'어제', r'내일'
        ]
        
        for pattern in time_patterns:
            if re.search(pattern, question):
                return True
        
        # 질문 형태 감지
        question_patterns = [
            r'어떻게\s+', r'어디서\s+', r'언제\s+', r'왜\s+', r'무엇을\s+', r'누가\s+',
            r'알려주세요', r'알려줘', r'도와주세요', r'도와줘'
        ]
        
        for pattern in question_patterns:
            if re.search(pattern, question):
                return True
        
        return False
    
    def search_and_format(self, question: str) -> str:
        """
        웹 검색을 실행하고 결과를 포맷팅
        
        Args:
            question: 검색할 질문
            
        Returns:
            포맷팅된 검색 결과
        """
        if not self.should_use_web_search(question):
            return ""
        
        try:
            # 웹 검색 실행
            results = self.web_search_engine.search(question, self.max_results)
            
            if not results:
                return ""
            
            # 결과 포맷팅 및 내용 추출
            formatted_results = "=== 최신 웹 검색 결과 ===\n"
            for i, result in enumerate(results, 1):
                formatted_results += f"{i}. {result['title']}\n"
                formatted_results += f"   🔗 링크: {result['url']}\n"
                
                # 웹 페이지 내용 추출 시도
                content = self._extract_web_content_simple(result['url'])
                
                if content and len(content) > 50:
                    # LLM을 사용하여 내용 요약
                    summary = self._summarize_content(content, question)
                    formatted_results += f"   📄 내용: {summary}\n"
                elif result['snippet'] and len(result['snippet']) > 20:
                    # snippet을 LLM으로 요약
                    summary = self._summarize_content(result['snippet'], question)
                    formatted_results += f"   📄 내용: {summary}\n"
                else:
                    # 기본 정보 제공
                    formatted_results += f"   📄 내용: {result['title']}에 대한 자세한 내용을 확인하려면 위 링크를 클릭해주세요.\n"
                formatted_results += "\n"
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"웹 검색 및 포맷팅 오류: {e}")
            return ""
    
    def _extract_web_content(self, url: str, max_length: int = 800) -> str:
        """
        웹 페이지에서 실제 내용 추출
        
        Args:
            url: 웹 페이지 URL
            max_length: 최대 추출 길이
            
        Returns:
            추출된 내용
        """
        try:
            import requests
            from bs4 import BeautifulSoup
            import time
            from urllib.parse import unquote, parse_qs
            import re
            
            # 요청 간격 조절
            time.sleep(0.3)
            
            # DuckDuckGo 리다이렉트 URL 처리
            if 'duckduckgo.com/l/?uddg=' in url:
                try:
                    # URL 디코딩
                    decoded_url = unquote(url.split('uddg=')[1])
                    url = decoded_url
                except:
                    pass
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 불필요한 태그 제거
            for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'menu', 'form', 'button']):
                tag.decompose()
            
            # 본문 내용 추출 - 더 많은 선택자 시도
            content_selectors = [
                'article', '.article-content', '.news-content', '.content',
                'main', '.main-content', '.post-content', '.entry-content',
                '.news-text', '.article-text', '.story-content', '.news-body',
                '.article-body', '.post-body', '.entry-body', '.content-body',
                '.news-article', '.article', '.post', '.entry',
                '.news-item', '.news-list', '.article-list',
                'div[class*="content"]', 'div[class*="article"]', 'div[class*="news"]',
                'div[class*="post"]', 'div[class*="entry"]', 'div[class*="story"]'
            ]
            
            content = ""
            for selector in content_selectors:
                try:
                    elements = soup.select(selector)
                    if elements:
                        for element in elements:
                            text = element.get_text(strip=True)
                            if len(text) > 100:  # 충분한 길이의 텍스트만 선택
                                content = text
                                break
                        if content:
                            break
                except:
                    continue
            
            # 본문을 찾지 못한 경우 전체 텍스트에서 추출
            if not content or len(content) < 50:
                # body 태그에서 추출
                body = soup.find('body')
                if body:
                    content = body.get_text(strip=True)
                else:
                    content = soup.get_text(strip=True)
            
            # 텍스트 정리
            content = ' '.join(content.split())
            
            # 불필요한 텍스트 제거
            content = re.sub(r'\s+', ' ', content)  # 여러 공백을 하나로
            content = re.sub(r'[^\w\s가-힣.,!?()]', '', content)  # 특수문자 제거
            
            # 길이 제한
            if len(content) > max_length:
                content = content[:max_length] + "..."
            
            return content
            
        except Exception as e:
            logger.error(f"웹 페이지 내용 추출 오류 ({url}): {e}")
            return ""
    
    def _extract_web_content_fallback(self, url: str, max_length: int = 800) -> str:
        """
        웹 페이지 내용 추출 실패 시 대체 방법
        
        Args:
            url: 웹 페이지 URL
            max_length: 최대 추출 길이
            
        Returns:
            추출된 내용
        """
        try:
            import requests
            import re
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # HTML에서 텍스트만 추출
            text = response.text
            
            # HTML 태그 제거
            text = re.sub(r'<[^>]+>', ' ', text)
            
            # 불필요한 문자 제거
            text = re.sub(r'\s+', ' ', text)
            text = re.sub(r'[^\w\s가-힣.,!?()]', '', text)
            
            # 길이 제한
            if len(text) > max_length:
                text = text[:max_length] + "..."
            
            return text
            
        except Exception as e:
            logger.error(f"웹 페이지 내용 추출 대체 방법 오류 ({url}): {e}")
            return ""
    
    def _extract_web_content_simple(self, url: str, max_length: int = 800) -> str:
        """
        간단한 웹 페이지 내용 추출
        
        Args:
            url: 웹 페이지 URL
            max_length: 최대 추출 길이
            
        Returns:
            추출된 내용
        """
        try:
            import requests
            import re
            from urllib.parse import unquote
            
            # DuckDuckGo 리다이렉트 URL 처리
            if 'duckduckgo.com/l/?uddg=' in url:
                try:
                    decoded_url = unquote(url.split('uddg=')[1])
                    url = decoded_url
                except:
                    pass
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # HTML에서 텍스트만 추출
            text = response.text
            
            # HTML 태그 제거
            text = re.sub(r'<[^>]+>', ' ', text)
            
            # 불필요한 문자 제거
            text = re.sub(r'\s+', ' ', text)
            text = re.sub(r'[^\w\s가-힣.,!?()]', '', text)
            
            # 길이 제한
            if len(text) > max_length:
                text = text[:max_length] + "..."
            
            # 디버깅을 위한 로그 추가
            logger.info(f"웹 페이지 내용 추출 성공 ({url}): {len(text)}자")
            return text
            
        except Exception as e:
            logger.error(f"간단한 웹 페이지 내용 추출 오류 ({url}): {e}")
            return ""
    
    def _summarize_content(self, content: str, question: str) -> str:
        """
        LLM을 사용하여 웹 페이지 내용을 요약
        
        Args:
            content: 웹 페이지 내용
            question: 원본 질문
            
        Returns:
            요약된 내용
        """
        try:
            import requests
            import json
            
            # Ollama API를 사용하여 요약
            ollama_url = "http://ollama:11434/api/generate"
            
            prompt = f"""
다음 웹 페이지 내용을 사용자의 질문에 맞게 요약해주세요.

사용자 질문: {question}

웹 페이지 내용:
{content}

요약 요구사항:
1. 핵심 내용만 간결하게 요약
2. 사용자 질문과 관련된 정보 중심으로 정리
3. 3-4문장 이내로 요약
4. 구체적인 수치나 날짜가 있으면 포함
5. 한국어로 작성

요약:
"""
            
            payload = {
                "model": "qwen2.5:3b-instruct",
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "max_tokens": 200
                }
            }
            
            response = requests.post(ollama_url, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            summary = result.get('response', '').strip()
            
            # 요약이 너무 길면 자르기
            if len(summary) > 300:
                summary = summary[:300] + "..."
            
            return summary
            
        except Exception as e:
            logger.error(f"LLM 요약 오류: {e}")
            # 요약 실패 시 원본 내용의 일부 반환
            return content[:200] + "..." if len(content) > 200 else content

class HybridRAGWithWeb:
    """RAG + 웹 검색을 결합한 하이브리드 시스템"""
    
    def __init__(self, rag_pipeline, web_search_retriever: WebSearchRetriever):
        """
        Args:
            rag_pipeline: 기존 RAG 파이프라인
            web_search_retriever: 웹 검색 리트리버
        """
        self.rag_pipeline = rag_pipeline
        self.web_search_retriever = web_search_retriever
    
    def ask_with_web(self, question: str, mode: str = "accuracy") -> Dict:
        """
        RAG + 웹 검색을 결합한 질의응답
        
        Args:
            question: 사용자 질문
            mode: 응답 모드
            
        Returns:
            답변 결과 (RAG 결과 + 웹 검색 결과)
        """
        # 1. 기존 RAG 시스템으로 답변 생성
        rag_result = self.rag_pipeline.ask(question, mode)
        
        # 2. 웹 검색이 필요한지 판단
        web_search_results = self.web_search_retriever.search_and_format(question)
        
        # 3. 결과 결합
        combined_answer = rag_result.text
        
        if web_search_results:
            combined_answer += "\n\n" + web_search_results
        
        # 4. 메타데이터 업데이트
        metrics = rag_result.metrics.copy()
        metrics["web_search_used"] = bool(web_search_results)
        metrics["web_search_results_count"] = len(web_search_results.split('\n')) if web_search_results else 0
        
        return {
            "answer": combined_answer,
            "confidence": rag_result.confidence,
            "sources": rag_result.sources,
            "metrics": metrics,
            "fallback_used": rag_result.fallback_used,
            "web_search_results": web_search_results
        }

def create_web_search_engine(api_key: str = None, search_engine: str = "google") -> WebSearchEngine:
    """웹 검색 엔진 생성"""
    return WebSearchEngine(api_key=api_key, search_engine=search_engine)

def create_hybrid_rag_with_web(rag_pipeline, api_key: str = None, search_engine: str = "google") -> HybridRAGWithWeb:
    """RAG + 웹 검색 하이브리드 시스템 생성"""
    web_search_engine = create_web_search_engine(api_key, search_engine)
    web_search_retriever = WebSearchRetriever(web_search_engine)
    return HybridRAGWithWeb(rag_pipeline, web_search_retriever)
