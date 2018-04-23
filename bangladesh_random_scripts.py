#encoding:utf-8
from __future__ import unicode_literals, print_function
import random
from datetime import datetime, timedelta
from django_podio import api
from django_expa import expaApi
from django_mailTemplates import mailApi
from . import bangladesh_conf, models, tools



def update_tl_managers(date):
    """
    This method will update the TL EP manager of all EPs who have had some kind of activity sonce the date that arrives as parameter
    If the member exists, it will reassign them as the TL EP manager
    If the member doesn't exist, it will tag the oGV head and ask her to take action
    """
    dict_api = api.PodioApi(20705812)
    p_api = api.PodioApi(19156174)
    #bd_api = expaApi.ExpaApi(account='camilo.forero@aiesec.net', fail_attempts=10)

    active_members = {} # THis dict has a ist of all members, and their TL
    member_list = dict_api.get_filtered_items({})
    for member in member_list:
        active_members[int(member['values'][169137334]['value'])] = {
            'name': member['values'][169137328]['value'],
            'expa_id': member['values'][169137333]['value'],
            'tl_name': member['values'][169137335]['value'],
            'tl_podio_id': member['values'][169137336]['value'],
        }

#    recent_items = p_api.get_filtered_items({
#        'last_edit_on':{'from':date}
#    })
    recent_items = p_api.get_items_by_view(37774706)
    no_ep_manager = 0
    inactive_ep_manager = 0
    properly_assigned = 0
    for item in recent_items:
        correct = False
        manager_id = -1
        manager_name = "NONE"
        tl_id = -1
        tl_name = "NONE"
        expa_id = item['values'][151795764]['value']
        update_dict = {}
        if 151795767 in item['values']:
            manager_id = int(item['values'][151795767]['value']['user_id'])
            manager_name = item['values'][151795767]['value']['name']
            if manager_id in active_members:
                member_data = active_members[manager_id]
                update_dict[151795765] = {'value': {'id': int(member_data['tl_podio_id']), 'type':'user'}}
                print("Assigning this lead (%s) to %s and %s" % (expa_id, member_data['tl_name'], manager_name)) 
                properly_assigned += 1
                correct = True
            else:
                update_dict[151795767] = None
        if not correct and 151795765 in item['values'] and int(item['values'][151795765]['value']['user_id']) in active_members:
                tl_id = int(item['values'][151795765]['value']['user_id'])
                tl_data = active_members[tl_id]
                tl_name = item['values'][151795765]['value']['name']
                update_dict[151795765] = {'value': {'id': int(tl_data['tl_podio_id']), 'type':'user'}}

                print("This EP (%s) has an inactive EP manager (%s) and an active TL (%s). The manager has been removed, the TL should reassign them." % (expa_id, manager_name, tl_data['tl_name']) )
                correct = True
        if not correct: 
            update_dict[151795765] = {'value': {'id': 888570, 'type':'user'}}
            print("Invalid EP manager (%s) and the TL (%s) was invalid, Assigning Louise. expa id: %s, Status: %s" % (manager_name, tl_name, item['values'][151795764]['value'],  item['values'][151795769]['value']))
        print("")

        p_api.updateItem(item['item'], update_dict)

        

def email_quizz_sender(podio_app_id, week):
    p_api = api.PodioApi(podio_app_id)
    items = p_api.get_filtered_items({}, no_html=True)
    email = mailApi.MailApi("ECBALQuizAnswer")
    from_email = 'louise.kim@aiesec.net'
    for item in items:
        context = {}
        for value in item['values'].values():
            context[value['label'].split(' - ')[0]] = value['value']
            context['week'] = week
        to_email = [context['Email']]
        email.send_mail(from_email, to_email, context)
            
