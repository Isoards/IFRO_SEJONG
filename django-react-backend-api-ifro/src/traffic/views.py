from django.shortcuts import render
from ninja_extra import Router
from typing import List
from .models import (
    Intersection, TrafficVolume, TotalTrafficVolume, Incident, TrafficInterpretation,
    S_Incident, S_TrafficVolume, S_TotalTrafficVolume, S_TrafficInterpretation
)
from .services import TrafficInterpretationService
from .gemini_service import GeminiTrafficAnalyzer
from .schemas import (
    IntersectionSchema, TrafficVolumeSchema, TotalTrafficVolumeSchema, IncidentSchema,
    IntersectionMapDataSchema, IntersectionLatestVolumeSchema, TrafficDataSchema, AllIntersectionsTrafficDataSchema,
    TrafficInterpretationRequestSchema, TrafficInterpretationResponseSchema, TrafficInterpretationSchema,
    ReportDataSchema, ValidationErrorSchema, ServiceErrorSchema
)
from django.db.models import Sum, OuterRef, Subquery
from datetime import datetime
from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from ninja_jwt.controller import NinjaJWTDefaultController
from ninja_jwt.tokens import RefreshToken
from ninja.errors import HttpError
from ninja_jwt.authentication import JWTAuth

router = Router()

@router.get("/intersections", response=List[IntersectionSchema])
@router.get("/intersections/", response=List[IntersectionSchema])
def list_intersections(request):
    return Intersection.objects.all()

@router.get("/intersections/map_data", response=List[IntersectionMapDataSchema])
def map_data(request):
    intersections = Intersection.objects.all()
    data = []
    for intersection in intersections:
        traffic_volumes = TrafficVolume.objects.filter(
            intersection=intersection
        ).values('direction').annotate(
            total_volume=Sum('volume')
        )
        intersection_data = {
            'id': intersection.id,
            'name': intersection.name,
            'latitude': float(intersection.latitude),
            'longitude': float(intersection.longitude),
            'traffic_volumes': list(traffic_volumes)
        }
        data.append(intersection_data)
    return data

@router.get("/intersections/{intersection_id}/traffic_volumes", response=List[TrafficVolumeSchema])
def intersection_traffic_volumes(request, intersection_id: int):
    traffic_volumes = TrafficVolume.objects.filter(intersection_id=intersection_id)
    return traffic_volumes

@router.get("/intersections/{intersection_id}/total_volumes", response=List[TotalTrafficVolumeSchema])
def intersection_total_volumes(request, intersection_id: int):
    total_volumes = TotalTrafficVolume.objects.filter(intersection_id=intersection_id).order_by("datetime")
    return total_volumes

@router.get("/intersections/latest_volume", response=List[IntersectionLatestVolumeSchema])
def latest_volume(request):
    latest_qs = TotalTrafficVolume.objects.filter(
        intersection=OuterRef('pk')
    ).order_by('-datetime')
    intersections = Intersection.objects.annotate(
        latest_volume=Subquery(latest_qs.values('total_volume')[:1]),
        latest_speed=Subquery(latest_qs.values('average_speed')[:1]),
        latest_time=Subquery(latest_qs.values('datetime')[:1])
    ).filter(
        latest_volume__isnull=False
    )
    data = []
    for inter in intersections:
        data.append({
            "id": inter.id,
            "name": inter.name,
            "latitude": inter.latitude,
            "longitude": inter.longitude,
            "total_volume": inter.latest_volume,
            "average_speed": inter.latest_speed,
            "datetime": inter.latest_time,
        })
    return data

@router.get("/traffic-volumes", response=List[TrafficVolumeSchema])
def list_traffic_volumes(request, intersection: int = None):
    qs = TrafficVolume.objects.all()
    if intersection:
        qs = qs.filter(intersection_id=intersection)
    return qs

