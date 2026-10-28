from identity.accounts import can_login


def can_open(account, membership):
    return can_login(account) and membership['status'] == 'active'


def remove(membership):
    return dict(membership, status='removed')
