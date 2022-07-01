from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.urls import reverse
from django.db import connection
from django.contrib.auth import authenticate, login, logout
from .models import *
from .functions import *
from django.db.models import Q
from .forms import CustomUserCreationForm,forms
from django.contrib import messages
import time
from django.contrib.auth import get_user_model
from django.conf import settings

cursor = connection.cursor()

# Create your views here.
def home(request):
    if request.user.is_authenticated:
        return redirect(reverse('feed'))
    return render(request, 'baseapp/home.html')

def loginPage(request):
    if request.user.is_authenticated:
        return redirect(reverse('feed'))
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect(reverse('feed'))
        else:
            messages.info(request, 'Username or Password is incorrect.')
    return render(request, 'baseapp/Login.html')

def signup(request):
    if request.user.is_authenticated:
        return redirect(reverse('feed'))
    form = CustomUserCreationForm()
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        username = request.POST.get('username')
        if form.is_valid():
            form.save()
            pw = form.cleaned_data['password1']
            usermodel = User.objects.get(username=username)
            login(request,usermodel, backend='django.contrib.auth.backends.ModelBackend')
            return redirect(reverse('accountSetup'))

    context = {'form': form}
    return render(request, 'baseapp/SignUp.html', context)

def logoutPage(request):
    logout(request)
    return redirect(reverse('home'))

def feed(request):
    if not request.user.is_authenticated:
        messages.info(request, 'You need to login to be able to access this feature.')
        return redirect(reverse('login'))
    if not UserDetails.objects.filter(user=request.user).first():
        messages.info(request,'Please set up your account first.')
        return redirect(reverse('accountSetup'))

    context = {}
    #POSTS
    final_posts = []
    final_posts_with_likes = []
    userFriends = findfriends(request.user)
    userPages = findFollowedPages(request.user)
    context['pagesFollowed'] = userPages
    for friend in userFriends:
        for post in findUserPosts(friend):
            if post.page == None:
                final_posts.append(post)
    for page in userPages:
        for post in findPagePosts(page):
                final_posts.append(post)
    myposts= Posts.objects.filter(user=request.user)
    for post in myposts:
        if post not in final_posts:
            final_posts.append(post) 
    
    final_posts.sort(key=lambda x:x.PostedOn)
    final_posts.reverse()
    for post in final_posts:
        if PostLikes.objects.filter(post=post,user=request.user).first():
            final_posts_with_likes.append((post,True))
        else:
            final_posts_with_likes.append((post,False))
    context['posts'] = final_posts_with_likes

    #FRIEND REQUESTS
    requestingUsers = friendRequests(request.user)
    context['friendRequests'] = requestingUsers
    if request.method=="POST":
        newpost = Posts()
        newpost.user = request.user
        newpost.Title = request.POST.get('Title')
        newpost.Body = request.POST.get('Body') if 'Body' in request.POST else None
        newpost.LikeCount, newpost.CommentCount = 0,0
        pageval = request.POST.get('Page')
        if pageval == 'profile':
            newpost.page = None
        else:
            newpost.page = Pages.objects.get(PageID = int(pageval))
        newpost.Image = request.FILES['PostImage'] if 'PostImage' in request.FILES else None
        newpost.save()
        return redirect(reverse('feed'))

    if request.method == 'GET':
        if request.GET.get('tag') == 'friendrequest':
            req = request.GET.get('type')
            uname = request.GET.get('userid')
            print(uname,request)
            usermodel = User.objects.get(username=uname)
            if req == 'accept':
                frnd = Friends.objects.get(Requester=usermodel, Requested=request.user)
                frnd.Confirmed = True
                frnd.save()
            if req == 'reject':
                frnd = Friends.objects.get(Requester=usermodel, Requested=request.user)
                frnd.delete()
        elif request.GET.get('tag') == 'likepost':
            post_id = int(request.GET.get('id'))
            postobject = Posts.objects.get(PostID = post_id)
            newlike = PostLikes(post=postobject, user=request.user)
            newlike.save()
            postobject.LikeCount += 1
            postobject.save()
        elif request.GET.get('tag') == 'unlikepost':
            post_id = int(request.GET.get('id'))
            postobject = Posts.objects.get(PostID = post_id)
            existinglike = PostLikes.objects.get(post=postobject, user=request.user)
            existinglike.delete()
            postobject.LikeCount -= 1
            postobject.save()
    return render(request, 'baseapp/Feed.html',context)