@router.get("/traffic-data/intersection/{intersection_id}", response=List[TrafficDataSchema])
def get_intersection_traffic_data(request, intersection_id: int, start_time: str, end_time: str):
    try:
        start_time_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        end_time_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
    except Exception:
        return []
    traffic_data = TotalTrafficVolume.objects.filter(
        intersection_id=intersection_id,
        datetime__range=(start_time_dt, end_time_dt)
    ).order_by('datetime')
    return [
        {
            'intersection_id': item.intersection_id,
            'datetime': item.datetime,
            'total_volume': item.total_volume,
            'average_speed': item.average_speed
        } for item in traffic_data
    ]

@router.get("/traffic-data/intersection/{intersection_id}/latest", response=List[TrafficDataSchema])
def get_latest_intersection_traffic_data(request, intersection_id: int, count: int = 10):
    """
    Get the latest N traffic data points for a specific intersection.
    """
    traffic_data = TotalTrafficVolume.objects.filter(
        intersection_id=intersection_id
    ).order_by('-datetime')[:count]
    
    # Since the query is ordered by -datetime, we reverse it to get chronological order for the chart.
    return sorted(list(traffic_data), key=lambda x: x.datetime)

@router.get("/traffic-data/intersections", response=List[AllIntersectionsTrafficDataSchema])
def get_all_intersections_traffic_data(request, time: str = None):
    if time:
        try:
            time_dt = datetime.fromisoformat(time.replace('Z', '+00:00'))
        except Exception:
            time_dt = timezone.now()
    else:
        time_dt = timezone.now()
    traffic_data = TotalTrafficVolume.objects.filter(
        datetime=time_dt
    ).order_by('intersection_id')
    return [
        {
            'intersection_id': item.intersection_id,
            'timestamp': item.datetime,
            'total_volume': item.total_volume
        } for item in traffic_data
    ]

@router.get("/incidents", response=List[IncidentSchema])
@router.get("/incidents/", response=List[IncidentSchema])
def list_incidents(request):
    incidents = Incident.objects.select_related("intersection").all().order_by("-registered_at")
    result = []
    for incident in incidents:
        result.append({
            "id": incident.incident_id,
            "incident_type": incident.incident_type,
            "intersection_name": incident.intersection_name,
            "district": incident.district,
            "managed_by": incident.managed_by,
            "assigned_to": incident.assigned_to,
            "registered_at": incident.registered_at,
            "status": incident.status,
            "user": incident.user,
            "equipment_locked": incident.equipment_locked,
            "last_status_update": incident.last_status_update,
            "ip_address": incident.ip_address,
            "sii_id": incident.sii_id,
            "intersection": incident.intersection.id if incident.intersection else None,
            "latitude": incident.intersection.latitude if incident.intersection else None,
            "longitude": incident.intersection.longitude if incident.intersection else None,
            "type": incident.type,
            "incident_number": getattr(incident, "incident_number", None),
            "ticket_number": getattr(incident, "ticket_number", None),
            "incident_detail_type": getattr(incident, "incident_detail_type", None),
            "location_name": getattr(incident, "location_name", None),
            "description": getattr(incident, "description", None),
            "operator": getattr(incident, "operator", None),
            "day": getattr(incident, "day", None),
            "month": getattr(incident, "month", None),
            "year": getattr(incident, "year", None),
        })
    return result

# 인증이 필요한 대시보드 데이터 API
@router.get("/dashboard-data", auth=JWTAuth())
def dashboard_data(request):
    return {"data": "This is protected dashboard data."}

@router.get("/intersections-data", response=List[dict])
def intersections_data(request):
    # TotalTrafficVolume과 Intersection을 join하여 프론트 요구 포맷으로 반환
    data = []
    for item in TotalTrafficVolume.objects.select_related('intersection').all().order_by('intersection_id', 'datetime'):
        data.append({
            "id": item.intersection.id,
            "name": item.intersection.name,
            "latitude": item.intersection.latitude,
            "longitude": item.intersection.longitude,
            "total_volume": item.total_volume,
            "average_speed": item.average_speed,
            "datetime": item.datetime.strftime("%Y-%m-%dT%H:%M:%SZ")
        })
    return data

