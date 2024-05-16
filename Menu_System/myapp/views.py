from django.shortcuts import render, redirect, get_object_or_404
from .models import Restaurant, Order, Member
from .forms import *
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect, JsonResponse
from utils import jwt 
from django.utils import timezone
from django.templatetags.static import static
from django.core.files.storage import FileSystemStorage


#
def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            user_name = request.POST.get('name')
            company_id = request.POST.get('company')
            print( company_id)
            company = get_object_or_404(Company, id=company_id)
            company_members = company.members
            print(company_members)
            member = Member(name=user_name, company=company)
            member.save()
            return redirect('login')
        else:
            return render(request, 'register.html', {'form': form})
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        form = CustomAuthForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)

            token = jwt.generate_jwt(user)
            response = redirect('home')
            response.set_cookie(key='jwt', value=token, httponly=True, samesite='Lax')
            return response
    else:
        form = CustomAuthForm()

    return render(request, 'login.html', {'form': form})

def admin_login(request):
    if request.method == 'POST':
        form = CustomAuthForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            token = jwt.generate_jwt(user)
            response = redirect('admin_home')
            response.set_cookie(key='jwt', value=token, httponly=True, samesite='Lax')
            return response
    else:
        form = CustomAuthForm()

    return render(request, 'admin_login.html', {'form': form})

@jwt.jwt_required
def select_restaurant(request):
    user_info = getattr(request, 'user_info', None) 
    print(user_info)
    if request.method == 'POST':
        keyword = request.GET['search_keyword']
        restaurant = Restaurant.objects.filter(name__icontains=keyword)
        if restaurant.is_valid():
            restaurant_id = restaurant.cleaned_data['id']
            return redirect('order_menu', id=restaurant_id)
        else:
            raise ValueError('請輸入正確的餐廳名稱')
    else:
        restaurant = Restaurant.objects.all
        return render(request, 'home.html', {"restaurants": restaurant})
    
@jwt.jwt_required
def order_menu(request, id):
    restaurant = get_object_or_404(Restaurant, id=id)
    user_info = getattr(request, 'user_info', None)
    member_id = user_info['name']
    order_item_tag = set(item['tag'] for item in restaurant.menu_list['data'] if item['status'] != 'delete')

    if request.method == 'POST':
        order_items = []
        total_price = 0

        for item in restaurant.menu_list['data']:
            item_name = item['name']
            item_data = request.POST.get(item_name, '')
            item_note = request.POST.get(item_name + '_note', '')

            if item_data:
                item_amount = int(item_data)
                item_price = float(item['price'])
                order_item = {
                    'id': item.get('id', 1),
                    'name': item_name,
                    'amount': item_amount,
                    'price': item_price,
                    'tag': item['tag'],
                    'note': item_note,
                }
                order_items.append(order_item)
                total_price += item_amount * item_price

        company_id = user_info.get('company', 1)
        company = get_object_or_404(Company, id=company_id)

        new_order = Order.objects.create(
            items=order_items,
            order_value=total_price,
            restaurant=restaurant,
            member=member_id,
            company=company,
            status='submitted',
            last_update_time=timezone.now()
        )

        orders = restaurant.orders.get('orders', [])  
        orders.append(new_order.id)
        restaurant.orders['orders'] = orders  
        restaurant.save()

        return redirect('check_order', order_id=new_order.id)
    else:
        context = {
            'member': member_id,
            'restaurant': restaurant,
            'menu_list': restaurant.menu_list,
            'order_item_tag': order_item_tag
        }
        return render(request, 'order_menu.html', context)
    
@jwt.jwt_required
def create_restaurant(request):
    if request.method == 'POST':
        form = RestaurantCreateForm(request.POST)
        if form.is_valid():
            restaurant = form.save(commit=False)
            restaurant.orders = {}
            restaurant.menu_list = {"data":[]}
            restaurant.save()
            print("Save this restaurant")
            return redirect('add_menu_list', restaurant_id=restaurant.id) 
        else:
            messages.error(request, "Error creating the restaurant. Please check the form data.")
    else:
        form = RestaurantCreateForm()
    return render(request, 'create_restaurant.html', {'form': form})

@jwt.jwt_required
def add_menu_list(request, restaurant_id):
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    menu_list = restaurant.menu_list if isinstance(restaurant.menu_list, dict) else {}
    menu_data = menu_list.get("data", [])
    default_image_url = static('images/50嵐.png')

    return render(request, 'add_menu.html', 
                  {'restaurant': restaurant,
                   'menu_list': menu_data,
                   'default_image_url': default_image_url})

