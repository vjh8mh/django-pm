# -*- coding: utf-8 -*-
import re
from datetime import datetime, timedelta
from time import strptime, mktime

from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.core.urlresolvers import reverse
from django.core.validators import alnum_re
from django.shortcuts import get_object_or_404
from django.views.generic.simple import direct_to_template
from django.views.generic.list_detail import object_detail, object_list
from django.utils.translation import ungettext, ugettext as _

from models import Contact, Message, DraftMessage, MessageBox, PAGINATE_BY
from forms import DraftMessageForm, ReplyMessageForm, NewMessageForm

from notification import notification

@login_required
@transaction.commit_on_success
def new(request, id=''):
    "Displays a form to compose a new message or edit a draft."

    draft = id and get_object_or_404(request.user.drafts, pk=id) or DraftMessage()

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

                notification(request, _('Your draft was saved.'))
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
                                              previous_message = form.cleaned_data['previous_message'],
                                              )
                notification(request, _('Your message was sent to %s.') % \
                    ', '.join([u.username.capitalize() for u in form.cleaned_data['recipient_list']]))
                
                return HttpResponseRedirect(form.cleaned_data['redirect'])
    else:
        initial_data = id and draft.__dict__ or {'recipient_list': request.GET.get(_('recipient'), '')}
        form = DraftMessageForm(initial=initial_data)
    return direct_to_template(request, 'pm/form.html', {'form': form})

@login_required
def forward(request, id, manager='inbox'):
    "Displays a new message form with the forward message data"
    mgr = getattr(request.user, manager)
    m = get_object_or_404(mgr, pk=id)
    form = DraftMessageForm(initial={
             'subject': '%s%s' % (m.message.subject[:4] != 'Fw: ' and 'Fw: ' or '', m.message.subject),
             'body': m.message.body,
             'redirect': reverse('pm_%s_read' % manager, args=[m.id])
             })
    post_to = reverse('pm_new')
    return direct_to_template(request, 'pm/form.html', {'form': form, 'post_to': post_to})
    
@login_required
def read(request, id, manager='inbox'):
    "Opens sent and received messages."
    mgr = getattr(request.user, manager)
    m = get_object_or_404(mgr.select_related(), id=id)
    
    contact = m.get_contact(request.user)
    
    # mark as read
    if not m.read_at and m.recipient == request.user:
        m.read_at = datetime.now()
        m.save()

    # Remove the previous message if it was deleted by the user
    m.set_previous_message(request.user)
        
    # fetch reply history
    replies = getattr(m.next_messages, 'for_read_%s_view' % manager)
    
    # Reply form for inbox
    if manager == 'inbox':
        form = ReplyMessageForm(initial={
             'recipient_list': m.sender.username,
             'subject': '%s%s' % (m.message.subject[:4] != 'Re: ' and 'Re: ' or '', m.message.subject),
             'previous_message': m.id,
             'redirect': reverse('pm_inbox_read', args=[m.id])
             })
    else:
        form = None
    
    return direct_to_template(request,
                              'pm/read_%s.html' % manager,
                              {'object': m,
                               'contact': contact,
                               'form': form,
                               'replies': replies,
                               })


@login_required
@transaction.commit_on_success
def list(request, contact='', manager='inbox'):
    "Lists messages for inbox, outbox and drafts"
    
    mgr = getattr(request.user, manager)
    mgr.filter_username(contact)
    qs = mgr.all().select_related()
    
    if request.POST:
        # Handle message deletion
        if request.POST.has_key('delete'):
            delete_time = datetime.now()
            messages = mgr.in_bulk(request.POST.getlist('checkbox')).values()
            for message in messages:
                message.set_delete_flag(request.user, delete_time)
                
            count_deleted = len(messages)
            if count_deleted:
                view = '%s/list%s%s/' % ( manager, contact and '/' or '', contact )
                timestamp = mktime(delete_time.timetuple()) + delete_time.microsecond / 1e6
                notification(request,
                       ungettext('Message deleted.',
                                   '%(count)d messages deleted.', count_deleted) % {'count': count_deleted},
                       template = 'notice_link',
                       link_url = reverse('pm_restore', args=['%f' % timestamp, view]),
                       link_text = _('undo'),
                       )
                return HttpResponseRedirect(mgr.get_redirect_list(message.id, contact))
            else:
                notification(request,_('No messages deleted.'))
        
        # Handle contact filter
        if alnum_re.search(request.POST.get('contact', '')):
            return HttpResponseRedirect(reverse('pm_%s_contact' % manager, args=[request.POST['contact']]))
    
    return object_list(request=request,
                       queryset=qs,
                       template_name='pm/list_%s.html' % manager,
                       allow_empty=True,
                       paginate_by=PAGINATE_BY,
                       extra_context={'contact': contact}
                       )


