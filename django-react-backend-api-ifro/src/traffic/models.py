from django.db import models
from django.utils import timezone
from django.conf import settings

# Create your models here.

class Intersection(models.Model):
    name = models.CharField(max_length=100)
    latitude = models.FloatField()
    longitude = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']

class TrafficVolume(models.Model):
    DIRECTION_CHOICES = [
        ('N', 'North'),
        ('S', 'South'),
        ('E', 'East'),
        ('W', 'West'),
    ]

    intersection = models.ForeignKey(Intersection, on_delete=models.CASCADE, related_name='traffic_volumes')
    datetime = models.DateTimeField()
    direction = models.CharField(max_length=1, choices=DIRECTION_CHOICES)
    volume = models.IntegerField()
    is_simulated = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.intersection.name} - {self.datetime} - {self.direction}"

    class Meta:
        ordering = ['-datetime']
        indexes = [
            models.Index(fields=['intersection', 'datetime']),
            models.Index(fields=['direction']),
        ]

# 프론트엔드에서 시간별 교차로 데이터(total_volume, average_speed, datetime 등)를 사용할 때 이 모델을 활용합니다.
class TotalTrafficVolume(models.Model):
    intersection = models.ForeignKey(Intersection, on_delete=models.CASCADE)
    datetime = models.DateTimeField()
    total_volume = models.IntegerField()
    average_speed = models.FloatField()

    class Meta:
        db_table = 'total_traffic_volume'
        indexes = [
            models.Index(fields=['intersection', 'datetime']),
        ]

    def __str__(self):
        return f"{self.intersection.name} - {self.datetime}: {self.total_volume}대, {self.average_speed}km/h"

class TrafficInterpretation(models.Model):
    CONGESTION_LEVEL_CHOICES = [
        ('low', 'Low'),
        ('moderate', 'Moderate'),
        ('high', 'High'),
        ('very_high', 'Very High'),
    ]
    
    DIRECTION_CHOICES = [
        ('N', 'North'),
        ('S', 'South'),
        ('E', 'East'),
        ('W', 'West'),
    ]

    intersection = models.ForeignKey(Intersection, on_delete=models.CASCADE, related_name='interpretations')
    datetime = models.DateTimeField()
    interpretation_text = models.TextField()
    congestion_level = models.CharField(max_length=20, choices=CONGESTION_LEVEL_CHOICES)
    peak_direction = models.CharField(max_length=1, choices=DIRECTION_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['intersection', 'datetime']
        ordering = ['-datetime']
        indexes = [
            models.Index(fields=['intersection', 'datetime']),
            models.Index(fields=['congestion_level']),
        ]

    def __str__(self):
        return f"{self.intersection.name} - {self.datetime} - {self.congestion_level}"

class Incident(models.Model):
    incident_id = models.AutoField(primary_key=True)
    incident_type = models.CharField(max_length=100, verbose_name="Incident Type", default="")
    intersection_name = models.CharField(max_length=200, verbose_name="Intersection Name", default="")
    district = models.CharField(max_length=100, verbose_name="District", default="")
    managed_by = models.CharField(max_length=100, verbose_name="Managed By", default="")
    assigned_to = models.CharField(max_length=100, verbose_name="Assigned To", default="")
    registered_at = models.DateTimeField(verbose_name="Registered At", auto_now_add=True)
    status = models.CharField(max_length=50, verbose_name="Status", default="OPEN")
    user = models.CharField(max_length=100, verbose_name="User", default="")
    equipment_locked = models.CharField(max_length=1, choices=[('S', 'Yes'), ('N', 'No')], verbose_name="Equipment Locked", default='N')
    last_status_update = models.DateTimeField(auto_now=True, verbose_name="Last Status Update")
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="IP Address")
    sii_id = models.IntegerField(null=True, blank=True, verbose_name="SII ID")
    intersection = models.ForeignKey("Intersection", on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Linked Intersection")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")
    type = models.CharField(max_length=100, verbose_name="Type", default="")

    def __str__(self):
        return f"{self.incident_id} - {self.intersection_name} - {self.status}"

    class Meta:
        ordering = ['-registered_at']
        verbose_name = "Incident"
        verbose_name_plural = "Incidents"
        indexes = [
            models.Index(fields=['incident_type']),
            models.Index(fields=['status']),
            models.Index(fields=['registered_at']),
            models.Index(fields=['district']),
            models.Index(fields=['intersection']),
        ]

