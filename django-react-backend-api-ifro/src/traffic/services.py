from typing import Dict, Any, Union
from .models import TrafficVolume, TrafficInterpretation, Intersection
from django.db.models import Sum
from datetime import datetime
from django.core.exceptions import ValidationError
import re


class TrafficInterpretationService:
    """
    Service class for analyzing traffic data and generating interpretation sentences.
    """
    
    def __init__(self):
        # Congestion thresholds based on total volume and average speed
        self.congestion_thresholds = {
            'very_high': {'min_volume': 800, 'max_speed': 20},
            'high': {'min_volume': 500, 'max_speed': 30},
            'moderate': {'min_volume': 200, 'max_speed': 50},
            'low': {'min_volume': 0, 'max_speed': 100}
        }
        
        # Valid direction codes
        self.valid_directions = {'N', 'S', 'E', 'W'}
    
    def validate_request_data(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate traffic interpretation request data.
        
        Args:
            request_data: Dictionary containing request data
            
        Returns:
            Dictionary with validation results
            
        Raises:
            ValueError: If validation fails
        """
        errors = {}
        
        # Validate intersection_id
        intersection_id = request_data.get('intersection_id')
        if not intersection_id or not isinstance(intersection_id, int) or intersection_id <= 0:
            errors['intersection_id'] = 'Valid intersection ID is required (positive integer)'
        else:
            # Check if intersection exists
            if not Intersection.objects.filter(id=intersection_id).exists():
                errors['intersection_id'] = f'Intersection with ID {intersection_id} does not exist'
        
        # Validate datetime
        datetime_str = request_data.get('datetime')
        if not datetime_str or not isinstance(datetime_str, str):
            errors['datetime'] = 'Datetime string is required'
        else:
            try:
                self._validate_datetime_format(datetime_str)
            except ValueError as e:
                errors['datetime'] = str(e)
        
        # Validate traffic_volumes
        traffic_volumes = request_data.get('traffic_volumes')
        if not traffic_volumes or not isinstance(traffic_volumes, dict):
            errors['traffic_volumes'] = 'Traffic volumes dictionary is required'
        else:
            volume_errors = self._validate_traffic_volumes(traffic_volumes)
            if volume_errors:
                errors['traffic_volumes'] = volume_errors
        
        # Validate total_volume
        total_volume = request_data.get('total_volume')
        if total_volume is None or not isinstance(total_volume, (int, float)) or total_volume < 0:
            errors['total_volume'] = 'Total volume must be a non-negative number'
        
        # Validate average_speed
        average_speed = request_data.get('average_speed')
        if average_speed is None or not isinstance(average_speed, (int, float)) or average_speed < 0 or average_speed > 200:
            errors['average_speed'] = 'Average speed must be between 0 and 200 km/h'
        
        if errors:
            raise ValueError(f"Validation failed: {errors}")
        
        return {'valid': True, 'errors': {}}
    
    def _validate_datetime_format(self, datetime_str: str) -> None:
        """
        Validate datetime string format.
        
        Args:
            datetime_str: Datetime string to validate
            
        Raises:
            ValueError: If datetime format is invalid
        """
        try:
            # Try to parse ISO format datetime
            datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
        except ValueError:
            # Try alternative formats
            formats = [
                '%Y-%m-%dT%H:%M:%S',
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%dT%H:%M:%SZ'
            ]
            
            for fmt in formats:
                try:
                    datetime.strptime(datetime_str, fmt)
                    return
                except ValueError:
                    continue
            
            raise ValueError('Invalid datetime format. Expected ISO format (YYYY-MM-DDTHH:MM:SS)')
    
    def _validate_traffic_volumes(self, traffic_volumes: Dict[str, Any]) -> Dict[str, str]:
        """
        Validate traffic volumes data.
        
        Args:
            traffic_volumes: Dictionary with direction keys and volume values
            
        Returns:
            Dictionary with validation errors (empty if valid)
        """
        errors = {}
        
        # Check required directions
        for direction in self.valid_directions:
            if direction not in traffic_volumes:
                errors[direction] = f'Missing traffic volume for direction {direction}'
            else:
                volume = traffic_volumes[direction]
                if not isinstance(volume, (int, float)) or volume < 0:
                    errors[direction] = f'Traffic volume for {direction} must be a non-negative number'
        
        # Check for invalid directions
        for direction in traffic_volumes:
            if direction not in self.valid_directions:
                errors[direction] = f'Invalid direction code: {direction}. Valid codes are: {", ".join(self.valid_directions)}'
        
        return errors
    
    def analyze_traffic_data(self, traffic_data: Dict[str, Any], language: str = 'ko') -> Dict[str, Any]:
        """
        Analyze traffic data and return analysis results.
        
        Args:
            traffic_data: Dictionary containing traffic volumes, total volume, and average speed
            
        Returns:
            Dictionary containing analysis results
        """
        traffic_volumes = traffic_data.get('traffic_volumes', {})
        total_volume = traffic_data.get('total_volume', 0)
        average_speed = traffic_data.get('average_speed', 0)
        
        # Identify peak direction
        peak_direction = self.identify_peak_direction(traffic_volumes)
        
        # Determine congestion level
        congestion_level = self.determine_congestion_level(total_volume, average_speed)
        
        # Generate interpretation
        interpretation = self.generate_interpretation({
            'peak_direction': peak_direction,
            'congestion_level': congestion_level,
            'total_volume': total_volume,
            'average_speed': average_speed,
            'traffic_volumes': traffic_volumes
        }, language)
        
        return {
            'interpretation': interpretation,
            'congestion_level': congestion_level,
            'peak_direction': peak_direction,
            'analysis_summary': {
                'busiest_direction': self._get_direction_name(peak_direction),
                'traffic_condition': self._get_condition_description(congestion_level),
                'speed_assessment': self._get_speed_assessment(average_speed)
            }
        }
    
    def identify_peak_direction(self, traffic_volumes: Dict[str, int]) -> str:
        """
        Identify the direction with the highest traffic volume.
        
        Args:
            traffic_volumes: Dictionary with direction keys (N, S, E, W) and volume values
            
        Returns:
            Direction code with highest volume
        """
        if not traffic_volumes:
            return 'N'  # Default direction
        
        return max(traffic_volumes.items(), key=lambda x: x[1])[0]
    
    def determine_congestion_level(self, total_volume: int, average_speed: float) -> str:
        """
        Determine congestion level based on volume and speed.
        
        Args:
            total_volume: Total traffic volume
            average_speed: Average speed in km/h
            
        Returns:
            Congestion level string
        """
        # Check from highest to lowest congestion
        for level, thresholds in self.congestion_thresholds.items():
            if (total_volume >= thresholds['min_volume'] and 
                average_speed <= thresholds['max_speed']):
                return level
        
        return 'low'  # Default to low congestion
    
    def generate_interpretation(self, analysis_result: Dict[str, Any], language: str = 'ko') -> str:
        """
        Generate interpretation sentence based on analysis results in specified language.
        
        Args:
            analysis_result: Dictionary containing analysis data
            language: Language code ('ko', 'en', 'es')
            
        Returns:
            Interpretation sentence in specified language
        """
        peak_direction = analysis_result['peak_direction']
        congestion_level = analysis_result['congestion_level']
        total_volume = analysis_result['total_volume']
        average_speed = analysis_result['average_speed']
        
        direction_name = self._get_direction_name(peak_direction, language)
        
        if language == 'ko':
            # Korean interpretation
            base_interpretation = f"현재 교차로의 총 교통량은 {total_volume}대이며, 평균 속도는 {average_speed:.1f}km/h입니다."
            direction_info = f" {direction_name} 방향의 교통량이 가장 많습니다."
            
            if congestion_level == 'very_high':
                congestion_info = " 교통 상황이 매우 혼잡하여 통행에 상당한 지연이 예상됩니다."
            elif congestion_level == 'high':
                congestion_info = " 교통 상황이 혼잡하여 통행 시 주의가 필요합니다."
            elif congestion_level == 'moderate':
                congestion_info = " 교통 상황이 보통 수준으로 원활한 통행이 가능합니다."
            else:
                congestion_info = " 교통 상황이 원활하여 쾌적한 통행이 가능합니다."
                
        elif language == 'en':
            # English interpretation
            base_interpretation = f"The current intersection has a total traffic volume of {total_volume} vehicles with an average speed of {average_speed:.1f} km/h."
            direction_info = f" The {direction_name} direction has the highest traffic volume."
            
            if congestion_level == 'very_high':
                congestion_info = " Traffic conditions are severely congested with significant delays expected."
            elif congestion_level == 'high':
                congestion_info = " Traffic conditions are congested and caution is needed when traveling."
            elif congestion_level == 'moderate':
                congestion_info = " Traffic conditions are moderate with smooth travel possible."
            else:
                congestion_info = " Traffic conditions are smooth with comfortable travel possible."
                
        else:  # Spanish (es)
            # Spanish interpretation
            base_interpretation = f"La intersección actual tiene un volumen total de tráfico de {total_volume} vehículos con una velocidad promedio de {average_speed:.1f} km/h."
            direction_info = f" La dirección {direction_name} tiene el mayor volumen de tráfico."
            
            if congestion_level == 'very_high':
                congestion_info = " Las condiciones del tráfico están severamente congestionadas con retrasos significativos esperados."
            elif congestion_level == 'high':
                congestion_info = " Las condiciones del tráfico están congestionadas y se necesita precaución al viajar."
            elif congestion_level == 'moderate':
                congestion_info = " Las condiciones del tráfico son moderadas con viaje fluido posible."
            else:
                congestion_info = " Las condiciones del tráfico son fluidas con viaje cómodo posible."
        
        return base_interpretation + direction_info + congestion_info
    
    def _get_direction_name(self, direction_code: str, language: str = 'ko') -> str:
        """Convert direction code to localized name."""
        if language == 'ko':
            direction_names = {
                'N': '북쪽',
                'S': '남쪽', 
                'E': '동쪽',
                'W': '서쪽'
            }
        elif language == 'en':
            direction_names = {
                'N': 'North',
                'S': 'South', 
                'E': 'East',
                'W': 'West'
            }
        else:  # Spanish
            direction_names = {
                'N': 'Norte',
                'S': 'Sur', 
                'E': 'Este',
                'W': 'Oeste'
            }
        return direction_names.get(direction_code, direction_names['N'])
    
    def _get_condition_description(self, congestion_level: str) -> str:
        """Convert congestion level to Korean description."""
        descriptions = {
            'very_high': '매우 혼잡',
            'high': '혼잡',
            'moderate': '보통',
            'low': '원활'
        }
        return descriptions.get(congestion_level, '보통')
    
    def _get_speed_assessment(self, average_speed: float) -> str:
        """Generate speed assessment description."""
        if average_speed >= 50:
            return '속도가 양호함'
        elif average_speed >= 30:
            return '속도가 보통임'
        elif average_speed >= 20:
            return '속도가 느림'
        else:
            return '속도가 매우 느림'
    
    def save_interpretation(self, intersection_id: int, datetime_str: str, 
                          interpretation_data: Dict[str, Any]) -> TrafficInterpretation:
        """
        Save traffic interpretation to database.
        
        Args:
            intersection_id: ID of the intersection
            datetime_str: Datetime string
            interpretation_data: Analysis results
            
        Returns:
            TrafficInterpretation instance
        """
        try:
            intersection = Intersection.objects.get(id=intersection_id)
            datetime_obj = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
            
            # Create or update interpretation
            interpretation, created = TrafficInterpretation.objects.update_or_create(
                intersection=intersection,
                datetime=datetime_obj,
                defaults={
                    'interpretation_text': interpretation_data['interpretation'],
                    'congestion_level': interpretation_data['congestion_level'],
                    'peak_direction': interpretation_data['peak_direction']
                }
            )
            
            return interpretation
            
        except Intersection.DoesNotExist:
            raise ValueError(f"Intersection with ID {intersection_id} does not exist")
        except Exception as e:
            raise ValueError(f"Error saving interpretation: {str(e)}")