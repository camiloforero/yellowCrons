#encoding:utf-8
from __future__ import unicode_literals, print_function
from datetime import datetime, timedelta
from django_podio import api
from django_mailTemplates import mailApi

from . import models, tools


def mark_not_interested():
    """
    Here are centralized all the scripts that require an specific action according to a PODIO field to happen after a day, two days, a week and so on.
    """
    cons_api = api.PodioApi(19156174) # Credentials for the applicant conversion application
    items = cons_api.get_items_by_view(37277816)
    for item in items:
        params = {
            151795769:"-2 - Not interested - Explain why in the comments"
        }
        cons_api.updateItem(item['item'], params)
        cons_api.comment('item', item['item'], {'value': "This person was marked as not interested automatically by a script, because they were too old (before February 1st)"})

def _filter_comment(api, filters, message, tag_type, tag_value):
    items = api.get_filtered_items(filters=filters)
    for item in items:
        l_message = message
        print(item['values'][151795764]['value'])
        print(item['values'][151795769]['value'])
        if tag_type == 'podio_field':
            try:
                l_message +=  tools.tags_from_podio_contacts([item['values'][tag_value]])
            except KeyError:
                pass
        elif tag_type == 'queryset':
            l_message += tools.tags_from_queryset(models.Role.objects.filter(role=tag_value))
        print(l_message)
        api.comment('item', item['item'], {'value': l_message})
        print()
        

def time_based_update(cons_api, vd_api):
    """
    Here are centralized all the scripts that require an specific action according to a PODIO field to happen after a day, two days, a week and so on.
    """
    #Notify the TL if uncontacted after three days
    filters={
        151950042:{"from": "-3d", "to": "-3d",},
        151795769:[1],
        }
    message = "This person has not been contacted after three days. Please check what is going on. "
    _filter_comment(cons_api, filters, message, tag_type ='podio_field', tag_value=151795765)


    #Notify the LCVP if uncontacted after 5 days
#    filters={
#        151950042:{"from": "-6d", "to": "-6d",},
#        151795769:[1],
#        }
#    message = "This person has not been contacted after five days. Please check what is going on. "
#    _filter_comment(cons_api, filters, message, tag_type ='podio_field', tag_value=165527150)


    #Notify the oGV responsible of uncontacted after 7 days
    filters={
        151950042:{"from": "-7d", "to": "-7d",},
        151795769:[1],
        }
    message = "This person has not been contacted after seven days. Please check what is going on. "
    _filter_comment(cons_api, filters, message, tag_type='queryset', tag_value='mcvp_ogv')

    #FOr EPs applied and accepted but uncontacted, Notify the TL next day to tell them to follow up ASAP
    filters = {
        151950042:{"from": "-1d", "to": "-1d",},
        151795769:[16, 17, 18],
        }
    message = "This person has already applied, but hasn't been contacted yet. Please check what is going on. "
    _filter_comment(cons_api, filters, message, tag_type ='podio_field', tag_value=151795765)


    #Notify the LCVP after two days if still uncontacted
#    filters = {
#        151950042:{"from": "-3d", "to": "-3d",},
#        151795769:[16, 17, 18],
#        }
#    message = "This person has already applied, but hasn't been contacted yet. Please check what is going on. "
#    _filter_comment(cons_api, filters, message, tag_type ='podio_field', tag_value=165527150)


    #Notify Louise if still uncontacted
    filters = {
        151950042:{"from": "-3d", "to": "-3d",},
        151795769:[16, 17, 18],
        }
    message = "This person has already applied, but hasn't been contacted yet. Please check what is going on. "
    _filter_comment(cons_api, filters, message, tag_type='queryset', tag_value='mcvp_ogv')


    #Notify the TM after three days waiting for answer to follow up
    filters = {
        159724899:{"from": "-3d", "to": "-3d",},
        151795769:[15],
        }

    message = "We are still waiting for an answer for this person. It is time to follow up :) " 
    _filter_comment(cons_api, filters, message, tag_type ='podio_field', tag_value=151795767)


    #Notify the TL after five days to follow up
    filters = {
        159724899:{"from": "-5d", "to": "-5d",},
        151795769:[15],
        }
    message = "This person hasn't been followed up for five days. Please review "
    _filter_comment(cons_api, filters, message, tag_type ='podio_field', tag_value=151795765)

    #Notify the LCVP oGV if the EP has been 15 days without being contacted
    filters = {
        159724899:{"from": "-15d", "to": "-15d",},
        151795769:[15],
        }
    message = "This person hasn't been followed up for a week. "
    _filter_comment(cons_api, filters, message, tag_type ='podio_field', tag_value=165527150)

    #Notify TM after two days of being a warm lead if they have not applied yet
    filters = {
        159724899:{"from": "-3d", "to": "-3d",},
        151795769:[12],
        }
    message = "We are still waiting for this person to apply. It is time to follow up :) "
    _filter_comment(cons_api, filters, message, tag_type ='podio_field', tag_value=151795767)

    
    #Notify TM after two days of application to see if they are following up with the opportunity manager.
    filters = {
        158519539:{"from": "-3d", "to": "-3d",},
        151795769:[5],
        }
    message = "This person has last applied three days ago without being accepted.. Remember to follow up with them and with their opportunity managers to continue with the process "
    _filter_comment(cons_api, filters, message, tag_type ='podio_field', tag_value=151795767)

