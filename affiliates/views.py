import json
from datetime import timedelta

from decouple import config
from django.contrib import messages
from django.contrib.auth import logout, authenticate, login, get_user_model, update_session_auth_hash
from django.contrib.auth.decorators import user_passes_test, login_required
from django.contrib.auth.forms import PasswordResetForm, PasswordChangeForm
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth.views import PasswordResetView
from django.contrib.sites.shortcuts import get_current_site
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse
from django.shortcuts import render, redirect
from django.template import loader
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.views.decorators.http import require_http_methods

from affiliates.models import Affiliate, AffiliateOccupationCategory, AffiliateOrganisationTypeCategory, \
    AffiliatePicture
from affiliates.tokens import account_activation_token
from affiliates.utils import send_account_verification_email, send_password_reset_email
from referrals.models import TenantReferral, HouseOwnerReferral
from referrals.utils import TENANT_REFERRAL, DASHBOARD_FORM_SOURCE, HOUSE_OWNER_REFERRAL
from utility.form_field_utils import get_number, get_datetime
from utility.random_utils import generate_random_code

LOGIN_URL = '/login/'

User = get_user_model()


def is_affiliate(user):
    return Affiliate.objects.filter(user=user).count()


affiliate_login_test = user_passes_test(is_affiliate, login_url=LOGIN_URL)


def affiliate_login_required(view):
    decorated_view = login_required(affiliate_login_test(view), login_url=LOGIN_URL)
    return decorated_view


def logout_view(request):
    logout(request)
    request.session.flush()
    request.user = AnonymousUser
    return HttpResponseRedirect(reverse(home_page))


def login_view(request):
    error_msg = None
    logout(request)
    if request.POST:
        email, password = request.POST['email'], request.POST['password']
        user = authenticate(username=email, password=password)
        if user is not None:
            if is_affiliate(user):
                if user.is_active:
                    login(request, user)
                    next_page = request.GET.get('next')
                    if next_page:
                        return HttpResponseRedirect(next_page)
                    else:
                        return HttpResponseRedirect(reverse(home_page))
            else:
                error_msg = 'You are not an Affiliate.'
        else:
            error_msg = 'Either the email ID or the password is incorrect!'
    return render(request, 'account/login.html', {'error': error_msg})


@require_http_methods(['GET', 'POST'])
def register_view(request):
    if request.user.is_authenticated:
        return redirect('home_page')

    if request.method == 'GET':
        return render(request, 'account/register.html')
    elif request.method == 'POST':
        data = request.POST
        email = data.get('email')

        if User.objects.filter(email=email).exists():
            return JsonResponse({'error': "User with this email already exists."}, status=500)

        first_name = data.get('first_name')
        last_name = data.get('last_name')
        password = data.get('password')
        phone_no = data.get('phone_no')
        username = generate_random_code(initials=first_name.lower(), n=3, alphabets=False,
                                        existing_codes=User.objects.values_list('username', flat=True))

        # create user
        try:
            user = User.objects.create(username=username, first_name=first_name, last_name=last_name,
                                       email=email)
            user.set_password(password)
            user.save()
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

        # create affiliate account
        Affiliate.objects.create(user=user, phone_no=phone_no)

        # send account verification link
        current_site = get_current_site(request)
        message = render_to_string('account/account_activation_email.html', {
            'user': user,
            'domain': current_site.domain,
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': account_activation_token.make_token(user),
        })
        send_account_verification_email(user.email, message)

        return JsonResponse({'detail': 'done'})


@affiliate_login_required
def change_password_view(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password was successfully updated!')
            return redirect('change_password')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'account/change_password.html', {
        'form': form
    })


def account_activation_sent(request):
    return render(request, 'account/account_activation_sent.html')


