import time
# from allauth.account.views import SignupView
from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect, Http404, HttpResponseForbidden
from django.shortcuts import render
from django.urls import reverse
from django import forms
from django.contrib.auth.decorators import permission_required, login_required
from django.contrib.gis.geoip2 import GeoIP2
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.middleware.csrf import get_token
import socket
import json
import pytz
from .models import User, Products, Bids, Orders, Notifications
from functools import wraps
from decimal import Decimal
from math import ceil
from datetime import datetime, timedelta
from asgiref.sync import async_to_sync, sync_to_async
import jwt
# from django.contrib.auth.decorators import login_required, login_required 
# TODO keep it in another file
SECRET_KEY = 'c544efcf10d5ecf720c9318e460cb3c2270a9637f34641142df4b437d43857df'
# import jinja2 as jinja
class LoginForm(forms.Form):
    username = forms.CharField(strip=True, required=True, min_length=8, widget=forms.TextInput(attrs={ 'autofocus': True, 'class': 'form-control', 'placeholder': 'Username'}))
    password = forms.CharField(min_length=8, widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password (min 8 char)'}))

class RegisterForm(forms.Form):
    username = forms.CharField(strip=True, required=True, min_length=8, widget=forms.TextInput(attrs={ 'autofocus': True, 'class': 'form-control', 'placeholder': 'Username', 'id': 'register_username'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'placeholder': 'Enter your email', 'class': 'form-control', 'id': 'register_email'}))                            
    password = forms.CharField(min_length=8, widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password (min 8 char)', 'class': 'form-control', 'id': 'register_password1'}))
    confirm_password = forms.CharField(min_length=8, widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm_password', 'class': 'form-control', 'id': 'register_password2'}))
# class RegistrationView(SignupView):
#     template_name = 'auctions/register.html'
#     form_class = RegisterForm



class NewItemForm(forms.ModelForm):
    class Meta: 
        model = Products
        fields = ['title', 'image', 'description', 'starting_bid', 'max_bid', 'last_bidding_datetime']
        widgets = {
            # 'item_hash': forms.TextInput(attrs={'class': 'form-control', 'id': 'itemform_hash'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'id': 'itemform_name'}),
            'description': forms.Textarea(attrs={'rows': 4, 'cols':40, 'id': 'itemform_description' }),
            'starting_bid': forms.NumberInput(attrs={'class': 'form-control', 'id': 'itemform_startbid'}),
            'max_bid': forms.NumberInput(attrs={'class': 'form-control', 'id': 'itemform_maxbid'}),
            'last_bidding_datetime': forms.DateTimeInput(format='[%m/%d/%Y %H:%M]',attrs={'class': 'form-control datetimepicker-input', 'data-target': 'datetimepicker1', 'autocomplete': 'off'}),
            'image': forms.FileInput(attrs={'class': 'form-control itemForm_image'})
        }

# def login_required(func):
    # @wraps(func)
    # def wrapper(request, *args, **kwargs):

    #     if request.user:
    #         if request.user.is_authenticated:
    #             if request.user.is_email_verified:
    #                 func(request, *args, **kwargs)
    #             else:
    #                 return HttpResponseForbidden("You need to verify your email")    
    #     else:
    #         return render(request, "auctions/login.html", {
    #             'message': 'You need to login to bid'
    #         })
    # return wrapper

def create_jwt(account_id):
    expiration_time = datetime.utcnow() + timedelta(days=30)
    payload = {
        'switchable_account_id': account_id,
        'exp': expiration_time
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    return token

def decode_jwt(token: str):
    try: 
        payload = jwt.decode(jwt=token, key=SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return -1
    # jwt.decode(token.split('.')[1] + '==', algorithms=['HS256'], verify=False)
    except jwt.InvalidTokenError:
        return None

async def add_account(response, switchable_accounts_tokens, id):
    switchable_accounts_tokens = json.loads(switchable_accounts_tokens) if switchable_accounts_tokens else []
    # Decode existing tokens and store them in switchable_accounts list
    switchable_accounts = [jwt.decode(switchable_accounts_token, SECRET_KEY, algorithms=['HS256']) for switchable_accounts_token in switchable_accounts_tokens]
    # Find the index of the account with the given id
    index = next((i for i, account in enumerate(switchable_accounts) if account is not None and account.get('switchable_account_id') == id), -1)
    # it is saying enumerate returns the index and the value in two variables so i contains the index and account the value and the result will be i if == id else it will be -1
    if index == -1:
        print("id: ", id)
        # If the account with the given id doesn't exist, create a new JWT for it
        jwt_id = create_jwt(id)
        switchable_accounts_tokens.append(jwt_id)
    else:
        print("index:", index)
        # If the account with the given id exists, update its expiration time
        switchable_accounts[index]['exp'] = datetime.utcnow() + timedelta(days=30)
        switchable_accounts_tokens[index] = jwt.encode(switchable_accounts[index], SECRET_KEY, algorithm='HS256')

    # Serialize the updated switchable_accounts_tokens to JSON
    switchable_accounts_tokens = json.dumps(switchable_accounts_tokens)

    response.set_cookie('switchable_accounts_tokens', switchable_accounts_tokens, secure=True)
    return response

def get_csrf_token(request):
    
    # Check for authentication and authorization (adjust as needed based on your authentication mechanism)
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Not authenticated'}, status=401)
    # Check for secure connection (HTTPS)
    if not request.is_secure():
        return JsonResponse({'error': 'Insecure connection'}, status=400)
    # Check for the presence of secure cookies (adjust as needed based on your cookies)
    if not request.COOKIES.get('sessionid_secure'):
        return JsonResponse({'error': 'Missing secure cookie'}, status=400)
    # Generate and return the CSRF token

    csrf_token = get_token(request)
    return JsonResponse({'csrf_token': csrf_token})
    
# current_bid_user_id
def get_user_timezone(request):
    client_ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', None))
    if client_ip is None:
        return timezone.get_current_timezone()
    geoip = GeoIP2()
    try:
        client_ip = "61.1.116.213"
        user_location = geoip.city(client_ip)
        user_timezone = user_location.get('time_zone')        
        timezone.activate(pytz.timezone(user_timezone))
        return timezone.get_current_timezone()
    except Exception as e:
        print("ERROR IN retriveing timezone", e)
        return timezone.get_current_timezone()
        
def index(request):
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        print("product_id: ", product_id)
        bid_amount = float(request.POST.get('bid'))
        user_id = request.POST.get('user_id')
        product = Products.objects.get(pk=product_id)
        previous_bid = product.current_bid
        bidder = User.objects.get(pk=user_id)
        
        if bid_amount >  bidder.cash:
            pass
            # * return render(request, "auctions/apology.html", {
                # TODO go to an apology page where they have option to add more cash
                # * 'message': 'Sorry but you do not have enough cash'
            # * })
        Bids.objects.create(user_id=bidder, product_id=product, bid=bid_amount)
        
        cart_products = bidder.cart.all()
        if product_id[0] not in cart_products:
            bidder.cart.add(product_id)
        # bid.save()
        bidder.cash -= Decimal(bid_amount)
        if bid_amount > product.max_bid:
            pass
            # TODO go to another page where you have bought the product
        if bid_amount != product.starting_bid:
            last_bidder  = product.current_bid_user 
        product.current_bid = bid_amount
        product.current_bid_user = bidder
        product.save()
        bidder.save()
        # name = last_bidder.first_name if last_bidder.first_name else last_bidder.username
        if last_bidder != bidder:
            # print("creating for: ", last_bidder.username)
            Notifications.objects.create(
                user = last_bidder,
                type = Notifications.NotificationType.OUTBIDDED,
                data = f"{last_bidder.username}|{product.title}|{previous_bid}|{product.current_bid}|https://amazon.in"
            )
        # name = bidder.first_name if bidder.first_name else bidder.username
        # print("creating for: ", bidder.username)
        Notifications.objects.create(
            user = bidder,
            type = Notifications.NotificationType.BID_PLACED,
            data = f"{bidder.username}|{product.title}|{product.current_bid}|https://amazon.in"
        )
        return HttpResponseRedirect(reverse(index))
        
        
    products = Products.objects.all().order_by('starting_bid')
    # print(products)
    products_per_page = 1
    page = request.GET.get('page')
    if page is None:
        page = 1
        # page_nums = [1, 2, 3, 4, 5, 6, 7, 8]
    else:
        page = int(page)
    # print(page)
    start_index = (int(page) - 1) * products_per_page
    # print('start_index: ', start_index);
    end_index = start_index + products_per_page
    if end_index > len(products):
        end_index = len(products)
    products_this_page = products[start_index:end_index]
    total_pages = ceil(len(products)/products_per_page)
    # total_pages = 18
    page_nums = []
    for i in range(1,10):
        if len(page_nums) >= 7:
            page_nums.append(page)
            break
        if page - i > 0:
            page_nums.append(page - i)
        if len(page_nums) >= 7:
            page_nums.append(page)
            break
        if page + i <= total_pages:
            page_nums.append(page + i)
    page_nums.sort()
    print(page_nums)
    try:
        user = User.objects.get(pk = request.session.get('user_id') )
    except ObjectDoesNotExist:
        user = None
    # if ref == "login" or ref == "switch_accounts":
    #     expiration_time = datetime.utcnow() + timedelta(minutes=1)
    #     payload = {
    #         'switchable_account_id': request.session.get('user_id'),
    #         'exp': expiration_time
    #     }
    #     time_limited_token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    if request.session.get('reload'):
        request.session['reload'] = False
        return render(request, "auctions/index.html", {
            'sendMessage': True,
            'user': user,
            'products': products_this_page,
            'page_nums' : page_nums,
            'total_pages': total_pages,
            'page': page
        })
    
    if request.user.is_authenticated:
        if request.user.is_email_verified:
            return render(request, "auctions/index.html", {
                'sendMessage': False,
                'user': user,
                'products': products_this_page,
                'page_nums' : page_nums,
                'total_pages': total_pages,
                'page': page
            })
        else:
            pass
            # TODO do an apology page and do a feature where if email not verified in 24 hrs then user will be removed

    return render(request, "auctions/index.html", {
        'sendMessage': False,
        'user': user,
        'products': products_this_page,
        'page': page,
        'page_nums' : page_nums,
        'total_pages': total_pages
    })

def notifications_view(request):
    user = request.user
    if not user:
        # TODO redirect to login page
        pass    
    if user.is_authenticated:
        if user.is_email_verified:
            user_notifications =  user.notifications.all().order_by('-created_at')
            user_timezone =  get_user_timezone(request)
            for notification in user_notifications:
                notification.data = notification.data.split('|')
            return render(request, 'auctions/notifications_view.html',{
                'notifications': user_notifications,
                'user_timezone': user_timezone
            })
    return render(request, 'auctions/notifications_view.html', {
        'message': 'Please login and verify your email to view your notifications'
    })

    # TODO redirect to please login to email

def seen_notifications(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            ids = data.get('ids', [])
            print(ids)
            for id in ids:
                notification = Notifications.objects.get(pk=id)
                notification.seen = True
                notification.save()
            return JsonResponse({'success': True})    
        except Exception as e:
            return JsonResponse({'success': False}, {'error': e})
    
    
    
def image(request, image_id):
    item = Products.objects.get(pk=image_id)
    if item.image:    
       image_url = f"{settings.MEDIA_URL}{item.image}"
    # Redirect the user to the image URL
       return HttpResponseRedirect(image_url)
        # return HttpResponseRedirect(reverse('display_image'), args=[image_id])
    else:
        raise Http404('Picture does not exist')

# @login_required
def NewItem(request):
    if request.method == 'POST':
        print("went to post")
        form = NewItemForm(request.POST,request.FILES)
        print("got form")
        raw_data = request.POST
        print(raw_data)
        if form.is_valid():
            print("form is proved valid")
            # hashes = [hash.strip() for hash in item_hash.split(',') if hash.strip()]
            last_bidding_datetime = form.cleaned_data["last_bidding_datetime"]
            title = form.cleaned_data["title"]
            description = form.cleaned_data["description"]
            starting_bid = form.cleaned_data["starting_bid"]
            max_bid = form.cleaned_data["max_bid"]
            last_bidding_datetime = form.cleaned_data["last_bidding_datetime"]
            # parsed_datetime = datetime.strptime(last_bidding_datetime, '%m/%d/%Y %I:%M %p')
            image = form.cleaned_data["image"]
            user = request.user
            if not user: 
                return render(request, "auctions/login.html", {
                    'message': 'you need to login to sell an item'
                })
            # hash_table = Hash_table.objects.all()
            
            product_instance = Products.objects.create(title=title, image=image, description=description, starting_bid=starting_bid, max_bid=max_bid, Sold=False , last_bidding_datetime=last_bidding_datetime, seller_id=user)
            # item_instance.item_hash.add(*[Hash_table.objects.get_or_create(hash=hash)[0] for hash in hashes])
            # print(item_instance)
        else:
            print("form not valid")
            print(form.errors)
            for field, errors in form.errors.items():
                print(f"Field: {field}")
                for error in errors:
                    print(f"errors: {error}")
                    field_instance = form.fields[field]
                    if hasattr(field_instance, 'error_messages'):
                        expected_format = field_instance
                        print(f"Excepted formatter: {expected_format}")
        return HttpResponseRedirect(reverse('index'))


    else:
        return render(request, "auctions/item_form.html", {
            'form': NewItemForm()
        })

def cart_view(request):
    user_id = request.session.get('user_id')
    if user_id:
        print("user: ", user_id)
        cart_items= User.objects.get(id=user_id).cart.all()
        print(cart_items.count())
        return render(request, "auctions/cart_view.html", {
            'cart_items': cart_items,
        })
    else:
        return render(request, "auctions/cart_view.html", {
            'message': 'Please login to view your cart'
        })
   
@async_to_sync
@csrf_protect
async def login_view(request):
    ref = request.GET.get('ref')
    if request.method == "POST":
        # Attempt to sign user in
        if ref == 'switch_accounts':
            username = request.POST.get('expired_username'),
            return render(request, "auctions/login.html", {
                'forms': LoginForm(initial={'username': username})
            })
        # default function of login below
        elif ref == 'check':
            form = LoginForm(request.POST)
            if form.is_valid():
                username = form.cleaned_data["username"]
                password = form.cleaned_data["password"]
                start_time = time.time()
                authenticate_async = sync_to_async(authenticate, thread_sensitive=True)
                user = await authenticate_async(request, username=username, password=password)
                end_time = time.time()
                print("time_taken: ", end_time - start_time)
                # def _login_():
                #     return authenticate(request, username=username, password=password)                 
                # user = _login_()
                # Check if authentication successful
                #  do not send the csrf token throught response as it might include potention risks
                if user is not None:
                    if user.is_email_verified:
                        response = HttpResponseRedirect(reverse("index") + "?ref=login")
                        try:
                            switchable_accounts_tokens = request.COOKIES.get('switchable_accounts_tokens', '[]')
                            response = add_account(response, switchable_accounts_tokens, user.id)
                        except KeyError:
                            response = add_account(response, None, user.id)
                        asynced_login = sync_to_async(login, thread_sensitive=True)
                        await asynced_login(request, user)
                        request.session['user_id'] = user.id
                        response = await response
                        request.session['reload'] = True
                        #  request.user is a user_instance that is automaticaally created and the request.session[] is a dictionary format provided to pass on any values with the request that you may want to access in the other 
                        return response
                    else:
                        return render(request, "auctions/login.html", {
                            "message":"Please verify your email address before logging in."
                        })
                else:
                    return render(request, "auctions/login.html", {
                        "message": "Invalid username and/or password."
                    })  
        else:
            sync_render = sync_to_async(render)
            return await sync_render(request, "auctions/login.html", {
                "forms": LoginForm()
            })
    else:
        if ref == 'register':
            user_id = request.session.get('user_id')
            response = HttpResponseRedirect(reverse("index") + "?ref=login")
            try:
                switchable_accounts_tokens = request.COOKIES.get('switchable_accounts_tokens', '[]')
                response = add_account(response, switchable_accounts_tokens, user_id)
            except KeyError:
                response = add_account(response, None, user_id)
            response = await response
            request.session['reload'] = True
            #  request.user is a user_instance that is automaticaally created and the request.session[] is a dictionary format provided to pass on any values with the request that you may want to access in the other 
            return response
        sync_render = sync_to_async(render)
        return await sync_render(request, "auctions/login.html", {
            "forms": LoginForm()
        })

@csrf_protect
def switch_accounts(request):
    ref = request.GET.get('ref')
    if request.method == "POST":
        if ref == "switch_accounts":
            index = int(request.POST.get('index'))
            tokens = [token for token in json.loads(request.COOKIES.get('switchable_accounts_tokens'))]     
            payload = decode_jwt(tokens[index])
            # print(payload)
            #  this is for the minute case the user logs in while token was just about to be expired
            if payload == -1:
                return render(request, "auctions/login.html", {
                    "message": "Your session has expired. Please login again."
                })
            elif payload is None:
                # print("hello")
                return render(request, "auctions/login.html", {
                    "message": "Invalid token. Please login again."
                })
            else:
                id = payload.get('switchable_account_id')
                user = User.objects.get(id=id)
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                request.session['user_id'] = user.id
                request.session['reload'] = True
                return HttpResponseRedirect(reverse("index") + "?ref=switch_accounts")
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid request. Please login again."
            })
        
    # if ref == "profile_pic_dropdown_down":
    try:
        switchable_accounts_tokens = json.loads(request.COOKIES.get('switchable_accounts_tokens', '[]'))
    except KeyError:
        switchable_accounts_tokens = []
    print("hello")
    for switchable_accounts_ in switchable_accounts_tokens:
        print(switchable_accounts_)

    switchable_accounts = [jwt.decode(switchable_accounts_token, SECRET_KEY, algorithms=['HS256']) for switchable_accounts_token in switchable_accounts_tokens] if switchable_accounts_tokens else []
    bad_index = [i for i, account in enumerate(switchable_accounts) if account is None]
    for index in bad_index:
        del switchable_accounts_tokens[index]
        del switchable_accounts[index]
    expired_index = [i for i, account in enumerate(switchable_accounts) if account == -1]
    expired_accounts_details = []
    for index in expired_index:
        expired_accounts_details.append({'username': user[0].username, 'email': user[0].email} for user in (User.objects.get(pk = (jwt.decode(switchable_accounts_tokens[index].split('.')[1] + '==', algorithms=['HS256'], verify=False)).get('switchable_account_id'))))
        del switchable_accounts_tokens[index]
        del switchable_accounts[index]
    # from all the decoded account_ids i am taking all the accounts payload value which is the id and i am filtering the one that match the id from the datablase and then i am enumerating over the list returned  where i am got all the users after filtering and i am taking their username and email and the index into a dictionary
    switchable_accounts_details = [{'index': i, 'username': user.username, 'email': user.email, 'img': user.profile_pic.url, 'current': False} if user.id != request.session.get('user_id') else {'index': i, 'username': user.username, 'email': user.email, 'current': True} for i, user in enumerate(User.objects.filter(pk__in=[account.get('switchable_account_id') for account in switchable_accounts]))]
    for switchable_account_details in switchable_accounts_details:
        print(switchable_account_details)
    response = render(request, "auctions/switch_accounts.html", {
        "expired_accounts": expired_accounts_details,
        "switchable_accounts": switchable_accounts_details
    })
    switchable_accounts_tokens =  json.dumps(switchable_accounts_tokens)
    response.set_cookie('switchable_accounts_tokens', switchable_accounts_tokens, secure=True)
    return response
    # else: 
    #     return render(request, "auctions/login.html", {
    #             "message": "Invalid request. Please login again."
    #         })
# @login_required
# @permission_required('auctions.can_delete_notifications')
def delete_notifications(request, cardId):
    try:
        notification = get_object_or_404(Notifications, pk=cardId)
        notification.delete()
        print("hellojsdk")
        return JsonResponse({'success': True})
    except Notifications.DoesNotExist:
        print("hello")
        return JsonResponse({'success': False, 'error': 'Notification not found'})
    except Exception as e:
        print("hello")
        print(f"An error occurred {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})
    
def  logout_view(request):
    #TODO REMOVE USER
    #TODO add option to add accounts
    request.session.clear()
    logout(request)
    return HttpResponseRedirect(reverse("index"))

def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            email = form.cleaned_data["email"]      
            confirmation = form.cleaned_data["confirm_password"]
            # Ensure password matches confirmation
            if password != confirmation:
                return render(request, "auctions/register.html", {
                    "message": "Passwords must match."
                })
            
            # Attempt to create new user
            try:
                user = User.objects.create_user(username, email, password)
                token = default_token_generator.make_token(user)
                print("token",token)
                token = urlsafe_base64_encode(force_bytes(token))
                uid64 = urlsafe_base64_encode(force_bytes(user.id))
                verification_link = reverse('verify_email', args=[uid64, token])
                current_site = get_current_site(request)
                # print(verification_link)
                subject = 'Email Verification'
                message = 'Click the following link to verify your email: {0}'.format(verification_link)
                from_email = 'auction.ebay.gain@gmail.com'  # Replace with your email
                recipient_list = [user.email]
                # Create an HTML email using a template
                html_message = render_to_string('account/email/confirmation.html', {
                    'domain': current_site.domain,
                    'uid64': uid64,
                    'token': token,
                    'verification_link': verification_link,
                })
                for i in range(100):
                    try:
                        send_mail(subject, message, from_email, recipient_list, fail_silently=False, html_message=html_message)
                        break
                    except socket.gaierror as e:
                        print(f"DNS ERROR {e} for the {i}th time")
                        if (i == 98):
                            initial_data = {
                                'username': username,
                                'email': email
                            }
                            return render(request, "auctions/register.html", {
                                'form' : RegisterForm(initial=initial_data)
                            }) 
                    except Exception as e:
                        print(f"An error occurred {str(e)}")
                # return render(request, "auctions/verification_page.html", {
                #     'user': user
                # })
                # return HttpResponseRedirect(reverse('verify', user=user))
                user.save()
                return render(request, "auctions/verify.html", {
                    'email': user.email
                })
            except IntegrityError:
                return render(request, "auctions/register.html", {
                    "message": "Username already taken."
                })

        else:
            return render(request, "auctions/register.html", {
                'forms': RegisterForm()
            })
        # return RegistrationView.as_view()(request)
    else:
        return render(request, "auctions/register.html", {
            'forms': RegisterForm()
        })

def verify_email(request, uid64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uid64))
        token = force_str(urlsafe_base64_decode(token))
        user = User.objects.get(pk=uid)
        print("uid", uid)
        print("token",token)
        print("hello")
        if default_token_generator.check_token(user, token):
            # Mark the user's email as verified
            user.is_email_verified = True
            add_account
            user.save()
            login(request, user, backend='allauth.account.auth_backends.AuthenticationBackend')
            request.session['user_id'] = user.id
            return HttpResponseRedirect(reverse("index") + "?ref=register")
            # return HttpResponse("Email verified successfully.")
        else:
            return HttpResponse("Email verification link is invalid.")
    except ():
        return HttpResponse("Email dfvdfbverification link is invalid.")
def verify(request, user):
    if request.method == 'POST':
        pass
    else:
        return render("auctions/verify.html", {
            'user': user
        })

# hash_results = [{'hash': hash.hash, 'index': 0, 'points': 0} for hash in Hash_table.objects.all()]
# item_results = [{'title': item.title, 'index': 0, 'points': 0} for item in Products.objects.all()]
# search_results = []
# hashes = hash_results
# items = item_results
    # item_hash
# def search(new, char, full):
#     if new:
#         for i in char:
#             if len(hashes) >= 6:
#                 for hash in hashes:
#                     result = lib.check(char[i], hash['hash'], hash['index'], hash['points'], len(hash['hash']))
#                     if result[0] != - 1:
#                         hash['points'] = result[1]
#                         hash['index'] = result[0]
#                     else:
#                         hashes.remove[hash]
#                 if (len(hashes)) < 6:
#                     for j in full:
#                         for item in items:
#                             result = lib.check(full[j], item['title'], item['index'], item['points'], len(item['title']))
#                             if result[0] != - 1:
#                                 item['points'] = result[1]
#                                 item['index'] = result[0]
#                             else:
#                                 items.remove[item]
#             else:
#                 for i in char:
#                     for item in items:
#                         result = lib.check(char[i], item['title'], item['index'], item['points'], len(item['title']))
#                         if result[0] != - 1:
#                             item['points'] = result[1]
#                             item['index'] = result[0]
#                         else:
#                             items.remove[item]
#     else:
#         hashes = hash_results
#         for i in char:
#             if len(hashes) >= 6:
#                 for hash in hashes:
#                     result = lib.check(char[i], hash['hash'], hash['index'], hash['points'], len(hash['hash']))

#                     if result[0] != - 1:
#                         hash['points'] = result[1]
#                         hash['index'] = result[0]
#                     else:
#                         hashes.remove[hash]
#                 if (len(hashes)) < 6:
#                     for j in full:
#                         items = item_results
#                         for item in items:
#                             result = lib.check(full[j], item['title'], item['index'], item['points'], len(item['title']))
#                             if result[0] != - 1:
#                                 item['points'] = result[1]
#                                 item['index'] = result[0]
#                             else:
#                                 items.remove[item]
#             else:
#                 for i in char:
#                     for item in items:
#                         result = lib.check(char[i], item['title'], item['index'], item['points'], len(item['title']))
#                         if result[0] != - 1:
#                             item['points'] = result[1]
#                             item['index'] = result[0]
#                         else:
#                             items.remove[item]
    #we need to set the table of search results back to the entire items list when the user searches
# def set_session_data(request):
#     # Create or update session data
#     request.session['user_id'] = 123
#     request.session['username'] = 'example_user'
    
#     return HttpResponse("Session data set successfully.")

# def get_session_data(request):
#     # Retrieve session data
#     user_id = request.session.get('user_id')
#     username = request.session.get('username')
    
#     if user_id is not None and username is not None:
#         return HttpResponse(f"User ID: {user_id}, Username: {username}")
#     else:
#         return HttpResponse("Session data not found.")
# message2 = render_to_string('email_confirmation.html' , {
#             'name' : myuser.first_name ,
#             'domain' : current_site.domain ,
#             'uid' : urlsafe_base64_encode(force_bytes(myuser.pk)) ,
#             'token' : generate_token().make_token(myuser)
#         })