def posts(request,postID):
    context = {}
    post = Posts.objects.get(PostID=postID)
    postedUserDetail = UserDetails.objects.get(user=post.user)
    
    if (not request.user.is_authenticated):
        messages.info(request, 'You need to login to be able to access this feature.')
        return redirect(reverse('login'))
    if not UserDetails.objects.filter(user=request.user).first():
            messages.info(request,'Please set up your account first.')
            return redirect(reverse('accountSetup'))
    # CHECKING PRIVACY
    if postedUserDetail.Private:
        if (not checkFriends(post.user, request.user)) and (request.user != post.user) :
            messages.info(request,"This post is private, only the friends of the user who made this post can view this.")
            return redirect(reverse('feed'))
    
    postlikeobjects = PostLikes.objects.filter(post=post)
    postLikers = [i.user for i in postlikeobjects]
    comments = Comments.objects.filter(post=post)
    commentWithLikes = []
    for comment in comments:
        Likers = []
        for likeobjecct in CommentLikes.objects.filter(comment=comment):
            if likeobjecct.user == request.user:
                Likers = [likeobjecct.user] + Likers
            else:
                Likers.append(likeobjecct.user)
        commentWithLikes.append((comment,Likers,len(Likers)))

    context['this_post']= post
    context['comment_info'] = commentWithLikes
    context['postLikers'] = postLikers

    
    if request.method == 'POST': 
        comment = request.POST.get('comment')
        newcomment = Comments(user=request.user, post=post)
        newcomment.Body = comment
        post.CommentCount += 1
        post.save()
        newcomment.save()

        return redirect(reverse('post', kwargs={'postID': post.PostID}))

    if request.method == 'GET':
        if request.GET.get('tag') == 'likepost':
            post.LikeCount += 1
            post.save()
            newlike = PostLikes(post=post, user=request.user)
            newlike.save()
        elif request.GET.get('tag') == 'unlikepost':
            post.LikeCount -= 1
            post.save()
            likeobj = PostLikes.objects.get(post=post, user=request.user)
            likeobj.delete()
        elif request.GET.get('tag') == 'likecomment':
            cid = int(request.GET.get("cid"))
            cmnt = Comments.objects.get(CommentID = cid)
            newlike = CommentLikes(comment=cmnt, user=request.user)
            newlike.save()
        elif request.GET.get('tag') == 'unlikecomment':
            cid = int(request.GET.get("cid"))
            cmnt = Comments.objects.get(CommentID = cid)
            like = CommentLikes.objects.get(comment=cmnt, user=request.user)
            like.delete()

    return render(request,'baseapp/Post.html',context)

