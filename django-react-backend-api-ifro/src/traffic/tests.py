from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import datetime, timedelta
import json
from unittest.mock import patch, MagicMock

from .models import Intersection, TrafficVolume, TotalTrafficVolume, TrafficInterpretation
from .services import TrafficInterpretationService
from .schemas import TrafficInterpretationRequestSchema


class TrafficInterpretationServiceTests(TestCase):
    """Unit tests for TrafficInterpretationService class methods"""
    
    def setUp(self):
        """Set up test data and service instance"""
        self.service = TrafficInterpretationService()
        
        # Create test intersection
        self.intersection = Intersection.objects.create(
            name="Test Intersection",
            latitude=37.5665,
            longitude=126.9780
        )
        
        # Test traffic data
        self.test_traffic_data = {
            'traffic_volumes': {'NS': 100, 'SN': 80, 'EW': 120, 'WE': 90},
            'total_volume': 390,
            'average_speed': 45.5
        }
        
        # Test request data
        self.test_request_data = {
            'intersection_id': self.intersection.id,
            'datetime': '2024-01-15T10:30:00Z',
            'traffic_volumes': {'NS': 100, 'SN': 80, 'EW': 120, 'WE': 90},
            'total_volume': 390,
            'average_speed': 45.5
        }
    
    def test_identify_peak_direction_normal_case(self):
        """Test peak direction identification with normal traffic data"""
        traffic_volumes = {'NS': 100, 'SN': 80, 'EW': 120, 'WE': 90}
        result = self.service.identify_peak_direction(traffic_volumes)
        self.assertEqual(result, 'EW', "Should identify EW as peak direction with highest volume")
    
    def test_identify_peak_direction_equal_volumes(self):
        """Test peak direction identification with equal volumes"""
        traffic_volumes = {'NS': 100, 'SN': 100, 'EW': 100, 'WE': 100}
        result = self.service.identify_peak_direction(traffic_volumes)
        self.assertIn(result, ['NS', 'SN', 'EW', 'WE'], "Should return one of the valid directions")
    
    def test_identify_peak_direction_empty_data(self):
        """Test peak direction identification with empty data"""
        result = self.service.identify_peak_direction({})
        self.assertEqual(result, 'NS', "Should return default NS direction for empty data")
    
    def test_determine_congestion_level_very_high(self):
        """Test congestion level determination for very high congestion"""
        result = self.service.determine_congestion_level(900, 15)
        self.assertEqual(result, 'very_high', "Should identify very high congestion")
    
    def test_determine_congestion_level_high(self):
        """Test congestion level determination for high congestion"""
        result = self.service.determine_congestion_level(600, 25)
        self.assertEqual(result, 'high', "Should identify high congestion")
    
    def test_determine_congestion_level_moderate(self):
        """Test congestion level determination for moderate congestion"""
        result = self.service.determine_congestion_level(300, 40)
        self.assertEqual(result, 'moderate', "Should identify moderate congestion")
    
    def test_determine_congestion_level_low(self):
        """Test congestion level determination for low congestion"""
        result = self.service.determine_congestion_level(100, 60)
        self.assertEqual(result, 'low', "Should identify low congestion")
    
    def test_determine_congestion_level_edge_cases(self):
        """Test congestion level determination for edge cases"""
        # Boundary case for very high
        result = self.service.determine_congestion_level(800, 20)
        self.assertEqual(result, 'very_high', "Should identify very high at boundary")
        
        # High volume but good speed
        result = self.service.determine_congestion_level(1000, 70)
        self.assertEqual(result, 'low', "Should prioritize speed over volume")
    
    def test_generate_interpretation_very_high_congestion(self):
        """Test interpretation generation for very high congestion"""
        analysis_result = {
            'peak_direction': 'EW',
            'congestion_level': 'very_high',
            'total_volume': 900,
            'average_speed': 15.0,
            'traffic_volumes': {'NS': 200, 'SN': 180, 'EW': 300, 'WE': 220}
        }
        
        result = self.service.generate_interpretation(analysis_result)
        
        self.assertIn('900대', result, "Should include total volume")
        self.assertIn('15.0km/h', result, "Should include average speed")
        self.assertIn('동서', result, "Should include peak direction in Korean")
        self.assertIn('매우 혼잡', result, "Should include congestion level description")
    
    def test_generate_interpretation_low_congestion(self):
        """Test interpretation generation for low congestion"""
        analysis_result = {
            'peak_direction': 'NS',
            'congestion_level': 'low',
            'total_volume': 150,
            'average_speed': 65.0,
            'traffic_volumes': {'NS': 50, 'SN': 40, 'EW': 30, 'WE': 30}
        }
        
        result = self.service.generate_interpretation(analysis_result)
        
        self.assertIn('150대', result, "Should include total volume")
        self.assertIn('65.0km/h', result, "Should include average speed")
        self.assertIn('남북', result, "Should include peak direction in Korean")
        self.assertIn('원활', result, "Should include low congestion description")
    
    def test_analyze_traffic_data_complete_flow(self):
        """Test complete traffic data analysis flow"""
        result = self.service.analyze_traffic_data(self.test_traffic_data)
        
        # Check all required fields are present
        self.assertIn('interpretation', result)
        self.assertIn('congestion_level', result)
        self.assertIn('peak_direction', result)
        self.assertIn('analysis_summary', result)
        
        # Check analysis summary structure
        summary = result['analysis_summary']
        self.assertIn('busiest_direction', summary)
        self.assertIn('traffic_condition', summary)
        self.assertIn('speed_assessment', summary)
        
        # Verify peak direction is correct
        self.assertEqual(result['peak_direction'], 'EW', "Should identify EW as peak direction")
        
        # Verify congestion level is reasonable
        self.assertEqual(result['congestion_level'], 'moderate', "Should identify moderate congestion")
    
    def test_validate_request_data_valid_input(self):
        """Test request data validation with valid input"""
        result = self.service.validate_request_data(self.test_request_data)
        self.assertTrue(result['valid'], "Should validate correct request data")
        self.assertEqual(result['errors'], {}, "Should have no validation errors")
    
    def test_validate_request_data_invalid_intersection_id(self):
        """Test request data validation with invalid intersection ID"""
        invalid_data = self.test_request_data.copy()
        invalid_data['intersection_id'] = -1
        
        with self.assertRaises(ValueError) as context:
            self.service.validate_request_data(invalid_data)
        
        self.assertIn('intersection ID', str(context.exception))
    
    def test_validate_request_data_nonexistent_intersection(self):
        """Test request data validation with non-existent intersection"""
        invalid_data = self.test_request_data.copy()
        invalid_data['intersection_id'] = 99999
        
        with self.assertRaises(ValueError) as context:
            self.service.validate_request_data(invalid_data)
        
        self.assertIn('does not exist', str(context.exception))
    
    def test_validate_request_data_invalid_datetime(self):
        """Test request data validation with invalid datetime"""
        invalid_data = self.test_request_data.copy()
        invalid_data['datetime'] = 'invalid-datetime'
        
        with self.assertRaises(ValueError) as context:
            self.service.validate_request_data(invalid_data)
        
        self.assertIn('datetime', str(context.exception))
    
    def test_validate_request_data_missing_traffic_volumes(self):
        """Test request data validation with missing traffic volumes"""
        invalid_data = self.test_request_data.copy()
        invalid_data['traffic_volumes'] = {'NS': 100, 'SN': 80}  # Missing EW, WE
        
        with self.assertRaises(ValueError) as context:
            self.service.validate_request_data(invalid_data)
        
        self.assertIn('traffic_volumes', str(context.exception))
    
    def test_validate_request_data_negative_volumes(self):
        """Test request data validation with negative traffic volumes"""
        invalid_data = self.test_request_data.copy()
        invalid_data['traffic_volumes']['NS'] = -50
        
        with self.assertRaises(ValueError) as context:
            self.service.validate_request_data(invalid_data)
        
        self.assertIn('non-negative', str(context.exception))
    
    def test_validate_request_data_invalid_speed(self):
        """Test request data validation with invalid average speed"""
        invalid_data = self.test_request_data.copy()
        invalid_data['average_speed'] = 250  # Too high
        
        with self.assertRaises(ValueError) as context:
            self.service.validate_request_data(invalid_data)
        
        self.assertIn('speed', str(context.exception))
    
    def test_save_interpretation_success(self):
        """Test successful interpretation saving"""
        interpretation_data = {
            'interpretation': 'Test interpretation text',
            'congestion_level': 'moderate',
            'peak_direction': 'EW'
        }
        
        result = self.service.save_interpretation(
            self.intersection.id,
            '2024-01-15T10:30:00Z',
            interpretation_data
        )
        
        self.assertIsInstance(result, TrafficInterpretation)
        self.assertEqual(result.interpretation_text, 'Test interpretation text')
        self.assertEqual(result.congestion_level, 'moderate')
        self.assertEqual(result.peak_direction, 'EW')
    
    def test_save_interpretation_update_existing(self):
        """Test updating existing interpretation"""
        # Create initial interpretation
        initial_data = {
            'interpretation': 'Initial interpretation',
            'congestion_level': 'low',
            'peak_direction': 'NS'
        }
        
        self.service.save_interpretation(
            self.intersection.id,
            '2024-01-15T10:30:00Z',
            initial_data
        )
        
        # Update with new data
        updated_data = {
            'interpretation': 'Updated interpretation',
            'congestion_level': 'high',
            'peak_direction': 'EW'
        }
        
        result = self.service.save_interpretation(
            self.intersection.id,
            '2024-01-15T10:30:00Z',
            updated_data
        )
        
        self.assertEqual(result.interpretation_text, 'Updated interpretation')
        self.assertEqual(result.congestion_level, 'high')
        
        # Verify only one record exists
        count = TrafficInterpretation.objects.filter(
            intersection=self.intersection,
            datetime__date=datetime(2024, 1, 15).date()
        ).count()
        self.assertEqual(count, 1, "Should update existing record, not create new one")
    
    def test_save_interpretation_nonexistent_intersection(self):
        """Test saving interpretation with non-existent intersection"""
        interpretation_data = {
            'interpretation': 'Test interpretation',
            'congestion_level': 'moderate',
            'peak_direction': 'EW'
        }
        
        with self.assertRaises(ValueError) as context:
            self.service.save_interpretation(
                99999,  # Non-existent ID
                '2024-01-15T10:30:00Z',
                interpretation_data
            )
        
        self.assertIn('does not exist', str(context.exception))
    
    def test_direction_name_conversion(self):
        """Test direction code to Korean name conversion"""
        self.assertEqual(self.service._get_direction_name('NS'), '남북')
        self.assertEqual(self.service._get_direction_name('SN'), '북남')
        self.assertEqual(self.service._get_direction_name('EW'), '동서')
        self.assertEqual(self.service._get_direction_name('WE'), '서동')
        self.assertEqual(self.service._get_direction_name('INVALID'), '남북')  # Default
    
    def test_condition_description_conversion(self):
        """Test congestion level to Korean description conversion"""
        self.assertEqual(self.service._get_condition_description('very_high'), '매우 혼잡')
        self.assertEqual(self.service._get_condition_description('high'), '혼잡')
        self.assertEqual(self.service._get_condition_description('moderate'), '보통')
        self.assertEqual(self.service._get_condition_description('low'), '원활')
        self.assertEqual(self.service._get_condition_description('invalid'), '보통')  # Default
    
    def test_speed_assessment(self):
        """Test speed assessment generation"""
        self.assertEqual(self.service._get_speed_assessment(60), '속도가 양호함')
        self.assertEqual(self.service._get_speed_assessment(40), '속도가 보통임')
        self.assertEqual(self.service._get_speed_assessment(25), '속도가 느림')
        self.assertEqual(self.service._get_speed_assessment(15), '속도가 매우 느림')