@router.post("/generate-interpretation", response=TrafficInterpretationResponseSchema)
def generate_traffic_interpretation(request, payload: TrafficInterpretationRequestSchema):
    """
    Generate traffic interpretation based on traffic data.
    
    This endpoint analyzes traffic data and generates Korean interpretation sentences
    describing the traffic conditions, congestion level, and peak direction.
    
    Request Body:
    - intersection_id: Valid intersection ID (positive integer)
    - datetime: ISO format datetime string
    - traffic_volumes: Object with NS, SN, EW, WE direction volumes (non-negative integers)
    - total_volume: Total traffic volume (non-negative integer)
    - average_speed: Average speed in km/h (0-200)
    
    Returns:
    - interpretation: Generated Korean interpretation text
    - congestion_level: Congestion level (low/moderate/high/very_high)
    - peak_direction: Direction with highest traffic volume
    - analysis_summary: Detailed analysis summary
    """
    try:
        # Initialize the traffic interpretation service
        service = TrafficInterpretationService()
        
        # Validate request data
        request_data = {
            'intersection_id': payload.intersection_id,
            'datetime': payload.datetime,
            'traffic_volumes': payload.traffic_volumes.dict(),
            'total_volume': payload.total_volume,
            'average_speed': payload.average_speed
        }
        
        # Perform comprehensive validation
        service.validate_request_data(request_data)
        
        # Prepare traffic data for analysis
        traffic_data = {
            'traffic_volumes': request_data['traffic_volumes'],
            'total_volume': request_data['total_volume'],
            'average_speed': request_data['average_speed']
        }
        
        # Analyze traffic data and generate interpretation
        analysis_result = service.analyze_traffic_data(traffic_data)
        
        # Save interpretation to database
        try:
            service.save_interpretation(
                intersection_id=request_data['intersection_id'],
                datetime_str=request_data['datetime'],
                interpretation_data=analysis_result
            )
        except Exception as e:
            # Log the error but don't fail the request
            print(f"Warning: Could not save interpretation to database: {str(e)}")
        
        return TrafficInterpretationResponseSchema(
            interpretation=analysis_result['interpretation'],
            congestion_level=analysis_result['congestion_level'],
            peak_direction=analysis_result['peak_direction'],
            analysis_summary=analysis_result['analysis_summary']
        )
        
    except ValueError as e:
        # Handle validation errors
        error_message = str(e)
        if "Validation failed:" in error_message:
            raise HttpError(400, "Request validation failed")
        else:
            raise HttpError(400, error_message)
    except Exception as e:
        # Handle service errors
        raise HttpError(500, "Internal server error occurred while processing traffic interpretation")

@router.get("/interpretations", response=List[TrafficInterpretationSchema])
def list_traffic_interpretations(request, intersection_id: int = None):
    """
    List traffic interpretations, optionally filtered by intersection.
    
    Query Parameters:
    - intersection_id: Optional intersection ID to filter results
    
    Returns:
    List of traffic interpretations with intersection details
    """
    try:
        qs = TrafficInterpretation.objects.select_related('intersection').all()
        if intersection_id:
            # Validate intersection exists
            if not Intersection.objects.filter(id=intersection_id).exists():
                raise HttpError(404, f"Intersection with ID {intersection_id} not found")
            qs = qs.filter(intersection_id=intersection_id)
        
        return [
            {
                'id': item.id,
                'intersection_id': item.intersection.id,
                'datetime': item.datetime,
                'interpretation_text': item.interpretation_text,
                'congestion_level': item.congestion_level,
                'peak_direction': item.peak_direction,
                'created_at': item.created_at
            } for item in qs
        ]
    except HttpError:
        raise
    except Exception as e:
        raise HttpError(500, "Internal server error occurred while retrieving interpretations")

