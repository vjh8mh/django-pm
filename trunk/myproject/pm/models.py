# -*- coding: utf-8 -*-
from datetime import datetime

from django.db import models
from django.db.models import permalink
from django.utils.translation import ugettext_lazy as _
from django.utils.timesince import timesince
from django.contrib.auth.models import User
from django.db.models.query import QuerySet
from django.core.urlresolvers import reverse

from formatters import format_subject, format_body

PAGINATE_BY = 4
        
    
class Contact(models.Model):
    """
    A contact list used for recipient auto completion and black listing
    
    """ 
    owner = models.ForeignKey(User, verbose_name=_('owner'), related_name='contacts')
    contact = models.ForeignKey(User, verbose_name=_('contact'), related_name='others_contacts')
    is_blocked = models.BooleanField(_('is blocked'), default=False)
    created_at = models.DateTimeField(_('created at'), blank=True,null=True)
    last_message_at = models.DateTimeField(_('last message at'), blank=True,null=True)
    
    def get_block_link_tuple(self):
        "Returns url and text to display the 'block user' link"
        if self.is_blocked:
            view_name = 'pm_contact_unblock'
            text = _('unblock %(username)s') % {'username': self.contact.username.capitalize()}
        else:
            view_name = 'pm_contact_block'
            text = _('block %(username)s') % {'username': self.contact.username.capitalize()}
        return [(reverse(view_name, args=[self.contact.username]), text)]
        
    class Meta:
        ordering = ['-last_message_at']
        verbose_name = _('contact')
        verbose_name_plural = _('contacts')

    class Admin:
        pass
    
    def __unicode__(self):
        return self.contact.username.capitalize()
    
    def save(self):
        if not self.created_at:
            self.created_at = datetime.now()
        super(Contact, self).save()


class Message(models.Model):
    """
    The content of a message
    
    """
    subject = models.CharField(_('subject'), maxlength=80)
    body = models.TextField(_('body'))
    
    class Meta:
        verbose_name = _('message content')
        verbose_name_plural = _('message contents')
    
    class Admin:
        pass
    
    def __unicode__(self):
        return self.subject or format_subject(self.body, from_body=True) 
    
    def save(self):
        "This method is overridden to clean data."
        if self.subject:
            self.subject = format_subject(self.subject)
        self.body = format_body(self.body)
        super(Message, self).save()



class HideDeletedQuerySet(QuerySet):
    """
    Subclasses the model manager's QuerySet to exclude deleted messages
    
    """
    def _filter_or_exclude(self, mapper, *args, **kwargs):
        if 'sender__pk' in kwargs:
            kwargs['sender_delete_at__isnull'] = True
        if 'recipient__pk' in kwargs:
            kwargs['recipient_delete_at__isnull'] = True
        return super(HideDeletedQuerySet, self)._filter_or_exclude(mapper, *args, **kwargs)


