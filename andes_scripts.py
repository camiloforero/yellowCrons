#encoding:utf-8
from __future__ import unicode_literals, print_function
from datetime import datetime
from django_podio import api
from django_expa import expaApi

def parse_date(old_date):
    datetime.strptime('%Y-%m-%d')

def load_andes_ogx_opens(andes_opens):
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
        print("Se ha agregado a %s al espacio de OGX de opens" % person['email'])

def load_approved_igv_trainees(apps):
    p_api = api.PodioApi(18275738)
    for app in apps['items']:
        attributes = {
            143812438:app['person']['first_name'],
            143812439:app['person']['last_name'],
            143812440:app['person']['email'],
            143812442:unicode(app['person']['id']),
            143812443:app['opportunity']['title'], #Nombre del proyecto
            143812444:unicode(app['opportunity']['id']),
            143812445:app['opportunity']['office']['name'],
            143815324:unicode(app['id']),
            143812446:app['person']['home_lc']['country'], #País origen
            }
        p_api.create_item({'fields':attributes})
        print("Se ha agregado a %s al espacio de IGV Strike de Trainees aprobados" % app['person']['email'])

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
            143813638:unicode(app['id']),
            143813285:app['opportunity']['office']['name'],
            143813286:app['person']['home_lc']['country'], #País origen
            }
        p_api.create_item({'fields':attributes})
        print("Se ha agregado a %s al espacio de IGV Strike de Trainees aprobados" % app['person']['email'])

def load_bangladesh_ogx_opens(people):
    pass

def load_bangladesh_ogx_apps(apps):
    p_api = api.PodioApi(19156174)
    modified_eps = {}
    for app in apps['items']:
        print("Loading application of %s" % app['person']['full_name'])
        if  app['person']['email'] not in modified_eps:
            search = p_api.search_in_application_v2(app_id=19156174, ref_type='item', query=app['person']['id'])
            if len(search['results']) == 1: #Found exactly one, as it should be
                item_id = search['results'][0]['id']
                item = p_api.get_item(item_id, external_id=False)
                stage = item['values'][151795769]['value']
                stage_number = int(stage.split(' - ')[0])
                print(stage)
                if stage_number == 0:
                    p_api.updateItem(item_id, {151795769:'0 - Applied at least once AND UNCONTACTED'})
                    print("EP has applied while being uncontacted, updated")
                elif stage_number == 1 or stage_number == 2:
                    p_api.updateItem(item_id, {151795769:'3 - Contacted and applied at least once'})
                    print("EP has applied, updated")
                elif stage_number < 1:
                    print("EP is not elegible for exchange, ignoring...")
                elif stage_number > 2:
                    print("This EP has already been accepted, or more, ignoring...")
            elif len(search['results']) == 0: #Found 0, not ideal but not unexpected, gotta create it and generate a warning
                attributes = {
                    151791638:app['person']['first_name'],
                    151795763:app['person']['last_name'],
                    151795764:unicode(app['person']['id']),
                    154339943:{'start_date':app['person']['dob']},
                    151795766:{'type': 'work', 'value':app['person']['email']},
                    151795772:app['person']['home_lc']['name'],
                    151795769:"0 - Applied at least once AND UNCONTACTED",
                    151818116:app['person']['referral_type'],
                    }
                new_item = p_api.create_item({'fields':attributes})
                item_id = new_item['item_id']
                p_api.comment('item', item_id, {'value': "This applications belongs to an EP who hasn't been loaded yet. It means that either 1) they registered before May, 2) they were assigned an EP Manager in EXPA before being loaded into PODIO or 3) the loading script didn't work properly. The reason should be found as soon as possible, and remedial action taken https://podio.com/users/1707071"})
                print("No EP was found, created")
            else: #FOund more than one, why, which one is it, help, abort
                print("######ERROR#####")
                print('Error, more than one item found')
                print("")
                break
            modified_eps[app['person']['email']] = item_id
        else: #We already know this EP's PODIO ID
            print ("Found in previously loaded apps, just add the comment")
            item_id = modified_eps[app['person']['email']]
        p_api.comment('item', item_id, {
            'value': "This person has applied to the %s project '%s' in %s, %s (link: https://experience.aiesec.org/#/opportunities/%s/)" % (
                app['opportunity']['programmes']['short_name'],
                app['opportunity']['title'],
                app['opportunity']['office']['name'],
                app['opportunity']['office']['country'],
                app['opportunity']['id']
                )})

load_dict = {
    load_applied_igv_trainees: {'interaction':'applied', 'days':1,
        'officeID': 1395, 'today': False, 'program': 'igv'},
    load_approved_igv_trainees: {'interaction':'approved', 'days': 1,
        'officeID': 1395, 'today': False, 'program': 'igv'},
    load_andes_ogx_opens: {'interaction':'registered', 'days': 1,
        'officeID': 1395, 'today': False, 'program': 'ogx'},
#    load_bangladesh_ogx_apps: {'interaction':'applied', 'days': 1,
#        'officeID': 2010, 'today': False, 'program': 'ogx'},
}

def andes_daily_load():
    print("Cargando en " + str(datetime.now()))
    ex_api = expaApi.ExpaApi(account='kevin.gonzalez@aiesec.net', fail_attempts=10)
    bd_api = expaApi.ExpaApi(account='camilo.forero@aiesec.net', fail_attempts=10)
    for function, kwargs in load_dict.items():
        try:
            print("Attempting to load all {interaction} people of the {program} program from {days} days ago in LC {officeID}".format(**kwargs))
            function(ex_api.get_past_interactions(**kwargs))
            print("Success")
        except (expaApi.APIUnavailableException) as e:
            print("Failure: EXPA is not working, the API is unavailable")
            print(e)
        except api.api.transport.TransportException as e:
            print("Failure: PODIO transport exception")
            print(e)
        except Exception as e:
            print("Failure: Unknown error")
            print(kwargs)
            print(e)

    print("Todas las cargas han sido exitosas")

