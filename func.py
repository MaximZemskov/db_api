import MySQLdb
from flask import jsonify


def db_connect():
    returned_data = MySQLdb.connect(host='localhost', user="db_api", passwd="secret", db="db", charset='utf8')
    return returned_data


def clear_execute(cursor):
    truncate_str = 'TRUNCATE TABLE '
    cursor.execute('{0}forums'.format(truncate_str))
    cursor.execute('{0}users'.format(truncate_str))
    cursor.execute('{0}threads'.format(truncate_str))
    cursor.execute('{0}posts'.format(truncate_str))
    cursor.execute('{0}followers'.format(truncate_str))
    cursor.execute('{0}subscriptions'.format(truncate_str))


def status_execute(cursor):
    truncate_str = 'SELECT COUNT(*) FROM '
    data_array = []
    names_array = ['users', 'threads', 'forums', 'posts']
    for name in names_array:
        cursor.execute(truncate_str + name)
        data_array.append(cursor.fetchone()[0])
    code = 0
    return_data = {"code": code, "response": {"user": data_array[0],
                                              "thread": data_array[1],
                                              "forum": data_array[2],
                                              "post": data_array[3]}}
    return jsonify(return_data)
