from .models import Category, Watchlist

def watchlist_count(request):
    categories = Category.objects.all()
    if request.user.is_authenticated:
        watchlist_count = Watchlist.objects.filter(user=request.user, watching=True).count()
    else:
        watchlist_count = 0
    return {'watchlist_count': watchlist_count, 'categories': categories}