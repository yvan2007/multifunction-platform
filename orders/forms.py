from django import forms

class OrderForm(forms.Form):
    address = forms.CharField(label="Adresse", max_length=255)
    city = forms.CharField(label="Ville", max_length=100)
    postal_code = forms.CharField(label="Code postal", max_length=20)
    country = forms.CharField(label="Pays", max_length=100)