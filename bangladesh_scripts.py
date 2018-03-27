#encoding:utf-8
from __future__ import unicode_literals, print_function
import random
from datetime import datetime, timedelta
from django_podio import api
from django_expa import expaApi
from django_mailTemplates import mailApi
from . import bangladesh_conf, models, tools
def parse_date(old_date):
    datetime.strptime('%Y-%m-%d')


def load_bangladesh_ogx_opens(people, *args, **kwargs):
    """
    This method loads all new oGX opens into the PODIO workspace. It works a bit differently than the usual; it also autoassigns EP managers to each EP it loads through EXPA before saving them in PODIO. This requires taking an extra step
    """
    p_api = api.PodioApi(19156174)
    active_lcvps = models.Member.objects.filter(is_lcvp=True, is_active=True).order_by('?')
    manager_index = 0 #The current VP who will be assigned to the next EP 
    tl_index = {} # Here we will initialize, for each VP, the index of the TL who will be assigned next
    for manager in active_lcvps:
        print(manager)
        tl_index[manager.expa_id] = random.randint(0, len(manager.team_members.filter(is_active=True)) - 1)
        print("TL index for %s" % manager.name)
        print(tl_index[manager.expa_id])
    for raw_person in people['items']:
        current_manager = None
        current_tl = None
        if len(raw_person['managers']) > 0:
            for manager in raw_person['managers']:
                mn_id = unicode(manager['id'])
                try:
                    current_manager = active_lcvps.get(expa_id=mn_id)
                    print("There was already at least one EP manager, %s will be assigned" % manager['full_name'])
                    break
                except models.Member.DoesNotExist:
                    continue
        if current_manager is None:
            current_manager = active_lcvps[manager_index]
            manager_index = (manager_index + 1) % len(active_lcvps)
        if current_tl is None:
            tl_list = current_manager.team_members.filter(is_active=True)
            current_tl = tl_list[tl_index[current_manager.expa_id]]
            print(tl_index)
            tl_index[current_manager.expa_id] = (tl_index[current_manager.expa_id] + 1) % len(tl_list) 
            print(tl_index)
        print("Updating %s (expa_id %s) with LCVP %s and TL %s" % (raw_person['full_name'], raw_person['id'], current_manager.name, current_tl.name)) 
        person = kwargs['ex_api'].update_person(unicode(raw_person['id']), {"manager_ids": [current_manager.expa_id, current_tl.expa_id]})
        print("EXPA success, starting PODIO load")
        try:
            referral_type = person['referral_type']
            if referral_type is None or referral_type == "":
                referral_type = "Other"
            if person['profile_completeness']['gv']:
                profile_complete = "Yes"
            else:
                profile_complete = "No"
            attributes = {
                151791638: {'value': person['first_name']},
                151795763: {'value': person['last_name']},
                151795764: {'value': unicode(person['id'])},
                165527150: {'value':{'id': current_manager.podio_id, 'type':'user'}},
                151795765: {'value':{'id': current_tl.podio_id, 'type':'user'}},
                151950042: {'start_utc': person['created_at'].replace('T', ' ').replace('Z', '')},
                151795766: {'type': 'work', 'value': person['email']},
                151795772: {'value': person['home_lc']['name']},
                151795769: {'value': '0 - Uncontacted'},
                151818116: {'value': referral_type},
                159966006: profile_complete,
                }
            if(person['dob']):
                attributes[154339943] = {'start_date': person['dob']}
            if(person['contact_info']):
                attributes[151795768] = {'type': 'mobile', 'value': '%s%s' % (person['contact_info']['country_code'], person['contact_info']['phone'])},
            if(len(person['academic_experiences']) > 0):
                attributes[151832581] = person['academic_experiences'][0]['organisation_name'] 
        except Exception as e:
            print("Argument load unsuccessful, check item for errors")
            print(e)
            print(person)
            raise e
        try:
            p_api.create_item({'fields':attributes})
            print("Se ha agregado a %s al espacio de OGX de opens" % person['email'])
        except Exception as e:
            print(e)
            print("Error adding %s (expa_id %s) to the Bangladesh opens space" % (person['full_name'], person['id']))
            continue


