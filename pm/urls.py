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
#    (r'^$', 'django.views.generic.simple.redirect_to', {'url': _('/message/received/')}),
#    (_(r'^send/(?P<username>[a-z0-9]*)/$'), new_message),
#    # TODO : en ajax, récupérer le contenu ou la liste d'envoi du dernier message
#    # TODO : en ajax récupérer un groupe de contacts pour envoi ( implique une gestion des groupes )
#    
#    (_(r'^(?P<type>(received|sent|new)/)$'), list_message),
#    (_(r'^(?P<type>(blacklist|contact)/)$'), list_contact),
#    (_(r'^(?P<type>(blacklist|contact)/)(?P<username>[a-z0-9]*)/$'), show_contact),
#    
#    (_(r'^(?P<type>(received|sent|new)/)(?P<message_id>\d+)/$'), show_message),
#    (_(r'^(?P<type>(received|sent|new)/)(?P<message_id>\d+)/delete/$'), delete_message, {'single_message': True}),
#    
#    (_(r'^(?P<type>(received|sent|new)/)(?P<message_id>\d+)/(?P<order>(previous|next)/)$'), redirect_message, {'username': None,}),
#    (_(r'^(?P<type>(received|sent|new)/)(?P<message_id>\d+)/(?P<order>(previous|next)/)(?P<username>[a-z0-9]*)/$'), redirect_message),
#    
#    (_(r'^(?P<action>(block|unblock)/)(?P<username>[a-z0-9]*)/$'), edit_contact),
