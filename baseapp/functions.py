from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.exceptions import ImmediateHttpResponse
from django.http import HttpResponse
from .models import *
import datetime,random,string
from twilio.rest import Client 

def findfriends(user):
    friends = []
    friendsList = Friends.objects.filter(Requester=user, Confirmed=True) | Friends.objects.filter(Requested=user, Confirmed=True)
    for frienditem in friendsList:
        if frienditem.Requester == user:
            friends.append(frienditem.Requested)
        else:
            friends.append(frienditem.Requester)
    return friends

def findFollowedPages(user):
    pages = []
    pageFollowerObjects = PageFollowers.objects.filter(user=user)
    for item in pageFollowerObjects:
        pages.append(item.page)
    return pages

def findUserPosts(user):
    return Posts.objects.filter(user=user,page=None).order_by('PostedOn')

def findPagePosts(page):
    return Posts.objects.filter(page=page).order_by('PostedOn')

def friendRequests(user):
    wannabeFriends = []
    friendsList = Friends.objects.filter(Requested=user, Confirmed=False)
    for frienditem in friendsList:
        wannabeFriends.append(frienditem.Requester)
    return wannabeFriends

def usersRequested(user):
    userWannabe = []
    listOfThem = Friends.objects.filter(Requester=user,Confirmed=False)
    for friendsItem in listOfThem:
        userWannabe.append(friendsItem.Requested)
    return userWannabe

def checkFriends(user1,user2):
    one = Friends.objects.filter(Requester=user1,Requested=user2,Confirmed=True).first()
    two = Friends.objects.filter(Requester=user2,Requested=user1,Confirmed=True).first()
    if one or two: return True
    else: return False

def parsedDate(stringdate):
    parts = stringdate.split('-')
    parts = [int(i) for i in parts]
    dateval = datetime.date(parts[0],parts[1],parts[2])
    return dateval

def returnFriend(user1,user2):
    one = Friends.objects.filter(Requester=user1,Requested=user2,Confirmed=True).first()
    two = Friends.objects.filter(Requester=user2,Requested=user1,Confirmed=True).first()
    if one: return one
    else: return two


def send_sms(account_sid, auth_token,body, from_, to):
    client = Client(account_sid,auth_token)
    message = client.messages \
            .create(
                body = body,
                from_ = from_,
                to = to,
            )

def generate_otp():
    N=6
    otp = ''.join(random.choices(string.ascii_uppercase + string.digits, k = N))
    return otp

# def activate(request, uidb64, token, backend='django.contrib.auth.backends.ModelBackend'):
#     try:
#         uid = force_text(urlsafe_base64_decode(uidb64))
#         user = User.objects.get(pk=uid)
#     except (TypeError, ValueError, OverflowError, User.DoesNotExist):
#         user = None

#     if user is not None and account_activation_token.check_token(user, token):
#         user.is_active = True
#         user.profile.email_confirmed = True
#         user.save()
#         login(request, user, backend='django.contrib.auth.backends.ModelBackend')
#         return redirect('home')
#     else:
#         return render(request, 'account_activation_invalid.html')

# class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
#     def is_open_for_signup(self, request, sociallogin):
#         u = sociallogin.user
#         # Optionally, set as staff now as well.
#         # This is useful if you are using this for the Django Admin login.
#         # Be careful with the staff setting, as some providers don't verify
#         # email address, so that could be considered a security flaw.
#         u.is_staff = False
#         if not u.email.split('@')[1] == "hyderabad.bits-pilani.ac.in":
#             raise ImmediateHttpResponse(response=HttpResponse('You Can Login With Only BITS Mail Account!'))
#         return super(CustomSocialAccountAdapter, self).is_open_for_signup(request, sociallogin)
