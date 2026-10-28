def can_login(account):
    return account['status'] == 'active'


def suspend(account):
    return dict(account, status='suspended')
