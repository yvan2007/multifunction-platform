# ecommerce/forms.py
from django import forms
from .models import Product, ProductImage, Review  # Ajoutez Review ici

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'price', 'stock', 'category', 'tags']
        widgets = {
            'description': forms.Textarea(attrs={'class': 'ckeditor5'}),
        }

class ProductImageForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        fields = ['image', 'alt_text']

from django import forms
from .models import Review

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.HiddenInput(),  # Le champ sera géré via JavaScript
            'comment': forms.Textarea(attrs={'rows': 4, 'class': 'form-control', 'placeholder': 'Votre commentaire...'}),
        }

# ecommerce/forms.py
from django import forms
import csv
from io import TextIOWrapper
from .models import Product, Category

class BulkProductImportForm(forms.Form):
    category = forms.ModelChoiceField(
        queryset=Category.objects.filter(category_type='product', is_active=True),
        label="Catégorie",
        help_text="Sélectionnez la catégorie pour les produits importés."
    )
    csv_file = forms.FileField(
        label="Fichier CSV",
        help_text="Téléchargez un fichier CSV avec les colonnes : name,description,price,stock,tags (séparés par des virgules)."
    )

    def clean_csv_file(self):
        csv_file = self.cleaned_data['csv_file']
        if not csv_file.name.endswith('.csv'):
            raise forms.ValidationError("Le fichier doit être un fichier CSV.")
        return csv_file

    def save(self, request):
        category = self.cleaned_data['category']
        csv_file = TextIOWrapper(self.cleaned_data['csv_file'].file, encoding='utf-8')
        reader = csv.DictReader(csv_file)
        errors = []
        created_count = 0

        required_columns = {'name', 'description', 'price', 'stock'}
        if not all(col in reader.fieldnames for col in required_columns):
            raise forms.ValidationError(
                "Le fichier CSV doit contenir les colonnes : name,description,price,stock,tags"
            )

        for row in reader:
            try:
                price = float(row['price'])
                stock = int(row['stock'])
                tags = row.get('tags', '').split(',') if row.get('tags') else []

                # Créer le produit
                product = Product(
                    name=row['name'],
                    description=row['description'],
                    price=price,
                    stock=stock,
                    category=category,
                    is_active=True,
                    created_by=request.user
                )
                product.save()
                if tags:
                    product.tags.set(tags)
                created_count += 1
            except (ValueError, KeyError) as e:
                errors.append(f"Erreur à la ligne {reader.line_num} : {str(e)}")

        return created_count, errors