def lda_score_updater():
    p_api = api.PodioApi(19600457)
    bd_api = expaApi.ExpaApi(account='camilo.forero@aiesec.net', fail_attempts=10)
    items = p_api.get_filtered_items({}, no_html=True)
    podio_dict = {
        'Self Aware': {'score':161812900, 'subqualities':161818453},
        'Solution Oriented': {'score':161812901, 'subqualities':161818454},
        'World Citizen': {'score':161812902, 'subqualities':161818455},
        'Empowering Others': {'score':161812903, 'subqualities':161818456},
        }
    for item in items:
        ldm_data = bd_api.lda_report(item['values'][157141794]['value'], 'person_id')
        for result_set in ldm_data:
            if result_set['opportunity_application_id'] == int(item['values'][157141793]['value']):
                #print(result['results'])
                for result in result_set['results']:
                    if result['ldm_response_type'] == 'initial': # Checks that it gets the initial LDM result, instead of the final or the AIESEC impact one
                        print('success')
                        params = {}
                        for key in result.keys():
                            if key in podio_dict:
                                params[podio_dict[key]['score']] = result[key]['score']
                                description = "";
                                for subresult in result[key]['sub_scores']:
                                    description2 = ""
                                    score = 0
                                    for measurement in subresult['measurements']:
                                        description2 += (measurement['result'] + ' - ' )
                                        score += int(measurement['score'])
                                    element_total = subresult['sub_quality'] + ': Total score: ' + str(score) + ". Description: " + description2 + "<br/>"
                                    description += element_total
                                        
                                print(description)
                                params[podio_dict[key]['subqualities']] = description
                        print(params)
                        p_api.updateItem(item['item'], params)
                        break
                break
            else:
                print(result['opportunity_application_id'])
                print(item['values'][157141793]['value'])
            
def update_country_applications():
    p_api = api.PodioApi(19156174)
    bd_api = expaApi.ExpaApi(account='camilo.forero@aiesec.net', fail_attempts=10)
    apps = bd_api.get_interactions(interaction='applied', start_date='01-03-2018', end_date='17-03-2018', officeID=2010, program='ogx')
    update_dict = {}
    print(len(apps))
    for app in apps['items']:
        # add app expa_id to update_dict
        person_id = app['person']['id']
        try:
            models.Office.objects.get(expa_id=app['opportunity']['office']['parent_id'])
            if person_id in update_dict:
                update_dict[person_id] += 1
            else:
                update_dict[person_id] = 1
        except models.Office.DoesNotExist:
            continue

    #now it updates the PODIO field for country partner applications in all items
    for expa_id, applications in update_dict.iteritems():
        # Search for the person by using the PODIO search function
        search = p_api.search_in_application_v2(app_id=19156174, ref_type='item', query=expa_id)
        item_id = search['results'][0]['id']

        p_api.updateItem(item_id, {167580470: applications})
        #Update the found podio item with the number of country partner applications
        #TODO

            

