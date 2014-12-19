import string, random, datetime, math, hashlib, json
from django.shortcuts import render_to_response, redirect, HttpResponse
from django.conf import settings
from django.template import RequestContext
from ledger.models import Transaction, Company, User, GoogleProfile
from django.contrib.auth import authenticate, login, logout
from django.middleware.csrf import get_token
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.db.utils import IntegrityError
from pennypledge.settings import PAYPAL_MODE, PAYPAL_CLIENT_ID
from pennypledge.settings import PAYPAL_CLIENT_SECRET
import stripe
import paypalrestsdk


def features(request):
    if not request.user.is_authenticated():
        return landingPage(request)

    user = request.user
    #transactions that have a balance * random that is over a threshold
    #then sort by newest
    #then give me the highest ones.
    last_week = datetime.date.today() - datetime.timedelta(days=7)
    transactions = Transaction.objects.filter(date__gt = last_week, image_url__isnull=False, private=False).exclude(image_url__exact='')
    a = [(random.random()*math.sqrt(trans.amount), trans) for trans in transactions]
    #sort by the calculated rating*random value
    randos = sorted(a, key=lambda tup: tup[0], reverse=True)[:20]
    randos = [x[1] for x in randos]

    return render_to_response('features.html', {
        'user': user,
        'random': randos,
    },RequestContext(request))

def dashboard(request):
    if request.user.is_authenticated():
        company = Company()
        try:
            company = request.user.company
        except:
            pass
        pledges = Transaction.objects.filter(company=company.id).order_by('date')
        pledge_count = pledges.count()
        pledges = pledges[:50]
        balance = float(company.balance-company.balance/10) / 100
        return render_to_response('dashboard.html', {
            'user':request.user,
            'pledges_count':pledge_count,
            'pledges':pledges,
            'balance':balance,
            'company':company,
        },RequestContext(request))
    else:
        return landingPage(request)

def loginView(request):
    if request.method == 'POST':
        email = request.POST['email'].lower()
        password = request.POST['password']
        if request.POST['login-signup'] == 'signup':
            try:
                user = User.objects.get(email=email)
                created = False
            except User.DoesNotExist:
                username = email.split('@')[0][:30]
                try:
                    user = User.objects.create_user(username, email, password)
                except IntegrityError:
                    username = username[:20]+''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(8))
                    user = User.objects.create_user(username, email, password)
                created = True
            user = authenticate(username=user.username, password=password)
            if user is not None and user.is_active:
                login(request, user)
                user.plugin_key = request.POST['ck']
                user.save()
                if created:
                    return redirect('overview_tutorial', tutorial='tutorial')
                else:
                    return redirect('overview')
            return landingPage(request, 'That email is already in use with a different password.')
        elif request.POST['login-signup'] == 'login':
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return landingPage(request, 'User does not exist.')
            user = authenticate(username=user.username, password=password)
            if user is not None and user.is_active:
                user.plugin_key = request.POST['ck']
                user.save()
                login(request, user)
                return redirect('overview')
            else:
                return landingPage(request, 'Double check that username and password.')
        elif request.POST['login-signup'] == 'forgot':
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return landingPage(request, 'A user with that email does not exist.')
            send_mail('Penny Pledge Password Reset', 'Go here to reset you password: https://pennypledge.co/resetPassword/?pk='+str(user.pk)+'&v='+hashString(user.username), 'password.reset@pennypledge.co', [user.email], fail_silently=False)
            return landingPage(request, 'An email has been sent to '+user.email+' with instructions to reset the password.')
    return landingPage(request, '')

def landingPage(request, error_msg=''):
    rand = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(16))
    return render_to_response('landingPage.html',
        {'error_msg': error_msg,
         'rand': rand,
        },
        RequestContext(request))

def resetPassword(request):
    error = ''
    if request.method == 'POST':
        user = User.objects.get(pk=request.POST.get('pk',''))
        v = request.POST.get('v','')
        if hashString(user.username) != v:
            return HttpResponse('Invalid URL. Please try again.')
        password = request.POST.get('password', '')
        if len(password) < 8:
            error = 'A '+str(len(password))+' character password? You can do better than that.'
        else:
            user.set_password(password)
            user.save()
            return redirect('overview')
    else:
        user = User.objects.get(pk=request.GET.get('pk',''))
        v = request.GET.get('v','')
        if hashString(user.username) != v:
            return HttpResponse('Invalid URL. Please try again.')

    return render_to_response('resetPassword.html',
        {
            'user': user,
            'v': v,
            'error':error
        },
        RequestContext(request))

