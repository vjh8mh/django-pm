import re
from datetime import datetime, timedelta

from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from django.core.validators import alnum_re
from django.shortcuts import get_object_or_404
from django.views.generic.simple import direct_to_template
from django.views.generic.list_detail import object_detail, object_list
from django.utils.translation import ugettext, ungettext, ugettext_lazy as _

from models import Contact, Message, DraftMessage, MessageBox
from forms import DraftMessageForm, NewMessageForm

PAGINATE_BY = 2


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

                request.user.message_set.create(message=ugettext('Your message was sent to %s.') % \
                    ', '.join([u.username.capitalize() for u in form.cleaned_data['recipient_list']]))
                
                return HttpResponseRedirect(reverse('pm_inbox'))
    else:
        initial_data = id and draft.__dict__ or {'recipient_list': request.GET.get(ugettext('recipient'), '')}
        form = DraftMessageForm(initial=initial_data)
    return direct_to_template(request, 'pm/form.html', {'form': form})


@login_required
def read(request, id, manager='inbox'):
    "Opens sent and received messages."
    mgr = getattr(request.user, manager)
        
    return object_detail(request=request,
                       queryset=mgr.all().select_related(),
                       object_id=id,
                       template_name='pm/read_%s.html' % manager,
                       )

    
@login_required
def list(request, contact='', manager='inbox'):
    "Lists messages for inbox, outbox and drafts"
    lookup = {}
    if contact:
        key = {'inbox': 'sender__username',
               'outbox': 'recipient__username',
               'drafts': 'recipient_list__icontains'}[manager]
        lookup = {key:contact.lower()}
    mgr = getattr(request.user, manager)
    qs = mgr.filter(**lookup).select_related()
    
    if request.POST:
        # Handle message deletion
        if request.POST.has_key('delete'):
            delete_time = datetime.now()
            messages = mgr.in_bulk(request.POST.getlist('checkbox')).values()
            for message in messages:
                message.delete_flag(request.user, delete_time)
                
            count_deleted = len(messages)
            if count_deleted:
                notice = ungettext('Message deleted.',
                                   '%(count)d messages deleted.', count_deleted) % {'count': count_deleted}
                notice += ' <a href="%s">%s</a>' % (
                                                  reverse('pm_restore', args=[manager, str(delete_time)]),
                                                  ugettext('undo'),
                                                  )
                request.user.message_set.create(message=notice)
                return redirect_list(request, message.id, manager, deleted=True)
            else:
                request.user.message_set.create(message=ugettext('No messages deleted.'))
        
        # Handle contact filter
        if alnum_re.search(request.POST.get('contact', '')):
            return HttpResponseRedirect(reverse('pm_%s_contact' % manager, args=[request.POST['contact'].lower()]))
    
    return object_list(request=request,
                       queryset=qs,
                       template_name='pm/list_%s.html' % manager,
                       allow_empty=True,
                       paginate_by=PAGINATE_BY,
                       extra_context={'contact': contact}
                       )


@login_required
@transaction.commit_on_success
def restore(request, manager, time):
    "Restores freshly deleted messages."
    max_restore_time = 15 # minutes
    
    # Parse deletion time
    m = re.search(r'(\d+)-(\d+)-(\d+) (\d+):(\d+):(\d+).(\d+)', time)
    args = []
    for i in range(1,8):
        args.append(int(m.group(i)))
    time_delete = datetime(*args)

    if datetime.now() - time_delete < timedelta(0, 60 * max_restore_time):
        Box = manager == 'drafts' and DraftMessage or MessageBox
        lookup = manager == 'inbox' and {'recipient_delete_at': time_delete} or {'sender_delete_at': time_delete}
        messages = Box.objects.filter(**lookup)
        count_restored = 0
        for message in messages:
            count_restored += message.delete_flag(request.user, None) and 1 or 0
        if count_restored:
            notice = ungettext('Message restored.',
                               '%(count)d messages restored.', count_restored) % {'count': count_restored}
        else:
            notice = ugettext('No messages restored.')
    else:
        notice = ugettext('You cannot restore messages deleted more than %d minutes ago.') % max_restore_time
    request.user.message_set.create(message=notice)
    
    return redirect_list(request, message.id, manager)


@login_required
def delete(request, id, manager='inbox'):
    "Deletes a single message."
    mgr = getattr(request.user, manager)    
    message = get_object_or_404(mgr.all(), id=id)
    
    delete_time = datetime.now()
    message.delete_flag(request.user, delete_time)
    
    notice = ugettext('Message deleted.')
    notice += ' <a href="%s">%s</a>' % (
                                        reverse('pm_restore', args=[manager, str(delete_time)]),
                                        ugettext('undo'),
                                        )
    request.user.message_set.create(message=notice)
    
    return redirect(request, id, '', manager)


@login_required
def redirect(request, id, direction='', manager='inbox'):
    "Redirects to a message according to filters or return to messagebox."
    
    mgr = getattr(request.user, manager)
    qs = mgr.filter(**{'pk__%s' % (direction and 'gt' or 'lt'): id})
    if direction:
        qs = qs.order_by('id')
    
    try:
        message = qs[0]
    except IndexError:
        page = ''
        if direction:
            # back to first page
            notice = ugettext('No more messages, you are back on the first page.')
        else:
            # last page
            p_num = (mgr.all().count() / PAGINATE_BY) + 1
            if p_num == 1:
                notice = ugettext('No more messages, you are back on the first page.')
            else:
                page = '?page=%s' % str(p_num)
                notice = ugettext('No more messages, you are back on the last page.')
            
        request.user.message_set.create(message=notice)
            
        return HttpResponseRedirect('%s%s' % (reverse('pm_%s' % manager), page))
    
    return HttpResponseRedirect(reverse('pm_%s_read' % manager, args=[str(message.id)]))


@login_required
def redirect_list(request, id, manager='inbox', deleted=False):
    "Redirects to the page where the message is listed or the previous page if it was deleted."
    
    mgr = getattr(request.user, manager)
    count_messages = mgr.filter(pk__gt=id).count()

    p_num = (count_messages / PAGINATE_BY) + 1
    if deleted and p_num > 1 and not count_messages % PAGINATE_BY:
        p_num -= 1
        
    return HttpResponseRedirect('%s%s' % (
                                          reverse('pm_%s' % manager),
                                          p_num != 1 and '?page=%d' % p_num or ''
                                          ))
    

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
        notice = ugettext('%(user)s was removed from your contact list%(blocked)s.') % {
                          'user': contact_username,
                          'blocked': contact.is_blocked and ugettext(' and unblocked') or '',
                          }
        contact.delete()
    else:
        if action == 'block':
            contact.is_blocked = True
            notice = ugettext('%s cannot contact you anymore.') % contact_username
            notice += ' <a href="%s">%s</a>' % (
                                        reverse('pm_contact_unblock', args=[contact.contact.username]),
                                        ugettext('undo'),
                                        )          
        else:
            contact.is_blocked = False
            notice = ugettext('%s is now allowed to contact you.') % contact_username
            notice += ' <a href="%s">%s</a>' % (
                                        reverse('pm_contact_block', args=[contact.contact.username]),
                                        ugettext('undo'),
                                        )     
        contact.save()
        
    request.user.message_set.create(message=notice)
    
    return HttpResponseRedirect(reverse('pm_contact'))




