from django.conf.urls.defaults import *
from django.utils.translation import ugettext as _

urlpatterns = patterns('pm.views',
   url(r'^%s$' % _('new/'), 'new', name='pm_new'),
   url(r'^%s(\d+)/$' % _('new/'), 'new', name='pm_draft'),
   
   url(r'^%s$' % _('inbox/'), 'list', name='pm_inbox'),
   url(r'^%s$' % _('outbox/'), 'list', {'manager': 'outbox'}, name='pm_outbox'),
   url(r'^%s$' % _('drafts/'), 'list', {'manager': 'drafts'}, name='pm_drafts'),
   
   url(r'^%s%s(\w+)/$' % (_('inbox/'), _('contact/')), 'list', name='pm_inbox_contact'),
   url(r'^%s%s(\w+)/$' % (_('outbox/'), _('contact/')), 'list', {'manager': 'outbox'}, name='pm_outbox_contact'),
   url(r'^%s%s(\w+)/$' % (_('drafts/'), _('contact/')), 'list', {'manager': 'drafts'}, name='pm_drafts_contact'),

   url(r'^%s(\d+)/$' % _('inbox/'), 'read', name='pm_inbox_read'),
   url(r'^%s(\d+)/$' % _('outbox/'), 'read', {'manager': 'outbox'}, name='pm_outbox_read'),
   
   url(r'^%s(\d+)/%s(%s|)$' % (_('inbox/'), _('redirect/'), _('up/')), 'redirect', name='pm_inbox_redirect'),
   url(r'^%s(\d+)/%s(%s|)$' % (_('outbox/'), _('redirect/'), _('up/')), 'redirect', {'manager': 'outbox'}, name='pm_outbox_redirect'),
   
   url(r'^%s(\d+)/%s$' % (_('inbox/'), _('list/')), 'redirect_list', name='pm_inbox_redirect_list'),
   url(r'^%s(\d+)/%s$' % (_('outbox/'), _('list/')), 'redirect_list', {'manager': 'outbox'}, name='pm_outbox_redirect_list'),
   
   url(r'^%s(\d+)/%s$' % (_('inbox/'), _('delete/')), 'delete', name='pm_inbox_delete'),
   url(r'^%s(\d+)/%s$' % (_('outbox/'), _('delete/')), 'delete', {'manager': 'outbox'}, name='pm_outbox_delete'),
   url(r'^%s(\d+)/%s$' % (_('drafts/'), _('delete/')), 'delete', {'manager': 'drafts'}, name='pm_drafts_delete'),
   
   url(r'^%s(\w+)/([\d\- :.]+)/$' % _('restore/'), 'restore', name='pm_restore'),
   
   url(r'^%s$' % _('contact/'), 'list_contact', name='pm_contact'),
   url(r'^%s$' % _('blocked/'), 'list_contact', {'list': 'blocked'},name='pm_blocked'),

   url(r'^%s(\w+)/%s$' % (_('contact/'), _('block/')), 'edit_contact', name='pm_contact_block'),
   url(r'^%s(\w+)/%s$' % (_('contact/'), _('unblock/')), 'edit_contact', {'action': 'unblock'}, name='pm_contact_unblock'),
   url(r'^%s(\w+)/%s$' % (_('contact/'), _('delete/')), 'edit_contact', {'action': 'delete'}, name='pm_contact_delete'),

)
