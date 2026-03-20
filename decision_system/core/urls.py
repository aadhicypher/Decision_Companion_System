from django.urls import path
from . import views

urlpatterns = [
    path("", views.landing_page, name="root"),
    path("accounts/login/", views.login_view, name="login"),
    path("accounts/logout/", views.logout_view, name="logout"),
    path("accounts/forgot-password/", views.forgot_password_view, name="forgot_password"),
    path("accounts/verify-otp/", views.verify_reset_otp_view, name="verify_reset_otp"),
    path("accounts/reset-password/", views.reset_password_view, name="reset_password"),
    path("signup/", views.signup, name="signup"),
    path("questions/", views.questions_page, name="questions_page"),
    path("result/", views.result_page, name="result_page"),
    path("home/", views.home_page, name="home_page"),
    path("decision/", views.decision_form, name="decision_form"),
    path("history/<int:decision_id>/", views.decision_history, name="decision_history"),

]
