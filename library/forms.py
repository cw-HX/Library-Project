from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from . import mongo_models


class RegisterForm(UserCreationForm):
    """Registration form extending Django's UserCreationForm.

    Adds a `role` choice so the UI can offer 'User' or 'Admin'. Note that
    `role` is only a form-level field and not stored on the `User` model
    directly; the view handles mapping the chosen role to `is_staff`.
    """

    ROLE_CHOICES = (
        ('User', 'User'),
        ('Admin', 'Admin'),
    )
    role = forms.ChoiceField(choices=ROLE_CHOICES)

    class Meta:
        model = User
        # 'role' is not a field on the User model; keep it on the form only
        fields = ('username', 'email', 'password1', 'password2')


class BookForm(forms.Form):
    """Form for creating or editing `Book` instances stored in MongoDB.

    This is a plain `forms.Form` (not a ModelForm) because we now use
    MongoEngine documents instead of Django ORM models for the app data.
    """

    title = forms.CharField(max_length=255)
    author = forms.CharField(max_length=255)
    genre = forms.CharField(max_length=100, required=False)
    total_copies = forms.IntegerField(min_value=0, initial=1)

    def save(self, commit=True, instance=None):
        """Create or update a `mongo_models.Book` document.

        If `instance` is provided (a mongo_models.Book), update it;
        otherwise create a new document.
        """
        data = {
            'title': self.cleaned_data['title'],
            'author': self.cleaned_data['author'],
            'genre': self.cleaned_data.get('genre', ''),
            'total_copies': self.cleaned_data['total_copies'],
        }
        if instance is None:
            book = mongo_models.Book(**data)
        else:
            for k, v in data.items():
                setattr(instance, k, v)
            book = instance
        if commit:
            book.save()
        return book