def activate(request, uidb64, token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.affiliate.verified = True
        user.save()
        login(request, user)
        return redirect('home_page')
    else:
        return render(request, 'account/account_activation_invalid.html')


class CustomPasswordResetForm(PasswordResetForm):
    def send_mail(self, subject_template_name, email_template_name,
                  context, from_email, to_email, html_email_template_name=None):
        body = loader.render_to_string(email_template_name, context)
        send_password_reset_email(to_email, body)


class CustomPasswordResetView(PasswordResetView):
    form_class = CustomPasswordResetForm


@require_http_methods(['GET'])
def home_page(request):
    return render(request, 'home.html')


@affiliate_login_required
@require_http_methods(['GET', 'POST'])
def profile_view(request):
    affiliate = Affiliate.objects.get(user=request.user)
    metadata = {'occupation_categories': AffiliateOccupationCategory.objects.values_list('name', flat=True),
                'organisation_type_categories': AffiliateOrganisationTypeCategory.objects.values_list('name',
                                                                                                      flat=True)}

    if request.method == 'GET':
        return render(request, 'profile.html', {'affiliate': affiliate, **metadata})
    else:
        data = request.POST

        if request.FILES.get('profile_pic'):
            AffiliatePicture.objects.create(affiliate=affiliate, image=request.FILES['profile_pic'],
                                            is_profile_pic=True)
            msg = "Your profile pic was updated successfully!"
        else:
            affiliate.user.first_name = data.get('first_name')
            affiliate.user.last_name = data.get('last_name')
            affiliate.user.save()

            affiliate.phone_no = data.get('phone_no')
            affiliate.occupation = AffiliateOccupationCategory.objects.filter(name=data.get('occupation')).first()
            affiliate.save()

            affiliate.address.street_address = data.get('street_address')
            affiliate.address.city = data.get('city')
            affiliate.address.pincode = data.get('pincode')
            affiliate.address.state = data.get('state')
            affiliate.address.country = data.get('country')
            affiliate.address.save()

            affiliate.bank_detail.account_holder_name = data.get('account_holder_name')
            affiliate.bank_detail.account_number = data.get('account_number')
            affiliate.bank_detail.bank_name = data.get('bank_name')
            affiliate.bank_detail.bank_branch = data.get('bank_branch')
            affiliate.bank_detail.bank_branch_address = data.get('bank_branch_address')
            affiliate.bank_detail.ifsc_code = data.get('ifsc_code')
            affiliate.bank_detail.save()

            affiliate.organisation.name = data.get('organisation_name')
            affiliate.organisation.type = AffiliateOrganisationTypeCategory.objects.filter(
                name=data.get('organisation_type')).first()
            affiliate.organisation.website = data.get('organisation_website')
            affiliate.organisation.save()

            affiliate.organisation.address.street_address = data.get('organisation_street_address')
            affiliate.organisation.address.city = data.get('organisation_city')
            affiliate.organisation.address.pincode = data.get('organisation_pincode')
            affiliate.organisation.address.state = data.get('organisation_state')
            affiliate.organisation.address.country = data.get('organisation_country')
            affiliate.organisation.address.save()
            affiliate.organisation.address.save()
            msg = "Your details have been saved successfully!"

        return render(request, 'profile.html', {'affiliate': affiliate, 'msg': msg, **metadata})


@affiliate_login_required
@require_http_methods(['GET', 'POST'])
def referral_upload_view(request):
    affiliate = Affiliate.objects.get(user=request.user)
    referral_type = request.GET.get('type')
    metadata = {'referral_type': referral_type,
                'GOOGLE_MAPS_API_KEY': config('GOOGLE_MAPS_API_KEY')}
    if request.method == 'GET':
        return render(request, 'referral_upload.html', metadata)
    else:
        data = request.POST
        name = data.get('name')
        phone_no = data.get('phone_no')
        gender = data.get('gender')
        email = data.get('email')

        error = None
        msg = None

        if referral_type == TENANT_REFERRAL:
            if TenantReferral.objects.filter(affiliate=affiliate, phone_no=phone_no,
                                             timestamp__lte=timezone.now()-timedelta(days=30)).exists():
                error = "Duplicate Tenant Referral!"
            else:
                preferred_location = data.get('preferred_location')
                expected_rent = get_number(data.get('expected_rent'))
                expected_movein_date = get_datetime(data.get('expected_movein_date'))
                accomodation_for = data.get('accomodation_for')
                accomodation_type = data.get('accomodation_type')
                TenantReferral.objects.create(affiliate=affiliate, name=name, phone_no=phone_no, gender=gender, email=email,
                                              preferred_location=preferred_location, expected_rent=expected_rent,
                                              expected_movein_date=expected_movein_date,
                                              accomodation_for=accomodation_for, accomodation_type=accomodation_type,
                                              source=DASHBOARD_FORM_SOURCE)
                msg = "Referral was submitted successfully."
        elif referral_type == HOUSE_OWNER_REFERRAL:
            if HouseOwnerReferral.objects.filter(affiliate=affiliate, phone_no=phone_no,
                                                 timestamp__lte=timezone.now()-timedelta(days=30)).exists():
                error = "Duplicate House Owner Referral!"
            else:
                house_address = data.get('house_address')
                house_type = data.get('house_type')
                bhk_count = data.get('bhk_count')
                HouseOwnerReferral.objects.create(affiliate=affiliate, name=name, phone_no=phone_no, gender=gender,
                                                  email=email, house_address=house_address, bhk_count=bhk_count,
                                                  house_type=house_type, source=DASHBOARD_FORM_SOURCE)
                msg = "Referral was submitted successfully."
        return render(request, 'referral_upload.html', {'msg': msg, 'error': error, **metadata})


def test_view(request):
    html = render_to_string('search.html')
    data = request.GET.get('callback', '') + "(" + json.dumps({'html': html}) + ")"
    return HttpResponse(data, content_type="text/javascript")
