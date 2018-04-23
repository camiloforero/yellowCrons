#coding:utf-8

from django_podio import api
from django_expa import expaApi
from django_mailTemplates import mailApi


def send_performance_email(): 
    p_api = api.PodioApi(19156174)
    email = mailApi.MailApi("Performance email")
    performance = {}
    gbm_date = '2018-04-06'
    recent_items = p_api.get_filtered_items({
        'last_edit_on':{'from':gbm_date}
    })
    for item in recent_items:
        if 151795767 not in item['values']:
            continue
        tm_id = item['values'][151795767]['value']['user_id']
        if tm_id not in performance:
            performance[tm_id] = {
                'contacted': 0,
                'applied': 0,
                'approved': 0,
                'name': item['values'][151795767]['value']['name'],
            }
        if 151950042 in item['values']:
            registration_date =  item['values'][151950042]['value']['start_date']
        status = item['values'][151795769]['value']
        status_number = status.split(' - ')[0]
        if status_number != 0: #if uncontacted, ignores everything
            if registration_date >= gbm_date:
                performance[tm_id]['contacted'] += 1
            elif 159724899 in item['values']:
                contacted_date = item['values'][159724899]['value']['start_date']
                if contacted_date >= gbm_date:
                    performance[tm_id]['contacted'] += 1

            if 158519539 in item['values']:
                application_date = item['values'][158519539]['value']['start_date']
                if application_date >= gbm_date:
                    performance[tm_id]['applied'] += 1
            if 159728809 in item['values']:
                approval_date = item['values'][159728809]['value']['start_date']
                if approval_date >= gbm_date:
                    performance[tm_id]['approved'] += 1
    status = email.send_mail('camilo.forero@aiesec.net', ['camilo.forero@aiesec.net', 'louise.kim@aiesec.net'], {'performance': performance})
    print(status)
    #print(performance)

def send_partners_email(): 
    ex_api = expaApi.ExpaApi(account='camilo.forero@aiesec.net')
    email = mailApi.MailApi("partners_analytics_mail")
    country_partners = [
        {'id':1609, 'name': 'Egypt'},
        {'id':1539, 'name': 'Indonesia'},
        {'id':1585, 'name': 'India'},
        {'id':1623, 'name': 'Sri Lanka'},
        {'id':112, 'name': 'Nepal'},
        {'id':1607, 'name': 'Thailand'},
        {'id':1622, 'name': 'Turkey'},
        {'id':1611, 'name': 'Malaysia'},
    ]
    results = {}
    for partner in country_partners:
        results[partner['name']] = ex_api.e2e_analytics(2010, partner['id'], 'ogv', '2018-04-01')
    email.send_mail('camilo.forero@aiesec.net', ['louise.kim@aiesec.net', 'camilo.forero@aiesec.net'], {'results': results})

def run():
    send_partners_email()
    send_performance_email()
