from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count
from django.utils import timezone
from .models import (
    (
    Intersection, TrafficVolume, TotalTrafficVolume, 
    PolicyProposal, ProposalAttachment, ProposalVote, ProposalViewLog, ProposalTag
), 
    IntersectionStats, IntersectionViewLog, IntersectionFavoriteLog,
    TrafficFlowAnalysisFavorite, TrafficFlowAnalysisStats
)

@admin.register(Intersection)
class IntersectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'latitude', 'longitude', 'created_at', 'updated_at')
    search_fields = ('name',)
    list_filter = ('created_at', 'updated_at')

@admin.register(TrafficVolume)
class TrafficVolumeAdmin(admin.ModelAdmin):
    list_display = ('intersection', 'datetime', 'direction', 'volume', 'is_simulated', 'created_at')
    list_filter = ('intersection', 'direction', 'is_simulated', 'datetime')
    search_fields = ('intersection__name',)
    date_hierarchy = 'datetime'
    ordering = ('-datetime',)

@admin.register(IntersectionStats)
class IntersectionStatsAdmin(admin.ModelAdmin):
    list_display = ('intersection', 'view_count', 'favorite_count', 'ai_report_count', 'last_viewed')
    list_filter = ('last_viewed', 'last_ai_report')
    search_fields = ('intersection__name',)
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-favorite_count', '-view_count')

@admin.register(IntersectionViewLog)
class IntersectionViewLogAdmin(admin.ModelAdmin):
    list_display = ('intersection', 'user', 'ip_address', 'viewed_at')
    list_filter = ('viewed_at', 'intersection')
    search_fields = ('intersection__name', 'user__username', 'ip_address')
    readonly_fields = ('viewed_at',)
    ordering = ('-viewed_at',)

@admin.register(IntersectionFavoriteLog)
class IntersectionFavoriteLogAdmin(admin.ModelAdmin):
    list_display = ('intersection', 'user', 'is_favorite', 'created_at')
    list_filter = ('is_favorite', 'created_at', 'intersection')
    search_fields = ('intersection__name', 'user__username')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)

@admin.register(TrafficFlowAnalysisFavorite)
class TrafficFlowAnalysisFavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'flow_route', 'favorite_name', 'access_count', 'last_accessed', 'created_at')
    list_filter = ('created_at', 'last_accessed', 'start_intersection', 'end_intersection')
    search_fields = ('user__username', 'start_intersection__name', 'end_intersection__name', 'favorite_name')
    readonly_fields = ('created_at',)
    ordering = ('-access_count', '-last_accessed')
    list_per_page = 25
    date_hierarchy = 'created_at'
    
    def flow_route(self, obj):
        return format_html(
            '<span style="color: #0066cc; font-weight: bold;">{}</span> → <span style="color: #cc6600; font-weight: bold;">{}</span>',
            obj.start_intersection.name,
            obj.end_intersection.name
        )
    flow_route.short_description = '교통 흐름 경로'
    flow_route.admin_order_field = 'start_intersection__name'
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('user', 'start_intersection', 'end_intersection')

@admin.register(TrafficFlowAnalysisStats)
class TrafficFlowAnalysisStatsAdmin(admin.ModelAdmin):
    list_display = ('flow_route', 'total_favorites', 'total_accesses', 'unique_users', 'popularity_score', 'last_accessed')
    list_filter = ('last_accessed', 'created_at', 'start_intersection', 'end_intersection')
    search_fields = ('start_intersection__name', 'end_intersection__name')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-total_favorites', '-total_accesses')
    
    def flow_route(self, obj):
        return format_html(
            '<span style="color: #0066cc; font-weight: bold;">{}</span> → <span style="color: #cc6600; font-weight: bold;">{}</span>',
            obj.start_intersection.name,
            obj.end_intersection.name
        )
    flow_route.short_description = '교통 흐름 경로'
    flow_route.admin_order_field = 'start_intersection__name'
    
    def popularity_score(self, obj):
        # 인기도 점수 계산 (즐겨찾기 수 * 2 + 접근 횟수)
        score = obj.total_favorites * 2 + obj.total_accesses
        if score >= 50:
            color = '#d32f2f'  # 빨간색 (매우 인기)
        elif score >= 20:
            color = '#f57c00'  # 주황색 (인기)
        elif score >= 10:
            color = '#388e3c'  # 초록색 (보통)
        else:
            color = '#757575'  # 회색 (낮음)
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            score
        )
    popularity_score.short_description = '인기도 점수'
    popularity_score.admin_order_field = 'total_favorites'

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('start_intersection', 'end_intersection')

admin.site.register(TotalTrafficVolume)

# 정책제안 관련 Admin 설정
@admin.register(PolicyProposal)
class PolicyProposalAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'priority', 'status', 'submitted_by', 'intersection', 'created_at')
    list_filter = ('category', 'priority', 'status', 'created_at', 'intersection')
    search_fields = ('title', 'description', 'location', 'submitted_by__username', 'submitted_by__email')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    readonly_fields = ('votes_count', 'views_count', 'created_at', 'updated_at')
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('title', 'description', 'category', 'priority', 'status')
        }),
        ('위치 정보', {
            'fields': ('location', 'intersection', 'latitude', 'longitude')
        }),
        ('제안자 정보', {
            'fields': ('submitted_by',)
        }),
        ('관리자 응답', {
            'fields': ('admin_response', 'admin_response_date', 'admin_response_by')
        }),
        ('통계', {
            'fields': ('votes_count', 'views_count')
        }),
        ('시간 정보', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if change and 'admin_response' in form.changed_data and obj.admin_response:
            obj.admin_response_by = request.user
            obj.admin_response_date = timezone.now()
        super().save_model(request, obj, form, change)

@admin.register(ProposalAttachment)
class ProposalAttachmentAdmin(admin.ModelAdmin):
    list_display = ('proposal', 'file_name', 'file_size', 'uploaded_at')
    list_filter = ('uploaded_at',)
    search_fields = ('proposal__title', 'file_name')
    readonly_fields = ('file_size', 'uploaded_at')

@admin.register(ProposalVote)
class ProposalVoteAdmin(admin.ModelAdmin):
    list_display = ('proposal', 'user', 'vote_type', 'created_at')
    list_filter = ('vote_type', 'created_at')
    search_fields = ('proposal__title', 'user__username')
    readonly_fields = ('created_at',)

@admin.register(ProposalViewLog)
class ProposalViewLogAdmin(admin.ModelAdmin):
    list_display = ('proposal', 'user', 'ip_address', 'viewed_at')
    list_filter = ('viewed_at',)
    search_fields = ('proposal__title', 'user__username', 'ip_address')
    readonly_fields = ('viewed_at',)

@admin.register(ProposalTag)
class ProposalTagAdmin(admin.ModelAdmin):
    list_display = ('name', 'get_proposals_count', 'created_at')
    search_fields = ('name',)
    readonly_fields = ('created_at',)
    
    def get_proposals_count(self, obj):
        return obj.proposals.count()
    get_proposals_count.short_description = '제안 수'
