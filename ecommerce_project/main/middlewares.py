from . import models


# get the basket Object from the database, to count objects and being viewed :
# basket has 5 elements.
def basket_middleware(get_response):

    def middleware(request):
        if 'basket_id' in request.session:
            basket_id = request.session['basket_id']
            basket = models.Basket.objects.get(id=basket_id) # filter instead of get at first time running the code
            request.basket = basket
        else:
            request.basket=None
        response = get_response(request)
        return response

    return middleware
