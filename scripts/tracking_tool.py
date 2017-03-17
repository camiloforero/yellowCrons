#encoding:utf-8
from __future__ import unicode_literals
from django_podio import api
from complex_hooks import models
from complex_hooks.scripts import email_document

"""
Este módulo guarda a todos los scripts relacionados con la tracking tool del comité.
"""

def email_falta_reportar():
    """
    Este script le envía un correo electrónico a todos los miembros del LC que tienen metas para esta semana, pero aún no han reportado su cumplimiento
    """
    p_api = api.PodioApi(15389408, client=True)
    items = p_api.get_items_by_view(28545599)
    email_hook = models.EmailDocumentHook.objects.get(id=9) #TODO: Esto es poco elegante, debo hallar una manera alternativa de hacer esto
    print "iniciando iteraciones"
    for item in items:
        email_document.email_document(item, email_hook, p_api)
        print "Se le envió el recordatorio a %s" % item['values'][130741485]['value']

def email_recordar_metas():
    """
    Este script le envía un correo electrónico a todos los miembros del LC que tienen metas para esta semana, pero aún no han reportado su cumplimiento
    """
    p_api = api.PodioApi(15389408)
    items = p_api.get_items_by_view(28622471)
    email_hook = models.EmailDocumentHook.objects.get(id=10) #TODO: Esto es poco elegante, debo hallar una manera alternativa de hacer esto
    for item in items:
        email_document.email_document(item, email_hook, p_api)

def email_falta_llenar():
    """
    Este script le envía un correo electrónico a todos los miembros del LC que no han llenado la tracking tool esta semana
    """
    p_api = api.PodioApi(15280717)
    items = p_api.get_filtered_items(None)
    unfilled_members = []
    for item in items:
        try:
            pass
        except KeyError:
            unfilled_members.append(item)
    email_hook = models.EmailDocumentHook.objects.get(id=10) #TODO: Esto es poco elegante, debo hallar una manera alternativa de hacer esto
    for item in unfilled_members:
        email_document.email_document(item, email_hook, p_api)