@login_required
def delete(request, id, manager='inbox', delete_time=datetime.now()):
    "Deletes a single message."
    mgr = getattr(request.user, manager)    
    message = get_object_or_404(mgr.all(), id=id)
    
    if message.set_delete_flag(request.user, delete_time):
        view = '%s/detail/' % manager
        timestamp = mktime(delete_time.timetuple()) + delete_time.microsecond / 1e6
        notification(request,
               _('Message deleted.'),
               template = 'notice_link',
               link_url = reverse('pm_restore', args=['%f' % timestamp, view]),
               link_text = _('undo'),
               )
    else:
        notification(request, _('No messages deleted.'))

    return redirect(request, id, '', manager)


@login_required
@transaction.commit_on_success
def restore(request, timestamp, view):
    "Restores freshly deleted messages."
    MAX_RESTORE_TIME = 15 # minutes
    
    # Parse deletion time
    time_delete = datetime.fromtimestamp(float(timestamp))
    
    # Parse manager info
    manager, view, contact = view.split('/')[:3]
    
    # Allow restoration
    if datetime.now() - time_delete < timedelta(0, 60 * MAX_RESTORE_TIME):
        
        mgr = getattr(request.user, manager)
        message, count_restored = mgr.restore_deleted_messages(time_delete, request.user)
        
        if count_restored:
            notice_message = ungettext('Message restored.',
                               '%(count)d messages restored.', count_restored) % {'count': count_restored}
        else:
            notice_message = _('No messages restored.')      
    else:
        count_restored = 0
        notice_message = _('You cannot restore messages deleted more than %d minutes ago.') % MAX_RESTORE_TIME
    
    notification(request, notice_message)
    
    if count_restored == 0:
        return HttpResponseRedirect(reverse('pm_%s' % manager))
    
    # Construct redirect url with the correct page if we have a list
    if view == 'detail':
        return HttpResponseRedirect(reverse('pm_%s_read' % manager, args=[message.id]))
    else:
        if contact:
            mgr.filter_username(contact)
        return HttpResponseRedirect(mgr.get_redirect_list(message.id, contact))
        


@login_required
def redirect(request, id, contact='', up=False, manager='inbox'):
    "Redirects to a message according to filters or return to messagebox."
    
    mgr = getattr(request.user, manager)
    if contact:
        mgr.filter_username(contact)
    redirect_url, page = mgr.get_redirect_detail(id, contact, up)
    
    if page:
        notice_message = page > 1 and _('No more messages, you are back on the last page.')\
                          or _('No more messages, you are back on the first page.')
        notification(request, notice_message)
      
    return HttpResponseRedirect(redirect_url)


@login_required
def redirect_list(request, id, contact='', manager='inbox'):
    "Redirects to the page where the message is listed or the previous page if it was deleted"
    
    mgr = getattr(request.user, manager)
    if contact:
        mgr.filter_username(contact)
    
    return HttpResponseRedirect(mgr.get_redirect_list(id, contact))
    

@login_required
def list_contact(request, list='contact'):
    
    qs = request.user.contacts.filter(is_blocked=list=='blocked').exclude(contact=request.user)
    
#    # If you prefer to order alphabetically
#    qs = request.user.contacts.filter(is_blocked=list=='blocked').exclude(contact=request.user).extra(
#         select={'username':'SELECT username FROM auth_user WHERE auth_user.id = pm_contact.contact_id'}
#         ).order_by('username')
        
    return object_list(request=request,
                       queryset=qs,
                       template_name='pm/list_%s.html' % list,
                       allow_empty=True,
                       paginate_by=PAGINATE_BY,
                       )

@login_required 
def edit_contact(request, username, action='block'):
    
    contact = get_object_or_404(request.user.contacts.exclude(contact=request.user), contact__username=username)
    contact_username = contact.contact.username.capitalize()

    if action == 'delete':
        notification(request, _('%(user)s was removed from your contact list%(blocked)s.') % {
                          'user': contact_username,
                          'blocked': contact.is_blocked and _(' and unblocked') or '',
                          }
              )
        contact.delete()
    else:
        if action == 'block':
            contact.is_blocked = True
            notice_message = _('%s cannot contact you anymore.') % contact_username
            link_url = reverse('pm_contact_unblock', args=[contact.contact.username])         
        else:
            contact.is_blocked = False
            notice_message = _('%s is now allowed to contact you.') % contact_username
            link_url = reverse('pm_contact_block', args=[contact.contact.username])    
        contact.save()
        
    notification(request,
           notice_message,
           template = 'notice_link',
           link_url = link_url,
           link_text = _('undo'),
           )
    
    return HttpResponseRedirect(reverse('pm_contact'))




