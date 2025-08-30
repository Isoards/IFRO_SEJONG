from django.contrib import admin
from django.utils import timezone
from .models import (
    Intersection, TrafficVolume, TotalTrafficVolume, 
    PolicyProposal, ProposalAttachment, ProposalVote, ProposalViewLog, ProposalTag
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