# --- Secure Models ---

class S_TrafficVolume(models.Model):
    DIRECTION_CHOICES = [
        ('N', 'North'),
        ('S', 'South'),
        ('E', 'East'),
        ('W', 'West'),
    ]

    intersection = models.ForeignKey(Intersection, on_delete=models.CASCADE, related_name='s_traffic_volumes')
    datetime = models.DateTimeField()
    direction = models.CharField(max_length=1, choices=DIRECTION_CHOICES)
    volume = models.IntegerField()
    is_simulated = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"S_{self.intersection.name} - {self.datetime} - {self.direction}"

    class Meta:
        db_table = 'S_traffic_volume'
        ordering = ['-datetime']
        indexes = [
            models.Index(fields=['intersection', 'datetime']),
            models.Index(fields=['direction']),
        ]

class S_TotalTrafficVolume(models.Model):
    intersection = models.ForeignKey(Intersection, on_delete=models.CASCADE, related_name='s_total_traffic_volumes')
    datetime = models.DateTimeField()
    total_volume = models.IntegerField()
    average_speed = models.FloatField()

    class Meta:
        db_table = 'S_total_traffic_volume'
        indexes = [
            models.Index(fields=['intersection', 'datetime']),
        ]

    def __str__(self):
        return f"S_{self.intersection.name} - {self.datetime}: {self.total_volume}대, {self.average_speed}km/h"

class S_TrafficInterpretation(models.Model):
    CONGESTION_LEVEL_CHOICES = [
        ('low', 'Low'),
        ('moderate', 'Moderate'),
        ('high', 'High'),
        ('very_high', 'Very High'),
    ]
    
    DIRECTION_CHOICES = [
        ('N', 'North'),
        ('S', 'South'),
        ('E', 'East'),
        ('W', 'West'),
    ]

    intersection = models.ForeignKey(Intersection, on_delete=models.CASCADE, related_name='s_interpretations')
    datetime = models.DateTimeField()
    interpretation_text = models.TextField()
    congestion_level = models.CharField(max_length=20, choices=CONGESTION_LEVEL_CHOICES)
    peak_direction = models.CharField(max_length=1, choices=DIRECTION_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'S_traffic_interpretation'
        unique_together = ['intersection', 'datetime']
        ordering = ['-datetime']
        indexes = [
            models.Index(fields=['intersection', 'datetime']),
            models.Index(fields=['congestion_level']),
        ]

    def __str__(self):
        return f"S_{self.intersection.name} - {self.datetime} - {self.congestion_level}"

class S_Incident(models.Model):
    incident_id = models.AutoField(primary_key=True)
    incident_type = models.CharField(max_length=100, verbose_name="Incident Type", default="")
    intersection_name = models.CharField(max_length=200, verbose_name="Intersection Name", default="")
    district = models.CharField(max_length=100, verbose_name="District", default="")
    managed_by = models.CharField(max_length=100, verbose_name="Managed By", default="")
    assigned_to = models.CharField(max_length=100, verbose_name="Assigned To", default="")
    registered_at = models.DateTimeField(verbose_name="Registered At", auto_now_add=True)
    status = models.CharField(max_length=50, verbose_name="Status", default="OPEN")
    user = models.CharField(max_length=100, verbose_name="User", default="")
    equipment_locked = models.CharField(max_length=1, choices=[('S', 'Yes'), ('N', 'No')], verbose_name="Equipment Locked", default='N')
    last_status_update = models.DateTimeField(auto_now=True, verbose_name="Last Status Update")
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="IP Address")
    sii_id = models.IntegerField(null=True, blank=True, verbose_name="SII ID")
    intersection = models.ForeignKey("Intersection", on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Linked Intersection", related_name='s_incidents')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")
    type = models.CharField(max_length=100, verbose_name="Type", default="")

    def __str__(self):
        return f"S_{self.incident_id} - {self.intersection_name} - {self.status}"

    class Meta:
        db_table = 'S_incident'
        ordering = ['-registered_at']
        verbose_name = "Secure Incident"
        verbose_name_plural = "Secure Incidents"
        indexes = [
            models.Index(fields=['incident_type']),
            models.Index(fields=['status']),
            models.Index(fields=['registered_at']),
            models.Index(fields=['district']),
            models.Index(fields=['intersection']),
        ]

