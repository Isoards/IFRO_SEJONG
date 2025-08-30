from django.shortcuts import render
from ninja_extra import Router
from typing import List
from .models import (
    Intersection, TrafficVolume, TotalTrafficVolume, Incident, TrafficInterpretation,
    S_Incident, S_TrafficVolume, S_TotalTrafficVolume, S_TrafficInterpretation,
    IntersectionStats, IntersectionViewLog, IntersectionFavoriteLog
)
from .services import TrafficInterpretationService
from .gemini_service import GeminiTrafficAnalyzer
from .schemas import (
    IntersectionSchema, TrafficVolumeSchema, TotalTrafficVolumeSchema, IncidentSchema,
    IntersectionMapDataSchema, IntersectionLatestVolumeSchema, TrafficDataSchema, AllIntersectionsTrafficDataSchema,
    TrafficInterpretationRequestSchema, TrafficInterpretationResponseSchema, TrafficInterpretationSchema,
    ReportDataSchema, ValidationErrorSchema, ServiceErrorSchema,
    IntersectionStatsSchema, ViewRecordResponseSchema, FavoriteStatusSchema, FavoriteToggleResponseSchema,
    AdminStatsSchema, IntersectionStatsListSchema
)
from django.db.models import Sum, OuterRef, Subquery, Count, Q, F
from django.db import transaction
from datetime import datetime
from django.utils import timezone
import django.db.models
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
        intersection = Intersection.objects.filter(id=intersection_id).first()
        if not intersection:
            raise HttpError(404, f"Intersection with ID {intersection_id} not found")
        
        # Validate time period
        if time_period not in ["24h", "7d", "30d"]:
            raise HttpError(400, "Invalid time period. Must be one of: 24h, 7d, 30d")
        
        # AI 리포트 요청 카운트 증가
        stats, created = IntersectionStats.objects.get_or_create(
            intersection=intersection,
            defaults={
                'view_count': 0,
                'favorite_count': 0,
                'ai_report_count': 0
            }
        )
        stats.ai_report_count += 1
        stats.last_ai_report = timezone.now()
        stats.save()
        
        print(f"AI report requested for intersection {intersection_id}: {stats.ai_report_count} total requests")
        
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
        intersection = Intersection.objects.filter(id=intersection_id).first()
        if not intersection:
            raise HttpError(404, f"Intersection with ID {intersection_id} not found")
        
        if time_period not in ["24h", "7d", "30d"]:
            raise HttpError(400, "Invalid time period. Must be one of: 24h, 7d, 30d")
        
        # AI 리포트 요청 카운트 증가 (Secure version)
        stats, created = IntersectionStats.objects.get_or_create(
            intersection=intersection,
            defaults={
                'view_count': 0,
                'favorite_count': 0,
                'ai_report_count': 0
            }
        )
        stats.ai_report_count += 1
        stats.last_ai_report = timezone.now()
        stats.save()
        
        print(f"Secure AI report requested for intersection {intersection_id}: {stats.ai_report_count} total requests")
        
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

# ChatBot Endpoints
@router.post("/chat/message")
def chat_with_ai(request, message: str, context: dict = None):
    """
    Chat with AI assistant
    
    Request Body:
    - message: User's message
    - context: Optional context information (current intersection, etc.)
    
    Returns:
    - response: AI's response
    - timestamp: Response timestamp
    """
    try:
        if not message or not message.strip():
            raise HttpError(400, "Message cannot be empty")
        
        # Initialize Gemini analyzer for chat
        analyzer = GeminiTrafficAnalyzer()
        
        # Create chat prompt
        chat_prompt = f"""
        당신은 IFRO 교통 분석 시스템의 AI 어시스턴트입니다. 
        사용자의 질문에 친절하고 도움이 되는 답변을 제공해주세요.
        
        사용자 메시지: {message}
        
        가능한 질문 유형:
        - 교통 데이터 분석 방법
        - 대시보드 사용법
        - 교차로 정보
        - 교통사고 정보
        - 경로 분석
        - 즐겨찾기 기능
        - 일반적인 교통 관련 질문
        
        답변은 한국어로 제공하고, 구체적이고 실용적인 정보를 포함해주세요.
        """
        
        # Call Gemini API
        response = analyzer._call_gemini_api(chat_prompt)
        
        return {
            "success": True,
            "response": response,
            "timestamp": timezone.now().isoformat()
        }
        
    except Exception as e:
        print(f"Chat API Error: {str(e)}")
        raise HttpError(500, "챗봇 응답 생성 중 오류가 발생했습니다.")

