"""
URL configuration for dashboard project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.http import JsonResponse
from ninja_extra import NinjaExtraAPI
from traffic.views import router as traffic_router, secure_router as secure_traffic_router
from user_auth.views import router as auth_router
from chatbot_proxy.views import router as chatbot_router

def health_check(request):
    return JsonResponse({"status": "healthy"}, status=200)

api = NinjaExtraAPI()
api.add_router("/traffic/", traffic_router)
api.add_router("/auth/", auth_router)
api.add_router("/secure/traffic/", secure_traffic_router)
api.add_router("/chatbot/", chatbot_router)
# 정책제안 API는 traffic 라우터에 포함되어 있음

# API 루트 뷰 추가
@api.get("/")
def api_root(request):
    return {"message": "IFRO API", "version": "1.0", "docs": "/docs", "openapi": "/openapi.json"}

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', api.urls),
    path('health/', health_check, name='health_check'),
]