def overview(request, tutorial='', success='', error=''):
    if not request.user.is_authenticated():
        return landingPage(request)

    user = request.user
    if not user.extension_key:
        user.extension_key = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(12))
    try:
        comp_title = user.company.title
    except:
        comp_title = ''

    pledges = Transaction.objects.filter(user=user.id).order_by('-date')[:50]
    balance = float(user.balance) / 100

    if not user.has_usable_password():
        tutorial = 'tutorial'

    #transactions that have a balance * random that is over a threshold
    #then sort by newest
    #then give me the highest ones.
    last_week = datetime.date.today() - datetime.timedelta(days=7)
    transactions = Transaction.objects.filter(date__gt = last_week, image_url__isnull=False, private=False).exclude(image_url__exact='')
    a = [(random.random()*math.sqrt(trans.amount), trans) for trans in transactions]
    #sort by the calculated rating*random value
    featured = sorted(a, key=lambda tup: tup[0], reverse=True)[:4]
    featured = [x[1] for x in featured]
    token = get_token(request)

    return render_to_response('overview.html', {
        'user': user,
        'pledges': pledges,
        'comp_title':comp_title,
        'balance': balance,
        'tutorial': tutorial,
        'featured': featured,
        'success':success,
        'error':error,
        'has_password':user.has_usable_password(),
        'csrf':token,
    },RequestContext(request))

def changeUsername(request):
    if request.user.is_authenticated():
        username = request.POST.get('username','')
        if username:
            try:
                request.user.username = username
                request.user.save()
            except IntegrityError:
                return HttpResponse('Username is not available.')
    return HttpResponse('success')

def addFunds(request):
    if request.user.is_authenticated():
        stripe.api_key = settings.STRIPE_API_KEY
        if request.method == 'POST':
            # Get the credit card details submitted by the form
            token = request.POST['token']
            amount = request.POST["amount"]
            if amount == '5':
                amount = 500
            elif amount == '10':
                amount = 1000
            elif amount == '20':
                amount = 2000
            else:
                return HttpResponse(str(amount)+'Nice Try. You just got banned.')
                # Create the charge on Stripe's servers - this will charge the user's card
            try:
                stripe.Charge.create(
                    amount=amount, # amount in cents, again
                    currency="usd",
                    card=token,
                    description="Penny Pledge Upload"
                )
            except stripe.CardError as e:
                # The card has been declined
                return HttpResponse("Transaction unsuccessful. Please try again.")

            request.user.balance += amount
            request.user.save()
            return HttpResponse('success')
    return redirect('overview')

def setPassword(request): #after they have signed in with google, we need them to create a password
    if request.method == 'POST':
        if request.user.has_usable_password():
            return HttpResponse('Error: you have already set a password.')
        else:
            request.user.set_password(request.POST['password'])
            request.user.save()
            return HttpResponse('success')
    return HttpResponse('Error.')

@csrf_exempt
def recieveEmail(request):
    if request.method == 'POST':
        user = User.objects.get(email = 'crobertsbmw@gmail.com')
        user.company.info = 'Its updating'
        user.company.save()
        try:
            email = json.loads(request.body.decode(encoding='UTF-8'))
            user.company.info += '\n\nEMAIL: \n'+email
            user.company.save()
            body = ''
            for key, value in email.items():
                body += key+': '+str(value)+'\n\n'
            subject = 'PennyPledge mail'
            try:
                subject = email['Subject']
            except:
                pass
            user.company.info += '\n\nBODY: \n'+body
            user.company.save()
            send_mail(subject, body, 'chase@pennypledge.co', ['crobertsbmw@gmail.com'], fail_silently=False)
        except Exception as e:
            send_mail('Error receiving email', 'It was trying to send you an email but it screwed up:\n\n'+str(e), 'chase@pennypledge.co', ['crobertsbmw@gmail.com'], fail_silently=False)
        return HttpResponse('success')

'''
curl -s -X GET \
    --user "b411d13c81b708040dd4c15a6fa1c9df:ed2fe46b4984bd1fba35ecebf4aca2f4" \
    https://api.mailjet.com/v3/REST/parseroute

curl -s -X PUT \
    --user "b411d13c81b708040dd4c15a6fa1c9df:ed2fe46b4984bd1fba35ecebf4aca2f4" \
    https://api.mailjet.com/v3/REST/parseroute/$ID \
    -H 'Content-Type: application/json' \
    -d '{"Email": "chase@pennypledge.co"}'
'''


