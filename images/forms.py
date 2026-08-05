from django import forms
from .services import download_safe_image
from django.utils.text import slugify


from .models import Image


class ImageCreateForm(forms.ModelForm):

    class Meta:
        model = Image
        fields = ['title', 'url', 'description']
        widgets = {
            'url': forms.HiddenInput,
        }

    

    def save(self, commit=True):
        image = super().save(commit=False)
    
        image_file, extension = download_safe_image(
            self.cleaned_data["url"]
        )
    
        filename = (
            f"{slugify(image.title) or 'image'}"
            f"{extension}"
        )
    
        image.image.save(
            filename,
            image_file,
            save=False,
        )
    
        if commit:
            image.save()
    
        return image