class BoxManager(models.Manager):
    """ 
    Custom manager for the ``DraftMessage`` and ``MessageBox`` model
    
    """
    
    def get_accessor_name(self):
        "Returns the messagebox related manager name"
        if not hasattr(self, 'core_filters'):
            raise AttributeError, _("Method is only accessible through RelatedManager instances")
        if self.core_filters.has_key('recipient__pk'):
            return 'inbox'
        elif self.core_filters.has_key('sender__pk'):
            if self.model == MessageBox:
                return 'outbox'
            else:
                return 'drafts'
        elif self.core_filters.has_key('previous_message__pk'):
            return 'next_messages'
        raise AttributeError, _("Method not available for this RelatedManager")
    
    def get_query_set(self):
        "Filters queryset if accessed through a RelatedManager"
        try:
            # Check related manager access
            self.get_accessor_name()
            return HideDeletedQuerySet(self.model)
        except AttributeError:
            return QuerySet(self.model)

    def filter_username(self, username=''):
        "Adds a filter for a specific user"
        if username:
            manager = self.get_accessor_name()
            if manager == 'inbox':
                key = 'sender__username'
            elif manager == 'outbox':
                key = 'recipient__username'
            else:
                key = 'recipient_list__icontains'
            self.core_filters.update({key: username})

    def _isnull_filter(self, manager, field):
        "Returns a query set with a field__isnull filter"
        if self.get_accessor_name() != manager:
            raise AttributeError, _("Method only available for the %s RelatedManager") % manager
        self.core_filters['%s__isnull' % field] = True
        return self.get_query_set()
        
    def for_read_outbox_view(self):
        "Filters deleted messages for the next_messages related manager in read_outbox.html"
        return self._isnull_filter('next_messages', 'recipient_delete_at')
    
    def for_read_inbox_view(self):
        "Filters deleted messages for the next_messages related manager in read_inbox.html"
        return self._isnull_filter('next_messages', 'sender_delete_at')
    
    def new(self):
        "Returns new messages for the inbox"
        return self._isnull_filter('inbox', 'read_at')
        
    def restore_deleted_messages(self, time_delete, user):
        # Bypass deleted messages filtering
        role = self.get_accessor_name() == 'inbox' and 'recipient' or 'sender'
        lookup = {'%s_delete_at' % role: time_delete}
        lookup.update(self.core_filters)
        qs = QuerySet(self.model).filter(**lookup)
        
        count_restore = qs.count()
        if count_restore:
            for message in qs:
                message.set_delete_flag(user, None)
            first_restore = qs[0]
        else:
            first_restore = None

        return first_restore, count_restore
    
    def get_page(self, id):
        "Returns the page number where the message is listed"
        if isinstance(id, self.model):
            id = id.id
            
        count_before = self.filter(pk__gt=id).count()

        if count_before:
            pos_on_page = count_before % PAGINATE_BY or PAGINATE_BY
            page = count_before / PAGINATE_BY
            if pos_on_page != PAGINATE_BY:
                page += 1
        else:
            #no message before
            pos_on_page = 0
            page = 1
        # correct page number for tail messages
        if pos_on_page == PAGINATE_BY and self.filter(pk__lte=id).count():
            page += 1
        
        return page
    
    def get_redirect_detail(self, id, contact, up):
        "Returns a redirect URL for the previous or next message if there is one"
        qs = self.filter(**{'pk__%s' % (up and 'gt' or 'lt'): id})
        if up:
            qs = qs.order_by('id')
            
        try:
            message = qs[0]
            return reverse('pm_%s_read' % self.get_accessor_name(), args=[str(message.id)]), None
        except IndexError:
            page = ''
            if up:
                # back to first page
                page_num = 1
            else:
                # back to last page
                page_num = self.get_page(id)
                if page_num > 1:
                    page = '?page=%d' % page_num
                    
            view = 'pm_%s' % self.get_accessor_name()
            args = []
            if contact:
                view = '%s_contact' % view
                args=[contact]
            return '%s%s' % (reverse(view, args=args), page), page_num
    
    def get_redirect_list(self, id, contact):
        "Returns a redirect URL for the page a message is listed on"
        if contact:
            reverse_url = reverse('pm_%s_contact' % self.get_accessor_name(), args=[contact])
        else:
            reverse_url = reverse('pm_%s' % self.get_accessor_name())
        page = self.get_page(id)
        if page > 1:
            reverse_url = '%s?page=%d' % (reverse_url, page)
        return reverse_url

     
class DraftMessage(models.Model):
    """
    Model for drafts
    
    """
    sender = models.ForeignKey(User, verbose_name=_('sender'), related_name='drafts')
    recipient_list = models.TextField(_('recipients'), blank=True, null=True)
    subject = models.CharField(_('subject'), maxlength=80, blank=True, null=True)
    body = models.TextField(_('body'), blank=True, null=True)
    previous_message = models.IntegerField(_('previous message'), blank=True, null=True)
    sender_delete_at = models.DateTimeField(_('deleted by sender'), blank=True,null=True)
    
    objects = BoxManager()

    def set_delete_flag(self, user, flag):
        if self.sender == user:
            self.sender_delete_at = flag
            self.save()
            return True
        
    class Meta:
        ordering = ['-id']
        verbose_name = _('draft')
        verbose_name_plural = _('drafts')
        
    @permalink
    def get_absolute_url(self):
        return ('pm_drafts_read', [str(self.id)])