# 즐겨찾기 및 조회수 관련 모델들
class IntersectionStats(models.Model):
    """교차로 통계 모델 (조회수, 즐겨찾기 수 등)"""
    intersection = models.OneToOneField(Intersection, on_delete=models.CASCADE, related_name='stats')
    view_count = models.PositiveIntegerField(default=0, verbose_name="조회수")
    favorite_count = models.PositiveIntegerField(default=0, verbose_name="즐겨찾기 수")
    ai_report_count = models.PositiveIntegerField(default=0, verbose_name="AI 리포트 요청 수")
    last_viewed = models.DateTimeField(null=True, blank=True, verbose_name="마지막 조회 시간")
    last_ai_report = models.DateTimeField(null=True, blank=True, verbose_name="마지막 AI 리포트 요청 시간")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "교차로 통계"
        verbose_name_plural = "교차로 통계들"
        indexes = [
            models.Index(fields=['view_count']),
            models.Index(fields=['favorite_count']),
            models.Index(fields=['last_viewed']),
        ]

    def __str__(self):
        return f"{self.intersection.name} - 조회: {self.view_count}, 즐겨찾기: {self.favorite_count}"

class IntersectionViewLog(models.Model):
    """교차로 조회 로그 모델"""
    intersection = models.ForeignKey(Intersection, on_delete=models.CASCADE, related_name='view_logs')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="사용자")
    ip_address = models.GenericIPAddressField(verbose_name="IP 주소")
    user_agent = models.TextField(blank=True, verbose_name="User Agent")
    viewed_at = models.DateTimeField(auto_now_add=True, verbose_name="조회 시간")

    class Meta:
        verbose_name = "교차로 조회 로그"
        verbose_name_plural = "교차로 조회 로그들"
        indexes = [
            models.Index(fields=['intersection', 'viewed_at']),
            models.Index(fields=['user', 'viewed_at']),
            models.Index(fields=['ip_address']),
        ]

    def __str__(self):
        return f"{self.intersection.name} - {self.viewed_at}"

