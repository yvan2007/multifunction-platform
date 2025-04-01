# In ecommerce/forms.py
from django import forms
from django.shortcuts import redirect, render
from .models import Product

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'price', 'stock', 'category', 'tags']
        widgets = {
            'description': forms.Textarea(attrs={'class': 'ckeditor5'}),
        }

# In views.py
def add_product(request):
    from ecommerce.forms import ProductForm
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save()
            return redirect('index')
    else:
        form = ProductForm()
    return render(request, 'add_product.html', {'form': form})