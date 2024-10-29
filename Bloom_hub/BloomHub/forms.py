from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User

class UserSignupForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput())
    password_confirm = forms.CharField(widget=forms.PasswordInput(), label="Repeat Password")

    class Meta:
        model = User
        fields = ['username', 'password', 'email']  # 'user_id'를 'username'으로 변경
        widgets = {
            'password': forms.PasswordInput(),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")

        # 패스워드 일치 여부 검증
        if password and password_confirm and password != password_confirm:
            raise ValidationError("Passwords do not match.")

        # 비밀번호 강도 검증
        if not any(char.isupper() for char in password) or not any(char in "!@#$%^&*()" for char in password):
            raise ValidationError("Password must contain at least one uppercase letter and one special character.")
        
        # 비밀번호 해시화
        cleaned_data['password'] = make_password(password)

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])  # 비밀번호 설정
        if commit:
            user.save()
        return user