def sync_bangladesh_ogx_approved(apps, ex_api, *args, **kwargs):
    """
    This method will check if a certain set of realizations exist or not in PODIO. If they do it will leave them alone. If they don't it will create a new one.
    """
    p_api = api.PodioApi(19600457) #With credentials for the VD application
    modified_apps = {} #Here it saves the EPs that have already been searched and found in PODIO, so it is not done again
    for app in apps['items']:
        print("Updating approval of %s in Value Delivery space" % app['person']['full_name'])
        breaker = False
        if  app['person']['email'] not in modified_apps:
            search = p_api.search_in_application_v2(app_id=19600457, ref_type='item', query=app['id'])
            if len(search['results']) == 1: #Found exactly one, as it should be
                # Initializes variables that may or may not be in the consideration space, to be transferred later to the VD space if they exist
                # gets the item
                print("Success!")
                print(app["status"])
                print("")
                continue #TODO: Everything after this should be cleaned up
                item_id = search['results'][0]['id']
                p_api.updateItem(item_id, {
                    163451022:{'start_utc':app['date_realized'].replace('T', ' ').replace('Z', '').replace('+00:00', '')},
                    168656289:{'start_utc':app['experience_end_date'].replace('T', ' ').replace('Z', '').replace('+00:00', '')}
                    })
                print(app['status'])
                item = p_api.get_item(item_id, external_id=False)
                # Finds the status of the exchange
                stage = item['values'][157141798]['value']
                stage_number = int(stage.split(' - ')[0])
                print(stage)
                if stage_number == 1:
                    p_api.updateItem(item_id, {
                        157141798:'2 - Realized',
                        163451022:{'start_utc':app['date_realized'].replace('T', ' ').replace('Z', '').replace('+00:00', '')}})
                    print("EP has been realized, updated")
                elif stage_number < 0:
                    print("Inelegible EP was realiZed?")
                    p_api.comment('item', item_id, {'value': "ALERT: An ep who was marked as break approval or break realization in PODIO has been realizeded in EXPA. This case should bechecked immediately @[%s](user:%s) @[%s](user:%s)" % (di_responsible['name'],di_responsible['user_id'], ogx_responsible['name'], ogx_responsible['user_id'])})
                elif stage_number > 1: #Higher than an approval already
                    p_api.comment('item', item_id, {'value': "NOTE: An ep who was in a sate higher than realized has been marked as just realized. CHeck this out, @[%s](user:%s)" % (di_responsible['name'],di_responsible['user_id']) })
            elif len(search['results']) == 0: #Found 0, not ideal but not unexpected, gotta create it and generate a warning
                print("Wow check this out")

                attributes = { # This is for creating a new realization at the VD space
                    157131079:app['person']['first_name'],
                    157141792:app['person']['last_name'],
                    157141793:unicode(app['id']),
                    157141794:unicode(app['person']['id']),
                    157141800:{'value':app['person']['email'], 'type': 'work'},
                    157141801:app['person']['home_lc']['name'],
                    157141802:app['opportunity']['title'], #Nombre del proyecto
                    157141795:unicode(app['opportunity']['id']),
                    157141803:app['opportunity']['programmes']['short_name'],
                    157141804:app['opportunity']['office']['name'],
                    157141805:app['opportunity']['office']['country'], #País origen
                    157141796:{'start_utc':app['date_approved'].replace('T', ' ').replace('Z', '').replace('+00:00', '')},
                    157141798:'-5 - Break Approval',
                    }
                new_item = p_api.create_item({'fields':attributes})
                if breaker:
                    print(app)
                    break
                else:
                    breaker = True
                item_id = new_item['item_id']
                p_api.comment('item', item_id, {'value': "This realization belongs to an EP who hasn't been loaded yet. It is probably from an approval that happened before the start of the quarter @[Camilo Forero](user:1707071)"})
                print("No EP was found, created in the space")
            else: #FOund more than one, why, which one is it, help, abort
                print("######ERROR#####")
                print('Error, more than one item found')
                print("")
                break
            modified_apps[app['id']] = item_id
        else: #We already know this EP's PODIO ID
            print ("Found in previously loaded approvals, just add the comment")
            continue
            item_id = modified_apps[app['id']]