@router.get("/intersections/{intersection_id}/report-data", response=ReportDataSchema)
def get_intersection_report_data(request, intersection_id: int, datetime_str: str = None, language: str = 'ko'):
    """
    Get comprehensive data for PDF report generation.
    
    Path Parameters:
    - intersection_id: ID of the intersection
    
    Query Parameters:
    - datetime_str: Optional datetime string for specific time data
    
    Returns:
    Comprehensive intersection data including traffic volumes, interpretation, and metadata
    """
    try:
        # Validate intersection exists
        try:
            intersection = Intersection.objects.get(id=intersection_id)
        except Intersection.DoesNotExist:
            raise HttpError(404, f"Intersection with ID {intersection_id} not found")
        
        # Parse datetime if provided
        target_datetime = None
        if datetime_str:
            try:
                target_datetime = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
            except ValueError:
                raise HttpError(400, "Invalid datetime format. Expected ISO format")
        
        # Get traffic volume data
        if target_datetime:
            # Get data for specific datetime
            total_volume_data = TotalTrafficVolume.objects.filter(
                intersection=intersection,
                datetime=target_datetime
            ).first()
            
            traffic_volumes_data = TrafficVolume.objects.filter(
                intersection=intersection,
                datetime=target_datetime
            ).values('direction', 'volume')
        else:
            # Get latest data
            total_volume_data = TotalTrafficVolume.objects.filter(
                intersection=intersection
            ).order_by('-datetime').first()
            
            if total_volume_data:
                traffic_volumes_data = TrafficVolume.objects.filter(
                    intersection=intersection,
                    datetime=total_volume_data.datetime
                ).values('direction', 'volume')
            else:
                traffic_volumes_data = []
        
        # Format traffic volumes by direction
        traffic_volumes = {'N': 0, 'S': 0, 'E': 0, 'W': 0}
        for volume_data in traffic_volumes_data:
            direction = volume_data['direction']
            if direction in traffic_volumes:
                traffic_volumes[direction] = volume_data['volume']
        
        # Get or generate interpretation
        interpretation_data = None
        if total_volume_data:
            # Always generate interpretation in requested language (don't use cached)
            try:
                from .services import TrafficInterpretationService
                service = TrafficInterpretationService()
                
                analysis_result = service.analyze_traffic_data({
                    'traffic_volumes': traffic_volumes,
                    'total_volume': total_volume_data.total_volume,
                    'average_speed': float(total_volume_data.average_speed)
                }, language)
                
                interpretation_data = {
                    'interpretation': analysis_result['interpretation'],
                    'congestion_level': analysis_result['congestion_level'],
                    'peak_direction': analysis_result['peak_direction']
                }
            except Exception as e:
                print(f"Warning: Could not generate interpretation: {str(e)}")
                interpretation_data = None
        
        # Prepare response data
        report_data = {
            'intersection': {
                'id': intersection.id,
                'name': intersection.name,
                'latitude': float(intersection.latitude),
                'longitude': float(intersection.longitude)
            },
            'datetime': total_volume_data.datetime.isoformat() if total_volume_data else None,
            'traffic_volumes': traffic_volumes,
            'total_volume': total_volume_data.total_volume if total_volume_data else 0,
            'average_speed': float(total_volume_data.average_speed) if total_volume_data else 0.0,
            'interpretation': interpretation_data,
            'generated_at': timezone.now().isoformat()
        }
        
        
        return report_data
        
    except HttpError:
        raise
    except Exception as e:
        raise HttpError(500, "Internal server error occurred while retrieving report data")

secure_router = Router()