def load_bangladesh_ogx_apps(apps, *args, **kwargs):
    p_api = api.PodioApi(19156174)
    modified_eps = {}
    for app in apps['items']:
        print("Loading application of %s" % app['person']['full_name'])
        is_partner = False
        is_blacklisted = False
        app_date = {'start_date': app['created_at'].split('T')[0]},
        update_params = { # Creates a dictionary of all the update parameters which are common to all updates
            158519539: app_date,
            154339943:{'start_date':app['person']['dob']},
            159966006:'Yes',
        }
        try: #Checks if the application belongs to a country partner or a blacklisted LC
            office = models.Office.objects.get(expa_id=app['opportunity']['office']['parent_id'])
            is_partner = office.is_partner
        except models.Office.DoesNotExist:
            pass

        try:
            office = models.Office.objects.get(expa_id=app['opportunity']['office']['id'])
            is_blacklisted = office.is_blacklisted
        except models.Office.DoesNotExist:
            pass

        print(is_partner)
        if  app['person']['email'] not in modified_eps or is_partner:
            search = p_api.search_in_application_v2(app_id=19156174, ref_type='item', query=app['person']['id'])
            if len(search['results']) == 1: #Found exactly one, as it should be
                item_id = search['results'][0]['id']
                item = p_api.get_item(item_id, external_id=False)

                if 167580470 not in item['values']:
                    update_params[167580470] = 0
                else:
                    update_params[167580470] = int(float(item['values'][167580470]['value']))

                if is_partner:
                    update_params[167580470] += 1

                if 151832580 not in item['values'] or 151832581 not in item['values']: #Checks if the university is there in the EP or not. If not, gets it from EXPA
                    person = kwargs['ex_api'].getPerson(item['values'][151795764]['value'])
                    update_params[151832581] = person['academic_experiences'][0]['organisation_name']


                if 158519539 not in item['values']: #Checks if the "last application date" field does not exist. This means that this is the EP's first application
                    print("First application: sending email")
                    update_params[159724898] = app_date #Updates the first application date
                    email = mailApi.MailApi("first_application_email")
                    if 151795767 in item['values']: # Checks if there is a TM responsible.
                        from_email = item['values'][151795767]['value']['mail'][0]
                        manager_name = item['values'][151795767]['value']['name']
                    else:
                        from_email = item['values'][151795765]['value']['mail'][0]
                        manager_name = item['values'][151795765]['value']['name']


                    context = {
                        'ep_first_name': item['values'][151791638]['value'],
                        'manager_name': manager_name,
                        }
                    to_email = [item['values'][151795766]['value']]
                    try:
                        email.send_mail(from_email, to_email, context)
                        p_api.comment('item', item_id, {'value': "An email has been sent successfully, for first application, from %s to %s" % (from_email, to_email)})
                    except Exception as e:
                        p_api.comment('item', item_id, {'value': "Warning: There was an error sending the email: %s . Check this out @[%s](user:%s)" % (e, di_responsible['name'],di_responsible['user_id']) })
                        #comment
                stage = item['values'][151795769]['value']
                stage_number = int(stage.split(' - ')[0])
                print(stage)
                if stage_number <= -5:
                    print("EP is not elegible for exchange, but has applied. @[Camilo Forero](user:1707071)")
                    p_api.comment('item', item_id, {'value': "INFO: An ep who is inelegible for exchange has applied in EXPA. Check it out @[%s](user:%s) @[%s](user:%s)" % (di_responsible['name'],di_responsible['user_id'], ogx_responsible['name'], ogx_responsible['user_id']) })
                elif stage_number <= 0:
                    update_params[151795769] = '0 - Applied at least once AND UNCONTACTED'
                    p_api.comment('item', item_id, {'value': "INFO: An uncontacted EP has applied to an opportunity. Follow up should be prioritized."  })
                    print("EP has applied while being uncontacted, updated")
                elif stage_number == 1 or stage_number == 2:
                    update_params[151795769] = '3 - Contacted and applied at least once'
                    print("EP has applied, updated")
                elif stage_number > 2:
                    print("This EP has already been accepted, or more, ignoring...")
                p_api.updateItem(item_id, update_params)
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
                    158519539:app_date,
                    159966006:'Yes',
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