def sync_bangladesh_ogx_realized(apps, ex_api, *args, **kwargs):
    """
    This method will check if a certain set of realizations exist or not in PODIO. If they do it will leave them alone. If they don't it will create a new one.
    """
    p_api = api.PodioApi(19600457) #With credentials for the VD application
    modified_apps = {} #Here it saves the EPs that have already been searched and found in PODIO, so it is not done again
    for app in apps['items']:
        print("Updating realizations of %s in Value Delivery space" % app['person']['full_name'])
        if  app['person']['email'] not in modified_apps:
            search = p_api.search_in_application_v2(app_id=19600457, ref_type='item', query=app['id'])
            if len(search['results']) == 1: #Found exactly one, as it should be
                # Initializes variables that may or may not be in the consideration space, to be transferred later to the VD space if they exist
                # gets the item
                item_id = search['results'][0]['id']
                p_api.updateItem(item_id, {
                    163451022:{'start_utc':app['date_realized'].replace('T', ' ').replace('Z', '').replace('+00:00', '')},
                    168656289:{'start_utc':app['experience_end_date'].replace('T', ' ').replace('Z', '').replace('+00:00', '')}
                    })
                continue #TODO: Everything after this should be cleaned up
                print(app['status'])
                item = p_api.get_item(item_id, external_id=False)
                # Finds the status of the exchange
                stage = item['values'][157141798]['value']
                stage_number = int(stage.split(' - ')[0])
                breaker = False
                print(stage)
                if stage_number == 1:
                    p_api.updateItem(item_id, {
                        157141798:'2 - Realized',
                        163451022:{'start_utc':app['date_realized'].replace('T', ' ').replace('Z', '').replace('+00:00', '')}})
                    print("EP has been realized, updated")
                elif stage_number < 0:
                    print("Inelegible EP was realiZed?")
                    p_api.comment('item', item_id, {'value': "ALERT: An ep who was marked as break approval or break realization in PODIO has been realizeded in EXPA. This case should bechecked immediately @[%s](user:%s) @[%s](user:%s)" % (di_responsible['name'],di_responsible['user_id'], ogx_responsible['name'], ogx_responsible['user_id'])})
                elif stage_number > 1: #Higher than an approval already
                    p_api.comment('item', item_id, {'value': "NOTE: An ep who was in a sate higher than realized has been marked as just realized. CHeck this out, @[%s](user:%s)" % (di_responsible['name'],di_responsible['user_id']) })
            elif len(search['results']) == 0: #Found 0, not ideal but not unexpected, gotta create it and generate a warning
                print("Wow check this out")

                attributes = { # This is for creating a new realization at the VD space
                    157131079:app['person']['first_name'],
                    157141792:app['person']['last_name'],
                    157141793:unicode(app['id']),
                    157141794:unicode(app['person']['id']),
                    157141800:{'value':app['person']['email'], 'type': 'work'},
                    157141801:app['person']['home_lc']['name'],
                    157141802:app['opportunity']['title'], #Nombre del proyecto
                    157141795:unicode(app['opportunity']['id']),
                    157141803:app['opportunity']['programmes']['short_name'],
                    157141804:app['opportunity']['office']['name'],
                    157141805:app['opportunity']['office']['country'], #País origen
                    157141796:{'start_utc':app['date_approved'].replace('T', ' ').replace('Z', '').replace('+00:00', '')},
                    163451022:{'start_utc':app['date_realized'].replace('T', ' ').replace('Z', '').replace('+00:00', '')},
                    }
                new_item = p_api.create_item({'fields':attributes})
                if breaker:
                    print(app)
                    break
                else:
                    breaker = True
                item_id = new_item['item_id']
                print("No EP was found, created in the space")
            else: #FOund more than one, why, which one is it, help, abort
                print("######ERROR#####")
                print('Error, more than one item found')
                print("")
                break
            modified_apps[app['id']] = item_id
        else: #We already know this EP's PODIO ID
            print ("Found in previously loaded approvals, just add the comment")
            continue
            item_id = modified_apps[app['id']]


