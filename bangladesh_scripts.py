#encoding:utf-8
from __future__ import unicode_literals, print_function
import random
from datetime import datetime, timedelta
from django_podio import api
from django_expa import expaApi
from django_mailTemplates import mailApi
from . import bangladesh_conf, models, tools

days_to_load = 5


def parse_date(old_date):
    datetime.strptime('%Y-%m-%d')


def find_or_create_open_in_podio(p_api, open_expa_id, managers, *args, **kwargs):
    # search is this person is already under PODIO
    search = p_api.search_in_application_v2(app_id=19156174, ref_type='item', query=open_expa_id)
    if len(search['results']) >= 1: #Found exactly one, as it should be
        print("%d result was already found, skipping" % len(search['results']))
    else:
        create_open_in_podio(p_api, open_expa_id, managers, *args, **kwargs)

def create_open_in_podio(p_api, open_expa_id, managers, *args, **kwargs):
    person = kwargs['ex_api'].getPerson(unicode(open_expa_id))
    alignment = kwargs['ex_api'].get_lc_alignment(unicode(open_expa_id))
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
            151950042: {'start_utc': person['created_at'].replace('T', ' ').replace('Z', '')},
            151795766: {'type': 'work', 'value': person['email']},
            151795772: {'value': person['home_lc']['name']},
            151795769: {'value': '0 - Uncontacted'},
            151818116: {'value': referral_type},
            159966006: profile_complete,
            151832581: alignment,
            }
        if(person['dob']):
            attributes[154339943] = {'start_date': person['dob']}
        try:
            manager = managers.get(expa_id=person['managers'][0]['id'])
            attributes[151795765] = {'value':{'id': manager.podio_id, 'type':'user'}},
        except Exception as e:
            print(e)
            pass
        if(person['contact_info']):
            attributes[151795768] = {'type': 'mobile', 'value': '%s%s' % (person['contact_info']['country_code'], person['contact_info']['phone'])},
    except Exception as e:
        print("Argument load unsuccessful, check item for errors")
        print(e)
        print(person)
        raise e
    try:
        p_api.create_item({'fields':attributes})
        print("%s has been added al espacio de OGX de opens" % person['email'])
        print("")
    except Exception as e:
        print(e)
        print("Error adding %s (expa_id %s) to the Bangladesh opens space" % (person['full_name'], person['id']))
        continue

def update_open_in_podio():
    pass

def create_approval_in_podio():
    pass

def update_approval_in_podio():
    pass

def multidaily_open_load():
    date = datetime.now().strftime('%Y-%m-%d')
    kwargs = {'interaction':'registered', 'start_date': date,
        'officeID': 2010, 'program': 'ogx', 'end_date': date}
    bd_api = expaApi.ExpaApi(account='louise.kim@aiesec.net', fail_attempts=10)
    load_bangladesh_ogx_opens_v2(bd_api.get_interactions(**kwargs), ex_api=bd_api)


def load_bangladesh_ogx_opens_v2(people, *args, **kwargs):
    """
    This method loads all new oGX opens into the PODIO workspace. It works a bit differently than the usual; it also autoassigns EP managers to each EP it loads through EXPA before saving them in PODIO. This requires taking an extra step
    This one method also searches for duplicates in PODIO before loading them.
    """
    p_api = api.PodioApi(19156174)
    managers = models.Member.objects.filter()

    for open in people['items']:
        find_or_create_open_in_podio(p_api, open['id'], managers, *args, **kwargs)


