from django.urls import path
from . import views

urlpatterns = [
    path('patterns/', views.PatternList.as_view(), name='pattern-list'),
    path('leaks/', views.DetectedLeakCreate.as_view(), name='leak-create'),
    path('slack/events/', views.slack_events_webhook, name='slack_events'),
]