def sync_bangladesh_ogx_finished(apps, ex_api, *args, **kwargs):
    """
    This method will check if a certain set of realizations exist or not in PODIO. If they do it will leave them alone. If they don't it will create a new one.
    """
    p_api = api.PodioApi(19600457) #With credentials for the VD application
    modified_apps = {} #Here it saves the EPs that have already been searched and found in PODIO, so it is not done again
    for app in apps['items']:
        print("Updating finished of %s in Value Delivery space" % app['person']['full_name'])
        breaker = False
        if  app['id'] not in modified_apps:
            search = p_api.search_in_application_v2(app_id=19600457, ref_type='item', query=app['id'])
            if len(search['results']) == 1: #Found exactly one, as it should be
                # Initializes variables that may or may not be in the consideration space, to be transferred later to the VD space if they exist
                # gets the item
                print("Success! updating standards...")
                update_application_standards(app, p_api, ex_api)
                print(app["status"])
                print("")
                continue #TODO: Everything after this should be cleaned up
                item_id = search['results'][0]['id']
                p_api.updateItem(item_id, {
                    163451022:{'start_utc':app['date_realized'].replace('T', ' ').replace('Z', '').replace('+00:00', '')},
                    168656289:{'start_utc':app['experience_end_date'].replace('T', ' ').replace('Z', '').replace('+00:00', '')}
                    })
                print(app['status'])
                item = p_api.get_item(item_id, external_id=False)
                # Finds the status of the exchange
                stage = item['values'][157141798]['value']
                stage_number = int(stage.split(' - ')[0])
                print(stage)
            elif len(search['results']) == 0: #Found 0, not ideal but not unexpected, gotta create it and generate a warning
                print("Wow check this out")

                attributes = { # This is for creating a new realization at the VD space
                    157131079:app['person']['first_name'],
                    157141792:app['person']['last_name'],
                    157141793:unicode(app['id']),
                    157141794:unicode(app['person']['id']),
                    157141800:{'value':app['person']['email'], 'type': 'work'},
                    157141801:app['person']['home_lc']['name'],
                    157141802:app['opportunity']['title'], #Nombre del proyecto
                    157141795:unicode(app['opportunity']['id']),
                    157141803:app['opportunity']['programmes']['short_name'],
                    157141804:app['opportunity']['office']['name'],
                    157141805:app['opportunity']['office']['country'], #País origen
                    157141796:{'start_utc':app['date_approved'].replace('T', ' ').replace('Z', '').replace('+00:00', '')},
                    163451022:{'start_utc':app['date_realized'].replace('T', ' ').replace('Z', '').replace('+00:00', '')},
                    168656289:{'start_utc':app['experience_end_date'].replace('T', ' ').replace('Z', '').replace('+00:00', '')},
                    157141798:'3 - Finished',
                    }
                new_item = p_api.create_item({'fields':attributes})
                update_application_standards(app, p_api, ex_api)
                if breaker:
                    print(app)
                    break
                else:
                    breaker = True
                item_id = new_item['item_id']
                print("No EP was found, created in the space")
            else: #FOund more than one, why, which one is it, help, abort
                print("######ERROR#####")
                print('Error, more than one item found')
                print("")
                break
            modified_apps[app['id']] = item_id
        else: #We already know this EP's PODIO ID
            print ("Found in previously loaded approvals, just add the comment")
            continue
            item_id = modified_apps[app['id']]



def super_sync_ogx_realized(start_date):
    kwargs = {'interaction':'realized', 'start_date': start_date,
        'officeID': 2010, 'program': 'ogx'}
    bd_api = expaApi.ExpaApi(account='camilo.forero@aiesec.net', fail_attempts=10)
    sync_bangladesh_ogx_realized(bd_api.get_interactions(**kwargs), ex_api=bd_api)

def super_sync_ogx_approved(start_date):
    kwargs = {'interaction':'approved', 'start_date': start_date,
        'officeID': 2010, 'program': 'ogx'}
    bd_api = expaApi.ExpaApi(account='camilo.forero@aiesec.net', fail_attempts=10)
    sync_bangladesh_ogx_approved(bd_api.get_interactions(**kwargs), ex_api=bd_api)


def super_sync_ogx_finished(start_date):
    kwargs = {'interaction':'finished', 'start_date': start_date,
        'officeID': 2010, 'program': 'ogx'}
    bd_api = expaApi.ExpaApi(account='camilo.forero@aiesec.net', fail_attempts=10)
    sync_bangladesh_ogx_finished(bd_api.get_interactions(**kwargs), ex_api=bd_api)


def fix_skipped_day(date):
    kwargs = {'interaction':'registered', 'start_date': date,
        'officeID': 2010, 'program': 'ogx', 'end_date': date}
    bd_api = expaApi.ExpaApi(account='camilo.forero@aiesec.net', fail_attempts=10)
    kwargs['interaction'] = 'applied'
    load_bangladesh_ogx_applied(bd_api.get_interactions(**kwargs), ex_api=bd_api)
    kwargs['interaction'] = 'accepted'
    load_bangladesh_ogx_accepted(bd_api.get_interactions(**kwargs), ex_api=bd_api)
    kwargs['interaction'] = 'approved'
    load_bangladesh_ogx_approved(bd_api.get_interactions(**kwargs), ex_api=bd_api)
    kwargs['interaction'] = 'realized'
    load_bangladesh_ogx_realized(bd_api.get_interactions(**kwargs), ex_api=bd_api)
