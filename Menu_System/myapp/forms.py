from django import forms
from .models import Restaurant, Account, Order
from django.contrib.auth.forms import AuthenticationForm,UserCreationForm
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
import json
User = get_user_model()

class CustomAuthForm(AuthenticationForm):
    username = forms.CharField(label='Account', widget=forms.TextInput(attrs={'autofocus': True}))

    def clean_username(self):
        account = self.cleaned_data['username']
        return account
    
class RegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('name', 'account', 'password1', 'password2', 'phone_number')

    def clean_account(self):
        account = self.cleaned_data.get('account')
        if User.objects.filter(account=account).exists():
            raise ValidationError("An account with this account name already exists.")
        return account

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user

class RestaurantForm(forms.ModelForm):
    class Meta:
        model = Restaurant
        fields = ['name', 'space_id', 'phone_number', 'line_id', 'menu_list', 'orders','area']

class RestaurantCreateForm(forms.ModelForm):
    class Meta:
        model = Restaurant
        fields = ['name', 'space_id', 'phone_number', 'line_id','area']

    # def clean_menu_list(self):
    #     menu_list = self.cleaned_data.get('menu_list', '')
    #     new_data = []
    #     try:
    #         if not isinstance(menu_list, dict) or 'data' not in menu_list:
    #             raise ValidationError("Invalid format for menu_list. Expected a dictionary containing a 'data' key.")

    #         for item in menu_list['data']:
    #             if not all(k in item for k in ['name', 'price', 'tag', 'status']):
    #                 raise ValidationError("Each item in 'data' must contain 'name', 'price', 'tag', and 'status'.")
                
    #             item['id'] = menu_list['data'].index(item) + 1
    #             new_data.append(item)
    #             print(item['id'])
    #         menu_list['data'] = new_data 
    #     except json.JSONDecodeError:
    #         raise ValidationError("menu_list must be a valid JSON string.")

    #     print("OK")
    #     return menu_list

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['items','order_value','restaurant','member','company', 'status']

    quantity = forms.IntegerField(initial=1, min_value=1)
    notes = forms.CharField(widget=forms.Textarea, required=False)
    
from .models import Company

class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ['name', 'members']
from .models import Order

class OrderEditForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = []

    def __init__(self, *args, **kwargs):
        super(OrderEditForm, self).__init__(*args, **kwargs)
        items = kwargs.get('initial', {}).get('items', [])
        for i, item in enumerate(items):
            self.fields[f'item_{i}_name'] = forms.CharField(initial=item['name'], label='Name')
            self.fields[f'item_{i}_amount'] = forms.IntegerField(initial=item['amount'], label='Amount')
            self.fields[f'item_{i}_price'] = forms.FloatField(initial=item['price'], label='Price')