@secure_router.get("/incidents", response=List[IncidentSchema])
@secure_router.get("/incidents/", response=List[IncidentSchema])
def list_secure_incidents(request):
    incidents = S_Incident.objects.select_related("intersection").all().order_by("-registered_at")
    result = []
    for incident in incidents:
        result.append({
            "id": incident.incident_id,
            "incident_type": incident.incident_type,
            "intersection_name": incident.intersection_name,
            "district": incident.district,
            "managed_by": incident.managed_by,
            "assigned_to": incident.assigned_to,
            "registered_at": incident.registered_at,
            "status": incident.status,
            "user": incident.user,
            "equipment_locked": incident.equipment_locked,
            "last_status_update": incident.last_status_update,
            "ip_address": incident.ip_address,
            "sii_id": incident.sii_id,
            "intersection": incident.intersection.id if incident.intersection else None,
            "latitude": incident.intersection.latitude if incident.intersection else None,
            "longitude": incident.intersection.longitude if incident.intersection else None,
            "type": incident.type,
            "incident_number": getattr(incident, "incident_number", None),
            "ticket_number": getattr(incident, "ticket_number", None),
            "incident_detail_type": getattr(incident, "incident_detail_type", None),
            "location_name": getattr(incident, "location_name", None),
            "description": getattr(incident, "description", None),
            "operator": getattr(incident, "operator", None),
            "day": getattr(incident, "day", None),
            "month": getattr(incident, "month", None),
            "year": getattr(incident, "year", None),
        })
    return result

@secure_router.get("/intersections", response=List[IntersectionSchema])
@secure_router.get("/intersections/", response=List[IntersectionSchema])
def list_secure_intersections(request):
    return Intersection.objects.all()

@secure_router.get("/intersections/map_data", response=List[IntersectionMapDataSchema])
def secure_map_data(request):
    intersections = Intersection.objects.all()
    data = []
    for intersection in intersections:
        traffic_volumes = S_TrafficVolume.objects.filter(
            intersection=intersection
        ).values('direction').annotate(
            total_volume=Sum('volume')
        )
        intersection_data = {
            'id': intersection.id,
            'name': intersection.name,
            'latitude': float(intersection.latitude),
            'longitude': float(intersection.longitude),
            'traffic_volumes': list(traffic_volumes)
        }
        data.append(intersection_data)
    return data

@secure_router.get("/intersections/{intersection_id}/traffic_volumes", response=List[TrafficVolumeSchema])
def secure_intersection_traffic_volumes(request, intersection_id: int):
    traffic_volumes = S_TrafficVolume.objects.filter(intersection_id=intersection_id)
    return traffic_volumes

@secure_router.get("/intersections/{intersection_id}/total_volumes", response=List[TotalTrafficVolumeSchema])
def secure_intersection_total_volumes(request, intersection_id: int):
    total_volumes = S_TotalTrafficVolume.objects.filter(intersection_id=intersection_id).order_by("datetime")
    return total_volumes

@secure_router.get("/intersections/latest_volume", response=List[IntersectionLatestVolumeSchema])
def secure_latest_volume(request):
    latest_qs = S_TotalTrafficVolume.objects.filter(
        intersection=OuterRef('pk')
    ).order_by('-datetime')
    intersections = Intersection.objects.annotate(
        latest_volume=Subquery(latest_qs.values('total_volume')[:1]),
        latest_speed=Subquery(latest_qs.values('average_speed')[:1]),
        latest_time=Subquery(latest_qs.values('datetime')[:1])
    ).filter(
        latest_volume__isnull=False
    )
    data = []
    for inter in intersections:
        data.append({
            "id": inter.id,
            "name": inter.name,
            "latitude": inter.latitude,
            "longitude": inter.longitude,
            "total_volume": inter.latest_volume,
            "average_speed": inter.latest_speed,
            "datetime": inter.latest_time,
        })
    return data

@secure_router.get("/traffic-volumes", response=List[TrafficVolumeSchema])
def list_secure_traffic_volumes(request, intersection: int = None):
    qs = S_TrafficVolume.objects.all()
    if intersection:
        qs = qs.filter(intersection_id=intersection)
    return qs

