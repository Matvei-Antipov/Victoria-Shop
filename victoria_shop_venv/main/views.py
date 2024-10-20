from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib import auth
from django.urls import reverse
from .translator import translate

from .models import Goods

#main page
def index(request):

    countries = ['egypt', 'turkey', 'emirates']
    categories = ['shampoos', 'cosmetic', 'perfume', 'massage', 'tea', 'coffee', 'cream', 'drugs', 'vitamin', 'oil', 'ointment', 'toothpaste', 'food', 'deodorant', 'gel', 'candle', 'depilation', 'wallet', 'swimming', 'mask', 'scrub']
    countries_ua = ['Єгипет', 'Турція', 'ОАЄ']
    categories_ua = ['Шампуні', 'Косметика', 'Парфуми', 'Масаж', 'Чай', 'Кава', 'Креми', 'Ліки', 'Вітаміни', 'Масло', 'Мазі', 'Зубні пасти', 'Їжа', 'Дезодоранти', 'Гелі', 'Свічки', 'Депіляція', 'Гаманці', 'Для плавання', 'Маски', 'Скраби']

    goods = Goods.objects.all()

    selected_countries = request.GET.getlist('country')
    selected_categories = request.GET.getlist('category')

    if selected_countries:
        goods = goods.filter(country__in=selected_countries)
    
    if selected_categories:
        goods = goods.filter(category__in=selected_categories)

    goods = goods.filter(status=True)

    goods_list = [{
        'name': good.name,
        'description': good.description,
        'price': good.price,
        'status': good.status,
        'article': good.article,
        'category': good.category,
        'country': good.country,
        'base64_data': good.base64_data,
    } for good in goods]

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        try:
            return JsonResponse({'goods': goods_list})
        except Exception as e:
            print (e)

    context = {
        'title': 'Victoria Shop',
        'goods': goods_list,
        'categories': categories_ua,
        'countries': countries_ua
    }
    return render(request, 'main/index.html', context)

#product page
def description(request, article):
    good = get_object_or_404(Goods, article=article)
    context = {
        'title': 'Victoria Shop',
        'good': {
            'name': good.name,
            'description': good.description,
            'price': good.price,
            'status': good.status,
            'article': good.article,
            'category': good.category,
            'country': good.country,
            'base64_data': good.base64_data,
        },
        'is_egypt': (good.country == 'egypt'),
        'is_available': (good.status == True),
        'article': article
    }
    return render(request, 'main/description.html', context)

#registration form
def registration(request) -> render:
    context: dict = {
        'title': 'Victoria Shop',
    }
    return render(request, 'main/registration.html', context)

#about us
def about(request) -> HttpResponse:
    return HttpResponse('About us')