#coding:utf-8


def _create_tag(name, podio_id):
    """
        Takes a name and a PODIO_ID and makes it a PODIO-ready tag
    """
    return "@[%s](user:%s)" % (name, podio_id)

def tags_from_queryset(queryset):
    """
        Takes a queryset (IMPORTANT: not an object) and makes PODIO tags out of it 
    """
    ans = ""
    for role in queryset:
        ans += _create_tag(role.member.name, role.member.podio_id)
        ans += " "
    return ans.strip()



def tags_from_podio_contacts(contacts):
    """
    Takes a LIST of PODIO contact objects (the ones usually found in the contact field on an item) and creates a PODIO-ready chain of tags
    """
    ans = ""
    for contact in contacts:
        ans += _create_tag(contact['value']['name'], contact['value']['user_id'])
        ans += " "
    return ans.strip()