@secure_router.get("/traffic-data/intersection/{intersection_id}", response=List[TrafficDataSchema])
def get_secure_intersection_traffic_data(request, intersection_id: int, start_time: str, end_time: str):
    try:
        start_time_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        end_time_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
    except Exception:
        return []
    traffic_data = S_TotalTrafficVolume.objects.filter(
        intersection_id=intersection_id,
        datetime__range=(start_time_dt, end_time_dt)
    ).order_by('datetime')
    return [
        {
            'intersection_id': item.intersection_id,
            'datetime': item.datetime,
            'total_volume': item.total_volume,
            'average_speed': item.average_speed
        } for item in traffic_data
    ]

@secure_router.get("/traffic-data/intersections", response=List[AllIntersectionsTrafficDataSchema])
def get_all_secure_intersections_traffic_data(request, time: str = None):
    if time:
        try:
            time_dt = datetime.fromisoformat(time.replace('Z', '+00:00'))
        except Exception:
            time_dt = timezone.now()
    else:
        time_dt = timezone.now()
    traffic_data = S_TotalTrafficVolume.objects.filter(
        datetime=time_dt
    ).order_by('intersection_id')
    return [
        {
            'intersection_id': item.intersection_id,
            'timestamp': item.datetime,
            'total_volume': item.total_volume
        } for item in traffic_data
    ]

@secure_router.get("/intersections-data", response=List[dict])
def secure_intersections_data(request):
    data = []
    for item in S_TotalTrafficVolume.objects.select_related('intersection').all().order_by('intersection_id', 'datetime'):
        data.append({
            "id": item.intersection.id,
            "name": item.intersection.name,
            "latitude": item.intersection.latitude,
            "longitude": item.intersection.longitude,
            "total_volume": item.total_volume,
            "average_speed": item.average_speed,
            "datetime": item.datetime.strftime("%Y-%m-%dT%H:%M:%SZ")
        })
    return data

@secure_router.post("/generate-interpretation", response=TrafficInterpretationResponseSchema)
def generate_secure_traffic_interpretation(request, payload: TrafficInterpretationRequestSchema):
    try:
        service = TrafficInterpretationService()
        request_data = {
            'intersection_id': payload.intersection_id,
            'datetime': payload.datetime,
            'traffic_volumes': payload.traffic_volumes.dict(),
            'total_volume': payload.total_volume,
            'average_speed': payload.average_speed
        }
        service.validate_request_data(request_data)
        traffic_data = {
            'traffic_volumes': request_data['traffic_volumes'],
            'total_volume': request_data['total_volume'],
            'average_speed': request_data['average_speed']
        }
        analysis_result = service.analyze_traffic_data(traffic_data)
        try:
            # This is where we would save to S_TrafficInterpretation, but we need a modified service or direct save
            S_TrafficInterpretation.objects.create(
                intersection_id=request_data['intersection_id'],
                datetime=request_data['datetime'],
                interpretation_text=analysis_result['interpretation'],
                congestion_level=analysis_result['congestion_level'],
                peak_direction=analysis_result['peak_direction'],
            )
        except Exception as e:
            print(f"Warning: Could not save secure interpretation to database: {str(e)}")
        
        return TrafficInterpretationResponseSchema(
            interpretation=analysis_result['interpretation'],
            congestion_level=analysis_result['congestion_level'],
            peak_direction=analysis_result['peak_direction'],
            analysis_summary=analysis_result['analysis_summary']
        )
    except ValueError as e:
        error_message = str(e)
        if "Validation failed:" in error_message:
            raise HttpError(400, "Request validation failed")
        else:
            raise HttpError(400, error_message)
    except Exception as e:
        raise HttpError(500, "Internal server error occurred while processing traffic interpretation")

@secure_router.get("/interpretations", response=List[TrafficInterpretationSchema])
def list_secure_traffic_interpretations(request, intersection_id: int = None):
    try:
        qs = S_TrafficInterpretation.objects.select_related('intersection').all()
        if intersection_id:
            if not Intersection.objects.filter(id=intersection_id).exists():
                raise HttpError(404, f"Intersection with ID {intersection_id} not found")
            qs = qs.filter(intersection_id=intersection_id)
        
        return [
            {
                'id': item.id,
                'intersection_id': item.intersection.id,
                'datetime': item.datetime,
                'interpretation_text': item.interpretation_text,
                'congestion_level': item.congestion_level,
                'peak_direction': item.peak_direction,
                'created_at': item.created_at
            } for item in qs
        ]
    except HttpError:
        raise
    except Exception as e:
        raise HttpError(500, "Internal server error occurred while retrieving interpretations")

