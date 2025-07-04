# testapp/urls.py ga qo'shimcha URL patterns

from django.urls import path
from . import views

app_name = 'testapp'

urlpatterns = [
    # Existing URLs...
    path('', views.home_view, name='home'),
    
    # Test sahifalari
    path('start/', views.test_start_view, name='test_start'),
    path('results/', views.test_results_view, name='test_results'),
    path('chatbot/', views.test_chatbot_view, name='test_chatbot'),
    
    # Admin sahifalari
    path('admin/login/', views.admin_login_view, name='admin_login'),
    path('admin/logout/', views.admin_logout_view, name='admin_logout'),
    path('admin/dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
    
    # Fan boshqaruvi
    path('admin/subjects/', views.admin_subjects_view, name='admin_subjects'),
    path('admin/subjects/add/', views.admin_subject_add_view, name='admin_subject_add'),
    path('admin/subjects/<int:subject_id>/edit/', views.admin_subject_edit_view, name='admin_subject_edit'),
    path('admin/subjects/<int:subject_id>/delete/', views.admin_subject_delete_view, name='admin_subject_delete'),
    
    # Savollar boshqaruvi
    path('admin/questions/', views.admin_questions_view, name='admin_questions'),
    path('admin/questions/add/', views.admin_question_add_view, name='admin_question_add'),
    path('admin/questions/bulk-add/', views.admin_questions_bulk_add_view, name='admin_questions_bulk_add'),
    path('admin/questions/<int:question_id>/edit/', views.admin_question_edit_view, name='admin_question_edit'),
    path('admin/questions/<int:question_id>/delete/', views.admin_question_delete_view, name='admin_question_delete'),
    path('admin/questions/import/', views.import_questions_view, name='import_questions'),
    
    # Testlar va natijalar
    path('admin/tests/', views.admin_tests_view, name='admin_tests'),
    path('admin/tests/<int:test_id>/', views.admin_test_detail_view, name='admin_test_detail'),
    path('admin/results/', views.admin_results_view, name='admin_results'),
    
    # Export URLs
    path('admin/export/results/', views.export_results_view, name='export_results'),
    path('admin/export/questions/', views.export_questions_view, name='export_questions'),
    path('admin/export/subjects/', views.export_subjects_view, name='export_subjects'),
    
    # Analytics URLs
    path('admin/analytics/', views.analytics_dashboard_view, name='analytics_dashboard'),
    path('admin/analytics/questions/', views.question_difficulty_analysis_view, name='question_difficulty_analysis'),
    path('admin/search/', views.advanced_search_view, name='advanced_search'),
    
    # Bulk operations
    path('admin/bulk/delete-questions/', views.bulk_delete_questions_view, name='bulk_delete_questions'),
    path('admin/bulk/activate-tests/', views.bulk_activate_tests_view, name='bulk_activate_tests'),
    
    # API endpoints
    path('api/create-test/', views.api_create_test, name='api_create_test'),
    path('api/check-test/', views.api_check_test, name='api_check_test'),
    path('api/subjects/', views.api_get_subjects, name='api_get_subjects'),
    path('api/subjects/<int:subject_id>/stats/', views.api_get_subject_stats, name='api_get_subject_stats'),
    path('api/tests/<int:test_id>/stats/', views.api_get_test_stats, name='api_get_test_stats'),
    path('api/tests/<int:test_id>/duplicate/', views.api_duplicate_test, name='api_duplicate_test'),
    path('api/tests/<int:test_id>/live-results/', views.api_live_results, name='api_live_results'),
    path('api/check-participation/', views.api_check_participation, name='api_check_participation'),
    path('api/generate-questions/', views.api_generate_questions, name='api_generate_questions'),
    path('api/generate-answer/', views.api_generate_answer, name='api_generate_answer'),
    path('api/chat-history/', views.api_get_chat_history, name='api_get_chat_history'),
    
    # Notifications
    path('admin/tests/<int:test_id>/notify/', views.send_test_notification_view, name='send_test_notification'),
]