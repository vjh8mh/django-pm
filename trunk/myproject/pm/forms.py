# -*- coding: utf-8 -*-
import re

from django import newforms as forms
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext, ugettext_lazy as _

from models import MessageBox
from formatters import format_subject, format_body

recipients_re = re.compile(r'[^\w]*(\w+)[^\w]*')

class DraftMessageForm(forms.Form):
    recipient_list = forms.CharField(
                      label=_('Recipients'),
                      required=False,
                      help_text=_('Separate multiple recipients with comas.'),
                      widget=forms.widgets.Textarea(attrs={'rows':2, 'cols':50})
                      )
    subject = forms.CharField(
                      label=_('Subject'),
                      required=False,
                      max_length=80
                      )
    body = forms.CharField(
                      label=_('Message'),
                      required=False,
                      widget=forms.widgets.Textarea(attrs={'rows':8, 'cols':50})
                      )
    previous_message = forms.IntegerField(
                      required=False,
                      widget=forms.widgets.HiddenInput()
                      )
    redirect = forms.CharField(
                      required=False,
                      widget=forms.widgets.HiddenInput()
                      )
            
class ReplyMessageForm(DraftMessageForm):
    def __init__(self, **kwargs):
        super(ReplyMessageForm, self).__init__(**kwargs)
        self.fields['subject'].widget.attrs.update({'disabled': 'disabled'})
        self.fields['recipient_list'].widget = forms.widgets.HiddenInput()
        


class NewMessageForm(DraftMessageForm):
    
    def clean_recipient_list(self):
        "Returns a set of valid User instances."
        rcpt_list = self.cleaned_data['recipient_list']
        
        if not rcpt_list:
            raise forms.ValidationError(self.fields['recipient_list'].error_messages['required'])
        
        self.valid_recipients = {}
        recipients_re.sub(self._validate_user, rcpt_list)
        
        if len(self.valid_recipients) == 0:
            raise forms.ValidationError(ugettext("Couldn't find any of your recipients."))
        return self.valid_recipients.values()

    def _validate_user(self, m):
        try:
            user = User.objects.get(username=m.group(1))
        except User.DoesNotExist:
            try:
                user = User.objects.get(username__iexact=m.group(1))
            except AssertionError, User.DoesNotExist:
                return
        self.valid_recipients[user.id] = user
        
    def clean_subject(self):
        return format_subject(self.cleaned_data['subject'])
        
    def clean_body(self):
        body = format_body(self.cleaned_data['body'])
        if not body:
            raise forms.ValidationError(self.fields['body'].error_messages['required'])
        return body 
        
    def clean_previous_message(self):
        previous_message = None
        if self.cleaned_data['previous_message']:
            try:
                previous_message = MessageBox.objects.get(pk=self.cleaned_data['previous_message'])
            except MessageBox.DoesNotExist:
                pass
        return previous_message
    
    def clean_redirect(self):
        redirect = self.cleaned_data['redirect']
        if not redirect:
            redirect = reverse('pm_inbox')
        return redirect

        
        