def profile_page(request, username):
    user = User.objects.get(username=username)
    pledges = Transaction.objects.filter(user=user, private=False).order_by('-date')
    return render_to_response('profile.html', {
            'users':user,
            'pledges':pledges
        }, RequestContext(request))

def hidePledge(request):
    if request.method == 'POST':
        if not request.user.is_authenticated():
            return HttpResponse('Error: Not logged in.')
        pledge_id = request.POST.get('pk','')
        try:
            trans = Transaction.objects.get(pk=pledge_id)
            if trans.user != request.user:
                return HttpResponse('Error: You must log in.')
            if request.POST.get('a', '') == 'remove':
                trans.company.balance -= trans.amount
                trans.company.save()
                request.user.balance += trans.amount
                request.user.save()
                trans.delete()
            elif request.POST.get('a','') == 'private':
                trans.private = True
                trans.save()
            elif request.POST.get('a','') == 'public':
                trans.private = False
                trans.save()
        except Transaction.DoesNotExist:
            pass
        return HttpResponse('success: '+str(float(request.user.balance) / 100))
    return HttpResponse('Error.')

def logoutUser(request):
    logout(request)
    return redirect('/')

def hashString(string):
    string = string.encode('utf-8')
    m = hashlib.md5()
    m.update(string)
    string = m.hexdigest()
    return string


def configure_paypal_sdk():
    """
        Configure the paypal SDK each time a function from the paypalrestsdk
        is called.

        TODO:
            Find another way to configure it without calling this function
            everytime or move this function to a more 'natural' place.
    """
    paypalrestsdk.configure({
        'mode': PAYPAL_MODE,
        'client_id': PAYPAL_CLIENT_ID,
        'client_secret': PAYPAL_CLIENT_SECRET
    })


def paypal_create(request):
    """ Create the paypal payment to be later executed """
    print('configure sdk')
    configure_paypal_sdk()
    print('configured')
    return_url = request.build_absolute_uri(reverse('paypal_execute'))
    cancel_url = request.build_absolute_uri(reverse('overview'))
    print('Return url is:', return_url)
    print('Cancel url is [Home]:', cancel_url)
    amount = request.GET.get('amount','')
    if amount == '5':
        amount = '5.00'
    elif amount == '10':
        amount = '10.00'
    elif amount == '20':
        amount = '20.00'
    else:
        return HttpResponse(str(amount)+'Nice Try. You just got banned.')
    payment = paypalrestsdk.Payment({
        'intent': 'sale',
        'payer': {
            'payment_method': 'paypal'
        },
        'redirect_urls': {
            'return_url': return_url,
            'cancel_url': cancel_url
        },
        'transactions': [{
            'item_list': {
                'items': [{
                    'name': 'Add to Penny Pledge Account',
                    'price': amount,
                    'currency': 'USD',
                    'quantity': 1
                }]
            },
            'amount': {
                'total': amount,
                'currency': 'USD'
            },
            'description': 'Donate down to a penny anywhere on the web.'
        }]
    })

    redirect_url = ''

    if payment.create():
        for link in payment.links:
            if link.method == 'REDIRECT':
                redirect_url = link.href
        print('Redirecting to:[', redirect_url, ']...')
        return redirect(redirect_url)
    else:
        print('An error has occurred in the payment:')
        print(payment.error)
        return redirect('/overview/')


def paypal_execute(request):
    """ Execute the payment after the user confirmed the purchase """
    print('configure sdk')
    configure_paypal_sdk()
    print('configured')
    payment_id = request.GET['paymentId']
    payer_id = request.GET['PayerID']

    payment = paypalrestsdk.Payment.find(payment_id)
    payment_name = payment.transactions[0].item_list.items[0].name
    print(payment)
    print(payment.transactions[0])
    print('\n\namount:')
    print(payment.transactions[0].amount.total)
    print('\n\n')
    print(payment.transactions[0].item_list.items[0])
    if payment.execute({'payer_id': payer_id}):
        request.user.balance += float(payment.transactions[0].amount.total)*100
        request.user.save()
        print('The payment has been accepted:', payment_name)

    else:
        print('Invalid payment!')
    return redirect('/overview/')