def load_bangladesh_ogx_apps(apps, *args, **kwargs):
    p_api = api.PodioApi(19156174)
    modified_eps = {}
    for app in apps['items']:
        print("Loading application of %s" % app['person']['full_name'], end=' - ')
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

        if  app['person']['email'] not in modified_eps or is_partner:
            search = p_api.search_in_application_v2(app_id=19156174, ref_type='item', query=app['person']['id'])
            if len(search['results']) == 1: #Found exactly one, as it should be
                item_id = search['results'][0]['id']
                item = p_api.get_item(item_id, external_id=False)
                stage = item['values'][151795769]['value']
                stage_number = int(stage.split(' - ')[0])
                print(stage)

                if 167580470 not in item['values']:
                    update_params[167580470] = 0
                else:
                    update_params[167580470] = int(float(item['values'][167580470]['value']))

                if is_partner:
                    update_params[167580470] += 1

                if 151832580 not in item['values'] or 151832581 not in item['values']: #Checks if the university is there in the EP or not. If not, gets it from EXPA
                    person = kwargs['ex_api'].getPerson(item['values'][151795764]['value'])
                    update_params[151832581] = person['academic_experiences'][0]['organisation_name']


                if stage_number <= -5:
                    tags = models.Role.objects.filter(role__in=['mcvp_di', 'mcvp_ogv'])
                    p_api.comment('item', item_id, {'value': "INFO: An ep who is inelegible for exchange has applied in EXPA. Check it out " + tools.tags_from_queryset(tags) })
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

                if 158519539 not in item['values']: #Checks if the "last application date" field does not exist. This means that this is the EP's first application
                    update_params[159724898] = app_date #Updates the first application date
                    email = mailApi.MailApi("first_application_email")
                    if 151795767 in item['values']: # Checks if there is a TM responsible.
                        from_email = item['values'][151795767]['value']['mail'][0]
                        manager_name = item['values'][151795767]['value']['name']
                    elif 151795765 in item['values']:
                        from_email = item['values'][151795765]['value']['mail'][0]
                        manager_name = item['values'][151795765]['value']['name']
                    else:
                        print("No TL or TM manager, no first application email will be sent")
                        continue

                    context = {
                        'ep_first_name': item['values'][151791638]['value'],
                        'manager_name': manager_name,
                        }
                    to_email = [item['values'][151795766]['value']]
                    try:
                        email.send_mail(from_email, to_email, context)
                        p_api.comment('item', item_id, {'value': "An email has been sent successfully, for first application, from %s to %s" % (from_email, to_email)})
                        print("First application email sent")
                    except Exception as e:
#                        p_api.comment('item', item_id, {'value': "Warning: There was an error sending the email: %s . Check this out @[%s](user:%s)" % (e, di_responsible['name'],di_responsible['user_id']) })
                        pass
                        print("First application email failed")
                        #comment
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
                print("No EP was found, with this application, created")
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


