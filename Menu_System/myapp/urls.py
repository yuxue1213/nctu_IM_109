from django.urls import path
from . import views

urlpatterns = [
    path('', views.user_login, name='login'),
    path('register/', views.register, name='register'),
    path('home', views.select_restaurant, name='home'),
    path('restaurant/order_menu/<int:id>/', views.order_menu, name='order_menu'),
    path('create_restaurant', views.create_restaurant, name='create_restaurant'),
    path('add_menu_list/<int:restaurant_id>/', views.add_menu_list, name='add_menu_list'),
    path('add_menu_item/', views.add_menu_item, name='add_menu_item'),
    path('update_menu_item/', views.update_menu_item, name='update_menu_item'),
    path('search/', views.search_restaurants, name='search_restaurants'),
    path('delete_menu_item/', views.delete_menu_item, name='delete_menu_item'),
    path('delete_all_restaurants/', views.delete_all_restaurants, name='delete_all_restaurants'),
    path('add_company/', views.add_company, name='add_company'),
    path('company_list/', views.company_list, name='company_list'), 
    path('delete_restaurant/', views.delete_restaurant, name='delete_restaurant'),
    path('delete_all_orders/', views.delete_all_orders, name='delete_all_orders'),    
    path('delete_order/<int:order_id>/', views.delete_order, name='delete_order'),
    path('check_order/<int:order_id>/', views.check_order, name='check_order'),
    path('edit_order/<int:order_id>/', views.edit_order, name='edit_order'),
    path('admin_home', views.admin_home, name='admin_home'),
    path('order_completed/<int:order_id>/', views.order_completed, name='order_completed'),
    path('order_list/', views.order_list, name='order_list')
]
