from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404
from django.views.generic.simple import direct_to_template
from django.views.generic.list_detail import object_detail, object_list
from django.utils.translation import ugettext, ugettext_lazy as _

from models import Message, DraftMessage, MessageBox
from forms import DraftMessageForm, NewMessageForm

paginate_by = 10

def _get_messages(user, manager):
    if manager == 'inbox':
        mgr = user.inbox
    elif manager == 'outbox':
        mgr = user.outbox
    else:
        mgr = user.drafts
    return mgr.all().select_related(depth=1)


@login_required
@transaction.commit_on_success
def new(request, id=''):
    if id:
        draft = get_object_or_404(DraftMessage, pk=id, sender=request.user)
        initial_data = draft.__dict__
    else:
        initial_data = {'recipient_list': request.GET.get(_('recipient'), '')}

    if request.POST:
        if request.POST.has_key('draft'):
            # Save draft
            form = DraftMessageForm(request.POST)
            if form.is_valid():
                if not id:
                    draft = DraftMessage()
                draft.sender = request.user
                draft.recipient_list = form.cleaned_data['recipient_list']
                draft.subject = form.cleaned_data['subject']
                draft.body = form.cleaned_data['body']
                draft.previous_message = form.cleaned_data['previous_message']
                draft.save()
                #TODO Your message was saved
                return HttpResponseRedirect(draft.get_absolute_url())            
        
        else:
            # Send message
            form = NewMessageForm(request.POST)
            if form.is_valid():
                if id:
                    draft.delete()
                message = Message.objects.create(
                                                 subject = form.cleaned_data['subject'],
                                                 body = form.cleaned_data['body'],
                                                 )
                for recipient in form.cleaned_data['recipient_list']:
                    MessageBox.objects.create(
                                              sender = request.user,
                                              recipient = recipient,
                                              message = message,
                                              )
                #TODO Your message was sent to...
                return HttpResponseRedirect(reverse('pm_inbox'))
    else:
        form = DraftMessageForm(initial=initial_data)
    return direct_to_template(request, 'pm/message_form.html', {'form': form})


@login_required
def read(request, id, manager='inbox'):
    
    qs = _get_messages(request.user, manager)
        
    return object_detail(request=request,
                       queryset=qs,
                       object_id=id,
                       template_name='pm/read_%s.html' % manager,
                       )


def delete():
    return

@login_required
def list(request, manager='inbox'):
    
    qs = _get_messages(request.user, manager)
        
    return object_list(request=request,
                       queryset=qs,
                       template_name='pm/list.html',
                       allow_empty=True,
                       paginate_by=paginate_by,
                       extra_context={'title': manager.capitalize(),
                                      'template_row': 'pm/row_%s.html' % manager},
                       )

def contact_list():
    return

def contact_status():
    return