def load_bangladesh_ogx_accepted(apps, ex_api, date, *args, **kwargs):
    """
    Loads all accepted EPs into PODIO
    has an extra argument date because the API doesn't show easily the acceptance date when grabbing a group of acceptances.
    """
    p_api = api.PodioApi(19156174)
    modified_eps = {}
    for app in apps['items']:
        print("Loading acceptance of %s" % app['person']['full_name'], end=' - ')
        if  app['person']['email'] not in modified_eps:
            search = p_api.search_in_application_v2(app_id=19156174, ref_type='item', query=app['person']['id'])
            if len(search['results']) == 1: #Found exactly one, as it should be
                item_id = search['results'][0]['id']
                item = p_api.get_item(item_id, external_id=False)
                update_dict = {
                    169759824: {'start_date': date},
                }
                if 159728808 not in item['values']:
                    update_dict[159728808] = {'start_date': date}
                stage = item['values'][151795769]['value']
                stage_number = int(stage.split(' - ')[0])
                print(stage)
                if stage_number <= -5:
                    print("EP is not elegible for exchange, ignoring...")
                    tags = models.Role.objects.filter(role__in=['mcvp_di', 'mcvp_ogv'])
                    p_api.comment('item', item_id, {'value': "ALERT: An ep who was marked as inelegible in PODIO has been accepted in EXPA. This case should bechecked immediately" + tools.tags_from_queryset(tags)})
                elif stage_number <= 0:
                    update_dict[151795769] = '0 - ACCEPTED AND UNCONTACTED'
                    print("EP has been accepted while being uncontacted, updated")
                elif stage_number == 1 or stage_number == 2 or stage_number == 3:
                    update_dict[151795769] = '4 - Contacted and accepted at least once'
                    print("EP has been accepted, updated")
                elif stage_number > 3:
                    print("This EP has already been accepted, or more, ignoring...")
                p_api.updateItem(item_id, update_dict)
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
        print("Updating approval of %s in applicants space" % app['person']['full_name'], end='')
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
                    tl_responsible = item['values'][151795765]
                if 151795767 in item['values']:
                    tm_responsible = item['values'][151795767]
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
                    tags = models.Role.objects.filter(role__in=['mcvp_di', 'mcvp_ogv'])
                    p_api.comment('item', item_id, {'value': "ALERT: An ep who had never been contacted according to PODIO has now been approved on EXPA. This case should be checked immediately" + tools.tags_from_queryset(tags)})
                elif stage_number < 0:
                    print("Inelegible EP was approved?")
                    tags = models.Role.objects.filter(role__in=['mcvp_di', 'mcvp_ogv'])
                    p_api.comment('item', item_id, {'value': "ALERT: An ep who was marked as inelegible in PODIO has been approved in EXPA. This case should bechecked immediately" + tools.tags_from_queryset(tags)})
                elif stage_number == 1 or stage_number == 2 or stage_number == 3 or stage_number == 4:
                    p_api.updateItem(item_id, {151795769:'7 - Approved', 154339943:{'start_date':app['person']['dob']}})
                    print("EP has been approved, updated")
                    tags = models.Role.objects.filter(role__in=['mcvp_di', 'mcvp_ogv'])
                    p_api.comment('item', item_id, {'value': "ALERT: An ep who hasn't requested a contract virtually in PODIO has been approved in EXPA. Maybe they signed a physical contract? Either way, this case should bechecked immediately " + tools.tags_from_queryset(tags)})
                elif stage_number == 5:
                    print("This EP has requested an invoice, updating...")
                    p_api.updateItem(item_id, {151795769:'7 - Approved', 154339943:{'start_date':app['person']['dob']}})
                    tags = models.Role.objects.filter(role__in=['mcvp_di', 'mcvp_ogv'])
                    p_api.comment('item', item_id, {'value': "NOTE: An ep who hasn't been marked as paid in PODIO has been approved in EXPA. It is important to start following this procedure now, to avoid unpaid approvals getting through in the future. " + tools.tags_from_queryset(tags)})
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
        comment = "Please update the realization date of this EP "
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
            attributes_2[157144215] = {'value':{'id': tl_responsible['value']['user_id'], 'type':'user'}},
            comment += " " + tools.tags_from_podio_contacts([tl_responsible])
        if tm_responsible:
            attributes_2[157144216] = {'value':{'id': tm_responsible['value']['user_id'], 'type':'user'}},
            comment += " " + tools.tags_from_podio_contacts([tm_responsible])
        if university:
            attributes_2[162269467] = {'value': university},
        if university_year:
            attributes_2[161921092] = {'value': university_year},
        new_item = p_api_2.create_item({'fields':attributes_2})
        p_api_2.comment('item', new_item['item_id'], {'value': comment})

        print("%s has been added to the PODIO application for Value Delivery" % app['person']['email'])

def load_bangladesh_ogx_realized(apps, ex_api, *args, **kwargs):
    p_api = api.PodioApi(19600457) #With credentials for the VD application
    for app in apps['items']:
        print("Updating realizations of %s in Value Delivery space" % app['person']['full_name'])
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
            update_dict= {
                157141798:'2 - Realized',
                163451022:{'start_utc':app['date_realized'].replace('T', ' ').replace('Z', '').replace('+00:00', '')},
                168656289:{'start_utc':app['experience_end_date'].replace('T', ' ').replace('Z', '').replace('+00:00', '')},
            }
            if stage_number == 1:
                print("EP has been realized, updated")
            elif stage_number < 0:
                print("Inelegible EP was realized?")
                update_dict[157141798] = '-20 - REPORT TO ICB'
                tags = models.Role.objects.filter(role__in=['mcvp_di', 'mcvp_ogv'])
                p_api.comment('item', item_id, {'value': "ALERT: An ep who was marked as break approval or break realization in PODIO has been realizeded in EXPA. This case should bechecked immediately " + tools.tags_from_queryset(tags)})
            elif stage_number > 1: #Higher than an approval already
                tags = models.Role.objects.filter(role__in=['mcvp_di'])
                p_api.comment('item', item_id, {'value': "NOTE: An ep who was in a sate higher than realized has been marked as just realized. Check this out, " + tools.tags_from_queryset(tags) })
            p_api.updateItem(item_id, update_dict)
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
                168656289:{'start_utc':app['experience_end_date'].replace('T', ' ').replace('Z', '').replace('+00:00', '')},
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

        #p_api.updateItem(item_id, {159728809:{'start_date':(datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')}}) # No need to update realization date... yet. But maybe it will be needed in the future. Remember to put the right field_id when that time comes
        p_api.comment('item', item_id, {
            'value': "Congratulations! This person has been realized!"
                })