@secure_router.get("/intersections/{intersection_id}/report-data", response=ReportDataSchema)
def get_secure_intersection_report_data(request, intersection_id: int, datetime_str: str = None):
    try:
        try:
            intersection = Intersection.objects.get(id=intersection_id)
        except Intersection.DoesNotExist:
            raise HttpError(404, f"Intersection with ID {intersection_id} not found")
        
        target_datetime = None
        if datetime_str:
            try:
                target_datetime = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
            except ValueError:
                raise HttpError(400, "Invalid datetime format. Expected ISO format")
        
        if target_datetime:
            total_volume_data = S_TotalTrafficVolume.objects.filter(
                intersection=intersection,
                datetime=target_datetime
            ).first()
            
            traffic_volumes_data = S_TrafficVolume.objects.filter(
                intersection=intersection,
                datetime=target_datetime
            ).values('direction', 'volume')
        else:
            total_volume_data = S_TotalTrafficVolume.objects.filter(
                intersection=intersection
            ).order_by('-datetime').first()
            
            if total_volume_data:
                traffic_volumes_data = S_TrafficVolume.objects.filter(
                    intersection=intersection,
                    datetime=total_volume_data.datetime
                ).values('direction', 'volume')
            else:
                traffic_volumes_data = []
        
        traffic_volumes = {'N': 0, 'S': 0, 'E': 0, 'W': 0}
        for volume_data in traffic_volumes_data:
            direction = volume_data['direction']
            if direction in traffic_volumes:
                traffic_volumes[direction] = volume_data['volume']
        
        interpretation_data = None
        if total_volume_data:
            interpretation = S_TrafficInterpretation.objects.filter(
                intersection=intersection,
                datetime=total_volume_data.datetime
            ).first()
            
            if interpretation:
                interpretation_data = {
                    'interpretation': interpretation.interpretation_text,
                    'congestion_level': interpretation.congestion_level,
                    'peak_direction': interpretation.peak_direction
                }
            else:
                # Generate interpretation if not exists
                try:
                    from .services import TrafficInterpretationService
                    service = TrafficInterpretationService()
                    
                    analysis_result = service.analyze_traffic_data({
                        'traffic_volumes': traffic_volumes,
                        'total_volume': total_volume_data.total_volume,
                        'average_speed': float(total_volume_data.average_speed)
                    })
                    
                    # Save the generated interpretation
                    interpretation = S_TrafficInterpretation.objects.create(
                        intersection=intersection,
                        datetime=total_volume_data.datetime,
                        interpretation_text=analysis_result['interpretation'],
                        congestion_level=analysis_result['congestion_level'],
                        peak_direction=analysis_result['peak_direction']
                    )
                    
                    interpretation_data = {
                        'interpretation': analysis_result['interpretation'],
                        'congestion_level': analysis_result['congestion_level'],
                        'peak_direction': analysis_result['peak_direction']
                    }
                except Exception as e:
                    print(f"Warning: Could not generate interpretation: {str(e)}")
                    interpretation_data = None
        
        report_data = {
            'intersection': {
                'id': intersection.id,
                'name': intersection.name,
                'latitude': float(intersection.latitude),
                'longitude': float(intersection.longitude)
            },
            'datetime': total_volume_data.datetime.isoformat() if total_volume_data else None,
            'traffic_volumes': traffic_volumes,
            'total_volume': total_volume_data.total_volume if total_volume_data else 0,
            'average_speed': float(total_volume_data.average_speed) if total_volume_data else 0.0,
            'interpretation': interpretation_data,
            'generated_at': timezone.now().isoformat()
        }
        
        return report_data
        
    except HttpError:
        raise
    except Exception as e:
        raise HttpError(500, "Internal server error occurred while retrieving report data")