def vd_scripts(vd_api):
    print("Sending second week email")
    items = vd_api.get_filtered_items(filters={163451022:{"from": "-2w", "to": "-2w",}})
    email = mailApi.MailApi("Week2GVEmail")
    from_email = 'aiesec@aiesecbd.org'
    for item in items:
        context = {
            "ep_firstname":item['values'][157131079]['value']
        }
        to_email = [item['values'][157141800]['value']]
        email.send_mail(from_email, to_email, context)
        print("Email sent to %s!" % to_email)

    print("Sending fifth week email")
    items = vd_api.get_filtered_items(filters={163451022:{"from": "-5w", "to": "-5w",}})
    email = mailApi.MailApi("Week5GVEmail")
    from_email = 'aiesec@aiesecbd.org'
    for item in items:
        context = {
            "ep_firstname":item['values'][157131079]['value']
        }
        to_email = [item['values'][157141800]['value']]
        email.send_mail(from_email, to_email, context)
        comment_message = "Fifth week email successfully sent! Remember to send the EP the six week challenge for the week and to ask him about the standards" + tools.tags_from_podio_contacts([item['values'][157144216]])
        vd_api.comment('item', item['item'], {
            'value': comment_message 
                })
        print("Email sent to %s!" % to_email)


def update_widgets():
    vd_api = api.PodioApi(19600457, client=True)
    config = {
      "layout": "table",
      "app_id": 19156174,
      "unit": "leads",
      "calculation": {
        "sorting": "value_desc",
        "aggregation": "count",
        "limit": 6,
        "filters": [
          {
            "values": [
              None,
              1,
              16,
              17,
              18
            ],
            "key": 151795769
          },
          {
            "values": {
              "to": (datetime.today() - timedelta(days=3)).strftime("%Y-%m-%d")
            },
            "key": 151950042
          }
        ],
        #"formula": null,
        "grouping": {
          "type": "field",
          #"sub_value": null,
          "value": 151795765
        },
      }
    }
    vd_api.update_widget(71592280, config=config)

    # per TL
    config = {
      "layout": "table",
      "app_id": 19156174,
      "unit": "leads",
      "calculation": {
        "sorting": "value_desc",
        "aggregation": "count",
        "limit": 6,
        "filters": [
          {
            "values": [
              None,
              1,
              16,
              17,
              18
            ],
            "key": 151795769
          },
          {
            "values": {
              "to": (datetime.today() - timedelta(days=3)).strftime("%Y-%m-%d")
            },
            "key": 151950042
          }
        ],
        "grouping": {
          "type": "field",
          "value": 151795767
        },
      }
    }
    vd_api.update_widget(72703132, config=config)
    #EPs who go on exchange soon and haven't been realized
    config = {
      "layout": "table",
      "app_id": 19600457,
      "unit": "customer",
      "calculation": {
        "sorting": "value_desc",
        "aggregation": "count",
        "limit": 5,
        "filters": [
          {
            "values": {
              "to": 99,
              "from": None 
            },
            "key": 163432667
          },
          {
            "values": {
              "to": (datetime.today() + timedelta(days=14)).strftime("%Y-%m-%d")
            },
            "key": 157141797
          },
          {
            "values": [
              4
            ],
            "key": 157141798
          }
        ],
        "grouping": {
          "type": "field",
          "value": 157144216
        },
      }
    }
    vd_api.update_widget(77289399, config=config)

    config = {
      "app_id": 19600457,
      "unit": "customers",
      "layout": "table",
      "calculation": {
        "sorting": "value_desc",
        "aggregation": "count",
        "limit": 10,
        "filters": [
          {
            "values": {
              "to": 66,
              "from": 0
            },
            "key": 163432756
          },
          {
            "values": [
              4
            ],
            "key": 157141798
          },
          {
            "values": {
              "to": (datetime.today() - timedelta(days=14)).strftime("%Y-%m-%d")
            },
            "key": 163451022
          },
        ],
        "grouping": {
          "type": "field",
          "value": 157144216
        },
      },
    }
    vd_api.update_widget(77291037, config=config)

    config = {
      "layout": "table",
      "app_id": 19600457,
      "unit": "customers",
      "calculation": {
        "sorting": "value_desc",
        "aggregation": "count",
        "limit": 5,
        "filters": [
          {
            "values": {
              "to": 99,
              "from": 0
            },
            "key": 163432756
          },
          {
            "values": {
              "to": (datetime.today() - timedelta(weeks=5)).strftime("%Y-%m-%d")
            },
            "key": 163451022
          },
          {
            "values": [
              4
            ],
            "key": 157141798
          }
        ],
        "grouping": {
          "type": "field",
          "value": 157144216
        }
      }
    }
    vd_api.update_widget(77291582, config=config)

def run():
    cons_api = api.PodioApi(19156174) # Credentials for the applicant conversion application
    vd_api = api.PodioApi(19600457) #With credentials for the VD application
    time_based_update(cons_api=cons_api, vd_api=vd_api)
    vd_scripts(vd_api=vd_api)
    update_widgets() # This one uses a client PODIO API, so it has it's own API object
