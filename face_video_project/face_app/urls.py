from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.home, name='home'),
    path('AdminLogin', views.admin_login, name='admin_login'),
    path('AdminHome', views.admin_home, name='admin_home'),
    path('UserList', views.user_list, name='user_list'),
    path('ComplaintList', views.complaint_list, name='complaint_list'),
    path('NewComplaint', views.new_complaint, name='new_complaint'),
    path('Complaint/<str:complaint_no>/', views.complaint_detail, name='complaint_detail'),
    path('UserLogin', views.user_login, name='user_login'),
    path('NewUser', views.new_user, name='new_user'),
    path('UComplaintInfo/<str:complaint_no>/', views.u_complaint_info, name='u_complaint_info'),
    path('InvestigationList', views.investigation_list, name='investigation_list'),
    path('UploadVideo/<str:complaint_no>/', views.upload_video, name='upload_video'),
    path('FaceMatch/<str:complaint_no>/', views.face_match, name='face_match'),
    path('UserHome', views.user_home, name='user_home'),
    path('UserComplaints', views.user_complaints, name='user_complaints'),
    path('investigation_details/<str:complaint_no>/', views.investigation_details, name='investigation_details'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)