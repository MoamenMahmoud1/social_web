from django import forms
from django.core.files.base import ContentFile
from django.utils.text import slugify
import requests

from .models import Image


class ImageCreateForm(forms.ModelForm):

    class Meta:
        model = Image
        fields = ['title', 'url', 'description']
        widgets = {
            'url': forms.HiddenInput,
        }

    def clean_url(self):
        url = self.cleaned_data['url']

        try:
            # نعمل طلب سريع للهيدر
            response = requests.head(url, timeout=5)
        except requests.exceptions.RequestException:
            raise forms.ValidationError("Could not reach the given URL.")

        # نتأكد إن السيرفر بيرجع صورة
        content_type = response.headers.get('Content-Type', '')
        if not content_type.startswith('image/'):
            raise forms.ValidationError("The URL does not point to a valid image.")

        return url

    def save(self, force_insert=False, force_update=False, commit=True):
        image = super().save(commit=False)

        image_url = self.cleaned_data['url']
        name = slugify(image.title)

        # نزّل الصورة فعليًا
        response = requests.get(image_url, timeout=10)

        # حدد الامتداد من Content-Type
        content_type = response.headers.get('Content-Type', '').lower()
        if 'jpeg' in content_type:
            extension = 'jpg'
        elif 'png' in content_type:
            extension = 'png'
        elif 'gif' in content_type:
            extension = 'gif'
        else:
            extension = 'jpg'  # fallback افتراضي

        image_name = f'{name}.{extension}'

        # خزّن الصورة
        image.image.save(
            image_name,
            ContentFile(response.content),
            save=False
        )

        if commit:
            image.save()
        return image