def update_menu_item(request):
    if request.method == 'POST':
        restaurant_id = request.POST.get('restaurant_id')
        item_id = request.POST.get('item_id')
        print(item_id)
        name = request.POST.get('name')
        price = request.POST.get('price')
        tag = request.POST.get('tag')
        try:
            restaurant = Restaurant.objects.get(id=restaurant_id)
            menu_list = restaurant.menu_list
            item_id = int(item_id) 
            for item in menu_list['data']:
                if int(item['id']) == item_id:
                    item['name'] = name
                    item['price'] = price
                    item['tag'] = tag
                    break
            restaurant.menu_list = menu_list
            restaurant.save()
            print('update success')
            return JsonResponse({'message': 'Menu item updated successfully'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

def add_menu_item(request):
    if request.method == 'POST':    
        restaurant_id = request.POST.get('restaurant_id')
        item_name = request.POST.get('name')
        item_price = request.POST.get('price')
        item_tag = request.POST.get('tag')
        item_photo = request.FILES.get('photo')
        item_photo= request.FILES['photo'] if 'photo' in request.FILES else None
        restaurant = get_object_or_404(Restaurant, id=restaurant_id)

        if item_photo:
            print('Success loading image')
            fs = FileSystemStorage(location='static/image')
            filename = fs.save(item_photo.name, item_photo)
            uploaded_file_url = fs.url("Menu_System\static\image")

            extension = item_photo.name.split('.')[-1]
            filename = f"{item_name}.{extension}"
            filename = fs.save(filename, item_photo)
            uploaded_file_url = fs.url(filename)
        else:
            uploaded_file_url = None

        if restaurant:
            print("Success")
            menu_list = restaurant.menu_list
        
            new_item_id = len(menu_list['data']) + 1
            add_item = {
                "name": item_name,
                "price": item_price,
                "tag": item_tag,
                **({"photo": "/image" + uploaded_file_url} if uploaded_file_url else {}),
                "status": "on",
                "id": new_item_id
            }

            menu_list['data'].append(add_item)
            restaurant.menu_list = menu_list
            restaurant.save()
        
            return JsonResponse({'message': 'Item added successfully'})
    return JsonResponse({'error': 'Invalid request'}, status=400)

def delete_menu_item(request):
    if request.method == 'POST':
        restaurant_id = request.POST.get('restaurant_id')
        item_id = request.POST.get('item_id')

        restaurant = Restaurant.objects.get(id=restaurant_id)
        menu_list = restaurant.menu_list
        item_id = int(item_id) 
        for item in menu_list['data']:
            if int(item['id']) == item_id:
                item['status'] = 'delete'
                break
        restaurant.menu_list = menu_list
        restaurant.save()
        print('Delete success')
        return redirect('add_menu_list', restaurant_id=restaurant_id)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

def search_restaurants(request):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        query = request.GET.get('term', '')
        restaurants = Restaurant.objects.filter(name__icontains=query)
        results = [{'id': restaurant.id, 'name': restaurant.name ,'space_id': restaurant.space_id, 'phone_number': restaurant.phone_number ,'line_id': restaurant.line_id, 'created_at': restaurant.created_at ,} for restaurant in restaurants]
        return JsonResponse(results, safe=False)
    return JsonResponse({'error': 'Not Ajax request'}, status=400)

def delete_all_restaurants(request):
    if request.method == 'POST':
        try:
            Restaurant.objects.all().delete()
            return JsonResponse({'message': 'All restaurants have been successfully deleted.'}, status=200)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': str(e)}, status=500)

def delete_restaurant(request):
    restaurant_id = request.POST.get('restaurant_id')
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    try:
        restaurant.delete()
        return JsonResponse({'message': 'Restaurant has been successfully deleted.'}, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def delete_all_orders(request):
    try:
        Order.objects.all().delete()
        return JsonResponse({'message': 'All restaurants have been successfully deleted.'}, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def delete_order(request):
    order_id = request.POST.get('order_id')
    print(order_id)
    order = get_object_or_404(Order, id=order_id)
    try:
        print('order_delete')
        order.delete()
        return JsonResponse({'message': 'Restaurant has been successfully deleted.'}, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
from .forms import CompanyForm

def company_list(request):
    companies = Company.objects.all()
    return render(request, 'company_list.html', {'companies': companies})

def add_company(request):
    if request.method == 'POST':
        form = CompanyForm(request.POST)
        if form.is_valid():
            company = form.save(commit=False)
            company.members = []  
            company.save()
            return redirect('company_list')
    else:
        form = CompanyForm()

    return render(request, 'add_company.html', {'form': form})

@jwt.jwt_required
def check_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if request.method == 'POST':
        if 'edit' in request.POST:
            order.status = 'completed'
            order.save()
            return redirect('home')
        elif 'cancel' in request.POST:
            order.status = 'cancel'
            order.save()
            return redirect('home')
        elif 'complete' in request.POST:
            order.status = 'completed'
            order.save()
            return redirect('order_completed', order_id=order.id)

    return render(request, 'check_order.html', {'order': order})

def edit_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if request.method == 'POST':
        form = OrderEditForm(request.POST, instance=order, initial={'items': order.items})
        if form.is_valid():
            order.items = [{'name': form.cleaned_data[f'item_{i}_name'], 'amount': form.cleaned_data[f'item_{i}_amount'], 'price': form.cleaned_data[f'item_{i}_price']} for i in range(len(order.items))]
            order.save()
            return redirect('check_order', order_id=order.id)
    else:
        form = OrderEditForm(initial={'items': order.items})

    return render(request, 'edit_order.html', {'form': form, 'order': order})

def order_completed(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'order_completed.html', {'order': order})

@jwt.jwt_required
def order_list(request):
    user_name = request.user_info['name']
    orders = Order.objects.filter(member=user_name).order_by('-created_at')
    restaurants = Restaurant.objects.all()
    orders_with_member_name = []
    for order in orders:
        member_name = order.member if order.member !=None else "未知會員"
        order_data = {
            'id': order.id,
            'items': order.items,
            'order_value': order.order_value,
            'restaurant_name': order.restaurant.name,
            'member_name': member_name,
            'company': order.company,
            'status': order.status,
            'last_update_time': order.last_update_time,
            'updated_at': order.updated_at,
            'created_at': order.created_at
        }
        orders_with_member_name.append(order_data)
    return render(request, 'order_list.html', {'orders': orders_with_member_name, 'restaurants': restaurants})




@jwt.jwt_required
def admin_home(request):
    user_info = getattr(request, 'user_info', None) 
    print(user_info)
    if request.method == 'POST':
        keyword = request.GET['search_keyword']
        restaurant = Restaurant.objects.filter(name__icontains=keyword)
        if restaurant.is_valid():
            restaurant_id = restaurant.cleaned_data['id']
            return redirect('order_menu', id=restaurant_id)
        else:
            raise ValueError('請輸入正確的餐廳名稱')
    else:
        restaurant = Restaurant.objects.all().values()
        print(restaurant)
        return render(request, 'admin_home.html', {"restaurants": restaurant})

def get_restaurants_by_area(request):
    area = request.GET.get('area')
    print(area)
    if area:
        restaurants = Restaurant.objects.all().values('id','name', 'space_id', 'phone_number', 'line_id')
        print("All restaurants data:", list(restaurants))  
        restaurants = Restaurant.objects.filter(area=area).values('id','name', 'space_id', 'phone_number', 'line_id')
        return JsonResponse(list(restaurants), safe=False)
    else:
        restaurants = Restaurant.objects.all().values('id','name', 'space_id', 'phone_number', 'line_id')
        print("All restaurants data:", list(restaurants))  

        return JsonResponse(list(restaurants), safe=False)
    

@jwt.jwt_required
def order_manage(request):
    orders = Order.objects.all().order_by('-created_at')
    restaurants = Restaurant.objects.all()
    orders_with_member_name = []

    for order in orders:
        member_name = order.member if order.member !=None else "未知會員"
        order_data = {
            'id': order.id,
            'items': order.items,
            'order_value': order.order_value,
            'restaurant_name': order.restaurant.name,
            'member_name': member_name,
            'company': order.company,
            'status': order.status,
            'last_update_time': order.last_update_time,
            'updated_at': order.updated_at,
            'created_at': order.created_at
        }
        orders_with_member_name.append(order_data)
    return render(request, 'order_manage.html', {'orders': orders_with_member_name, 'restaurants':restaurants})

def complete_order(request):
    order_id = request.POST.get('order_id')
    if order_id:
        try:
            order = Order.objects.get(id=order_id)
            order.status = 'completed'
            order.save()
            return JsonResponse({'message': 'Order marked as complete'}, status=200)
        except Order.DoesNotExist:
            return JsonResponse({'error': 'Order not found'}, status=404)
    return JsonResponse({'error': 'Invalid request'}, status=400)