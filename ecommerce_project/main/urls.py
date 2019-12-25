from django.urls import path, include
from django.views.generic import TemplateView, DetailView
from main import views, models, forms
from django.contrib.auth import views as auth_views


urlpatterns = [
    path('', TemplateView.as_view(template_name="home.html"), name='home'),
    path('about-us/', TemplateView.as_view(template_name="about_us.html"), name='about_us'),
    path('contact-us/', views.ContactUsView.as_view(), name='contact-us'),
    path('products/<slug:tag>/', views.ProductListView.as_view(), name='products'),
    path('product/<slug:slug>/',views.ProductDetailView.as_view(), name="product"),
    path('signup/', views.SignupView.as_view(), name='signup'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html', form_class=forms.AuthenticationForm,),name='login'),

    path('address/', views.AddressListView.as_view(), name='address_list'),
    path('address/create/', views.AddressCreateView.as_view(), name='address_create'),
    path('address/<int:pk>/edit/', views.AddressUpdateView.as_view(), name='address_update'),
    path('address/<int:pk>/delete/', views.AddressDeleteView.as_view(), name='address_delete'),
    path('add_to_basket/', views.add_to_basket, name="add_to_basket",),
    path('basket/', views.manage_basket, name='basket',),

    path('order/done/', TemplateView.as_view(template_name="order_done.html"),name="checkout_done", ),
    path('order/address_select/', views.AddressSelectionView.as_view(),  name="address_select", ),


]
