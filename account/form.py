from django import forms
from django.contrib.auth import get_user_model 
from .models import Profile
from django.contrib.auth.models import User


class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)
    
    
    

class UserRegistrationForm(forms.ModelForm):
    
    password = forms.CharField(label='password' , widget=forms.PasswordInput)
    password2 = forms.CharField(label='confirm password' , widget=forms.PasswordInput)
    
    class Meta:
        model = get_user_model()
        fields = ['username' , 'first_name' ,'email']
        
        
    def clean_password2(self):
        cd = self.cleaned_data
        if cd['password'] != cd['password2']:
            raise forms.ValidationError('passwords do not match')
        return cd['password2']
    
    
    def clean_email(self):
        data = self.cleaned_data['email']
        if User.objects.filter(email=data).exists():
            raise forms.ValidationError('email already exists')
        return data
    
    
class UserEditForm(forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = ['first_name' , 'last_name' , 'email']
        
    def clean_email(self):
        data = self.cleaned_data['email']
        rs = User.objects.exclude(pk=self.instance.pk).filter(email=data)
        if rs.exists():
            raise forms.ValidationError('email already exists')
        return data
        
        
        
class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['date_of_birth' , 'photo']