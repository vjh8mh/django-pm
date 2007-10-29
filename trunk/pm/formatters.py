
from django.utils.text import normalize_newlines
from django.utils.html import strip_tags, clean_html
       
from utils.html import decode_entities

def format_html(html):
    "Default html filter"
    # TODO: replace clean_html with html_filter
    return clean_html(decode_entities(normalize_newlines(html))).strip()

def format_text(text):
    "Default text filter"
    return text.strip()

def format_text_from_html(html):
    "Default text from html filter"
    return decode_entities(strip_tags(html)).strip()

def format_subject(text, from_body=False):
    "Formats message body in models and forms."
    if from_body:
        return format_text_from_html(text)[:80].strip()
    else:
        return format_text(text[:80])
    
def format_body(html):
    "Formats message body in models and forms."
    return format_html(html)