class MessageBox(models.Model):
    """
    Model for inbox and outbox
    
    """
    sender = models.ForeignKey(User, verbose_name=_('sender'), related_name='outbox')
    recipient = models.ForeignKey(User, verbose_name=_('recipients'), related_name='inbox')
    message = models.ForeignKey(Message, verbose_name=_('message'), related_name='enveloppes')
    
    # status
    sent_at = models.DateTimeField(_('sent'))
    read_at = models.DateTimeField(_('read'), blank=True, null=True) # first time
    replied_at = models.DateTimeField(_('replied'), blank=True,null=True) # last time
    sender_delete_at = models.DateTimeField(_('deleted by sender'), blank=True,null=True)
    recipient_delete_at = models.DateTimeField(_('deleted by recipient'), blank=True,null=True)
    
    # parent message
    previous_message = models.ForeignKey('self', verbose_name=_('previous message'),
                                         related_name='next_messages', blank=True, null=True)
    
    objects = BoxManager()

    # inbox status
    @property
    def status(self):
        if self.read_at:
            return self.replied_at and 'replied' or 'read'
        else:
            return 'new'

    @property
    def sent_at_since(self):
        return timesince(self.sent_at).split(',', 1)[0]
    
    def set_delete_flag(self, user, flag):
        change = False
        if self.sender == user:
            self.sender_delete_at = flag
            change = True
        if self.recipient == user:
            self.recipient_delete_at = flag
            change = True
        if change:
            self.save()
        return change
        
    def get_contact(self, user):
        "Returns a contact instance for your correspondent"
        if user == self.sender and user != self.recipient:
            contact_user = self.recipient
        elif user == self.recipient and user != self.sender:
            contact_user = self.sender
        else:
            return None
        return Contact.objects.get_or_create(owner=user, contact=contact_user)[0]
    
    def set_previous_message(self, user):
        "Removes the previous message if it was deleted by the user"
        if self.previous_message:
            if user == self.sender and self.sender_delete_at or \
               user == self.recipient and self.recipient_delete_at:
                self.previous_message = None
            
    class Meta:
        ordering = ['-id']
        verbose_name = _('message')
        verbose_name_plural = _('messages')
        
    class Admin:
        pass
    
    def __unicode__(self):
        return _(u"%(sender)s sent message %(id)s to %(recipient)s") % {
                                                               'sender': self.sender.username,
                                                               'id': self.id,
                                                               'recipient': self.recipient.username
                                                               }

    def save(self):
        if not self.id:
            self.sent_at = datetime.now()
            
            # Check and edit previous message with reply time
            if self.previous_message:
                if self.previous_message.recipient == self.sender and \
                            self.previous_message.sender == self.recipient :
                    self.previous_message.replied_at = self.sent_at
                    self.previous_message.save()
                else:
                    self.previous_message = None
                
            # Check or create contact info
            recipient_contact = self.get_contact(self.recipient)
            if recipient_contact and recipient_contact.is_blocked:
                # if the recipient has blocked the sender in his contacts, delete his message
                self.recipient_delete_at = self.sent_at
                
            sender_contact = self.get_contact(self.sender)
            if sender_contact:
                sender_contact.last_message_at = self.sent_at
                # if the recipient was previously blocked by the sender, unblock him
                sender_contact.is_blocked = False
                sender_contact.save()
                
        super(MessageBox, self).save()

        
    @permalink
    def get_absolute_url(self):
        return ('pm_inbox_read', [str(self.id)])
    
    @permalink
    def get_absolute_url_for_outbox(self):
        return ('pm_outbox_read', [str(self.id)])
    