def load_bangladesh_ogx_accepted(apps, ex_api, *args, **kwargs):
    p_api = api.PodioApi(19156174)
    modified_eps = {}
    for app in apps['items']:
        print("Loading acceptance of %s" % app['person']['full_name'])
        if  app['person']['email'] not in modified_eps:
            search = p_api.search_in_application_v2(app_id=19156174, ref_type='item', query=app['person']['id'])
            if len(search['results']) == 1: #Found exactly one, as it should be
                item_id = search['results'][0]['id']
                item = p_api.get_item(item_id, external_id=False)
                accepted_date = {'start_date': app['updated_at'].split('T')[0]},
                p_api.updateItem(item_id, {159728808: accepted_date})
                stage = item['values'][151795769]['value']
                stage_number = int(stage.split(' - ')[0])
                print(stage)
                if stage_number <= -5:
                    print("EP is not elegible for exchange, ignoring...")
                    p_api.comment('item', item_id, {'value': "ALERT: An ep who was marked as inelegible in PODIO has been accepted in EXPA. This case should bechecked immediately @[Camilo Forero](user:1707071) @[Louise Kim](user:888570)"})
                elif stage_number <= 0:
                    p_api.updateItem(item_id, {151795769:'0 - ACCEPTED AND UNCONTACTED'})
                    print("EP has been accepted while being uncontacted, updated")
                elif stage_number == 1 or stage_number == 2 or stage_number == 3:
                    p_api.updateItem(item_id, {151795769:'4 - Contacted and accepted at least once', 154339943:{'start_date':app['person']['dob']}})
                    print("EP has been accepted, updated")
                elif stage_number > 3:
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
                    159966006:'Yes',
                    }
                new_item = p_api.create_item({'fields':attributes})
                item_id = new_item['item_id']
                p_api.comment('item', item_id, {'value': "This acceptance belongs to an EP who hasn't been loaded yet. It means that either 1) they registered before May, 2) they were assigned an EP Manager in EXPA before being loaded into PODIO or 3) the loading script didn't work properly. The reason should be found as soon as possible, and remedial action taken @[Camilo Forero](user:1707071)"})
                print("No EP was found, created")
            else: #FOund more than one, why, which one is it, help, abort
                print("######ERROR#####")
                print('Error, more than one item found')
                print("")
                continue
            modified_eps[app['person']['email']] = item_id
        else: #We already know this EP's PODIO ID
            print ("Found in previously loaded acceptances, just add the comment")
            item_id = modified_eps[app['person']['email']]
        p_api.comment('item', item_id, {
            'value': "This person has been accepted to the %s project '%s' in %s, %s (link: https://experience.aiesec.org/#/opportunities/%s/)" % (
                app['opportunity']['programmes']['short_name'],
                app['opportunity']['title'],
                app['opportunity']['office']['name'],
                app['opportunity']['office']['country'],
                app['opportunity']['id']
                )})


