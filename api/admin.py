from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.core.exceptions import ValidationError

from .models import *


class UserCreationForm(forms.ModelForm):
   password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
   password2 = forms.CharField(label='Password confirmation', widget=forms.PasswordInput)

   class Meta:
       model = User
       fields = ('nickname', 'name')

   def clean_password2(self):
       # Check that the two password entries match
       password1 = self.cleaned_data.get("password1")
       password2 = self.cleaned_data.get("password2")
       if password1 and password2 and password1 != password2:
           raise ValidationError("Passwords don't match")
       return password2

   def save(self, commit=True):
       # Save the provided password in hashed format
       user = super().save(commit=False)
       user.set_password(self.cleaned_data["password1"])
       if commit:
           user.save()
       return user


class UserChangeForm(forms.ModelForm):
   """A form for updating users. Includes all the fields on
   the user, but replaces the password field with admin's
   disabled password hash display field.
   """
   class Meta:
       model = User
       fields = ('nickname', 'password', 'name', 'phoneNumber', 'consultantRegisterStatus', 'is_active', 'is_admin')


class UserAdmin(BaseUserAdmin):
   # The forms to add and change user instances
   form = UserChangeForm
   add_form = UserCreationForm

   # The fields to be used in displaying the User model.
   # These override the definitions on the base UserAdmin
   # that reference specific fields on auth.User.
   list_display = ('nickname', 'id','name', 'consultantRegisterStatus', 'is_admin', 'created_date', 'updated_date')
   list_filter = ('is_admin','consultantRegisterStatus')
   fieldsets = (
       (None, {'fields': ('nickname', 'password')}),
       ('Personal info', {'fields': ('name','phoneNumber')}),
       ('Permissions', {'fields': ('is_admin','consultantRegisterStatus','isConsultant')}),
   )
   # add_fieldsets is not a standard ModelAdmin attribute. UserAdmin
   # overrides get_fieldsets to use this attribute when creating a user.
   add_fieldsets = (
       (None, {
           'classes': ('wide',),
           'fields': ('nickname', 'name', 'password1', 'password2'),
       }),
   )
   search_fields = ('nickname',)
   ordering = ('nickname',)
   filter_horizontal = ()

class PortfolioAdmin(admin.ModelAdmin):
    list_display = ('title', 'id', 'user','created_date', 'updated_date')
    list_filter = ('user',)
    ordering = ('created_date', 'updated_date')
    search_fields = ('title',)


# Now register the new UserAdmin...
admin.site.register(User, UserAdmin)
admin.site.register(Portfolio, PortfolioAdmin)
admin.site.register(Image)
admin.site.register(File)
admin.site.register(Contact)