def friends(request):
    context = {}
    if not request.user.is_authenticated:
        messages.info(request, 'You need to login to be able to access this feature.')
        return redirect(reverse('login'))
    
    if not UserDetails.objects.filter(user=request.user).first():
        messages.info(request,'Please set up your account first.')
        return redirect(reverse('accountSetup'))


    userFriends = findfriends(request.user)
    context['myFriends'] = userFriends
 
    requestingUsers = friendRequests(request.user)
    context['friendRequests'] = requestingUsers
    megaOthers = userFriends + requestingUsers
    megaOthers.append(request.user)
        
    # allOthers = [user for user in (User.objects.filter(~Q(id__in=[o.id for o in megaOthers])))]
    users = list(get_user_model().objects.all())
    allOthers=[]
    for user in users:
        if user not in megaOthers:
            allOthers.append(user)
    
    requestedFellas = usersRequested(request.user)
    unrequisitedFellas = [el for el in allOthers if el not in requestedFellas]
    
    context['unknownPeople'] = unrequisitedFellas
    context['mySentPendingReqs'] = requestedFellas
    
    jsonobject = {}
    allusers = UserDetails.objects.all()
    for i in allusers:
        jsonobject[i.user.username] = i.ProfilePic.url

    context['images'] = jsonobject
    
    if request.method == 'GET':
        if request.GET.get('tag') == 'sendrequest':
            uname = request.GET.get('userid')
            usermodel = User.objects.get(username=uname)
            frnd = Friends(Requester = request.user, Requested = usermodel, Confirmed = False)
            frnd.save()
        elif request.GET.get('tag') == 'friendrequest':
            req = request.GET.get('type')
            uname = request.GET.get('userid')
            print(uname,request)
            usermodel = User.objects.get(username=uname)
            if req == 'accept':
                frnd = Friends.objects.get(Requester=usermodel, Requested=request.user)
                frnd.Confirmed = True
                frnd.save()
            if req == 'reject':
                frnd = Friends.objects.get(Requester=usermodel, Requested=request.user)
                frnd.delete()
        elif request.GET.get('tag') == 'unfriend':
            print('something')
            uname = request.GET.get('userid')
            usermodel = User.objects.get(username = uname)
            if Friends.objects.filter(Requester=request.user,Requested=usermodel,Confirmed = True).first(): 
                friend = Friends.objects.filter(Requester=request.user,Requested=usermodel,Confirmed = True)
                friend.delete()
            else :
                friend = Friends.objects.filter(Requester=usermodel,Requested=request.user,Confirmed = True)
                friend.delete()
 
    return render(request,'baseapp/Friends.html',context)

def userpage(request,name):
    context = {}
    accessuser = User.objects.get(username = name)
    accessUserDetails = UserDetails.objects.get(user = accessuser)
    if not request.user.is_authenticated:
        messages.info(request, 'You need to login to be able to access this feature.')
        return redirect(reverse('login'))
    
    if accessUserDetails.Private:
        if (not checkFriends(accessuser, request.user)) and (request.user != accessuser) :
            messages.info(request,"This profile is private, only the friends of this user can view this.")
            return redirect(reverse('feed'))

    if not UserDetails.objects.filter(user=request.user).first():
        messages.info(request,'Please set up your account first.')
        return redirect(reverse('accountSetup'))

    userPages = findFollowedPages(request.user)
    context['pagesFollowed'] = userPages
    context['accesseduser']=accessuser
    context['them']=accessUserDetails.Name
    if accessUserDetails.Private:
        # if checkFriends(accessuser, request.user) |( accessuser == request.user):
        #THEIR FRIENDS
        accessUserFriends = findfriends(accessuser)
        context['theirFriends'] = accessUserFriends

        #THEIR POSTS
        postsMade = Posts.objects.filter(user=accessuser,page=None).order_by('PostedOn')
        final_posts = []
        final_posts_with_likes = []
        for post in postsMade:
            final_posts.append(post)


        final_posts.sort(key=lambda x:x.PostedOn)
        final_posts.reverse()

        for post in final_posts:
            if PostLikes.objects.filter(post=post,user=request.user).first():
                final_posts_with_likes.append((post,True))
            else:
                final_posts_with_likes.append((post,False))
        context['theirPosts'] = final_posts_with_likes 

        #ABOUT THEM
        context['theirInfo'] = accessUserDetails
            
    else:
        #THEIR FRIENDS
        accessUserFriends = findfriends(accessuser)
        context['theirFriends'] = accessUserFriends
        #THEIR POSTS
        postsMade = Posts.objects.filter(user=accessuser,page=None).order_by('PostedOn')
        final_posts = []
        final_posts_with_likes = []
        for post in postsMade:
            final_posts.append(post)
        final_posts.sort(key=lambda x:x.PostedOn)
        final_posts.reverse()
        for post in final_posts:
            if PostLikes.objects.filter(post=post,user=request.user).first():
                final_posts_with_likes.append((post,True))
            else:
                final_posts_with_likes.append((post,False))
        context['theirPosts'] = final_posts_with_likes

        #ABOUT THEM
        context['theirInfo'] = accessUserDetails


    if request.method == 'GET':
        if request.GET.get('tag') == 'sendrequest':
            frnd = Friends(Requester = request.user, Requested = accessuser, Confirmed = False)
            frnd.save()
        elif request.GET.get('tag') == 'likepost':
            post_id = int(request.GET.get('id'))
            postobject = Posts.objects.get(PostID = post_id)
            newlike = PostLikes(post=postobject, user=request.user)
            newlike.save()
            postobject.LikeCount += 1
            postobject.save()
        elif request.GET.get('tag') == 'unlikepost':
            post_id = int(request.GET.get('id'))
            postobject = Posts.objects.get(PostID = post_id)
            existinglike = PostLikes.objects.get(post=postobject, user=request.user)
            existinglike.delete()
            postobject.LikeCount -= 1
            postobject.save()

    return render(request,'baseapp/Profile.html',context)

