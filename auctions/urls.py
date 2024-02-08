from django.urls import path
from allauth.account.views import SignupView
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("", views.index, name="index"),
    # path("", views.Bid, name="bid")
    path('login', views.login_view, name="login"),
    path('logout', views.logout_view, name="logout"),
    path('register', views.register , name="account_signup"),
    path('verify', views.verify, name="verify"),
    path('verify/<str:uid64>/<str:token>/', views.verify_email, name='verify_email'),
    path('NewItem', views.NewItem, name="NewItem"),
    path('media/<int:image_id>/', views.image, name="display_image"),
    path('notifications_view', views.notifications_view, name="notifications_view"),
    path('cart_view', views.cart_view, name="cart_view"),
    path('delete_notifications/<int:cardId>/', views.delete_notifications, name="delete_notifications"),
    path('seen_notifications/', views.seen_notifications, name="seen+notifications"),
    path('get_csrf_token', views.get_csrf_token, name="get_csrf_token"),
    # path('search_results', views.search, name="search_results")
    path('switch_accounts/', views.switch_accounts, name="switch_accounts"),
    
]
# you can use api on your webapp
#  to show media files
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)