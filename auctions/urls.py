from django.urls import path
from django.contrib.auth.views import LoginView
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("createListing", views.createListing, name="createListing"),
    path('listing/<int:listingId>/', views.listing_detail, name='listing'),
    path('listing/<int:listingId>/comment', views.add_comment, name='add_comment'),
    path('listing/<int:listingId>/payment', views.make_payment, name='make_payment'),
    path("removingWatchlist/<str:listingId>", views.removingWatchlist, name="removingWatchlist"),
    path("addingWatchlist/<str:listingId>", views.addingWatchlist, name="addingWatchlist"),
    path("bid/<str:listingId>", views.bid, name="bid"),
    path("categories", views.category, name="categories"),
    path("closingBid/<str:listingId>", views.closingBid, name="closingBid"),
    path("watchList/<str:userId>", views.watchList, name="watchlist"),
    path('create-checkout-session/', views.watchlist_checkout, name='watchlist_checkout'),
    path('create-checkout-session/<int:listing_id>/', views.listed_detail_checkout, name='listed_detail_checkout'),
    path('success/', views.success, name='success'),
    path('cancel/', views.cancel, name='cancel'),
    path('about/', views.about, name='about')
]
