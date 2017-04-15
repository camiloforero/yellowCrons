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
        print "Cargando Approved de IGV"
        approved_igv_apps = ex_api.get_past_interactions('approved', 1, 1395, False, program='igv')
        #approved_igcdp_apps = ex_api.get_interactions('approved', 1395, program='icx', start_date='2016-01-01', end_date='2016-11-29')
        load_approved_igv_trainees(approved_igv_apps)
        print "Los EPs aprobados de ICX fueron cargados exitosamente"
    except (expaApi.APIUnavailableException) as e:
        print "Error cargando los trainees aprobados de ICX"
        print e
    except Exception as e:
        print "Unknown error - ICX approved apps"
        print e

    try:
        print "Cargando Opens de IGV"
        applied_igv_apps = ex_api.get_past_interactions('applied', 1, 1395, False, program='igv')
        #approved_igcdp_apps = ex_api.get_interactions('approved', 1395, program='icx', start_date='2016-01-01', end_date='2016-11-29')
        load_applied_igv_trainees(applied_igv_apps)
        print "Los EPs aprobados de ICX fueron cargados exitosamente"
    except (expaApi.APIUnavailableException) as e:
        print "Error cargando los trainees aprobados de ICX"
        print e
    except Exception as e:
        print "Unknown error - ICX applied apps"
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

def load_approved_igv_trainees(apps):
    p_api = api.PodioApi(18275738)
    for app in apps['items']:
        attributes = {
            143812438:app['person']['first_name'],
            143812439:app['person']['last_name'],
            143812440:app['person']['email'],
            143812442:unicode(app['person']['id']),
            143812444:unicode(app['opportunity']['id']),
            143812445:app['opportunity']['office']['name'],
            143815324:app['id'],
            143812446:app['person']['home_lc']['country'], #País origen
            143812443:app['opportunity']['title'], #Nombre del proyecto
            }
        try:
            p_api.create_item({'fields':attributes})
            print "Se ha agregado a %s al espacio de IGV Strike de Trainees aprobados" % app['person']['email']

        except api.api.transport.TransportException as te:
            print "Transport exception en %s" % app['person']['email']
            print app
            print te

def load_applied_igv_trainees(apps):
    p_api = api.PodioApi(18275836)
    for app in apps['items']:
        attributes = {
            143813278:app['person']['first_name'],
            143813279:app['person']['last_name'],
            143813280:app['person']['email'],
            143813282:unicode(app['person']['id']),
            143813283:app['opportunity']['title'], #Nombre del proyecto
            143813284:unicode(app['opportunity']['id']),
            143813638:app['id'],
            143813285:app['opportunity']['office']['name'],
            143813286:app['person']['home_lc']['country'], #País origen
            }
        try:
            p_api.create_item({'fields':attributes})
            print "Se ha agregado a %s al espacio de IGV Strike de Trainees aprobados" % app['person']['email']

        except api.api.transport.TransportException as te:
            print "Transport exception en %s" % app['person']['email']
            print app
            print te

def email_new_visitors(new_visitors):
    email = mailApi.MailApi('correo_nuevos_inscritos')


            122923603:{'start_date':app['an_signed_at'].split('T')[0]}
            }
        try:
            p_api.create_item({'fields':attributes})

        except api.api.transport.TransportException as te:
            print app
            print te