def load_bangladesh_ogx_finished(apps, ex_api, *args, **kwargs):
    p_api = api.PodioApi(19600457) #With credentials for the VD application
    for app in apps['items']:
        print("Updating finished status of %s in Value Delivery space" % app['person']['full_name'])
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
            if stage_number == 2:
                p_api.updateItem(item_id, {
                    157141798:'3 - Finished',
                    })
                print("EP has finished their experience according to EXPA, updated")
            elif stage_number < 0:
                print("Inelegible EP has finished?")
                tags = models.Role.objects.filter(role__in=['mcvp_di', 'mcvp_ogv'])
                p_api.comment('item', item_id, {'value': "ALERT: An ep who was marked as break approval realization in PODIO has been finished in EXPA. This case should be checked immediately " + tools.tags_from_queryset(tags)})
            elif stage_number > 2: #Higher than an approval already
                tags = models.Role.objects.filter(role__in=['mcvp_di'])
                p_api.comment('item', item_id, {'value': "NOTE: An ep who was in a sate higher than finished has been marked as just finished. Check this out, " + tools.tags_from_queryset(tags) })
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
                168656289:{'start_utc':app['experience_end_date'].replace('T', ' ').replace('Z', '').replace('+00:00', '')},
                157141798:'3 - Finished',
                }
            new_item = p_api.create_item({'fields':attributes})
            item_id = new_item['item_id']
            p_api.comment('item', item_id, {'value': "This finished belongs to an EP who hasn't been loaded yet. WHYYYYYYYY @[Camilo Forero](user:1707071)"})
            print("No EP was found, created in the space")
        else: #FOund more than one, why, which one is it, help, abort
            print("######ERROR#####")
            print('Error, more than one item found')
            print("")
            continue

        #p_api.updateItem(item_id, {159728809:{'start_date':(datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')}}) # No need to update realization date... yet. But maybe it will be needed in the future. Remember to put the right field_id when that time comes
        p_api.comment('item', item_id, {
            'value': "Congratulations! This person has been finished! Remember to set up the debrief date with them."
                })

def load_bangladesh_ogx_standards(apps, ex_api):
    """
    This synchronizes the Standards Survey in EXPA with the Standards Tracker in PODIO
    """
    p_api = api.PodioApi(19600457) #With credentials for the VD application
    for app in apps['items']:
        update_application_standards(app, p_api, ex_api)


def update_application_standards(app, p_api, ex_api):
    """
    This synchronizes the Standards Survey in EXPA with the Standards Tracker in PODIO
    """
    print("Updating standards of %s in Value Delivery space" % app['person']['full_name'])
    search = p_api.search_in_application_v2(app_id=19600457, ref_type='item', query=app['id'])
    if len(search['results']) == 1: #Found exactly one, as it should be
        # Initializes variables that may or may not be in the consideration space, to be transferred later to the VD space if they exist
        # gets the item
        item_id = search['results'][0]['id']
        update_dict = {}
        update_count = 0
        nps_count = 0
        lda_count = 0
        #Proceed to update the Standards
        for standard in app['standards']:
            standard_field = bangladesh_conf.STANDARDS_FIELDS[standard['position']] # Gets the PODIO field related to the standard that will be updated
            if standard['option'] is None:
                continue # breaks the cycle, the update count won't go up
            elif standard['option'] == "true" or standard['option'] == "not needed":
                update_dict[standard_field] = "Yes"
            elif standard['option'] == "false":
                update_dict[standard_field] = "No"
            else:
                print(standard['option'])
                raise Exception("Code misfire")
            update_count += 1
        if update_count > 0:
            update_dict[170331800] = update_count
        if(update_count == 16):
            update_dict[163432513]  = "Yes - completely"
            if app['status'] == 'completed':
                update_dict[157141798] = '4 - Complete'
            elif app['status'] == 'realized':
                update_dict[157141798] = '4 - Incomplete'

        elif(update_count >= 14):
            update_dict[163432513]  = "Yes - partially"
        if app['nps_grade'] is not None:
            nps_count += 1
            update_dict[163432514] = "Yes"
            update_dict[166683670] = app['nps_grade']
            print("NPS survey has been updated for this person")
        if app['permissions']['has_filled_complete_ldm'] == 'true':
            update_dict[163432515] = "Yes"
            lda_count += 1
        if(update_count + nps_count + lda_count > 0):
            p_api.updateItem(item_id, update_dict)
        comment_message = ("A total of %d Standards have been updated according to the EXPA Standards Survey." % update_count)
        if nps_count > 0:
            comment_message += " The NPS was also updated."
        if lda_count > 0:
            comment_message += " The LDA was also updated."
