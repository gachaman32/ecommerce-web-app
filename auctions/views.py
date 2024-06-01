from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.http import JsonResponse
import stripe
from .forms import whenCreatingListingForms
from .models import Listing, Comment, Watchlist, Category, Bid, User
from django.db.models import Sum
from decimal import Decimal
from django.contrib.sites.shortcuts import get_current_site

stripe.api_key = settings.STRIPE_SECRET_KEY





def is_ajax(request):
    return request.headers.get('x-requested-with') == 'XMLHttpRequest'


def watchlist_checkout(request):
    listOfIds = Watchlist.objects.filter(user=request.user, watching=True).values('listing')
    listings = Listing.objects.filter(id__in=listOfIds)
    total_price = sum(listing.price for listing in listings)

    if total_price <= 0:
        return JsonResponse({
            'error': 'No items in the cart'
        })

    domain_url = settings.DOMAIN_URL
    checkout_session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[
            {
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': "Your Cart Items",
                    },
                    'unit_amount': int(total_price * 100),  # total price in cents
                },
                'quantity': 1,
            },
        ],
        mode='payment',
        success_url=domain_url + 'success/',
        cancel_url=domain_url + 'cancel/',
    )
    return JsonResponse({
        'id': checkout_session.id
    })

def listed_detail_checkout(request, listing_id):
    listing = Listing.objects.get(id=listing_id)
    domain_url = settings.DOMAIN_URL
    checkout_session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[
            {
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': listing.title,
                    },
                    'unit_amount': int(listing.price * 100),  # price in cents
                },
                'quantity': 1,
            },
        ],
        mode='payment',
        success_url=domain_url + 'success/',
        cancel_url=domain_url + 'cancel/',
    )
    return JsonResponse({
        'id': checkout_session.id
    })

def success(request):
    return render(request, 'auctions/success.html')

def cancel(request):
    return render(request, 'auctions/cancel.html')

def index(request):
    listings = Listing.objects.filter(sold=False)
    categories = Category.objects.all()  # Retrieve all categories
    context = {'active_listings': listings, 'categories': categories}
    context.update(navbar(request))
    return render(request, "auctions/index.html", context)

def navbar(request):
    categories = Category.objects.all()  # Retrieve all categories
    watchlist_count = 0
    if request.user.is_authenticated:
        watchlist_count = Watchlist.objects.filter(user=request.user, watching=True).count()
    return {'categories': categories, 'watchlist_count': watchlist_count}


def login_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")

def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))

def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]
        password1 = request.POST["password1"]  # Correctly access password1
        password2 = request.POST["password2"]  # Correctly access password2

        if password1 != password2:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })
        
        try:
            user = User.objects.create_user(username, email, password1)  # Use password1 here
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")


@login_required
def listing_detail(request, listingId):
    listing = get_object_or_404(Listing, id=listingId)
    related_listings = Listing.objects.filter(category=listing.category).exclude(id=listing.id)[:4]
    categories = Category.objects.all()  # Retrieve all categories
    context = {
        "listing": listing,
        "comments": Comment.objects.filter(listing=listing),
        "related_listings": related_listings,
        "stripe_publishable_key": settings.STRIPE_PUBLISHABLE_KEY,
        "categories": categories,  # Include categories in the context
    }
    return render(request, "auctions/listing_detail.html", context)


@login_required
def add_comment(request, listingId):
    if request.method == "POST":
        listing = get_object_or_404(Listing, id=listingId)
        comment_text = request.POST.get("comment")
        if comment_text:
            Comment.objects.create(user=request.user, listing=listing, comment=comment_text)
    return redirect('listing', listingId=listingId)

@login_required
def make_payment(request, listingId):
    listing = get_object_or_404(Listing, id=listingId)
    return redirect('listing', listingId=listingId)

@login_required
def listingInfos(request, listingId):
    listing = Listing.objects.get(id=listingId)
    user = request.user
    owner = listing.user
    category = Category.objects.get(category=listing.category)
    comments = Comment.objects.filter(listing=listing.id)
    watching = Watchlist.objects.filter(user=user, listing=listing).first()  # Get the first entry or None
    return listing, user, owner, category, comments, watching

