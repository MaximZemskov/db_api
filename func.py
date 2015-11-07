import MySQLdb


def db_connect():
    returned_data = MySQLdb.connect(host='localhost', user="db_api", passwd="secret", db="db", charset='utf8')
    return returned_data


def execute(cursor):
    truncate_str = 'truncate table '
    cursor.execute('{0}forums'.format(truncate_str))
    cursor.execute('{0}users'.format(truncate_str))
    cursor.execute('{0}threads'.format(truncate_str))
    cursor.execute('{0}posts'.format(truncate_str))
    cursor.execute('{0}followers'.format(truncate_str))
    cursor.execute('{0}subscriptions'.format(truncate_str))