#        p_api.comment('item', item_id, {
#            'value': comment_message
#                })
        print("A total of %d Standards have been updated according to the EXPA Standards Survey" % update_count)
        #item = p_api.get_item(item_id, external_id=False)
    else: #FOund more than one, why, which one is it, help, abort
        print("######ERROR#####")
        print('Error, more than one item found')
        print("")


def _update_standards():
    ex_api = expaApi.ExpaApi(account='louise.kim@aiesec.net', fail_attempts=10)
    print("Updating EPs currently approved")
    apps=ex_api.make_query(
        routes=['applications'],
        query_params = {
            'filters[is_pop_user]': False,
            'filters[person_committee]': 2010,
            'filters[statuses][]': ['approved'],
            'per_page':200
        }
    )
    apps['items'] = apps['data']
    load_bangladesh_ogx_standards(apps, ex_api)

    print("Updating EPs being currently realized")
    start_date = (datetime.today() - timedelta(days=42 + days_to_load - 1)).strftime('%Y-%m-%d')
    end_date = datetime.today().strftime('%Y-%m-%d')
    apps = ex_api.get_interactions(interaction='realized', start_date=start_date, end_date=end_date, officeID=2010, program='ogx')
    load_bangladesh_ogx_standards(apps, ex_api)

    #Update six weeks after the realization date
    print("Updating right after the experience finishes")
    start_date = (datetime.today() - timedelta(days=(days_to_load - 1))).strftime('%Y-%m-%d')
    end_date = datetime.today().strftime('%Y-%m-%d')
    apps = ex_api.get_interactions(interaction='finished', start_date=start_date, end_date=end_date, officeID=2010, program='ogx')
    load_bangladesh_ogx_standards(apps, ex_api)

    #Update seven weeks after the realization date
    print("Updating 1 week after finished")
    start_date = (datetime.today() - timedelta(days=7 + days_to_load - 1)).strftime('%Y-%m-%d')
    end_date = (datetime.today() - timedelta(days=7)).strftime('%Y-%m-%d')
    apps = ex_api.get_interactions(interaction='finished', start_date=start_date, end_date=end_date, officeID=2010, program='ogx')
    load_bangladesh_ogx_standards(apps, ex_api)

    #Update eight weeks after the realization date
    print("Updating 2 weeks after finished")
    start_date = (datetime.today() - timedelta(days=14 + (days_to_load - 1))).strftime('%Y-%m-%d')
    end_date = (datetime.today() - timedelta(days=14)).strftime('%Y-%m-%d')
    apps = ex_api.get_interactions(interaction='realized', start_date=start_date, end_date=end_date, officeID=2010, program='ogx')
    load_bangladesh_ogx_standards(apps, ex_api)


load_list = [
#    (load_bangladesh_ogx_opens, {'interaction':'registered', 'days': days_to_load,
#        'officeID': 2010, 'today': False, 'program': 'ogx'}),
    (load_bangladesh_ogx_apps, {'interaction':'applied', 'days': days_to_load,
        'officeID': 2010, 'today': False, 'program': 'ogx'}),
    (load_bangladesh_ogx_accepted, {'interaction':'accepted', 'days': days_to_load,
        'officeID': 2010, 'today': False, 'program': 'ogx'}),
    (load_bangladesh_ogx_approved, {'interaction':'approved', 'days': days_to_load,
        'officeID': 2010, 'today': False, 'program': 'ogx'}),
    (load_bangladesh_ogx_realized, {'interaction':'realized', 'days': days_to_load,
        'officeID': 2010, 'today': False, 'program': 'ogx'}),
    (load_bangladesh_ogx_finished, {'interaction':'finished', 'days': days_to_load,
        'officeID': 2010, 'today': False, 'program': 'ogx'}),
]


