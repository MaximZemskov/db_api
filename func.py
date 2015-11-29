import MySQLdb
from flask import jsonify, request


def db_connect():
    returned_data = MySQLdb.connect(host='localhost', user="db_api", passwd="secret", db="db", charset='utf8')
    return returned_data


def clear_execute(cursor):
    query_str = 'TRUNCATE TABLE '
    names_array = ['forums', 'users', 'threads', 'posts', 'followers', 'subscriptions']
    for name in names_array:
        cursor.execute(query_str + name)


def status_execute(cursor):
    query_str = 'SELECT COUNT(*) FROM '
    data_array = []
    names_array = ['users', 'threads', 'forums', 'posts']
    for name in names_array:
        cursor.execute(query_str + name)
        data_array.append(cursor.fetchone()[0])
    code = 0
    return_data = {"code": code, "response": {"user": data_array[0],
                                              "thread": data_array[1],
                                              "forum": data_array[2],
                                              "post": data_array[3]}}
    return jsonify(return_data)


# USER

def user_create_helper(data, cursor):
    about = data['about']
    email = data['email']
    username = data['username']
    name = data['name']
    is_anonymous = data.get('isAnonymous', False)
    query_str = """INSERT INTO users (username, about, name, email, isAnonymous) VALUES
    ('%s','%s','%s','%s',%d)""" % (username, about, name, email, is_anonymous)
    cursor.execute(query_str)
    # return data
    code = 0
    new_id = cursor.lastrowid
    return_data = {"code": code, "response": {"about": about, "email": email, "id": new_id,
                                              "isAnonymous": is_anonymous, "name": name, "username": username}}
    return return_data


def fetch_args_user():
    user = request.args.get('user', False)
    limit = request.args.get('limit', False)
    since = request.args.get('since', False)
    order = request.args.get('order', 'desc')
    data = {'user': user, 'order': order, 'limit': limit, 'since': since}
    return data


def fetch_args_user_followers():
    user = request.args.get('user', False)
    limit = request.args.get('limit', False)
    since_id = request.args.get('since_id', False)
    order = request.args.get('order', 'desc')
    data = {'user': user, 'order': order, 'limit': limit, 'since_id': since_id}
    return data


# FORUM


def forum_create_execute(cursor, data):
    query_str = "INSERT INTO forums (name,short_name,user) " \
                "values ('%s','%s','%s')" \
                % (data['name'], data['short_name'], data['user'])
    cursor.execute(query_str)


def integrity_err_action(e, data):
    if 'short_name_UNIQUE' in e[1]:
        query_str = "SELECT * from forums where short_name = '%s'" % (data['short_name'])
    else:
        query_str = "SELECT * from forums where name = '%s'" % (data['name'])
    db = db_connect()
    cursor = db.cursor()
    cursor.execute(query_str)
    forum = cursor.fetchone()
    return_data = {"code": 0, "response": {"id": forum[3], "name": forum[0], "short_name": forum[1],
                                           "user": forum[2]}}
    return return_data


def fetch_listpost_forum_args():
    forum = request.args.get('forum')
    related = request.args.getlist('related')
    order = request.args.get('order', 'desc')
    limit = request.args.get('limit', False)
    since = request.args.get('since', False)
    data = {'forum': forum, 'related': related, 'order': order, 'limit': limit, 'since': since}
    return data


def fetch_listthreads_forum_args():
    forum = request.args.get('forum')
    related = request.args.getlist('related')
    order = request.args.get('order', 'desc')
    limit = request.args.get('limit', False)
    since = request.args.get('since', False)
    data = {'forum': forum, 'related': related, 'order': order, 'limit': limit, 'since': since}
    return data


def fetch_listusers_forum_args():
    forum = request.args.get('forum')
    order = request.args.get('order', 'desc')
    limit = request.args.get('limit', False)
    since = request.args.get('since_id', False)
    data = {'forum': forum, 'order': order, 'limit': limit, 'since': since}
    return data

# THREADS