class IntersectionFavoriteLog(models.Model):
    """교차로 즐겨찾기 로그 모델"""
    intersection = models.ForeignKey(Intersection, on_delete=models.CASCADE, related_name='favorite_logs')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="사용자")
    is_favorite = models.BooleanField(verbose_name="즐겨찾기 여부")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성 시간")

    class Meta:
        verbose_name = "교차로 즐겨찾기 로그"
        verbose_name_plural = "교차로 즐겨찾기 로그들"
        indexes = [
            models.Index(fields=['intersection', 'user', 'is_favorite']),
            models.Index(fields=['user', 'is_favorite']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        status = "추가" if self.is_favorite else "제거"
        return f"{self.intersection.name} - {self.user.username} - {status}"

class TrafficFlowAnalysisFavorite(models.Model):
    """교통 흐름 분석 즐겨찾기 모델 (시작점 -> 끝점)"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="사용자")
    start_intersection = models.ForeignKey(
        'Intersection', 
        on_delete=models.CASCADE, 
        related_name='flow_favorites_as_start',
        verbose_name="시작 교차로"
    )
    end_intersection = models.ForeignKey(
        'Intersection', 
        on_delete=models.CASCADE, 
        related_name='flow_favorites_as_end',
        verbose_name="도착 교차로"
    )
    favorite_name = models.CharField(max_length=200, blank=True, verbose_name="즐겨찾기 이름")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성 시간")
    last_accessed = models.DateTimeField(null=True, blank=True, verbose_name="마지막 접근 시간")
    access_count = models.PositiveIntegerField(default=0, verbose_name="접근 횟수")

    class Meta:
        verbose_name = "교통 흐름 분석 즐겨찾기"
        verbose_name_plural = "교통 흐름 분석 즐겨찾기들"
        unique_together = ['user', 'start_intersection', 'end_intersection']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['start_intersection', 'end_intersection']),
            models.Index(fields=['access_count']),
            models.Index(fields=['last_accessed']),
        ]

    def save(self, *args, **kwargs):
        if not self.favorite_name:
            self.favorite_name = f"{self.start_intersection.name} → {self.end_intersection.name}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username}: {self.start_intersection.name} → {self.end_intersection.name}"

class TrafficFlowAnalysisStats(models.Model):
    """교통 흐름 분석 통계 모델 (시작점 -> 끝점별 인기도)"""
    start_intersection = models.ForeignKey(
        'Intersection', 
        on_delete=models.CASCADE, 
        related_name='flow_stats_as_start',
        verbose_name="시작 교차로"
    )
    end_intersection = models.ForeignKey(
        'Intersection', 
        on_delete=models.CASCADE, 
        related_name='flow_stats_as_end',
        verbose_name="도착 교차로"
    )
    total_favorites = models.PositiveIntegerField(default=0, verbose_name="총 즐겨찾기 수")
    total_accesses = models.PositiveIntegerField(default=0, verbose_name="총 접근 횟수")
    unique_users = models.PositiveIntegerField(default=0, verbose_name="고유 사용자 수")
    last_accessed = models.DateTimeField(null=True, blank=True, verbose_name="마지막 접근 시간")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성 시간")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="업데이트 시간")

    class Meta:
        verbose_name = "교통 흐름 분석 통계"
        verbose_name_plural = "교통 흐름 분석 통계들"
        unique_together = ['start_intersection', 'end_intersection']
        indexes = [
            models.Index(fields=['total_favorites']),
            models.Index(fields=['total_accesses']),
            models.Index(fields=['unique_users']),
            models.Index(fields=['last_accessed']),
        ]

    def __str__(self):
        return f"{self.start_intersection.name} → {self.end_intersection.name} (즐겨찾기: {self.total_favorites}명)"

# 정책제안 관련 모델들
class PolicyProposal(models.Model):
    """정책제안 모델"""
    CATEGORY_CHOICES = [
        ('traffic_signal', '신호등 관련'),
        ('road_safety', '도로 안전'),
        ('traffic_flow', '교통 흐름'),
        ('infrastructure', '인프라 개선'),
        ('policy', '교통 정책'),
        ('other', '기타'),
    ]
    
    STATUS_CHOICES = [
        ('pending', '대기 중'),
        ('under_review', '검토 중'),
        ('in_progress', '진행 중'),
        ('completed', '완료'),
        ('rejected', '반려'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', '낮음'),
        ('medium', '보통'),
        ('high', '높음'),
        ('urgent', '긴급'),
    ]

    title = models.CharField(max_length=200, verbose_name="제목")
    description = models.TextField(verbose_name="내용")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, verbose_name="카테고리")
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium', verbose_name="우선순위")
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending', verbose_name="상태")
    
    # 위치 관련 필드
    location = models.CharField(max_length=500, blank=True, verbose_name="위치 설명")
    intersection = models.ForeignKey(
        Intersection, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='proposals',
        verbose_name="관련 교차로"
    )
    latitude = models.FloatField(null=True, blank=True, verbose_name="위도")
    longitude = models.FloatField(null=True, blank=True, verbose_name="경도")
    
    # 제안자 정보
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='submitted_proposals',
        verbose_name="제안자"
    )
    
    # 관리자 응답
    admin_response = models.TextField(blank=True, verbose_name="관리자 답변")
    admin_response_date = models.DateTimeField(null=True, blank=True, verbose_name="답변일")
    admin_response_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='admin_responses',
        verbose_name="답변자"
    )
    
    # 통계
    votes_count = models.IntegerField(default=0, verbose_name="투표수")
    views_count = models.IntegerField(default=0, verbose_name="조회수")
    
    # 시간 필드
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="작성일")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일")

    class Meta:
        verbose_name = "정책제안"
        verbose_name_plural = "정책제안들"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['category']),
            models.Index(fields=['status']),
            models.Index(fields=['priority']),
            models.Index(fields=['intersection']),
            models.Index(fields=['submitted_by']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.title} - {self.get_status_display()}"

class ProposalAttachment(models.Model):
    """정책제안 첨부파일 모델"""
    proposal = models.ForeignKey(
        PolicyProposal, 
        on_delete=models.CASCADE, 
        related_name='attachments',
        verbose_name="정책제안"
    )
    file = models.FileField(upload_to='proposal_attachments/%Y/%m/%d/', verbose_name="파일")
    file_name = models.CharField(max_length=255, verbose_name="파일명")
    file_size = models.PositiveIntegerField(verbose_name="파일 크기")
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="업로드일")

    class Meta:
        verbose_name = "정책제안 첨부파일"
        verbose_name_plural = "정책제안 첨부파일들"
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.proposal.title} - {self.file_name}"

class ProposalVote(models.Model):
    """정책제안 투표 모델"""
    VOTE_CHOICES = [
        ('up', '추천'),
        ('down', '비추천'),
    ]

    proposal = models.ForeignKey(
        PolicyProposal, 
        on_delete=models.CASCADE, 
        related_name='votes',
        verbose_name="정책제안"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        verbose_name="투표자"
    )
    vote_type = models.CharField(max_length=4, choices=VOTE_CHOICES, verbose_name="투표 타입")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="투표일")

    class Meta:
        verbose_name = "정책제안 투표"
        verbose_name_plural = "정책제안 투표들"
        unique_together = ['proposal', 'user']  # 한 사용자는 한 제안에 하나의 투표만
        indexes = [
            models.Index(fields=['proposal', 'vote_type']),
            models.Index(fields=['user']),
        ]

    def __str__(self):
        return f"{self.proposal.title} - {self.user.username} - {self.get_vote_type_display()}"

class ProposalViewLog(models.Model):
    """정책제안 조회 로그 모델"""
    proposal = models.ForeignKey(
        PolicyProposal, 
        on_delete=models.CASCADE, 
        related_name='view_logs',
        verbose_name="정책제안"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name="사용자"
    )
    ip_address = models.GenericIPAddressField(verbose_name="IP 주소")
    viewed_at = models.DateTimeField(auto_now_add=True, verbose_name="조회일")

    class Meta:
        verbose_name = "정책제안 조회 로그"
        verbose_name_plural = "정책제안 조회 로그들"
        indexes = [
            models.Index(fields=['proposal', 'viewed_at']),
            models.Index(fields=['user']),
            models.Index(fields=['ip_address']),
        ]

    def __str__(self):
        return f"{self.proposal.title} - {self.viewed_at}"

class ProposalTag(models.Model):
    """정책제안 태그 모델"""
    name = models.CharField(max_length=50, unique=True, verbose_name="태그명")
    proposals = models.ManyToManyField(
        PolicyProposal, 
        related_name='tags',
        verbose_name="정책제안들"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일")

    class Meta:
        verbose_name = "정책제안 태그"
        verbose_name_plural = "정책제안 태그들"
        ordering = ['name']

    def __str__(self):
        return self.name