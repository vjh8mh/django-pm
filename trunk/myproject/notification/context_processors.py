# -*- coding: utf-8 -*-
"""
request processor for the user notification system
"""
import datetime

from django.contrib.sessions.models import Session
from django.conf import settings

NOTICE_TEMPLATES = {
                  'notice': '<li class="%(css_class)s">%(message)s</li>',
                  'notice_link': '<li class="%(css_class)s">%(message)s <a href="%(link_url)s">%(link_text)s</a></li>',
                  }

DEFAULT_TEMPLATE = 'notice'

def notices(request):
    "Adds HTML formating to the notices"

    notices = []
    if request.session.get('notices', False):
        for notice in request.session['notices'].values():
            # Default values
            notice['template'] = notice.get('template', DEFAULT_TEMPLATE)
            notice['css_class'] = notice.get('css_class', DEFAULT_TEMPLATE)
            # Add HTML formating
            html_template = NOTICE_TEMPLATES.get(notice['template'], DEFAULT_TEMPLATE)
            notice['as_html'] = html_template % notice
            notices.append(notice)        
            
        try:
            del request.session['notices']
        except KeyError:
            pass
         
    return {'notices': notices}