def load_bangladesh_ogx_approved(apps, ex_api, *args, **kwargs):
    p_api = api.PodioApi(19156174) # Credentials for the applicant conversion application
    p_api_2 = api.PodioApi(19600457) #With credentials for the VD application
    modified_eps = {} #Here it saves the EPs that have already been searched and found in PODIO, so it is not done again
    for app in apps['items']:
        print("Updating approval of %s in applicants space" % app['person']['full_name'])
        if  app['person']['email'] not in modified_eps:
            search = p_api.search_in_application_v2(app_id=19156174, ref_type='item', query=app['person']['id'])
            if len(search['results']) == 1: #Found exactly one, as it should be
                # Initializes variables that may or may not be in the consideration space, to be transferred later to the VD space if they exist
                tm_responsible = None
                tl_responsible = None
                university = None
                university_year = None
                # gets the item
                item_id = search['results'][0]['id']
                item = p_api.get_item(item_id, external_id=False)
                #checks for the existance of the initialized variables
                if 151795765 in item['values']:
                    tl_responsible = item['values'][151795765]['value']['user_id']
                if 151795767 in item['values']:
                    tm_responsible = item['values'][151795767]['value']['user_id']
                if 151832580 in item['values']:
                    university = item['values'][151832580]['value']
                if 162269470 in item['values']:
                    university_year = item['values'][162269470]['value']

                # Finds the status of the exchange
                stage = item['values'][151795769]['value']
                stage_number = int(stage.split(' - ')[0])
                print(stage)
                if stage_number == 0:
                    p_api.updateItem(item_id, {151795769:'0 - APPROVED AND UNCONTACTED'})
                    print("EP has been approved while being uncontacted, updated")
                    p_api.comment('item', item_id, {'value': "ALERT: An ep who had never been contacted according to PODIO has now been approved on EXPA. This case should be checked immediately @[Camilo Forero](user:1707071) @[Louise Kim](user:888570)"})
                elif stage_number < 0:
                    print("Inelegible EP was approved?")
                    p_api.comment('item', item_id, {'value': "ALERT: An ep who was marked as inelegible in PODIO has been approved in EXPA. This case should bechecked immediately @[Camilo Forero](user:1707071) @[Louise Kim](user:888570)"})
                elif stage_number == 1 or stage_number == 2 or stage_number == 3 or stage_number == 4:
                    p_api.updateItem(item_id, {151795769:'7 - Approved', 154339943:{'start_date':app['person']['dob']}})
                    print("EP has been approved, updated")
                    p_api.comment('item', item_id, {'value': "ALERT: An ep who hasn't requested a contract virtually in PODIO has been approved in EXPA. Maybe they signed a physical contract? Either way, this case should bechecked immediately @[Camilo Forero](user:1707071) @[Louise Kim](user:888570)"})
                elif stage_number == 5:
                    print("This EP has requested an invoice, updating...")
                    p_api.updateItem(item_id, {151795769:'7 - Approved', 154339943:{'start_date':app['person']['dob']}})
                    p_api.comment('item', item_id, {'value': "NOTE: An ep who hasn't been marked as paid in PODIO has been approved in EXPA. It is important to start following this procedure now, to avoid unpaid approvals getting through in the future. @[Camilo Forero](user:1707071) @[Louise Kim](user:888570)"})
                elif stage_number == 6:
                    p_api.updateItem(item_id, {151795769:'7 - Approved', 154339943:{'start_date':app['person']['dob']}})
                    print("This EP has already paid, updating...")
            elif len(search['results']) == 0: #Found 0, not ideal but not unexpected, gotta create it and generate a warning
                attributes = {
                    151791638:app['person']['first_name'],
                    151795763:app['person']['last_name'],
                    151795764:unicode(app['person']['id']),
                    154339943:{'start_date':app['person']['dob']},
                    151795766:{'type': 'work', 'value':app['person']['email']},
                    151795772:app['person']['home_lc']['name'],
                    151795769:"0 - APPROVED AND UNCONTACTED",
                    151818116:app['person']['referral_type'],
                    159966006:'Yes',
                    }
                new_item = p_api.create_item({'fields':attributes})
                item_id = new_item['item_id']
                p_api.comment('item', item_id, {'value': "This approval belongs to an EP who hasn't been loaded yet. It shouldn't had gotten to this stage at all, this means something is really really wrong @[Camilo Forero](user:1707071)"})
                print("No EP was found, created")
            else: #FOund more than one, why, which one is it, help, abort
                print("######ERROR#####")
                print('Error, more than one item found')
                print("")
                continue
            modified_eps[app['person']['email']] = item_id
        else: #We already know this EP's PODIO ID
            print ("Found in previously loaded approvals, just add the comment")
            item_id = modified_eps[app['person']['email']]
        p_api.updateItem(item_id, {159728809:{'start_date':(datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')}})
        p_api.comment('item', item_id, {
            'value': "Congratulations! This person has been approved to the %s project '%s' in %s, %s (link: https://experience.aiesec.org/#/opportunities/%s/)" % (
                app['opportunity']['programmes']['short_name'],
                app['opportunity']['title'],
                app['opportunity']['office']['name'],
                app['opportunity']['office']['country'],
                app['opportunity']['id']
                )})
        attributes_2 = { # This is for creating a new approval at the VD space
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
            }
        if tl_responsible:
            attributes_2[157144215] = {'value':{'id': tl_responsible, 'type':'user'}},
        if tm_responsible:
            attributes_2[157144216] = {'value':{'id': tm_responsible, 'type':'user'}},
        if university:
            attributes_2[162269467] = {'value': university},
        if university_year:
            attributes_2[161921092] = {'value': university_year},
        p_api_2.create_item({'fields':attributes_2})
        print("%s has been added to the PODIO application for Value Delivery" % app['person']['email'])

def load_bangladesh_ogx_realized(apps, ex_api, *args, **kwargs):
    p_api = api.PodioApi(19600457) #With credentials for the VD application
    modified_eps = {} #Here it saves the EPs that have already been searched and found in PODIO, so it is not done again
    for app in apps['items']:
        print("Updating realizations of %s in Value Delivery space" % app['person']['full_name'])
        if  app['person']['email'] not in modified_eps:
            search = p_api.search_in_application_v2(app_id=19600457, ref_type='item', query=app['id'])
            if len(search['results']) == 1: #Found exactly one, as it should be
                # Initializes variables that may or may not be in the consideration space, to be transferred later to the VD space if they exist
                # gets the item
                item_id = search['results'][0]['id']
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
                    157141798:'2 - Realized',
                    }
                new_item = p_api.create_item({'fields':attributes})
                item_id = new_item['item_id']
                p_api.comment('item', item_id, {'value': "This realization belongs to an EP who hasn't been loaded yet. It is probably from an approval that happened before the start of the quarter @[Camilo Forero](user:1707071)"})
                print("No EP was found, created in the space")
            else: #FOund more than one, why, which one is it, help, abort
                print("######ERROR#####")
                print('Error, more than one item found')
                print("")
                continue
            modified_eps[app['person']['email']] = item_id
        else: #We already know this EP's PODIO ID
            print ("Found in previously loaded approvals, just add the comment")
            item_id = modified_eps[app['person']['email']]

        #p_api.updateItem(item_id, {159728809:{'start_date':(datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')}}) # No need to update realization date... yet. But maybe it will be needed in the future. Remember to put the right field_id when that time comes
        p_api.comment('item', item_id, {
            'value': "Congratulations! This person has been realized!"
                })

def load_bangladesh_ogx_standards(apps, ex_api):
    """ 
    This synchronizes the Standards Survey in EXPA with the Standards Tracker in PODIO
    """
    p_api = api.PodioApi(19600457) #With credentials for the VD application
    for app in apps['items']:
        print("Updating standards of %s in Value Delivery space" % app['person']['full_name'])
        search = p_api.search_in_application_v2(app_id=19600457, ref_type='item', query=app['id'])
        if len(search['results']) == 1: #Found exactly one, as it should be
            # Initializes variables that may or may not be in the consideration space, to be transferred later to the VD space if they exist
            # gets the item
            item_id = search['results'][0]['id']
            update_dict = {} 
            update_count = 0
            nps_count = 0
            #Proceed to update the Standards
            for standard in app['standards']:
                standard_field = bangladesh_conf.STANDARDS_FIELDS[standard['position']] # Gets the PODIO field related to the standard that will be updated
                if standard['option'] is None:
                    continue
                elif standard['option'] == "true":
                    update_dict[standard_field] = "Yes"
                elif standard['option'] == "false":
                    update_dict[standard_field] = "No"
                else:
                    raise Exception("Code misfire")
                update_count += 1
            if(update_count == 16):
                update_dict[163432513]  = "Yes - completely"
            elif(update_count >= 14):
                update_dict[163432513]  = "Yes - partially"
            if app['nps_grade'] is not None:
                nps_count += 1
                update_dict[163432514] = "Yes"
                update_dict[166683670] = app['nps_grade']
                print("NPS survey has been updated for this person")
            if(update_count + nps_count > 0):
                p_api.updateItem(item_id, update_dict)
            comment_message = ("A total of %d Standards have been updated according to the EXPA Standards Survey." % update_count)
            if nps_count > 0:
                comment_message += " The NPS was also updated."
            p_api.comment('item', item_id, {
                'value': comment_message
                    })
            print("A total of %d Standards have been updated according to the EXPA Standards Survey" % update_count)
            #item = p_api.get_item(item_id, external_id=False)
        else: #FOund more than one, why, which one is it, help, abort
            print("######ERROR#####")
            print('Error, more than one item found')
            print("")
            continue


days_to_load = 1
def _update_standards():
    ex_api = expaApi.ExpaApi(account='camilo.forero@aiesec.net', fail_attempts=10)
    #Update six weeks after the realization date
    print("Updating right after realization")
    start_date = (datetime.today() - timedelta(days=42 + (days_to_load - 1))).strftime('%Y-%m-%d')
    end_date = (datetime.today() - timedelta(days=42)).strftime('%Y-%m-%d')
    apps = ex_api.get_interactions(interaction='realized', start_date=start_date, end_date=end_date, officeID=2010, program='ogx')
    load_bangladesh_ogx_standards(apps, ex_api)

    #Update seven weeks after the realization date
    print("Updating 1 week after realization")
    start_date = (datetime.today() - timedelta(days=49 + (days_to_load - 1))).strftime('%Y-%m-%d')
    end_date = (datetime.today() - timedelta(days=49)).strftime('%Y-%m-%d')
    apps = ex_api.get_interactions(interaction='realized', start_date=start_date, end_date=end_date, officeID=2010, program='ogx')
    load_bangladesh_ogx_standards(apps, ex_api)

    #Update eight weeks after the realization date
    print("Updating 2 weeks after realization")
    start_date = (datetime.today() - timedelta(days=56 + (days_to_load - 1))).strftime('%Y-%m-%d')
    end_date = (datetime.today() - timedelta(days=56)).strftime('%Y-%m-%d')
    apps = ex_api.get_interactions(interaction='realized', start_date=start_date, end_date=end_date, officeID=2010, program='ogx')
    load_bangladesh_ogx_standards(apps, ex_api)


load_list = [
    (load_bangladesh_ogx_opens, {'interaction':'registered', 'days': days_to_load,
        'officeID': 2010, 'today': False, 'program': 'ogx'}),
    (load_bangladesh_ogx_apps, {'interaction':'applied', 'days': days_to_load,
        'officeID': 2010, 'today': False, 'program': 'ogx'}),
    (load_bangladesh_ogx_accepted, {'interaction':'accepted', 'days': days_to_load,
        'officeID': 2010, 'today': False, 'program': 'ogx'}),
    (load_bangladesh_ogx_approved, {'interaction':'approved', 'days': days_to_load,
        'officeID': 2010, 'today': False, 'program': 'ogx'}),
    (load_bangladesh_ogx_realized, {'interaction':'realized', 'days': days_to_load,
        'officeID': 2010, 'today': False, 'program': 'ogx'}),
]


def bangladesh_daily_load():
    print("loading in " + str(datetime.now()))
    bd_api = expaApi.ExpaApi(account='camilo.forero@aiesec.net', fail_attempts=10)
    for function, kwargs in load_list:
        try:
            print("Attempting to load all {interaction} people of the {program} program from {days} days ago in office {officeID}".format(**kwargs))
            function(bd_api.get_past_interactions(**kwargs), ex_api=bd_api)
            print("Success. Sleeping to allow PODIO search function to update itself")
            from time import sleep
            sleep(30)
        except (expaApi.APIUnavailableException) as e:
            print("Failure: EXPA is not working, the API is unavailable")
            print(e)
        except api.api.transport.TransportException as e:
            print("Failure: PODIO transport exception")
            print(e)
#        except Exception as e:
#            print("Failure: Unknown error")
#            print(kwargs)
#            print(e)
    _update_standards()

    print("Todas las cargas han sido exitosas")



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

            
    