@login_required
def listing(request, listingId):
    info = listingInfos(request, listingId)
    listing, user, owner, category = info[0], info[1], info[2], info[3]

    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse('login'))

    if request.method == "POST":
        comment = request.POST.get("comment")
        if comment:
            Comment.objects.create(user=user, listing=listing, comment=comment)

    watching = False
    watchlist_entry = Watchlist.objects.filter(user=user, listing=listing).first()
    if watchlist_entry:
        watching = watchlist_entry.watching

    context = {
        "listing": listing,
        "category": category,
        "comments": Comment.objects.filter(listing=listing),
        "watching": watching,
        "owner": owner,
    }
    return render(request, "auctions/listings.html", context)

@login_required
def addingWatchlist(request, listingId):
    info = listingInfos(request, listingId)
    listing, user, owner, category, comments, watching = info
    watchlist_entry, created = Watchlist.objects.get_or_create(user=user, listing=listing)
    watchlist_entry.watching = True
    watchlist_entry.save()
    return redirect('listing', listingId=listingId)



@login_required
def removingWatchlist(request, listingId):
    listing = get_object_or_404(Listing, id=listingId)
    watchlist_entry = Watchlist.objects.filter(user=request.user, listing=listing).first()
    if watchlist_entry:
        watchlist_entry.delete()
        
        # Recalculate total price
        total_price = Listing.objects.filter(id__in=Watchlist.objects.filter(user=request.user, watching=True).values('listing')).aggregate(Sum('price'))['price__sum'] or 0
        
        # Check if the cart is empty
        if total_price == 0:
            # If the cart is empty, return a response to indicate that
            return JsonResponse({
                'success': True,
                'empty_cart': True,
            })
        else:
            # If the cart still contains items, return the updated total price
            return JsonResponse({
                'success': True,
                'new_total_price': total_price
            })
    else:
        return JsonResponse({
            'success': False,
            'error': 'Watchlist entry not found'
        })
    
@login_required
def bid(request, listingId):
    info = listingInfos(request, listingId)
    listing, user, owner, category, comments, watch = info[0], info[1], info[2], info[3]
    if request.method == "POST":
        bid = request.POST["bid"]
        listing.price = float(bid)
        listing.save()
        Bid.objects.create(user=user, price=bid, listing=listing)
    context = {
        "listing": listing,
        "category": category,
        "comments": comments,
        "watching": watch,
        "owner": owner,
    }
    return render(request, "auctions/listings.html", context)

@login_required
def closingBid(request, listingId):
    info = listingInfos(request, listingId)
    listing, user, category, owner, comments, watch = info[0], info[1], info[2], info[3]
    listing.sold = True
    listing.save()
    winner = Bid.objects.get(price=listing.price, listing=listing).user
    winning = user.id == winner.id
    context = {
        "listing": listing,
        "category": category,
        "comments": comments,
        "watching": watch,
        "owner": owner,
        "thewinner": winning,
    }
    return render(request, "auctions/closebids.html", context)

def category(request):
    category_id = request.GET.get('category')
    listings = None
    category_name = None
    if category_id:
        listings = Listing.objects.filter(category=category_id)
        category_name = Category.objects.get(id=category_id).category
    context = {
        "categories": Category.objects.all(),
        "category": category_name if category_name else "",
        "listings": listings,
    }
    return render(request, "auctions/categories.html", context)


@login_required
def watchList(request, userId):
    listOfIds = Watchlist.objects.filter(user=request.user, watching=True).values('listing')
    listings = Listing.objects.filter(id__in=listOfIds)
    total_price = sum(float(listing.price) for listing in listings)  # Convert to float here
    
    return render(request, "auctions/watchlist.html", {
        "listings": listings,
        "total_price": total_price,
        "stripe_publishable_key": settings.STRIPE_PUBLISHABLE_KEY
    })



@login_required
def createListing(request):
    if request.method == "POST":
        form = whenCreatingListingForms(request.POST)
        if form.is_valid():
            title = form.cleaned_data["title"]
            desc = form.cleaned_data["desc"]
            # Remove commas from bid field and convert to Decimal
            bid = Decimal(form.cleaned_data["bid"].replace(',', ''))
            imgLink = form.cleaned_data["imgLink"]
            user = request.user
            categoryId = Category.objects.get(id=request.POST["categories"])
            Listing.objects.create(user=user, title=title, desc=desc, price=bid, imgLink=imgLink, category=categoryId)
            return HttpResponseRedirect(reverse('index'))
    else:
        context = {
            "listingForm": whenCreatingListingForms(),
            "categories": Category.objects.all(),
        }
        return render(request, "auctions/createlisting.html", context)
    
def about(request):
    return render(request, 'auctions/about.html')