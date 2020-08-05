from . import models


# get the basket Object from the database, to count objects and being viewed :
# basket has 5 elements.


# get the basket_id from the session data, from the request sent
def basket_middleware(get_response):

    def middleware(request):
        if 'basket_id' in request.session:
            basket_id = request.session['basket_id']
            basket = models.Basket.objects.get(id=basket_id) # filter instead of get at first time running the code
            request.basket = basket         # it is the secret, sending the basket to the view
        else:
            request.basket=None
        response = get_response(request)
        return response

    return middleware
