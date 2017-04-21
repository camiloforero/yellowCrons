#encoding:utf-8
from __future__ import unicode_literals, print_function
from datetime import datetime
from django_expa import expaApi
from django_mailTemplates import mailApi

CORREOS = {
	1611: 'administrator@aiesec.my',
	1500: 'kedah-perlis@aiesec.my',
	97:'cu@aiesec.my',
	555:'johorbahru@aiesec.my',
	1674:'kuching@aiesec.my',
	1217:'upm@aiesec.my',
	1326:'penang@aiesec.my',
	480:'tu@aiesec.my',
	101:'sunway@aiesec.my',
	102:'unmc@aiesec.my',
	1213:'ukm@aiesec.my',
	99:'ump@aiesec.my',
	1962:'utar@aiesec.my',
	103:'utp@aiesec.my',
	619:'um@aiesec.my',
}

def malaysia_daily_load():
    print("Cargando en " + str(datetime.now()))
    ex_api = expaApi.ExpaApi(fail_attempts=10)
    try:
        malaysia_opens = ex_api.get_past_interactions('registered', 1, 1611, today=False, filters={'filters[has_managers]':False})
        send_malaysia_opens_emails(malaysia_opens)
        print("Los correos a los LCs han sido enviados exitosamente")
    except (expaApi.APIUnavailableException) as e:
        print("Error de EXPA cargando a los EPs aprobados de OGX")
        print(e)
#    except Exception as e:
#        print("Unknown error")
#        print(e)

    print("Todas las cargas han sido exitosas")

def send_malaysia_opens_emails(eps):
    lcs = {}
    for ep in eps['items']:
        if len(ep['managers']) == 0:
            lc_id = ep['home_lc']['id']
            ep_info = {
                'name': ep['full_name'],
                'expa_link': "experience.aiesec.org/#/people/" + str(ep['id']),
            }
            try:
                lc = lcs[lc_id]
                lc['unassigned'].append(ep_info)

            except KeyError:
                lcs[lc_id] = {'lc_name': ep['home_lc']['name'], 'unassigned': [ep_info], 'email':CORREOS[lc_id]}
    mail_generator = mailApi.MailApi('opens_email')
    for lc_id, data in lcs.items():
        mail_generator.send_mail(
            'information@aiesec.my',
            [data['email'], 'youthexperience@aiesec.my'],
            data,
            sender_name="IM AIESEC in Malaysia"
            )

