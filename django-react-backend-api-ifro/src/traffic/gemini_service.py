"""
Gemini AI Service for Traffic Analysis
Provides intelligent analysis of traffic data using Google's Gemini 2.5 Flash API
Updated: 2025-07-31 - Upgraded to Gemini 2.5 Flash for enhanced analysis
"""

import os
import json
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from django.conf import settings
from .models import TrafficVolume, Intersection


class GeminiTrafficAnalyzer:
    """
    Service class for analyzing traffic data using Gemini 2.5 Flash AI
    Enhanced with improved response parsing and error handling
    """
    
    def __init__(self):
        self.api_key = os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
        self.headers = {
            'Content-Type': 'application/json',
        }
    
    def analyze_intersection_traffic(
        self, 
        intersection_id: int, 
        time_period: str = "24h",
        language: str = "ko",
        use_report_data: bool = True
    ) -> Dict[str, Any]:
        """
        Analyze traffic data for a specific intersection
        
        Args:
            intersection_id: ID of the intersection to analyze
            time_period: Time period for analysis ("24h", "7d", "30d")
            
        Returns:
            Dictionary containing analysis results
        """
        try:
            # Get intersection data
            intersection = Intersection.objects.get(id=intersection_id)
            
            # Get traffic data based on time period or use report data
            total_info = {}
            if use_report_data:
                traffic_data, total_info = self._get_report_data_for_ai(intersection_id)
            else:
                traffic_data = self._get_traffic_data(intersection_id, time_period)
            
            # Track if we're using sample data
            is_sample_data = False
            
            # Check if we have sufficient real data
            # For report data mode, we accept even small amounts of real data
            min_records = 1 if use_report_data else 3
            
            # Check if traffic data has meaningful volume data (not all zeros)
            has_meaningful_data = False
            if traffic_data:
                total_volume = sum(item['volume'] for item in traffic_data)
                has_meaningful_data = total_volume > 0
            
            if not traffic_data or len(traffic_data) < min_records or not has_meaningful_data:
                print(f"Insufficient or empty real data ({len(traffic_data)} records, total volume: {sum(item['volume'] for item in traffic_data) if traffic_data else 0}) for intersection {intersection_id}")
                
                # Try to get any available data before falling back to sample data
                if use_report_data:
                    # For report mode, try regular traffic data method as fallback
                    fallback_data = self._get_traffic_data(intersection_id, "24h")
                    if fallback_data and sum(item['volume'] for item in fallback_data) > 0:
                        print(f"Using fallback traffic data: {len(fallback_data)} records")
                        traffic_data = fallback_data
                        is_sample_data = False
                    else:
                        print("No meaningful fallback data found, using sample data")
                        traffic_data = self._generate_sample_traffic_data(intersection, time_period)
                        is_sample_data = True
                else:
                    print("Using sample data")
                    traffic_data = self._generate_sample_traffic_data(intersection, time_period)
                    is_sample_data = True
            else:
                print(f"Using {len(traffic_data)} real traffic data records for intersection {intersection_id}")
                print(f"Total volume in real data: {sum(item['volume'] for item in traffic_data)}")
                is_sample_data = False
            
            # Prepare data for Gemini analysis
            # Pass additional context for report data mode
            extra_context = {}
            if use_report_data and not is_sample_data and total_info:
                extra_context = {
                    'total_volume': total_info.get('total_volume', sum(item['volume'] for item in traffic_data)),
                    'average_speed': total_info.get('average_speed', 0),
                    'is_report_data': True
                }
            
            analysis_prompt = self._create_analysis_prompt(intersection, traffic_data, time_period, language, is_sample_data, extra_context)
            
            # Call Gemini API
            gemini_response = self._call_gemini_api(analysis_prompt)
            
            # Parse and structure the response
            structured_analysis = self._parse_gemini_response(gemini_response, traffic_data)
            
            # Add sample data flag to response
            structured_analysis['is_sample_data'] = is_sample_data
            
            return structured_analysis
            
        except Intersection.DoesNotExist:
            return {
                'error': f'Intersection with ID {intersection_id} not found',
                'analysis': 'Error: Intersección no encontrada',
                'congestion_level': 'unknown',
                'peak_direction': 'N/A',
                'recommendations': [],
                'trends': [],
                'insights': []
            }
        except Exception as e:
            error_str = str(e)
            print(f"Gemini API Error: {error_str}")
            
            # Get traffic data for fallback analysis
            try:
                fallback_traffic_data = self._get_traffic_data(intersection_id, time_period)
                if not fallback_traffic_data:
                    fallback_traffic_data = self._generate_sample_traffic_data(intersection, time_period)
            except Exception as fallback_error:
                print(f"Fallback data generation error: {fallback_error}")
                fallback_traffic_data = self._generate_sample_traffic_data(intersection, time_period)
            
            # Language-specific error messages
            error_messages = {
                'ko': {
                    'analysis': f'AI 분석 생성 중 오류가 발생했습니다. 기본 분석을 사용합니다. (오류: {error_str[:100]})',
                    'recommendations': ['AI 분석 시스템 설정을 확인해주세요', 'API 키가 올바르게 설정되었는지 확인해주세요', '네트워크 연결 상태를 확인해주세요']
                },
                'en': {
                    'analysis': f'Error generating AI analysis. Using basic analysis. (Error: {error_str[:100]})',
                    'recommendations': ['Please check AI analysis system configuration', 'Verify API key is correctly set', 'Check network connectivity']
                },
                'es': {
                    'analysis': f'Error al generar análisis con IA. Usando análisis básico. (Error: {error_str[:100]})',
                    'recommendations': ['Revisar configuración del sistema de análisis IA', 'Verificar que la clave API esté configurada correctamente', 'Verificar conectividad de red']
                }
            }
            
            lang_error = error_messages.get(language, error_messages['ko'])
            
            # Determine error type for better handling
            error_type = 'unknown'
            if 'api key' in error_str.lower() or 'authentication' in error_str.lower():
                error_type = 'auth_error'
            elif 'quota' in error_str.lower() or 'limit' in error_str.lower():
                error_type = 'quota_error'
            elif 'network' in error_str.lower() or 'connection' in error_str.lower():
                error_type = 'network_error'
            elif 'timeout' in error_str.lower():
                error_type = 'timeout_error'
                
            return {
                'error': error_str,
                'error_type': error_type,
                'analysis': lang_error['analysis'],
                'congestion_level': self._calculate_basic_congestion(fallback_traffic_data) if fallback_traffic_data else 'unknown',
                'peak_direction': self._find_peak_direction(fallback_traffic_data) if fallback_traffic_data else 'N/A',
                'recommendations': lang_error['recommendations'],
                'trends': [],
                'insights': [],
                'ai_generated': False,
                'fallback_used': True,
                'timestamp': datetime.now().isoformat()
            }
    
    def _get_traffic_data(self, intersection_id: int, time_period: str) -> List[Dict]:
        """Get traffic data for the specified time period"""
        from .models import TotalTrafficVolume
        
        # First try to get recent data (within the specified time period from now)
        now = datetime.now()
        
        if time_period == "24h":
            start_time = now - timedelta(hours=24)
        elif time_period == "7d":
            start_time = now - timedelta(days=7)
        elif time_period == "30d":
            start_time = now - timedelta(days=30)
        else:
            start_time = now - timedelta(hours=24)
        
        traffic_volumes = TrafficVolume.objects.filter(
            intersection_id=intersection_id,
            datetime__gte=start_time
        ).order_by('-datetime')  # Order by most recent first
        
        # If no recent data found, get the latest available data regardless of time
        if not traffic_volumes.exists():
            print(f"No recent data found for intersection {intersection_id}, getting latest available data...")
            traffic_volumes = TrafficVolume.objects.filter(
                intersection_id=intersection_id
            ).order_by('-datetime')[:50]  # Get latest 50 records
        
        # Get TotalTrafficVolume data for speed information
        total_volumes = TotalTrafficVolume.objects.filter(
            intersection_id=intersection_id
        ).order_by('-datetime')[:20]  # Get more records for better speed mapping
        
        # Create a mapping of datetime to speed
        speed_map = {tv.datetime: tv.average_speed for tv in total_volumes}
        
        traffic_data = []
        for tv in traffic_volumes:
            # Get speed from TotalTrafficVolume if available, try to find closest datetime
            speed = speed_map.get(tv.datetime)
            if speed is None:
                # Find the closest datetime in speed_map
                closest_datetime = min(speed_map.keys(), key=lambda x: abs((x - tv.datetime).total_seconds()), default=None)
                speed = speed_map.get(closest_datetime, 45.0) if closest_datetime else 45.0
            
            traffic_data.append({
                'timestamp': tv.datetime.isoformat(),
                'direction': tv.direction,
                'volume': tv.volume,
                'speed': float(speed),
                'vehicle_type': getattr(tv, 'vehicle_type', 'unknown')
            })
        
        print(f"Found {len(traffic_data)} traffic data records for intersection {intersection_id}")
        if traffic_data:
            print(f"Latest data timestamp: {traffic_data[0]['timestamp']}")
            print(f"Traffic volumes by direction: {[(d['direction'], d['volume']) for d in traffic_data[:8]]}")  # Show first 8 records
        
        return traffic_data
    
    def _get_report_data_for_ai(self, intersection_id: int) -> tuple[List[Dict], Dict]:
        """Get the same data that Report Data API uses for consistency"""
        from .models import TotalTrafficVolume
        
        try:
            # Get the latest TotalTrafficVolume data (same as Report API)
            total_volume_data = TotalTrafficVolume.objects.filter(
                intersection_id=intersection_id
            ).order_by('-datetime').first()
            
            if not total_volume_data:
                print(f"No TotalTrafficVolume data found for intersection {intersection_id}")
                return [], {}
            
            # Get TrafficVolume data for the same datetime
            traffic_volumes_data = TrafficVolume.objects.filter(
                intersection_id=intersection_id,
                datetime=total_volume_data.datetime
            ).values('direction', 'volume')
            
            # Convert to the format expected by AI analysis
            traffic_data = []
            for volume_data in traffic_volumes_data:
                traffic_data.append({
                    'timestamp': total_volume_data.datetime.isoformat(),
                    'direction': volume_data['direction'],
                    'volume': volume_data['volume'],
                    'speed': float(total_volume_data.average_speed),
                    'vehicle_type': 'unknown'
                })
            
            # If no traffic volume data found for the specific datetime, try to get any available data
            if not traffic_data:
                print(f"No TrafficVolume data found for datetime {total_volume_data.datetime}, trying to get latest available data...")
                
                # Get the latest TrafficVolume data regardless of datetime
                latest_traffic_volumes = TrafficVolume.objects.filter(
                    intersection_id=intersection_id
                ).order_by('-datetime')[:4]  # Get latest 4 records (one for each direction)
                
                for volume_data in latest_traffic_volumes:
                    traffic_data.append({
                        'timestamp': volume_data.datetime.isoformat(),
                        'direction': volume_data.direction,
                        'volume': volume_data.volume,
                        'speed': float(total_volume_data.average_speed),
                        'vehicle_type': 'unknown'
                    })
                
                print(f"Found {len(traffic_data)} latest TrafficVolume records")
            
            # Return both traffic data and total volume info
            total_info = {
                'total_volume': total_volume_data.total_volume,
                'average_speed': float(total_volume_data.average_speed),
                'datetime': total_volume_data.datetime.isoformat()
            }
            
            print(f"Using Report Data: {len(traffic_data)} records from {total_volume_data.datetime}")
            print(f"Total volume: {total_volume_data.total_volume}, Average speed: {total_volume_data.average_speed}")
            print(f"Traffic data by direction: {[(d['direction'], d['volume']) for d in traffic_data]}")
            
            return traffic_data, total_info
            
        except Exception as e:
            print(f"Error getting report data for AI: {e}")
            return [], {}
    
    def _generate_sample_traffic_data(self, intersection: Intersection, time_period: str) -> List[Dict]:
        """Generate sample traffic data for demonstration when no real data exists"""
        import random
        from datetime import datetime, timedelta
        
        now = datetime.now()
        sample_data = []
        
        # Generate sample data points based on time period
        if time_period == "24h":
            data_points = 24  # 24 hours
            interval = timedelta(hours=1)
        elif time_period == "7d":
            data_points = 28  # 7 days * 4 points per day
            interval = timedelta(hours=6)
        else:  # 30d
            data_points = 30  # 30 days
            interval = timedelta(days=1)
        
        directions = ['N', 'S', 'E', 'W']
        
        for i in range(min(data_points, 50)):  # Limit to 50 data points
            timestamp = now - (interval * i)
            
            for direction in directions:
                # Generate realistic traffic patterns
                base_volume = random.randint(20, 100)
                # Add rush hour patterns (7-9 AM, 5-7 PM)
                hour = timestamp.hour
                if 7 <= hour <= 9 or 17 <= hour <= 19:
                    base_volume = int(base_volume * 1.5)
                
                sample_data.append({
                    'timestamp': timestamp.isoformat(),
                    'direction': direction,
                    'volume': base_volume + random.randint(-10, 10),
                    'speed': random.randint(25, 60),
                    'vehicle_type': random.choice(['car', 'truck', 'bus', 'motorcycle'])
                })
        
        return sample_data
    
    def _create_analysis_prompt(self, intersection: Intersection, traffic_data: List[Dict], time_period: str, language: str = "ko", is_sample_data: bool = False, extra_context: Dict = None) -> str:
        """Create a comprehensive prompt for Gemini analysis"""
        
        # Calculate basic statistics
        if extra_context and 'total_volume' in extra_context:
            total_volume = extra_context['total_volume']
            avg_speed = extra_context.get('average_speed', 0)
        else:
            total_volume = sum(item['volume'] for item in traffic_data)
            avg_speed = sum(item['speed'] for item in traffic_data if item['speed']) / len(traffic_data) if traffic_data else 0
        
        # Group by direction
        direction_volumes = {}
        for item in traffic_data:
            direction = item['direction']
            if direction not in direction_volumes:
                direction_volumes[direction] = []
            direction_volumes[direction].append(item['volume'])
        
        direction_stats = {
            direction: {
                'total': sum(volumes),
                'average': sum(volumes) / len(volumes) if volumes else 0,
                'peak': max(volumes) if volumes else 0
            }
            for direction, volumes in direction_volumes.items()
        }
        
        # Language-specific prompts
        prompts = {
            "es": {
                "title": "Eres un experto analista de tráfico y consultor de políticas públicas. Analiza los siguientes datos de tráfico para la intersección",
                "data_section": "DATOS DE LA INTERSECCIÓN",
                "name": "Nombre",
                "location": "Ubicación",
                "period": "Período de análisis",
                "total_records": "Total de registros",
                "general_stats": "ESTADÍSTICAS GENERALES",
                "total_volume": "Volumen total de tráfico",
                "avg_speed": "Velocidad promedio",
                "directions": "Direcciones analizadas",
                "direction_stats": "ESTADÍSTICAS POR DIRECCIÓN",
                "detailed_data": "DATOS DETALLADOS (últimos 20 registros)",
                "analysis_request": "Por favor, proporciona un análisis completo en formato JSON con la siguiente estructura",
                "analysis_field": "Análisis detallado de la situación del tráfico en español",
                "instructions": [
                    "El análisis debe ser en español y profesional",
                    "Identifica patrones de tráfico y horas pico",
                    "Evalúa el nivel de congestión basado en volumen y velocidad",
                    "Características temporales: Analiza en detalle las variaciones de tráfico por horas, períodos pico y patrones temporales del flujo vehicular",
                    "Características espaciales: Analiza la distribución direccional del tráfico, características geográficas de la ubicación del cruce y conectividad con la red vial circundante",
                    "Proporciona recomendaciones prácticas para mejorar el flujo",
                    "Considera factores como seguridad vial y eficiencia",
                    "Si hay datos insuficientes, menciona las limitaciones",
                    "Usa terminología técnica apropiada para gestión de tráfico",
                    "EVALUACIÓN DE POLÍTICAS: Evalúa la necesidad de políticas específicas como mejoras en semáforos, señalización, infraestructura peatonal, y accesibilidad",
                    "PRIORIZACIÓN: Clasifica las mejoras sugeridas por urgencia (alta, media, baja) y impacto esperado",
                    "FACTIBILIDAD: Considera la viabilidad técnica, económica y temporal de las recomendaciones"
                ],
                "sample_data_notice": "IMPORTANTE: Este análisis se basa en datos de muestra generados para demostración, no en datos reales de tráfico."
            },
            "en": {
                "title": "You are an expert traffic analyst and public policy consultant. Analyze the following traffic data for intersection",
                "data_section": "INTERSECTION DATA",
                "name": "Name",
                "location": "Location",
                "period": "Analysis period",
                "total_records": "Total records",
                "general_stats": "GENERAL STATISTICS",
                "total_volume": "Total traffic volume",
                "avg_speed": "Average speed",
                "directions": "Analyzed directions",
                "direction_stats": "STATISTICS BY DIRECTION",
                "detailed_data": "DETAILED DATA (last 20 records)",
                "analysis_request": "Please provide a complete analysis in JSON format with the following structure",
                "analysis_field": "Detailed analysis of traffic situation in English",
                "instructions": [
                    "The analysis should be in English and professional",
                    "Identify traffic patterns and peak hours",
                    "Evaluate congestion level based on volume and speed",
                    "Temporal characteristics: Analyze hourly traffic variations, peak periods, and temporal traffic flow patterns in detail",
                    "Spatial characteristics: Analyze directional traffic distribution, geographical features of intersection location, and connectivity with surrounding road network",
                    "Provide practical recommendations to improve flow",
                    "Consider factors like road safety and efficiency",
                    "If data is insufficient, mention limitations",
                    "Use appropriate technical terminology for traffic management",
                    "POLICY EVALUATION: Assess the need for specific policies such as traffic signal improvements, signage, pedestrian infrastructure, and accessibility enhancements",
                    "PRIORITIZATION: Classify suggested improvements by urgency (high, medium, low) and expected impact",
                    "FEASIBILITY: Consider technical, economic, and temporal feasibility of recommendations"
                ],
                "sample_data_notice": "IMPORTANT: This analysis is based on generated sample data for demonstration purposes, not actual traffic data."
            },
            "ko": {
                "title": "당신은 교통 분석 전문가이자 정책 제안 컨설턴트입니다. 다음 교차로의 교통 데이터를 분석해주세요",
                "data_section": "교차로 데이터",
                "name": "이름",
                "location": "위치",
                "period": "분석 기간",
                "total_records": "총 기록 수",
                "general_stats": "일반 통계",
                "total_volume": "총 교통량",
                "avg_speed": "평균 속도",
                "directions": "분석된 방향",
                "direction_stats": "방향별 통계",
                "detailed_data": "상세 데이터 (최근 20개 기록)",
                "analysis_request": "다음 구조의 JSON 형식으로 완전한 분석을 제공해주세요",
                "analysis_field": "한국어로 교통 상황에 대한 상세 분석",
                "instructions": [
                    "분석은 한국어로 전문적으로 작성해주세요",
                    "제공된 실제 교통 데이터를 기반으로 정확한 분석을 수행해주세요",
                    "각 방향별 교통량을 구체적으로 분석하고 0대인 방향이 있다면 그 이유를 설명해주세요",
                    "교통 패턴과 피크 시간을 식별해주세요",
                    "교통량과 속도를 기반으로 혼잡 수준을 평가해주세요",
                    "시간적 특성: 시간대별 교통량 변화, 피크 시간대, 교통 흐름의 시간적 패턴을 상세히 분석해주세요",
                    "공간적 특성: 방향별 교통량 분포, 교차로 위치의 지리적 특성, 주변 도로망과의 연계성을 분석해주세요",
                    "교통 흐름 개선을 위한 실용적인 권장사항을 제공해주세요",
                    "도로 안전과 효율성 같은 요소들을 고려해주세요",
                    "데이터가 불충분한 경우 한계점을 언급해주세요",
                    "교통 관리에 적절한 전문 용어를 사용해주세요",
                    "정책 평가: 신호등 개선, 표지판 설치, 보행자 인프라, 접근성 향상 등 구체적인 정책 필요성을 평가해주세요",
                    "우선순위: 제안된 개선사항을 긴급도(높음, 보통, 낮음)와 예상 효과에 따라 분류해주세요",
                    "실행 가능성: 권장사항의 기술적, 경제적, 시간적 실행 가능성을 고려해주세요",
                    "정책 제안 데이터: 시민 제안에 활용할 수 있는 구체적인 정책 제안 내용을 포함해주세요"
                ],
                "sample_data_notice": "중요: 이 분석은 실제 교통 데이터가 아닌 시연용 샘플 데이터를 기반으로 작성되었습니다."
            }
        }
        
        lang_prompt = prompts.get(language, prompts["ko"])
        
        # Add sample data notice if applicable
        sample_notice = ""
        if is_sample_data:
            sample_notice = f"\n⚠️ {lang_prompt['sample_data_notice']}\n"
        
        # Add report data notice if applicable
        report_notice = ""
        if extra_context and extra_context.get('is_report_data') and not is_sample_data:
            report_notice = f"\n📊 이 분석은 실제 교통 데이터를 기반으로 작성되었습니다. 총 교통량: {total_volume}대, 평균 속도: {avg_speed:.1f}km/h\n"
        elif not is_sample_data:
            report_notice = f"\n📊 이 분석은 실제 교통 데이터를 기반으로 작성되었습니다. 총 교통량: {total_volume}대, 평균 속도: {avg_speed:.1f}km/h\n"
        
        prompt = f"""
{lang_prompt["title"]} "{intersection.name}" {intersection.latitude}, {intersection.longitude}.
{sample_notice}{report_notice}
{lang_prompt["data_section"]}:
- {lang_prompt["name"]}: {intersection.name}
- {lang_prompt["location"]}: {intersection.latitude}, {intersection.longitude}
- {lang_prompt["period"]}: {time_period}
- {lang_prompt["total_records"]}: {len(traffic_data)}

{lang_prompt["general_stats"]}:
- {lang_prompt["total_volume"]}: {total_volume} vehicles
- {lang_prompt["avg_speed"]}: {avg_speed:.1f} km/h
- {lang_prompt["directions"]}: {list(direction_stats.keys())}

{lang_prompt["direction_stats"]}:
{json.dumps(direction_stats, indent=2, ensure_ascii=False)}

{lang_prompt["detailed_data"]}:
{json.dumps(traffic_data[-20:], indent=2, ensure_ascii=False)}

{lang_prompt["analysis_request"]}:
{{
    "analysis": "{lang_prompt["analysis_field"]}",
    "congestion_level": "low|medium|high",
    "peak_direction": "direction with highest flow",
    "recommendations": ["list", "of", "specific", "recommendations"],
    "trends": ["identified", "traffic", "trends"],
    "insights": ["key", "analysis", "insights"],
    "peak_hours": ["identified", "peak", "hours"],
    "improvement_suggestions": ["specific", "improvement", "suggestions"],
    "policy_evaluation": {{
        "safety_priority": "high|medium|low",
        "infrastructure_needs": ["specific", "infrastructure", "improvements"],
        "accessibility_issues": ["identified", "accessibility", "problems"],
        "signal_optimization": "needed|not_needed|urgent"
    }},
    "policy_proposals": [
        {{
            "category": "traffic_signal|road_safety|traffic_flow|infrastructure|policy|other",
            "title": "specific policy proposal title",
            "description": "detailed policy proposal description",
            "priority": "high|medium|low|urgent",
            "expected_impact": "high|medium|low",
            "implementation_difficulty": "easy|medium|hard",
            "estimated_cost": "low|medium|high",
            "timeline": "short|medium|long"
        }}
    ],
    "citizen_concerns": ["identified", "citizen", "concerns", "and", "complaints"],
    "data_driven_insights": ["data", "based", "insights", "for", "policy", "making"]
}}

INSTRUCTIONS:
{chr(10).join([f"{i+1}. {instruction}" for i, instruction in enumerate(lang_prompt["instructions"])])}
"""
        
        return prompt
    
    def _call_gemini_api(self, prompt: str) -> str:
        """Call Gemini API with the analysis prompt"""
        payload = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }],
            "generationConfig": {
                "temperature": 0.3,
                "topK": 40,
                "topP": 0.95,
                "maxOutputTokens": 8192,  # Significantly increased for complete analysis
                "candidateCount": 1,
                "stopSequences": []
            }
        }
        
        url = f"{self.base_url}?key={self.api_key}"
        
        try:
            print(f"Calling Gemini 2.5 Flash API with URL: {url[:50]}...")
            print(f"Request payload tokens estimate: {len(prompt.split()) * 1.3:.0f}")  # Rough estimate
            response = requests.post(url, headers=self.headers, json=payload, timeout=120)  # Increased timeout
            print(f"Response status: {response.status_code}")
            
            if response.status_code != 200:
                print(f"Response content: {response.text}")
                response.raise_for_status()
            
            result = response.json()
            print(f"API response keys: {result.keys()}")
            print(f"🔍 DEBUG: Full API response structure:")
            print(f"Response: {json.dumps(result, indent=2, ensure_ascii=False)[:1000]}...")
            
            # Enhanced logging for Gemini 2.5 Flash
            if 'candidates' in result and len(result['candidates']) > 0:
                candidate = result['candidates'][0]
                print(f"Candidate keys: {list(candidate.keys())}")
                if 'content' in candidate:
                    print(f"Content structure available: {list(candidate['content'].keys())}")
                    if 'parts' in candidate['content']:
                        print(f"Parts count: {len(candidate['content']['parts'])}")
                        if candidate['content']['parts']:
                            first_part = candidate['content']['parts'][0]
                            print(f"First part keys: {list(first_part.keys())}")
                            text_preview = first_part.get('text', '')[:100]
                            print(f"Text preview: '{text_preview}...'")
                else:
                    print("Warning: No content structure in candidate")
            
            if 'candidates' in result and len(result['candidates']) > 0:
                candidate = result['candidates'][0]
                if 'content' in candidate and 'parts' in candidate['content'] and len(candidate['content']['parts']) > 0:
                    text_content = candidate['content']['parts'][0].get('text', '')
                    if text_content:
                        return text_content
                    else:
                        # Debug: Print full response structure for empty content
                        print(f"🔍 DEBUG: Empty text content - Full candidate structure:")
                        print(f"Candidate keys: {list(candidate.keys())}")
                        if 'content' in candidate:
                            print(f"Content keys: {list(candidate['content'].keys())}")
                            if 'parts' in candidate['content']:
                                print(f"Parts: {candidate['content']['parts']}")
                        print(f"Full candidate: {json.dumps(candidate, indent=2, ensure_ascii=False)}")
                        raise Exception("Empty response from Gemini 2.5 Flash API - Debug info logged")
                else:
                    print(f"Invalid content structure in response: {candidate}")
                    raise Exception("Invalid response structure from Gemini 2.5 Flash API")
            else:
                print(f"No candidates in response: {result}")
                raise Exception("No response from Gemini 2.5 Flash API")
                
        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
            raise Exception(f"Gemini API request failed: {str(e)}")
        except Exception as e:
            print(f"General error: {e}")
            raise
    
    def _parse_gemini_response(self, gemini_response: str, traffic_data: List[Dict]) -> Dict[str, Any]:
        """Parse and structure Gemini's response"""
        try:
            # Enhanced JSON extraction for Gemini 2.5 Flash
            import re
            
            # First try to extract JSON from code blocks (```json ... ```)
            json_code_block = re.search(r'```json\s*(\{.*?\})\s*```', gemini_response, re.DOTALL)
            if json_code_block:
                json_str = json_code_block.group(1)
                print(f"🔍 Found JSON in code block: {json_str[:200]}...")
            else:
                # Fallback to general JSON pattern
                json_match = re.search(r'\{.*\}', gemini_response, re.DOTALL)
                if json_match:
                    json_str = json_match.group()
                    print(f"🔍 Found JSON pattern: {json_str[:200]}...")
                else:
                    json_str = None
            
            if json_str:
                try:
                    parsed_response = json.loads(json_str)
                    print(f"✅ Successfully parsed JSON: {list(parsed_response.keys())}")
                    
                    # Validate and clean the response
                    return {
                        'analysis': parsed_response.get('analysis', 'AI 분석이 생성되었습니다'),
                        'congestion_level': parsed_response.get('congestion_level', 'medium').lower(),
                        'peak_direction': parsed_response.get('peak_direction', 'N/A'),
                        'recommendations': parsed_response.get('recommendations', []),
                        'trends': parsed_response.get('trends', []),
                        'insights': parsed_response.get('insights', []),
                        'peak_hours': parsed_response.get('peak_hours', []),
                        'improvement_suggestions': parsed_response.get('improvement_suggestions', []),
                        'policy_evaluation': parsed_response.get('policy_evaluation', {
                            'safety_priority': 'medium',
                            'infrastructure_needs': [],
                            'accessibility_issues': [],
                            'signal_optimization': 'not_needed'
                        }),
                        'policy_proposals': parsed_response.get('policy_proposals', []),
                        'citizen_concerns': parsed_response.get('citizen_concerns', []),
                        'data_driven_insights': parsed_response.get('data_driven_insights', []),
                        'ai_generated': True,
                        'timestamp': datetime.now().isoformat()
                    }
                except json.JSONDecodeError as e:
                    print(f"❌ JSON parsing failed: {e}")
                    print(f"Raw JSON string: {json_str}")
                    # Continue to fallback
            
            # If JSON parsing fails, use the raw response but clean it up
            print("⚠️ No JSON found, using raw response")
            # Remove markdown code blocks and clean up the text
            clean_response = re.sub(r'```json\s*', '', gemini_response)
            clean_response = re.sub(r'\s*```', '', clean_response)
            clean_response = clean_response.strip()
            
            # Check if response seems incomplete (ends abruptly)
            if len(clean_response) > 100 and not clean_response.endswith(('.', '다.', '습니다.', '됩니다.', '있습니다.')):
                clean_response += "\n\n[참고: AI 분석이 완전하지 않을 수 있습니다. 더 자세한 분석이 필요한 경우 다시 시도해주세요.]"
            
            # Extract basic insights from the text
            extracted_recommendations = self._extract_recommendations_from_text(clean_response)
            extracted_insights = self._extract_insights_from_text(clean_response)
            
            return {
                'analysis': clean_response,
                'congestion_level': self._calculate_basic_congestion(traffic_data),
                'peak_direction': self._find_peak_direction(traffic_data),
                'recommendations': extracted_recommendations if extracted_recommendations else ['상세 분석이 텍스트 형태로 제공되었습니다'],
                'trends': [],
                'insights': extracted_insights,
                'policy_evaluation': {
                    'safety_priority': 'medium',
                    'infrastructure_needs': ['기본 인프라 개선 필요'],
                    'accessibility_issues': ['접근성 개선 필요'],
                    'signal_optimization': 'needed'
                },
                'policy_proposals': [],
                'citizen_concerns': ['시민 안전 및 편의성 개선 필요'],
                'data_driven_insights': ['데이터 기반 정책 수립 필요'],
                'ai_generated': True,
                'timestamp': datetime.now().isoformat()
            }
                
        except json.JSONDecodeError:
            # Fallback to basic analysis
            return {
                'analysis': gemini_response,
                'congestion_level': self._calculate_basic_congestion(traffic_data),
                'peak_direction': self._find_peak_direction(traffic_data),
                'recommendations': ['Ver análisis detallado en el texto principal'],
                'trends': [],
                'insights': [],
                'policy_evaluation': {
                    'safety_priority': 'medium',
                    'infrastructure_needs': ['Mejoras básicas de infraestructura necesarias'],
                    'accessibility_issues': ['Mejoras de accesibilidad necesarias'],
                    'signal_optimization': 'needed'
                },
                'policy_proposals': [],
                'citizen_concerns': ['Mejoras de seguridad y conveniencia ciudadana necesarias'],
                'data_driven_insights': ['Políticas basadas en datos necesarias'],
                'ai_generated': True,
                'timestamp': datetime.now().isoformat()
            }
    
    def _calculate_basic_congestion(self, traffic_data: List[Dict]) -> str:
        """Calculate basic congestion level from traffic data"""
        if not traffic_data:
            return 'unknown'
        
        avg_volume = sum(item['volume'] for item in traffic_data) / len(traffic_data)
        avg_speed = sum(item['speed'] for item in traffic_data if item['speed']) / len([item for item in traffic_data if item['speed']])
        
        # Simple heuristic for congestion level
        if avg_volume > 100 and avg_speed < 30:
            return 'high'
        elif avg_volume > 50 and avg_speed < 50:
            return 'medium'
        else:
            return 'low'
    
    def _extract_recommendations_from_text(self, text: str) -> List[str]:
        """Extract recommendations from AI analysis text"""
        recommendations = []
        
        # Look for recommendation patterns
        patterns = [
            r'권장사항[:\s]*([^\.]+\.)',
            r'추천[:\s]*([^\.]+\.)',
            r'제안[:\s]*([^\.]+\.)',
            r'개선[:\s]*([^\.]+\.)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            recommendations.extend([match.strip() for match in matches])
        
        return recommendations[:5]  # Limit to 5 recommendations
    
    def _extract_insights_from_text(self, text: str) -> List[str]:
        """Extract key insights from AI analysis text"""
        insights = []
        
        # Look for insight patterns
        patterns = [
            r'주요\s*특징[:\s]*([^\.]+\.)',
            r'핵심\s*분석[:\s]*([^\.]+\.)',
            r'중요한\s*점[:\s]*([^\.]+\.)',
            r'특이사항[:\s]*([^\.]+\.)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            insights.extend([match.strip() for match in matches])
        
        return insights[:5]  # Limit to 5 insights

    def _find_peak_direction(self, traffic_data: List[Dict]) -> str:
        """Find the direction with highest traffic volume"""
        if not traffic_data:
            return 'N/A'
        
        direction_volumes = {}
        for item in traffic_data:
            direction = item['direction']
            if direction not in direction_volumes:
                direction_volumes[direction] = 0
            direction_volumes[direction] += item['volume']
        
        if direction_volumes:
            peak_dir = max(direction_volumes, key=direction_volumes.get)
            peak_vol = direction_volumes[peak_dir]
            print(f"Peak direction calculation: {direction_volumes} -> {peak_dir} ({peak_vol})")
            return peak_dir
        return 'N/A'