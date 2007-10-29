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

PAGINATE_BY = 5


@login_required
@transaction.commit_on_success
def new(request, id=''):
    "Displays a form to compose a new message or edit a draft."

    draft = id and get_object_or_404(DraftMessage, pk=id, sender=request.user) or DraftMessage()

    if request.POST:
        if request.POST.has_key('draft'):
            # Save draft
            form = DraftMessageForm(request.POST)
            if form.is_valid():
                draft.sender = request.user
                draft.recipient_list = form.cleaned_data['recipient_list']
                draft.subject = form.cleaned_data['subject']
                draft.body = form.cleaned_data['body']
                draft.previous_message = form.cleaned_data['previous_message']
                draft.save()

                request.user.message_set.create(message=ugettext('Your draft was saved.'))
                
                return HttpResponseRedirect(draft.get_absolute_url())            
        
        else:
            # Send message
            form = NewMessageForm(request.POST)
            if form.is_valid():
                id and draft.delete()
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

                request.user.message_set.create(message=ugettext('Your message was sent to %s.' % \
                    ', '.join([u.username.capitalize() for u in form.cleaned_data['recipient_list']])))
                
                return HttpResponseRedirect(reverse('pm_inbox'))
    else:
        initial_data = id and draft.__dict__ or {'recipient_list': request.GET.get(_('recipient'), '')}
        form = DraftMessageForm(initial=initial_data)
    return direct_to_template(request, 'pm/form.html', {'form': form})



def _get_messages(user, manager, filters={}):
    "Returns a queryset corresponding to a messagebox."
    try:
        mgr = getattr(user, manager)
    except AttributeError:
        mgr = user.inbox
    return mgr.all().select_related(depth=1).filter(**filters)


@login_required
def read(request, id, manager='inbox'):
    "Opens sent and received messages."
    qs = _get_messages(request.user, manager)
        
    return object_detail(request=request,
                       queryset=qs,
                       object_id=id,
                       template_name='pm/read_%s.html' % manager,
                       )


@login_required
def list(request, manager='inbox'):
    "Lists messages for inbox, outbox and drafts"
   
    qs = _get_messages(request.user, manager)
    # TODO: add filtering and ordering logic in request.GET        
    
    return object_list(request=request,
                       queryset=qs,
                       template_name='pm/list_%s.html' % manager,
                       allow_empty=True,
                       paginate_by=PAGINATE_BY,
                       )


def delete(request):
    "Deletes messages."
    return


def redirect(request):
    "Redirects to a message according to filters or return to messagebox"
    return HttpResponseRedirect()


def contact_list():
    return


def contact_status():
    return