def accountSetup(request):
    if not request.user.is_authenticated:
        messages.info(request, 'You need to login to be able to access this feature.')
        return redirect(reverse('login'))
    context = {}
    if request.method == "POST":
        details = UserDetails()
        details.user = request.user
        details.Name = request.POST.get('Name')
        details.DateOfBirth = parsedDate(request.POST.get('DateOfBirth'))
        details.PhoneNumber = request.POST.get('PhoneNumber')
        details.Gender = request.POST.get('Gender')
        details.About = request.POST.get('About')
        details.Private = 'Private' in request.POST
        details.ProfilePic = request.FILES['ProfilePic']
        random_otp = generate_otp()
        msg_body = f'''
        Hi {details.Name}. Welcome to SocialButterfly!😀 
        Your username is {details.user} and phone number is {details.PhoneNumber}.
        Your OTP for verification is: {random_otp}
        '''
        # send_sms(settings.ACCOUNT_SID, settings.AUTH_TOKEN, msg_body, '+19789991688', '+91' + details.PhoneNumber)
        details.otp = random_otp
        details.save()
        time.sleep(3)
        messages.info(request,"Account activated!")
        return redirect(reverse('feed'))
    return render(request,'baseapp/accountSetup.html',context)

# def verify(request):
#     if not request.user.is_authenticated:
#         messages.info(request, 'You need to login to be able to access this feature.')
#         return redirect(reverse('login'))
    
#     if not UserDetails.objects.filter(user=request.user).first():
#         messages.info(request,'Please set up your account first.')
#         return redirect(reverse('accountSetup'))

#     if request.method == "POST":
        
def editProfile(request):
    if not request.user.is_authenticated:
        messages.info(request, 'You need to login to be able to access this feature.')
        return redirect(reverse('login'))
    
    if not UserDetails.objects.filter(user=request.user).first():
        messages.info(request,'Please set up your account first.')
        return redirect(reverse('accountSetup'))

    context = {}
    context['userdetail'] = UserDetails.objects.get(user=request.user)

    if request.method == "POST":
        details = UserDetails.objects.get(user = request.user)
 
        details.Name = request.POST.get('Name')
        details.PhoneNumber = request.POST.get('PhoneNumber')
        details.About = request.POST.get('About')
        details.Private = 'Private' in request.POST
        if 'ProfilePic' in request.FILES:
            details.ProfilePic = request.FILES['ProfilePic']
 
        details.save()
 
        return redirect(reverse('feed'))
    return render(request,'baseapp/editUser.html',context)