def bangladesh_daily_load():
    print("loading in " + str(datetime.now()))
    bd_api = expaApi.ExpaApi(account='louise.kim@aiesec.net', fail_attempts=10)
    load_bangladesh_ogx_opens_v2(bd_api.get_past_interactions(interaction='registered', days=days_to_load, officeID=2010, today=False, program='ogx'), ex_api=bd_api)
    date = datetime.now().strftime('%Y-%m-%d')
    for function, kwargs in load_list:
        try:
            print("Attempting to load all {interaction} people of the {program} program from {days} days ago in office {officeID}".format(**kwargs))
            function(bd_api.get_past_interactions(**kwargs), ex_api=bd_api, date=date)
            print("Success. Sleeping to allow PODIO search function to update itself")
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
    bd_api = expaApi.ExpaApi(account='louise.kim@aiesec.net', fail_attempts=10)
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
    bd_api = expaApi.ExpaApi(account='louise.kim@aiesec.net', fail_attempts=10)
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
                    tags = models.Role.objects.filter(role__in=['mcvp_di', 'mcvp_ogv'])
                    p_api.comment('item', item_id, {'value': "ALERT: An ep who was marked as break approval or break realization in PODIO has been realizeded in EXPA. This case should be checked immediately" + tools.tags_from_queryset(tags)})
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
                        163451022:{'start_utc':app['date_realized'].replace('T', ' ').replace('Z', '').replace('+00:00', '')},
                        168656289:{'start_utc':app['experience_end_date'].replace('T', ' ').replace('Z', '').replace('+00:00', '')},
                    })
                    print("EP has been realized, updated")
                elif stage_number < 0:
                    print("Inelegible EP was realiZed?")
                    tags = models.Role.objects.filter(role__in=['mcvp_di', 'mcvp_ogv'])
                    p_api.comment('item', item_id, {'value': "ALERT: An ep who was marked as break approval or break realization in PODIO has been realizeded in EXPA. This case should bechecked immediately " + tools.tags_from_queryset(tags) })
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
    bd_api = expaApi.ExpaApi(account='louise.kim@aiesec.net', fail_attempts=10)
    sync_bangladesh_ogx_realized(bd_api.get_interactions(**kwargs), ex_api=bd_api)

def super_sync_ogx_approved(start_date):
    kwargs = {'interaction':'approved', 'start_date': start_date,
        'officeID': 2010, 'program': 'ogx'}
    bd_api = expaApi.ExpaApi(account='louise.kim@aiesec.net', fail_attempts=10)
    sync_bangladesh_ogx_approved(bd_api.get_interactions(**kwargs), ex_api=bd_api)


def super_sync_ogx_finished(start_date):
    kwargs = {'interaction':'finished', 'start_date': start_date,
        'officeID': 2010, 'program': 'ogx'}
    bd_api = expaApi.ExpaApi(account='louise.kim@aiesec.net', fail_attempts=10)
    sync_bangladesh_ogx_finished(bd_api.get_interactions(**kwargs), ex_api=bd_api)


def fix_skipped_day(date):
    kwargs = {'interaction':'registered', 'start_date': date,
        'officeID': 2010, 'program': 'ogx', 'end_date': date}
    bd_api = expaApi.ExpaApi(account='louise.kim@aiesec.net', fail_attempts=10)
#    kwargs['interaction'] = 'applied'
#    load_bangladesh_ogx_applied(bd_api.get_interactions(**kwargs), ex_api=bd_api)
#    kwargs['interaction'] = 'accepted'
#    load_bangladesh_ogx_accepted(bd_api.get_interactions(**kwargs), ex_api=bd_api)
#    kwargs['interaction'] = 'approved'
#    load_bangladesh_ogx_approved(bd_api.get_interactions(**kwargs), ex_api=bd_api)
    kwargs['interaction'] = 'realized'
    load_bangladesh_ogx_realized(bd_api.get_interactions(**kwargs), ex_api=bd_api)
