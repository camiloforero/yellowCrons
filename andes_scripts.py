#encoding:utf-8
from __future__ import unicode_literals
from datetime import datetime
from django_podio import api
from django_expa import expaApi

def andes_daily_load():
    print "Cargando en " + str(datetime.now())
    ex_api = expaApi.ExpaApi(fail_attempts=10)
    try:
        andes_opens = ex_api.get_past_interactions('registered', 1, 1395, today=False)
        load_andes_opens(andes_opens)
        print "Los EPs aprobados de OGX fueron cargados exitosamente"
    except (expaApi.APIUnavailableException) as e:
        print "Error cargando los EPs aprobados de OGX"
        print e
    except Exception as e:
        print "Unknown error"
        print e

    try:
        print "Cargando Approved de OGX"
        approved_apps = ex_api.get_past_interactions('approved', 1, 1395, False)
        load_approved_apps(approved_apps)
        print "Los EPs aprobados de OGX fueron cargados exitosamente"
    except (expaApi.APIUnavailableException) as e:
        print "Error de EXPA cargando los EPs aprobados de OGX"
        print e
    except Exception as e:
        print "Unknown error: OGX approved apps"
        print e

    try:
        print "Cargando Approved de ICX"
        approved_igcdp_apps = ex_api.get_past_interactions('approved', 1, 1395, False, program='icx')
        #approved_igcdp_apps = ex_api.get_interactions('approved', 1395, program='icx', start_date='2016-01-01', end_date='2016-11-29')
        load_approved_icx_eps(approved_igcdp_apps)
        print "Los EPs aprobados de ICX fueron cargados exitosamente"
    except (expaApi.APIUnavailableException) as e:
        print "Error cargando los trainees aprobados de ICX"
        print e
    except Exception as e:
        print "Unknown error - ICX approved apps"
        print e
#    try:
#        udea_opens = ex_api.get_past_interactions('registered', 1, 1746, False, program='icx')
#        load_udea_opens(udea_opens)
#        print "Los opens de UdeA fueron cargados exitosamente"
#    except (expaApi.APIUnavailableException) as e:
#        print "Error cargando los EPs de UdeA"
#        print e
#    except Exception as e:
#        print "Unknown error"
#        print e
    print "Todas las cargas han sido exitosas"
    new_visitors = ex_api.get_past_interactions('registered', 1, 1395, False)

def load_accepted_apps(accepted_apps):
    p_api = api.PodioApi(15586895)
    for app in accepted_apps['items']:
        attributes = {
            120335031:app['person']['first_name'],
            120836240:app['person']['last_name'],
            120836241:app['person']['email'],
            123886690:app['opportunity']['programmes'][0]['short_name'],
            120335070:unicode(app['person']['id']),
            120335071:unicode(app['opportunity']['id']),
            120836243:app['opportunity']['office']['name'],
            124730925:app['opportunity']['title'], #Nombre del proyecto
            }
        p_api.create_item({'fields':attributes})
        #elif app['opportunity']['programmes'][0]['id'] == 2:#FOr GIP
        #    p_api = api.PodioApi(15812927)
        #    attributes = {
        #        122297408:app['person']['first_name'],
        #        122297409:app['person']['last_name'],
        #        122297410:app['person']['email'],
        #        122297411:unicode(app['person']['id']),
        #        122297412:unicode(app['opportunity']['id']),
        #        122297414:app['opportunity']['office']['name']
        #        }
        #    p_api.create_item({'fields':attributes})
        #    print "Se ha agregado a %s al espacio de OGIP" % app['person']['email']

def load_udea_opens(udea_opens):
    p_api = api.PodioApi(16805611)
    for person in udea_opens['items']:
        attributes = {
            130898858:person['first_name'],
            130899098:person['last_name'],
            130899099:person['email'],
            130899100:unicode(person['id']),
            130899101:person['phone'],
            }
        p_api.create_item({'fields':attributes})
        print "Se ha agregado a %s al espacio de OGX (UdeA) de opens" % person['email']

def load_andes_opens(andes_opens):
    """
    """
    for person in andes_opens['items']:
        p_api = api.PodioApi(16504431)
        attributes = {
            128296712:person['first_name'],
            128296713:person['last_name'],
            134415808:person['email'],
            134414121:unicode(person['id']),
            134415678:person['phone'],
            }
        p_api.create_item({'fields':attributes})
        print "Se ha agregado a %s al espacio de OGX de opens" % person['email']

def load_approved_apps(approved_apps):
    for app in approved_apps['items']:
        p_api = api.PodioApi(15998856)
        attributes = {
            123889165:app['person']['first_name'],
            123889166:app['person']['last_name'],
            123889167:app['person']['email'],
            123889168:app['opportunity']['programmes'][0]['short_name'],
            123889169:unicode(app['person']['id']),
            123889170:unicode(app['opportunity']['id']),
            123889171:app['opportunity']['office']['name'],
            124789464:app['opportunity']['title'], #Nombre del proyecto
            129666024:{'start_date':app['an_signed_at'].split('T')[0]}#Fecha del match
            }
        try:
            p_api.create_item({'fields':attributes})
            print "Se ha agregado a %s al espacio de OGX de EPs aprobados" % app['person']['email']

        except api.api.transport.TransportException as te:
            print "Transport exception en %s" % app['person']['email']
            print app
            print te

def email_new_visitors(new_visitors):
    email = mailApi.MailApi('correo_nuevos_inscritos')


def load_approved_icx_eps(applications):
    p_api = api.PodioApi(15886643)
    for app in applications['items']:
        attributes = {
            122922712:app['person']['first_name'],
            122923595:app['person']['last_name'],
            122923598:app['person']['email'],
            122923596:app['opportunity']['programmes'][0]['short_name'], #Programa
            122923597:unicode(app['person']['id']), #Trainee EXPA ID
            122923599:app['opportunity']['title'], #Nombre del proyecto
            122923600:unicode(app['opportunity']['id']), #Nombre del trainee
            122923601:app['person']['home_lc']['name'], #LC origen
            122923604:app['person']['home_lc']['country'], #País origen
            122923603:{'start_date':app['an_signed_at'].split('T')[0]}
            }
        try:
            p_api.create_item({'fields':attributes})

        except api.api.transport.TransportException as te:
            print app
            print te

