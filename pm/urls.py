from django.conf.urls.defaults import *
from django.utils.translation import ugettext as _

urlpatterns = patterns('pm.views',
   url(r'^%s$' % _('new/'), 'new', name='pm_new'),
   url(r'^%s(\d+)/$' % _('new/'), 'new', name='pm_draft'),
   
   url(r'^%s$' % _('inbox/'), 'list', name='pm_inbox'),
   url(r'^%s$' % _('outbox/'), 'list', {'manager': 'outbox'}, name='pm_outbox'),
   url(r'^%s$' % _('drafts/'), 'list', {'manager': 'drafts'}, name='pm_drafts'),

   url(r'^%s(\d+)/$' % _('inbox/'), 'read', name='pm_received'),
   url(r'^%s(\d+)/$' % _('outbox/'), 'read', {'manager': 'outbox'}, name='pm_sent'),

)
