from django.views.generic.edit import FormView
from main import forms, models
from django.shortcuts import get_object_or_404, render
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.core.mail import send_mail
import logging
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy, reverse
from django.views.generic import(
    ListView, DetailView, CreateView, UpdateView, DeleteView, )
from django.http import HttpResponseRedirect

from django import forms as django_forms
from django.db import models as django_models
import django_filters
from django_filters.views import FilterView




logger = logging.getLogger(__name__)


class DateInput(django_forms.DateInput):
    input_type = 'date'


class OrderFilter(django_filters.FilterSet):

    class Meta:
        model = models.Order
        fields = {
                'user__email': ['icontains'],
                'status': ['exact'],
                'date_updated': ['gt', 'lt'],
                'date_added': ['gt', 'lt'],
                }

        filter_overrides = {
                django_models.DateTimeField: {
                    'filter_class': django_filters.DateFilter,
                    'extra': lambda f:{
                        'widget': DateInput}}}

class OrderView(UserPassesTestMixin, FilterView):
    filterset_class = OrderFilter
    login_url = reverse_lazy("login")
    def test_func(self):
        return self.request.user.is_staff is True



# signup view
class SignupView(FormView):
    template_name = "signup.html"
    form_class = forms.UserCreationForm

    def get_success_url(self):
        redirect_to = self.request.GET.get("next", "/")
        return redirect_to

    def form_valid(self, form):
        response = super().form_valid(form)
        form.save()

        # for auth and logging in
        email = form.cleaned_data.get("email")
        raw_password = form.cleaned_data.get("password1")
        logger.info("New signup for email=%s through SignupView", email)
        user = authenticate(email=email, password=raw_password) # return boolean value
        login(self.request, user) # log the user in if true

        form.send_mail()    # call the function send_email from the original form
        messages.info(self.request, "You signed up successfully.")  # message on the browser of the user
        return response


# contact us view
class ContactUsView(FormView):
    template_name = "contact_form.html"
    form_class = forms.ContactForm
    success_url = '/'

    def form_valid(self, form):
        form.send_mail()
        return super().form_valid(form)

''' ---------------------------------------------- Product -----------------------------'''

class ProductDetailView(DetailView):
    model = models.Product
    template_name = 'main/product_detail.html'
    context_object_name = 'product_detail'



class ProductListView(ListView):
    template_name = "main/product_list.html"
    paginate_by = 4
    context_object_name = 'products_list'

    def get_queryset(self):
        searching_tag = self.kwargs["tag"]   # get the tag/slug 'drama' from the searching link
        # from the official docs searching_tag = self.kwargs.get("tag")
        # why?? because path('products/<slug:tag>/', views.ProductListView.as_view(), name='product'),
        # is defined as => products + slug:tage so we write kwargs["tag"]

        # also to get the full searching link :
        # search_text = self.request.GET.get('search_text')

        self.tag = None     # self.tag is nothing, we add a var called tag to the self
        # so we can replace self.tag with obj or any other Var
        self.tag = get_object_or_404(models.ProductTag, slug=searching_tag)
        # obj = get_object_or_404(MyModel, pk=1)
        # we get a full object of the ProductTag table, wich slug is the users searching

        if self.tag:    # not equal None
            products = models.Product.objects.active().filter(tags=self.tag)
        else: products = models.Product.objects.active()

        return products.order_by("name")


''' --------------------------------------- Address Views -------------------------------- '''
# list address
class AddressListView(LoginRequiredMixin, ListView):
    model = models.Address

    def get_queryset(self):
        return self.model.objects.filter(user=self.request.user)



# create address
class AddressCreateView(LoginRequiredMixin, CreateView):
    model = models.Address
    fields = ["name", "address1", "address2", "zip_code", "city", "country", ]
    success_url = reverse_lazy("address_list")

    # This method is called when valid form data has been POSTed.
    # It should return an HttpResponse.
    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.user = self.request.user
        obj.save()
        return super().form_valid(form)



class AddressUpdateView(LoginRequiredMixin, UpdateView):
    model = models.Address
    fields = ["name", "address1", "address2", "zip_code", "city", "country", ]
    success_url = reverse_lazy("address_list")
    # with no template, it searching automaticly for address_update.html cuz it is in the url
    # chaching the database
    def form_valid(self, form):
        return self.model.objects.filter(user=self.request.user)



class AddressDeleteView(LoginRequiredMixin, DeleteView):
    model = models.Address
    success_url = reverse_lazy("address_list")

    # chaching the database
    def get_queryset(self):
        return self.model.objects.filter(user=self.request.user)



# address select view
class AddressSelectionView(LoginRequiredMixin, FormView):
    template_name = "address_select.html"
    form_class = forms.AddressSelectionForm
    success_url = reverse_lazy('checkout_done')


    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        del self.request.session['basket_id']
        basket = self.request.basket
        basket.create_order(
            form.cleaned_data['billing_address'],
            form.cleaned_data['shipping_address'],
            )
        return super().form_valid(form)


''' ---------------------------------------- Basket view --------------------------------'''
# note : every request add_to_basket, creates a new basket, by using the middleware,
    # it give the old basket id so it will not create new one. it is request.basket

# 1. create basket, 2. create basket line using the basket id
def add_to_basket(request):


    product = get_object_or_404(models.Product, pk=request.GET.get("product_id"))
    basket = request.basket


    # it is ok to be =>> if not basket:
    if not request.basket:  # 1. if there No basket, will create. if there jump to step 2
        if request.user.is_authenticated:   # put the user (user or none)
            user = request.user
        else:
            user = None

        basket = models.Basket.objects.create(user=user)    # finally create the basket anyway with user
        request.session["basket_id"] = basket.id        # put the basked id to the session data
    # 2. Get or Create basket Line, and put the basket id
    basketline, created = models.BasketLine.objects.get_or_create(basket=basket, product=product)
    if not created:
        basketline.quantity += 1
        basketline.save()
    return HttpResponseRedirect(reverse("product", args=(product.slug,)))



def manage_basket(request):
    if not request.basket:
        return render(request, "basket.html", {"formset": None})

    if request.method == "POST":
        formset = forms.BasketLineFormSet(request.POST, instance=request.basket)
        if formset.is_valid():
            formset.save()

    else:
        formset = forms.BasketLineFormSet(instance=request.basket)

    if request.basket.is_empty():
        return render(request, "basket.html", {"formset": None})

    return render(request, "basket.html", {"formset": formset})