def aboutPage(request,id):
    if not request.user.is_authenticated:
        messages.info(request, 'You need to login to be able to access this feature.')
        return redirect(reverse('login'))
    
    if not UserDetails.objects.filter(user=request.user).first():
        messages.info(request,'Please set up your account first.')
        return redirect(reverse('accountSetup'))

    context = {}
    
    currpage = Pages.objects.get(PageID=id)
    context['page']=currpage
    postsMade = Posts.objects.filter(page=currpage).order_by('PostedOn')
    final_posts = []
    final_posts_with_likes = []
    for post in postsMade:
        final_posts.append(post)
    final_posts.reverse()
    for post in final_posts:
        if PostLikes.objects.filter(post=post,user=request.user).first():
            final_posts_with_likes.append((post,True))
        else:
            final_posts_with_likes.append((post,False))
    context['posts']=final_posts_with_likes
    pageFollows = PageFollowers.objects.filter(page=currpage)
    checker = [a.user for a in PageFollowers.objects.filter(page=currpage)]

    pageOwner = currpage.PageAdmin
    context['owner'] = pageOwner


    if (request.user not in checker) and request.user != pageOwner:
        context['allowfollow'] = True
    else:
        context['allowfollow'] = False
    
    if request.user == pageOwner:
        context['creator'] = True
    

    context['followers'] = checker

    if request.method == 'GET':
        if request.GET.get('tag') == 'followpage':
            # newflr = PageFollowers.objects.filter(page = currpage, user = request.user).exists()
            if not PageFollowers.objects.filter(user = request.user, page = currpage).first():
                follow = PageFollowers(user = request.user, page = currpage)
                follow.save()
        elif request.GET.get('tag') == 'unfollowpage':
            PageFollowers.objects.filter(page = currpage, user = request.user).delete()
        elif request.GET.get('tag') == 'likepost':
            post_id = int(request.GET.get('id'))
            postobject = Posts.objects.get(PostID = post_id)
            newlike = PostLikes(post=postobject, user=request.user)
            newlike.save()
            postobject.LikeCount += 1
            postobject.save()
        elif request.GET.get('tag') == 'unlikepost':
            post_id = int(request.GET.get('id'))
            postobject = Posts.objects.get(PostID = post_id)
            existinglike = PostLikes.objects.get(post=postobject, user=request.user)
            existinglike.delete()
            postobject.LikeCount -= 1
            postobject.save()
    return render(request,'baseapp/Pages.html',context)

def pagesPage(request):
    if not request.user.is_authenticated:
        messages.info(request, 'You need to login to be able to access this feature.')
        return redirect(reverse('login'))
    
    if not UserDetails.objects.filter(user=request.user).first():
        messages.info(request,'Please set up your account first.')
        return redirect(reverse('accountSetup'))

    context = {}

    myPagesRaw = PageFollowers.objects.filter(user = request.user)
    pagesFollowed = [a.page for a in PageFollowers.objects.filter(user = request.user)]

    pagesCreated = [a for a in Pages.objects.filter(PageAdmin = request.user)]

    megaOthers = pagesFollowed + pagesCreated

    
    allOthers = []
    for page in Pages.objects.all():
        if page not in megaOthers:
            allOthers.append(page)

    context['follow'] = pagesFollowed
    context['created'] = pagesCreated
    context['others'] = allOthers

    if request.method == 'GET':

        if request.GET.get('tag') == 'followpage':
            pid = request.GET.get('pageid')
            pagemodel = Pages.objects.get(PageID=pid)
            newflr = PageFollowers(user = request.user, page = pagemodel)
            newflr.save()

    if request.method=="POST":
        newpage = Pages()
        newpage.PageAdmin = request.user
        newpage.PageName = request.POST.get('PageName')
        newpage.About = request.POST.get('About') if 'About' in request.POST else None
        newpage.PageImage = request.FILES['PageImage'] if 'PageImage' in request.FILES else None

        newpage.save()

        return redirect(reverse('allPages'))
    return render(request, 'baseapp/allPages.html',context)
