from django import forms
from django.core.mail import send_mail
import logging
from django.contrib.auth.forms import UserCreationForm as DjangoUserCreationForm
from django.contrib.auth.forms import UsernameField
from . import models
from django.contrib.auth import authenticate
from django.forms import inlineformset_factory
from . import widgets


logger = logging.getLogger(__name__)



# login form
class AuthenticationForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(strip=False, widget=forms.PasswordInput)

    def __init__(self, request=None, *args, **kwargs):  # Forms do not interact with the request object directly and therefore are limited in what they can do. They normally interact with request.POST or, in some specific cases, other attributes of the request.
        self.request = request
        self.user = None
        super().__init__(*args, **kwargs)

    def clean(self):    # get the email and password cobjects
        email = self.cleaned_data.get("email")
        password = self.cleaned_data.get("password")

        if email is not None and password:  # if not None, get boolean if the user is authenticated
            self.user = authenticate(self.request, email=email, password=password)
            if self.user is None: # if not authenticated
                raise forms.ValidationError("Invalid email/password combination.")

            logger.info("Authentication successful for email=%s", email)
        return self.cleaned_data


    def get_user(self):
        return self.user



# contact us form
class ContactForm(forms.Form):

    name = forms.CharField(label='Your name', max_length=100)
    message = forms.CharField(label='Your message', max_length=600, widget=forms.TextInput)

    # imported from core.mail
    def send_mail(self):
        logger.info("Sending email to customer service")
        message = "From: {0}\n{1}".format(self.cleaned_data["name"],self.cleaned_data["message"],)
        send_mail("Site message", message, "site@booktime.domain", ["customerservice@booktime.domain"], fail_silently=False,)



# signup form
class UserCreationForm(DjangoUserCreationForm):
    class Meta(DjangoUserCreationForm.Meta):
        model = models.User
        fields = ("email", )
        fields_classes = {"email": UsernameField}

    def send_mail(self):
        logger.info("Sending signup email for email=%s", self.cleaned_data["email"],)
        message = "Welcome {}".format(self.cleaned_data["email"])
        send_mail("Welcome to BookTime", message, "site@booktime.domain", [self.cleaned_data["email"]], fail_silently=True,)



''' This formset will automatically build forms for all basket lines
    connected to the basket spsecified; the only editable fields will be quantity
    and there will be no extra form to add new entries '''

BasketLineFormSet = inlineformset_factory(
    models.Basket,
    models.BasketLine,
    fields=("quantity",),
    extra=0,
    widgets={"quantity": widgets.PlusMinusNumberInput()},
)





class AddressSelectionForm(forms.Form):

    billing_address = forms.ModelChoiceField(queryset=None)
    shipping_address = forms.ModelChoiceField(queryset=None)

    def __init__(self, user, *args, **kwargs):
        super(). __init__(*args, **kwargs)
        queryset = models.Address.objects.filter(user=user)
        self.fields['billing_address'].queryset = queryset
        self.fields['shipping_address'].queryset = queryset