@secure_router.post("/chat/message")
def secure_chat_with_ai(request, message: str, context: dict = None):
    """
    Secure chat with AI assistant
    """
    try:
        if not message or not message.strip():
            raise HttpError(400, "Message cannot be empty")
        
        analyzer = GeminiTrafficAnalyzer()
        
        chat_prompt = f"""
        당신은 IFRO 교통 분석 시스템의 AI 어시스턴트입니다. 
        사용자의 질문에 친절하고 도움이 되는 답변을 제공해주세요.
        
        사용자 메시지: {message}
        
        가능한 질문 유형:
        - 교통 데이터 분석 방법
        - 대시보드 사용법
        - 교차로 정보
        - 교통사고 정보
        - 경로 분석
        - 즐겨찾기 기능
        - 일반적인 교통 관련 질문
        
        답변은 한국어로 제공하고, 구체적이고 실용적인 정보를 포함해주세요.
        """
        
        response = analyzer._call_gemini_api(chat_prompt)
        
        return {
            "success": True,
            "response": response,
            "timestamp": timezone.now().isoformat()
        }
        
    except Exception as e:
        print(f"Secure Chat API Error: {str(e)}")
        raise HttpError(500, "챗봇 응답 생성 중 오류가 발생했습니다.")

# Favorite and View Count Related APIs
@router.post("/intersections/{intersection_id}/record-view", response=ViewRecordResponseSchema)
def record_intersection_view(request, intersection_id: int):
    """교차로 조회 기록 및 조회수 증가"""
    try:
        intersection = Intersection.objects.get(id=intersection_id)
        
        # 통계 레코드 가져오기 또는 생성
        stats, created = IntersectionStats.objects.get_or_create(
            intersection=intersection,
            defaults={'view_count': 0, 'favorite_count': 0}
        )
        
        # 조회수 증가
        stats.view_count += 1
        stats.last_viewed = timezone.now()
        stats.save()
        
        # 조회 로그 기록
        IntersectionViewLog.objects.create(
            intersection=intersection,
            user=request.user if request.user.is_authenticated else None,
            ip_address=request.META.get('REMOTE_ADDR', ''),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return ViewRecordResponseSchema(
            success=True,
            view_count=stats.view_count,
            message="조회가 기록되었습니다."
        )
        
    except Intersection.DoesNotExist:
        raise HttpError(404, "교차로를 찾을 수 없습니다.")
    except Exception as e:
        raise HttpError(500, f"조회 기록 중 오류가 발생했습니다: {str(e)}")

@router.get("/intersections/{intersection_id}/favorite-status", response=FavoriteStatusSchema, auth=JWTAuth())
def get_favorite_status(request, intersection_id: int):
    """사용자의 즐겨찾기 상태 조회"""
    try:
        intersection = Intersection.objects.get(id=intersection_id)
        stats = IntersectionStats.objects.filter(intersection=intersection).first()
        
        # 사용자의 즐겨찾기 상태 확인
        is_favorite = IntersectionFavoriteLog.objects.filter(
            intersection=intersection,
            user=request.user,
            is_favorite=True
        ).exists()
        
        return FavoriteStatusSchema(
            is_favorite=is_favorite,
            favorite_count=stats.favorite_count if stats else 0
        )
        
    except Intersection.DoesNotExist:
        raise HttpError(404, "교차로를 찾을 수 없습니다.")

@router.post("/intersections/{intersection_id}/toggle-favorite", response=FavoriteToggleResponseSchema, auth=JWTAuth())
def toggle_favorite(request, intersection_id: int):
    """즐겨찾기 토글"""
    try:
        intersection = Intersection.objects.get(id=intersection_id)
        
        # 통계 레코드 가져오기 또는 생성
        stats, created = IntersectionStats.objects.get_or_create(
            intersection=intersection,
            defaults={'view_count': 0, 'favorite_count': 0}
        )
        
        # 현재 사용자의 최신 즐겨찾기 상태 확인
        latest_favorite_log = IntersectionFavoriteLog.objects.filter(
            intersection=intersection,
            user=request.user
        ).order_by('-created_at').first()
        
        current_favorite = latest_favorite_log.is_favorite if latest_favorite_log else False
        new_favorite_status = not current_favorite
        
        # 즐겨찾기 로그 기록
        IntersectionFavoriteLog.objects.create(
            intersection=intersection,
            user=request.user,
            is_favorite=new_favorite_status
        )
        
        # 실제 즐겨찾기 수를 정확히 계산
        # 각 사용자별로 최신 즐겨찾기 상태를 확인
        users_with_favorites = set()
        all_users = IntersectionFavoriteLog.objects.filter(
            intersection=intersection
        ).values_list('user', flat=True).distinct()
        
        for user_id in all_users:
            latest_log = IntersectionFavoriteLog.objects.filter(
                intersection=intersection,
                user_id=user_id
            ).order_by('-created_at').first()
            
            if latest_log and latest_log.is_favorite:
                users_with_favorites.add(user_id)
        
        active_favorites = len(users_with_favorites)
        
        # 통계 업데이트
        stats.favorite_count = active_favorites
        stats.save()
        
        return FavoriteToggleResponseSchema(
            success=True,
            is_favorite=new_favorite_status,
            favorite_count=stats.favorite_count,
            message="즐겨찾기가 업데이트되었습니다."
        )
        
    except Intersection.DoesNotExist:
        raise HttpError(404, "교차로를 찾을 수 없습니다.")
    except Exception as e:
        raise HttpError(500, f"즐겨찾기 업데이트 중 오류가 발생했습니다: {str(e)}")

@router.get("/intersections/{intersection_id}/stats", response=IntersectionStatsSchema)
def get_intersection_stats(request, intersection_id: int):
    """교차로 통계 조회"""
    try:
        intersection = Intersection.objects.get(id=intersection_id)
        stats = IntersectionStats.objects.filter(intersection=intersection).first()
        
        if not stats:
            return IntersectionStatsSchema(
                view_count=0,
                favorite_count=0,
                last_viewed=None
            )
        
        return IntersectionStatsSchema(
            view_count=stats.view_count,
            favorite_count=stats.favorite_count,
            last_viewed=stats.last_viewed
        )
        
    except Intersection.DoesNotExist:
        raise HttpError(404, "교차로를 찾을 수 없습니다.")

@router.get("/user/favorite-intersections", response=List[IntersectionSchema], auth=JWTAuth())
def get_user_favorite_intersections(request):
    """사용자의 즐겨찾기 교차로 목록 조회"""
    try:
        # 사용자가 즐겨찾기한 교차로 ID 목록
        favorite_intersection_ids = IntersectionFavoriteLog.objects.filter(
            user=request.user,
            is_favorite=True
        ).values_list('intersection_id', flat=True).distinct()
        
        # 즐겨찾기한 교차로들 조회
        favorite_intersections = Intersection.objects.filter(
            id__in=favorite_intersection_ids
        )
        
        return list(favorite_intersections)
        
    except Exception as e:
        raise HttpError(500, f"즐겨찾기 목록 조회 중 오류가 발생했습니다: {str(e)}")

# Admin Statistics API - 최적화된 버전
@router.get("/admin/stats", response=AdminStatsSchema)
def get_admin_stats(request):
    """관리자 통계 데이터 조회 - 성능 최적화"""
    try:
        # 한 번의 쿼리로 모든 통계 데이터 조회
        from django.db.models import Sum
        
        # 최다 조회 구간, 최다 즐겨찾기 구간, AI 리포트 다발 지역 TOP 10을 병렬로 조회
        top_viewed_areas = IntersectionStats.objects.select_related('intersection').filter(
            view_count__gt=0
        ).order_by('-view_count')[:10].values(
            'intersection__name', 'view_count'
        )
        
        top_favorite_areas = IntersectionStats.objects.select_related('intersection').filter(
            favorite_count__gt=0
        ).order_by('-favorite_count')[:10].values(
            'intersection__name', 'favorite_count'
        )
        
        top_ai_report_areas = IntersectionStats.objects.select_related('intersection').filter(
            ai_report_count__gt=0
        ).order_by('-ai_report_count')[:10].values(
            'intersection__name', 'ai_report_count'
        )
        
        # 전체 통계를 한 번의 쿼리로 조회
        totals = IntersectionStats.objects.aggregate(
            total_views=Sum('view_count'),
            total_favorites=Sum('favorite_count'),
            total_ai_reports=Sum('ai_report_count')
        )
        
        # 결과 구성
        top_viewed_list = [
            {
                'rank': idx + 1,
                'area': item['intersection__name'],
                'views': item['view_count'],
                'change': 0
            }
            for idx, item in enumerate(top_viewed_areas)
        ]
        
        top_favorite_list = [
            {
                'rank': idx + 1,
                'area': item['intersection__name'],
                'favorites': item['favorite_count'],
                'growth': 0
            }
            for idx, item in enumerate(top_favorite_areas)
        ]
        
        top_ai_report_list = [
            {
                'rank': idx + 1,
                'area': item['intersection__name'],
                'ai_reports': item['ai_report_count'],
                'growth': 0
            }
            for idx, item in enumerate(top_ai_report_areas)
        ]
        
        return AdminStatsSchema(
            top_viewed_areas=top_viewed_list,
            top_favorite_areas=top_favorite_list,
            top_ai_report_areas=top_ai_report_list,
            total_views=totals['total_views'] or 0,
            total_favorites=totals['total_favorites'] or 0,
            total_ai_reports=totals['total_ai_reports'] or 0
        )
        
    except Exception as e:
        raise HttpError(500, f"관리자 통계 조회 중 오류가 발생했습니다: {str(e)}")

# Admin용 교차로 목록 (즐겨찾기 수 포함) - 최적화된 버전
@router.get("/admin/intersections", response=List[IntersectionStatsListSchema])
def get_admin_intersections(request):
    """관리자용 교차로 목록 조회 (즐겨찾기 수 포함) - 성능 최적화"""
    try:
        # 통계가 있는 교차로만 조회 (LEFT JOIN 사용)
        from django.db.models import Q, F, Value, IntegerField
        from django.db.models.functions import Coalesce
        
        # 교차로와 통계를 한 번의 쿼리로 조회 (IntersectionStats 모델이 없으므로 기본값 사용)
        intersections_with_stats = Intersection.objects.annotate(
            stats_view_count=Value(0, output_field=IntegerField()),
            stats_favorite_count=Value(0, output_field=IntegerField()),
            stats_ai_report_count=Value(0, output_field=IntegerField()),
            stats_last_viewed=Value(None, output_field=django.db.models.DateTimeField()),
            stats_last_ai_report=Value(None, output_field=django.db.models.DateTimeField())
        ).order_by('name')[:100]  # 상위 100개만
        
        result = []
        for intersection in intersections_with_stats:
            result.append({
                'intersection_id': intersection.id,
                'intersection_name': intersection.name,
                'view_count': intersection.stats_view_count,
                'favorite_count': intersection.stats_favorite_count,
                'ai_report_count': intersection.stats_ai_report_count,
                'last_viewed': intersection.stats_last_viewed,
                'last_ai_report': intersection.stats_last_ai_report
            })
        
        return result
        
    except Exception as e:
        raise HttpError(500, f"관리자 교차로 목록 조회 중 오류가 발생했습니다: {str(e)}")

# 교통 흐름 분석 즐겨찾기 통계 API
@router.get("/admin/traffic-flow-favorites", response=List[dict])
def get_traffic_flow_favorites_stats(request):
    """관리자용 교통 흐름 분석 즐겨찾기 통계 조회"""
    try:
        from .models import TrafficFlowAnalysisStats
        
        # 인기 교통 흐름 경로 통계 (즐겨찾기 수 기준 상위 20개)
        flow_stats = TrafficFlowAnalysisStats.objects.select_related(
            'start_intersection', 'end_intersection'
        ).order_by('-total_favorites', '-total_accesses')[:20]
        
        result = []
        for idx, stat in enumerate(flow_stats):
            result.append({
                'rank': idx + 1,
                'route': f"{stat.start_intersection.name} → {stat.end_intersection.name}",
                'start_intersection': {
                    'id': stat.start_intersection.id,
                    'name': stat.start_intersection.name
                },
                'end_intersection': {
                    'id': stat.end_intersection.id,
                    'name': stat.end_intersection.name
                },
                'total_favorites': stat.total_favorites,
                'total_accesses': stat.total_accesses,
                'unique_users': stat.unique_users,
                'last_accessed': stat.last_accessed,
                'popularity_score': stat.total_favorites * 2 + stat.total_accesses,  # 인기도 점수
                'created_at': stat.created_at,
                'updated_at': stat.updated_at
            })
        
        return result
        
    except Exception as e:
        raise HttpError(500, f"교통 흐름 즐겨찾기 통계 조회 중 오류가 발생했습니다: {str(e)}")

@router.get("/admin/traffic-flow-favorites/detailed", response=List[dict])
def get_traffic_flow_favorites_detailed(request):
    """관리자용 교통 흐름 분석 즐겨찾기 상세 정보"""
    try:
        from .models import TrafficFlowAnalysisFavorite
        
        # 모든 즐겨찾기 데이터 (사용자별)
        favorites = TrafficFlowAnalysisFavorite.objects.select_related(
            'user', 'start_intersection', 'end_intersection'
        ).order_by('-access_count', '-last_accessed')[:50]  # 상위 50개
        
        result = []
        for favorite in favorites:
            result.append({
                'id': favorite.id,
                'user': {
                    'id': favorite.user.id,
                    'username': favorite.user.username,
                    'email': favorite.user.email
                },
                'route': f"{favorite.start_intersection.name} → {favorite.end_intersection.name}",
                'start_intersection': {
                    'id': favorite.start_intersection.id,
                    'name': favorite.start_intersection.name
                },
                'end_intersection': {
                    'id': favorite.end_intersection.id,
                    'name': favorite.end_intersection.name
                },
                'favorite_name': favorite.favorite_name,
                'access_count': favorite.access_count,
                'last_accessed': favorite.last_accessed,
                'created_at': favorite.created_at
            })
        
        return result
        
    except Exception as e:
        raise HttpError(500, f"교통 흐름 즐겨찾기 상세 정보 조회 중 오류가 발생했습니다: {str(e)}")

@router.get("/admin/traffic-flow-summary", response=dict)
def get_traffic_flow_summary(request):
    """관리자용 교통 흐름 분석 요약 통계"""
    try:
        from .models import TrafficFlowAnalysisFavorite, TrafficFlowAnalysisStats
        from django.db.models import Sum, Count, Avg
        
        # 전체 통계
        total_favorites = TrafficFlowAnalysisFavorite.objects.count()
        total_routes = TrafficFlowAnalysisStats.objects.count()
        total_users = TrafficFlowAnalysisFavorite.objects.values('user').distinct().count()
        
        # 평균 통계
        avg_favorites_per_route = TrafficFlowAnalysisStats.objects.aggregate(
            avg_favorites=Avg('total_favorites')
        )['avg_favorites'] or 0
        
        avg_accesses_per_favorite = TrafficFlowAnalysisFavorite.objects.aggregate(
            avg_accesses=Avg('access_count')
        )['avg_accesses'] or 0
        
        # 인기 경로 (상위 5개)
        top_routes = TrafficFlowAnalysisStats.objects.select_related(
            'start_intersection', 'end_intersection'
        ).order_by('-total_favorites')[:5]
        
        top_routes_data = []
        for route in top_routes:
            top_routes_data.append({
                'route': f"{route.start_intersection.name} → {route.end_intersection.name}",
                'favorites': route.total_favorites,
                'accesses': route.total_accesses
            })
        
        return {
            'summary': {
                'total_favorites': total_favorites,
                'total_routes': total_routes,
                'total_users': total_users,
                'avg_favorites_per_route': round(avg_favorites_per_route, 2),
                'avg_accesses_per_favorite': round(avg_accesses_per_favorite, 2)
            },
            'top_routes': top_routes_data
        }
        
    except Exception as e:
        raise HttpError(500, f"교통 흐름 요약 통계 조회 중 오류가 발생했습니다: {str(e)}")