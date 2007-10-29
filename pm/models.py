from datetime import datetime

from django.db import models
from django.db.models import permalink
from django.db.models.query import QuerySet
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User

from formatters import format_subject, format_body

# TODO: "core" ! Read doc, implement...

class Contact(models.Model):
    """
    A contact list used for recipient auto completion and black listing
    
    """ 
    owner = models.ForeignKey(User, verbose_name=_('owner'), related_name='contacts')
    contact = models.ForeignKey(User, verbose_name=_('contact'), related_name='others_contacts')
    is_blocked = models.BooleanField(_('is blocked'), default=False)

    class Meta:
        verbose_name = _('contact')
        verbose_name_plural = _('contacts')


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
        

class DraftMessage(models.Model):
    """
    Model for drafts
    
    """
    sender = models.ForeignKey(User, verbose_name=_('sender'), related_name='drafts')
    recipient_list = models.TextField(_('recipients'), blank=True, null=True)
    subject = models.CharField(_('subject'), maxlength=80, blank=True, null=True)
    body = models.TextField(_('body'), blank=True, null=True)
    previous_message = models.IntegerField(_('previous message'), blank=True, null=True)
    
    class Meta:
        verbose_name = _('draft')
        verbose_name_plural = _('drafts')
        
    @permalink
    def get_absolute_url(self):
        return ('pm_draft', [str(self.id)])
    

class MessageFilterQuerySet(QuerySet):
    """
    Subclasses the model manager's QuerySet to exclude deleted messages
    
    """
    def _filter_or_exclude(self, mapper, *args, **kwargs):
        if 'sender__pk' in kwargs:
            kwargs['sender_delete_at__isnull'] = True
        if 'recipient__pk' in kwargs:
            kwargs['recipient_delete_at__isnull'] = True
        return super(MessageFilterQuerySet, self)._filter_or_exclude(mapper, *args, **kwargs)


class MessageBoxManager(models.Manager):
    """ 
    Custom manager for the ``MessageBox`` model
    
    """
    def get_query_set(self):
        return MessageFilterQuerySet(self.model)
    
    def unread(self):
        return self.get_query_set().filter(read_at__isnull=True)


class MessageBox(models.Model):
    """
    Model for inbox and outbox
    
    """
    sender = models.ForeignKey(User, verbose_name=_('sender'), related_name='outbox')
    recipient = models.ForeignKey(User, verbose_name=_('recipients'), related_name='inbox')
    message = models.ForeignKey(Message, verbose_name=_('message'), related_name='enveloppes')
    
    # history
    sent_at = models.DateTimeField(_('sent'))
    read_at = models.DateTimeField(_('read'), blank=True, null=True) # first time
    replied_at = models.DateTimeField(_('replied'), blank=True,null=True) # last time
    sender_delete_at = models.DateTimeField(_('deleted by sender'), blank=True,null=True)
    recipient_delete_at = models.DateTimeField(_('deleted by recipient'), blank=True,null=True)
    
    # parent message
    previous_message = models.ForeignKey('self', verbose_name=_('previous message'),
                                         related_name='next_messages', blank=True, null=True)
    
    objects = MessageBoxManager()

    class Meta:
        ordering = ['-id']
        verbose_name = _('message')
        verbose_name_plural = _('messages')
        
    class Admin:
        pass
    
    def __unicode__(self):
        return _("%(sender)s sent message %(id)s to %(recipient)s") % {
                                                               'sender': self.sender,
                                                               'id': self.id,
                                                               'recipient': self.recipient
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
            recipient_contact, c = Contact.objects.get_or_create(owner=self.recipient,
                                                                 contact=self.sender)
            if recipient_contact.is_blocked:
                # if the recipient has blocked the sender in his contacts, delete his message
                self.recipient_delete_at = now
                
            sender_contact, c = Contact.objects.get_or_create(owner=self.sender,
                                                              contact=self.recipient)
            if sender_contact.is_blocked:
                # if the recipient was previously blocked by the sender, unblock him
                sender_contact.is_blocked = False
                sender_contact.save()
                
        super(MessageBox, self).save()        

        
    @permalink
    def get_absolute_url(self):
        return ('pm_received', [str(self.id)])
    
    @permalink
    def get_absolute_url_for_outbox(self):
        return ('pm_sent', [str(self.id)])
    