class TrafficInterpretationAPITests(TestCase):
    """Unit tests for traffic interpretation API endpoints"""
    
    def setUp(self):
        """Set up test data and client"""
        self.client = Client()
        
        # Create test intersection
        self.intersection = Intersection.objects.create(
            name="API Test Intersection",
            latitude=37.5665,
            longitude=126.9780
        )
        
        # Create test traffic data
        self.test_datetime = timezone.now()
        TotalTrafficVolume.objects.create(
            intersection=self.intersection,
            datetime=self.test_datetime,
            total_volume=400,
            average_speed=35.0
        )
        
        # Create traffic volumes by direction
        directions = [('NS', 100), ('SN', 90), ('EW', 120), ('WE', 90)]
        for direction, volume in directions:
            TrafficVolume.objects.create(
                intersection=self.intersection,
                datetime=self.test_datetime,
                direction=direction,
                volume=volume
            )
        
        # Valid request payload
        self.valid_payload = {
            'intersection_id': self.intersection.id,
            'datetime': '2024-01-15T10:30:00Z',
            'traffic_volumes': {
                'NS': 100,
                'SN': 90,
                'EW': 120,
                'WE': 90
            },
            'total_volume': 400,
            'average_speed': 35.0
        }
    
    def test_generate_interpretation_api_success(self):
        """Test successful traffic interpretation generation via API"""
        response = self.client.post(
            '/api/traffic/generate-interpretation',
            data=json.dumps(self.valid_payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn('interpretation', data)
        self.assertIn('congestion_level', data)
        self.assertIn('peak_direction', data)
        self.assertIn('analysis_summary', data)
        
        # Verify interpretation content
        self.assertIn('400대', data['interpretation'])
        self.assertIn('35.0km/h', data['interpretation'])
        self.assertEqual(data['peak_direction'], 'EW')
        
        # Verify analysis summary
        summary = data['analysis_summary']
        self.assertIn('busiest_direction', summary)
        self.assertIn('traffic_condition', summary)
        self.assertIn('speed_assessment', summary)
    
    def test_generate_interpretation_api_invalid_intersection(self):
        """Test API response with invalid intersection ID"""
        invalid_payload = self.valid_payload.copy()
        invalid_payload['intersection_id'] = 99999
        
        response = self.client.post(
            '/api/traffic/generate-interpretation',
            data=json.dumps(invalid_payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        
        data = response.json()
        self.assertIn('detail', data)
        self.assertIn('Request validation failed', data['detail'])
    
    def test_generate_interpretation_api_invalid_data(self):
        """Test API response with invalid request data"""
        invalid_payload = self.valid_payload.copy()
        invalid_payload['traffic_volumes']['NS'] = -50  # Negative volume
        
        response = self.client.post(
            '/api/traffic/generate-interpretation',
            data=json.dumps(invalid_payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 422)  # Schema validation error
        
        data = response.json()
        self.assertIn('detail', data)
    
    def test_generate_interpretation_api_missing_fields(self):
        """Test API response with missing required fields"""
        incomplete_payload = {
            'intersection_id': self.intersection.id,
            'datetime': '2024-01-15T10:30:00Z'
            # Missing traffic_volumes, total_volume, average_speed
        }
        
        response = self.client.post(
            '/api/traffic/generate-interpretation',
            data=json.dumps(incomplete_payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 422)  # Unprocessable Entity for schema validation
    
    def test_list_interpretations_api_success(self):
        """Test successful listing of traffic interpretations"""
        # Create test interpretation
        TrafficInterpretation.objects.create(
            intersection=self.intersection,
            datetime=self.test_datetime,
            interpretation_text='Test interpretation',
            congestion_level='moderate',
            peak_direction='EW'
        )
        
        response = self.client.get('/api/traffic/interpretations')
        
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)
        
        interpretation = data[0]
        self.assertIn('id', interpretation)
        self.assertIn('intersection_id', interpretation)
        self.assertIn('interpretation_text', interpretation)
        self.assertIn('congestion_level', interpretation)
        self.assertIn('peak_direction', interpretation)
    
    def test_list_interpretations_api_filtered(self):
        """Test listing interpretations filtered by intersection"""
        # Create another intersection and interpretation
        other_intersection = Intersection.objects.create(
            name="Other Intersection",
            latitude=37.5000,
            longitude=127.0000
        )
        
        TrafficInterpretation.objects.create(
            intersection=self.intersection,
            datetime=self.test_datetime,
            interpretation_text='First interpretation',
            congestion_level='moderate',
            peak_direction='EW'
        )
        
        TrafficInterpretation.objects.create(
            intersection=other_intersection,
            datetime=self.test_datetime,
            interpretation_text='Second interpretation',
            congestion_level='high',
            peak_direction='NS'
        )
        
        # Test filtered request
        response = self.client.get(f'/api/traffic/interpretations?intersection_id={self.intersection.id}')
        
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['intersection_id'], self.intersection.id)
    
    def test_list_interpretations_api_nonexistent_intersection(self):
        """Test listing interpretations with non-existent intersection"""
        response = self.client.get('/api/traffic/interpretations?intersection_id=99999')
        
        self.assertEqual(response.status_code, 404)
        
        data = response.json()
        self.assertIn('detail', data)
        self.assertIn('not found', data['detail'])
    
    def test_get_report_data_api_success(self):
        """Test successful report data retrieval"""
        # Create interpretation for the test data
        TrafficInterpretation.objects.create(
            intersection=self.intersection,
            datetime=self.test_datetime,
            interpretation_text='Report test interpretation',
            congestion_level='moderate',
            peak_direction='EW'
        )
        
        response = self.client.get(f'/api/traffic/intersections/{self.intersection.id}/report-data')
        
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn('intersection', data)
        self.assertIn('datetime', data)
        self.assertIn('traffic_volumes', data)
        self.assertIn('total_volume', data)
        self.assertIn('average_speed', data)
        self.assertIn('interpretation', data)
        self.assertIn('generated_at', data)
        
        # Verify intersection data
        intersection_data = data['intersection']
        self.assertEqual(intersection_data['id'], self.intersection.id)
        self.assertEqual(intersection_data['name'], self.intersection.name)
        
        # Verify traffic data
        self.assertEqual(data['total_volume'], 400)
        self.assertEqual(data['average_speed'], 35.0)
        
        # Verify interpretation data
        interpretation_data = data['interpretation']
        self.assertIsNotNone(interpretation_data)
        self.assertEqual(interpretation_data['congestion_level'], 'moderate')
        self.assertEqual(interpretation_data['peak_direction'], 'EW')
    
    def test_get_report_data_api_nonexistent_intersection(self):
        """Test report data retrieval with non-existent intersection"""
        response = self.client.get('/api/traffic/intersections/99999/report-data')
        
        self.assertEqual(response.status_code, 404)
        
        data = response.json()
        self.assertIn('detail', data)
        self.assertIn('not found', data['detail'])
    
    def test_get_report_data_api_invalid_datetime(self):
        """Test report data retrieval with invalid datetime parameter"""
        response = self.client.get(
            f'/api/traffic/intersections/{self.intersection.id}/report-data?datetime_str=invalid-datetime'
        )
        
        self.assertEqual(response.status_code, 400)
        
        data = response.json()
        self.assertIn('detail', data)
        self.assertIn('Invalid datetime format', data['detail'])
    
    @patch('traffic.services.TrafficInterpretationService.analyze_traffic_data')
    def test_generate_interpretation_api_service_error(self, mock_analyze):
        """Test API response when service throws an error"""
        mock_analyze.side_effect = Exception("Service error")
        
        response = self.client.post(
            '/api/traffic/generate-interpretation',
            data=json.dumps(self.valid_payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 500)
        
        data = response.json()
        self.assertIn('detail', data)
        self.assertIn('Internal server error', data['detail'])


class TrafficDataPatternTests(TestCase):
    """Tests for various traffic data patterns and interpretation generation"""
    
    def setUp(self):
        """Set up service and test intersection"""
        self.service = TrafficInterpretationService()
        self.intersection = Intersection.objects.create(
            name="Pattern Test Intersection",
            latitude=37.5665,
            longitude=126.9780
        )
    
    def test_rush_hour_pattern(self):
        """Test interpretation for rush hour traffic pattern"""
        rush_hour_data = {
            'traffic_volumes': {'NS': 300, 'SN': 280, 'EW': 250, 'WE': 270},
            'total_volume': 1100,
            'average_speed': 18.0
        }
        
        result = self.service.analyze_traffic_data(rush_hour_data)
        
        self.assertEqual(result['congestion_level'], 'very_high')
        self.assertEqual(result['peak_direction'], 'NS')
        self.assertIn('매우 혼잡', result['interpretation'])
        self.assertIn('상당한 지연', result['interpretation'])
    
    def test_off_peak_pattern(self):
        """Test interpretation for off-peak traffic pattern"""
        off_peak_data = {
            'traffic_volumes': {'NS': 50, 'SN': 45, 'EW': 60, 'WE': 40},
            'total_volume': 195,
            'average_speed': 55.0
        }
        
        result = self.service.analyze_traffic_data(off_peak_data)
        
        self.assertEqual(result['congestion_level'], 'low')
        self.assertEqual(result['peak_direction'], 'EW')
        self.assertIn('원활', result['interpretation'])
        self.assertIn('쾌적한 통행', result['interpretation'])
    
    def test_unidirectional_heavy_pattern(self):
        """Test interpretation for heavy unidirectional traffic"""
        unidirectional_data = {
            'traffic_volumes': {'NS': 400, 'SN': 50, 'EW': 80, 'WE': 70},
            'total_volume': 600,
            'average_speed': 25.0
        }
        
        result = self.service.analyze_traffic_data(unidirectional_data)
        
        self.assertEqual(result['peak_direction'], 'NS')
        self.assertEqual(result['congestion_level'], 'high')
        self.assertIn('남북', result['interpretation'])
        self.assertIn('혼잡', result['interpretation'])
    
    def test_balanced_moderate_pattern(self):
        """Test interpretation for balanced moderate traffic"""
        balanced_data = {
            'traffic_volumes': {'NS': 120, 'SN': 115, 'EW': 125, 'WE': 110},
            'total_volume': 470,
            'average_speed': 42.0
        }
        
        result = self.service.analyze_traffic_data(balanced_data)
        
        self.assertEqual(result['congestion_level'], 'moderate')
        self.assertIn('보통', result['interpretation'])
        self.assertIn('원활한 통행', result['interpretation'])
    
    def test_zero_traffic_pattern(self):
        """Test interpretation for zero traffic scenario"""
        zero_data = {
            'traffic_volumes': {'NS': 0, 'SN': 0, 'EW': 0, 'WE': 0},
            'total_volume': 0,
            'average_speed': 0.0
        }
        
        result = self.service.analyze_traffic_data(zero_data)
        
        self.assertEqual(result['congestion_level'], 'low')
        self.assertEqual(result['peak_direction'], 'NS')  # Default
        self.assertIn('0대', result['interpretation'])
        self.assertIn('0.0km/h', result['interpretation'])


class ErrorHandlingTests(TestCase):
    """Tests for error handling scenarios"""
    
    def setUp(self):
        """Set up test data"""
        self.service = TrafficInterpretationService()
        self.client = Client()
        
        self.intersection = Intersection.objects.create(
            name="Error Test Intersection",
            latitude=37.5665,
            longitude=126.9780
        )
    
    def test_malformed_json_request(self):
        """Test API response to malformed JSON"""
        response = self.client.post(
            '/api/traffic/generate-interpretation',
            data='{"invalid": json}',
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
    
    def test_empty_request_body(self):
        """Test API response to empty request body"""
        response = self.client.post(
            '/api/traffic/generate-interpretation',
            data='',
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 422)
    
    def test_invalid_content_type(self):
        """Test API response to invalid content type"""
        response = self.client.post(
            '/api/traffic/generate-interpretation',
            data='some data',
            content_type='text/plain'
        )
        
        self.assertEqual(response.status_code, 400)  # Bad Request for invalid content type
    
    def test_service_database_error_handling(self):
        """Test service behavior when database operations fail"""
        with patch('traffic.models.Intersection.objects.get') as mock_get:
            mock_get.side_effect = Exception("Database connection error")
            
            with self.assertRaises(ValueError) as context:
                self.service.save_interpretation(
                    self.intersection.id,
                    '2024-01-15T10:30:00Z',
                    {'interpretation': 'test', 'congestion_level': 'low', 'peak_direction': 'NS'}
                )
            
            self.assertIn('Error saving interpretation', str(context.exception))
    
    def test_datetime_parsing_edge_cases(self):
        """Test datetime parsing with various edge cases"""
        valid_formats = [
            '2024-01-15T10:30:00Z',
            '2024-01-15T10:30:00',
            '2024-01-15 10:30:00',
            '2024-01-15T10:30:00+00:00'
        ]
        
        for datetime_str in valid_formats:
            try:
                self.service._validate_datetime_format(datetime_str)
            except ValueError:
                self.fail(f"Valid datetime format {datetime_str} was rejected")
        
        invalid_formats = [
            '2024/01/15 10:30:00',
            '15-01-2024T10:30:00',
            '2024-13-15T10:30:00',  # Invalid month
            '2024-01-32T10:30:00',  # Invalid day
            'not-a-date'
        ]
        
        for datetime_str in invalid_formats:
            with self.assertRaises(ValueError):
                self.service._validate_datetime_format(datetime_str)
    
    def test_traffic_volume_validation_edge_cases(self):
        """Test traffic volume validation with edge cases"""
        # Test with float values (should be accepted)
        valid_volumes = {
            'NS': 100.5,
            'SN': 80.0,
            'EW': 120.7,
            'WE': 90.2
        }
        
        errors = self.service._validate_traffic_volumes(valid_volumes)
        self.assertEqual(errors, {}, "Should accept float values for traffic volumes")
        
        # Test with string values (should be rejected)
        invalid_volumes = {
            'NS': '100',
            'SN': 80,
            'EW': 120,
            'WE': 90
        }
        
        errors = self.service._validate_traffic_volumes(invalid_volumes)
        self.assertIn('NS', errors, "Should reject string values for traffic volumes")
    
    def test_concurrent_interpretation_saving(self):
        """Test handling of concurrent interpretation saving attempts"""
        interpretation_data = {
            'interpretation': 'Concurrent test interpretation',
            'congestion_level': 'moderate',
            'peak_direction': 'EW'
        }
        
        # This should work without issues due to update_or_create
        result1 = self.service.save_interpretation(
            self.intersection.id,
            '2024-01-15T10:30:00Z',
            interpretation_data
        )
        
        # Second save with same datetime should update, not create new
        updated_data = interpretation_data.copy()
        updated_data['interpretation'] = 'Updated concurrent interpretation'
        
        result2 = self.service.save_interpretation(
            self.intersection.id,
            '2024-01-15T10:30:00Z',
            updated_data
        )
        
        self.assertEqual(result1.id, result2.id, "Should update existing record")
        self.assertEqual(result2.interpretation_text, 'Updated concurrent interpretation')