# LLM Analysis Endpoints
@router.post("/intersections/{intersection_id}/ai-analysis")
def generate_ai_traffic_analysis(request, intersection_id: int, time_period: str = "24h", language: str = "ko"):
    """
    Generate AI-powered traffic analysis using Gemini API
    
    Path Parameters:
    - intersection_id: ID of the intersection to analyze
    
    Query Parameters:
    - time_period: Time period for analysis ("24h", "7d", "30d")
    
    Returns:
    AI-generated analysis including congestion level, recommendations, and insights
    """
    try:
        # Validate intersection exists
        if not Intersection.objects.filter(id=intersection_id).exists():
            raise HttpError(404, f"Intersection with ID {intersection_id} not found")
        
        # Validate time period
        if time_period not in ["24h", "7d", "30d"]:
            raise HttpError(400, "Invalid time period. Must be one of: 24h, 7d, 30d")
        
        # Initialize Gemini analyzer
        analyzer = GeminiTrafficAnalyzer()
        
        # Generate analysis using report data for consistency
        analysis_result = analyzer.analyze_intersection_traffic(intersection_id, time_period, language, use_report_data=True)
        
        # Check if analysis was successful
        if analysis_result.get('error') and not analysis_result.get('fallback_used'):
            # If there's an error and no fallback was used, raise an HTTP error
            error_type = analysis_result.get('error_type', 'unknown')
            if error_type == 'auth_error':
                raise HttpError(500, "AI 분석 서비스 인증 오류. API 키를 확인해주세요.")
            elif error_type == 'quota_error':
                raise HttpError(429, "AI 분석 서비스 사용량 한도 초과. 잠시 후 다시 시도해주세요.")
            elif error_type == 'network_error':
                raise HttpError(503, "AI 분석 서비스 연결 오류. 네트워크 상태를 확인해주세요.")
            elif error_type == 'timeout_error':
                raise HttpError(504, "AI 분석 요청 시간 초과. 다시 시도해주세요.")
            else:
                raise HttpError(500, f"AI 분석 생성 실패: {analysis_result.get('error', '알 수 없는 오류')}")
        
        return {
            "success": True,
            "intersection_id": intersection_id,
            "time_period": time_period,
            "language": language,
            "analysis": analysis_result,
            "generated_at": timezone.now().isoformat()
        }
        
    except ValueError as e:
        raise HttpError(400, str(e))
    except Exception as e:
        # Log the error for debugging
        print(f"AI Analysis Error: {str(e)}")
        raise HttpError(500, "Failed to generate AI analysis. Please check API configuration.")

@secure_router.post("/intersections/{intersection_id}/ai-analysis")
def generate_secure_ai_traffic_analysis(request, intersection_id: int, time_period: str = "24h", language: str = "ko"):
    """
    Generate AI-powered traffic analysis using Gemini API (Secure version)
    """
    try:
        if not Intersection.objects.filter(id=intersection_id).exists():
            raise HttpError(404, f"Intersection with ID {intersection_id} not found")
        
        if time_period not in ["24h", "7d", "30d"]:
            raise HttpError(400, "Invalid time period. Must be one of: 24h, 7d, 30d")
        
        analyzer = GeminiTrafficAnalyzer()
        analysis_result = analyzer.analyze_intersection_traffic(intersection_id, time_period, language, use_report_data=True)
        
        return {
            "intersection_id": intersection_id,
            "time_period": time_period,
            "analysis": analysis_result,
            "generated_at": timezone.now().isoformat()
        }
        
    except ValueError as e:
        raise HttpError(400, str(e))
    except Exception as e:
        print(f"Secure AI Analysis Error: {str(e)}")
        raise HttpError(500, "Failed to generate AI analysis. Please check API configuration.")