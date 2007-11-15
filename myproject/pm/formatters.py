# -*- coding: utf-8 -*-
#from django.utils.text import normalize_newlines
#from django.utils.html import strip_tags, clean_html

def format_text_from_html(html):
    "Default text from html filter"
    return html

def format_subject(text, from_body=False):
    "Formats message body in models and forms."
    if from_body:
        return text[:80]
    else:
        return text[:80]
    
def format_body(html):
    "Formats message body in models and forms."
    return html
