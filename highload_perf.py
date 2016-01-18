# -*- coding: utf-8 -*-
from flask import Flask
from _mysql_exceptions import IntegrityError
# from flaskext.mysql import MySQL
from func_perf import *
import ujson

app = Flask(__name__)

# CONFIG
app.config['JSON_SORT_KEYS'] = False
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False
#mysql = MySQL()
#app.config['MYSQL_DATABASE_USER'] = 'db_api_user'
#app.config['MYSQL_DATABASE_DB'] = 'db_func_test'
#app.config['MYSQL_DATABASE_HOST'] = 'localhost'
#app.config['MYSQL_DATABASE_PASSWORD'] = 'passwd'
#mysql.init_app(app)
#connection = mysql.connect()


# def curs():
#     connection.ping(True)
#     return connection.cursor()


@app.route('/db/api/clear/', methods=['POST'])
def clear():
    """Truncate all tables"""
    db = db_connect()
    cursor = db.cursor()
    query_str = 'TRUNCATE TABLE '
    names_array = ['forums', 'users', 'threads', 'posts', 'followers', 'subscriptions']
    for name in names_array:
        cursor.execute(query_str + name)
    db.commit()
    return_data = {"code": 0, "response": "OK"}
    return ujson.dumps(return_data)


@app.route('/db/api/status/', methods=['GET'])
def status():
    """Show status info: maps table name to number of rows in that table"""
    db = db_connect()
    cursor = db.cursor()
    query_str = 'SELECT COUNT(*) FROM '
    data_array = []
    names_array = ['users', 'threads', 'forums', 'posts']
    for name in names_array:
        cursor.execute(query_str + name)
        data_array.append(cursor.fetchone()[0])
    code = 0
    return_data = {
        "code": code,
        "response": {
            "user": data_array[0],
            "thread": data_array[1],
            "forum": data_array[2],
            "post": data_array[3]
        }
    }
    db.close()
    return ujson.dumps(return_data)


# FORUMS

@app.route('/db/api/forum/create/', methods=['POST'])
def forum_create():
    """Create new forum"""
    try:
        db = db_connect()
        cursor = db.cursor()
        data = request.get_json()
        name = data['name']
        short_name = data['short_name']
        user = data['user']
        query_stmt = """
            INSERT INTO forums (name,short_name,user)
            VALUES ('%s','%s','%s')
            """ % (name, short_name, user)
        cursor.execute(query_stmt)
        return_data = {
            "code": 0,
            "response": {
                'id': cursor.lastrowid,
                "name": name,
                "short_name": short_name,
                "user": user
            }
        }
        db.commit()
        db.close()
        return ujson.dumps(return_data)
    except IntegrityError, e:
        if e[0] == 1062:
            if 'short_name_UNIQUE' in e[1]:
                query_stmt = """
                    SELECT *
                    FROM forums
                    WHERE short_name = '%s'
                    """ % short_name
            else:
                query_stmt = """
                    SELECT *
                    FROM forums
                    WHERE name = '%s'
                    """ % name
            cursor = db.cursor()
            cursor.execute(query_stmt)
            forum_data = cursor.fetchone()
            return_data = {
                "code": 0,
                "response": {
                    "id": forum_data[3],
                    "name": forum_data[0],
                    "short_name": forum_data[1],
                    "user": forum_data[2]
                }
            }
            db.close()
            return ujson.dumps(return_data)
    except KeyError:
        return_data = {"code": 2, "response": "invalid json format"}
        db.close()
        return ujson.dumps(return_data)


@app.route('/db/api/forum/details/', methods=['GET'])
def forum_details():
    """Get forum details"""
    db = db_connect()
    cursor = db.cursor()
    forum = request.args.get('forum', '')
    related = request.args.getlist('related')
    query_stmt = """
        SELECT *
        FROM forums
        WHERE short_name = '%s'
        """ % forum
    if cursor.execute(query_stmt) == 0:
        return_data = {"code": 1, "response": "FORUM NOT FOUND"}
        db.close()
        return ujson.dumps(return_data)
    forum_data = cursor.fetchone()
    if 'user' in related:
        query_stmt = """
            SELECT *
            FROM users
            WHERE email = '%s'
            """ % forum_data[2]
        cursor.execute(query_stmt)
        user_data = cursor.fetchone()
        if user_data[2] == 'None':
            about = None
        else:
            about = user_data[2]
        if user_data[1] == 'None':
            username = None
        else:
            username = user_data[1]
        if user_data[3] == 'None':
            name = None
        else:
            name = user_data[3]
        query_stmt = """
            SELECT who_user
            FROM followers
            WHERE whom_user = '%s'
            """ % user_data[4]
        cursor.execute(query_stmt)
        followers = cursor.fetchall()
        query_stmt = """
            SELECT whom_user
            FROM followers
            WHERE who_user = '%s'
            """ % user_data[4]
        cursor.execute(query_stmt)
        following = cursor.fetchall()
        query_stmt = """
            SELECT thread_id
            FROM subscriptions
            WHERE user = '%s'
            """ % user_data[4]
        cursor.execute(query_stmt)
        subs = cursor.fetchall()
        user_info = {
            "about": about,
            "email": user_data[4],
            "followers": [x[0] for x in followers],
            "following": [x[0] for x in following],
            "id": user_data[0],
            "isAnonymous": bool(user_data[5]),
            "name": name,
            "subscriptions": [x[0] for x in subs],
            "username": username
        }
    else:
        user_info = forum_data[2]
    return_data = {
        "code": 0,
        "response": {
            "id": forum_data[3],
            "name": forum_data[0],
            "short_name": forum_data[1],
            "user": user_info
        }
    }
    db.close()
    return ujson.dumps(return_data)


@app.route('/db/api/forum/listPosts/', methods=['GET'])
def forum_listPosts():
    """Get posts from this forum"""
    db = db_connect()
    cursor = db.cursor()
    forum = request.args.get('forum')
    if not forum:
        return_data = {"code": 3, "response": "bad syntax"}
        db.close()
        return ujson.dumps(return_data)
    related = request.args.getlist('related')
    order = request.args.get('order', 'desc')
    limit = request.args.get('limit', False)
    since = request.args.get('since', False)
    query_stmt = """
        SELECT *
        FROM forums
        WHERE short_name = '%s'
        """ % forum
    if cursor.execute(query_stmt) == 0:
        return_data = {"code": 1, "response": "FORUM NOT FOUND"}
        db.close()
        return ujson.dumps(return_data)
    forum_data = cursor.fetchone()
    query_stmt = """
        SELECT *
        FROM posts
        WHERE forum = '%s'
        """ % forum
    if since:
        query_stmt += " AND date >= '%s' " % since
    query_stmt += " ORDER BY  date %s " % order
    if limit:
        query_stmt += " LIMIT %d" % (int(limit))
    cursor.execute(query_stmt)
    post_datas = cursor.fetchall()
    if 'forum' in related:
        related.remove('forum')
        forum_info = {
            "id": forum_data[3],
            "name": forum_data[0],
            "short_name": forum_data[1],
            "user": forum_data[2]
        }
    else:
        forum_info = forum
    ListPosts = []
    for post_data in post_datas:
        if 'user' in related:
            query_stmt = """
                SELECT *
                FROM users
                WHERE email = '%s'
                """ % post_data[8]
            cursor.execute(query_stmt)
            user_data = cursor.fetchone()
            if user_data[2] == 'None':
                about = None
            else:
                about = user_data[2]
            if user_data[1] == 'None':
                username = None
            else:
                username = user_data[1]
            if user_data[3] == 'None':
                name = None
            else:
                name = user_data[3]
            query_stmt = """
                SELECT who_user
                FROM followers
                WHERE whom_user = '%s'
                """ % user_data[4]
            cursor.execute(query_stmt)
            followers = cursor.fetchall()
            query_stmt = """
                SELECT whom_user
                FROM followers
                WHERE who_user = '%s'
                """ % user_data[4]
            cursor.execute(query_stmt)
            following = cursor.fetchall()
            query_stmt = """
                SELECT thread_id
                FROM subscriptions
                WHERE user = '%s'
                """ % user_data[4]
            cursor.execute(query_stmt)
            subs = cursor.fetchall()
            user_info = {
                "about": about,
                "email": user_data[4],
                "followers": [x[0] for x in followers],
                "following": [x[0] for x in following],
                "id": user_data[0],
                "isAnonymous": bool(user_data[5]),
                "name": name,
                "subscriptions": [x[0] for x in subs],
                "username": username
            }
        else:
            user_info = post_data[8]

        if 'thread' in related:
            query_stmt = """
            SELECT *
            FROM threads
            WHERE thread_id = '%s'
            """ % post_data[12]
            cursor.execute(query_stmt)
            thread_data = cursor.fetchone()
            thread_info = {
                "date": thread_data[5].strftime("%Y-%m-%d %H:%M:%S"),
                "dislikes": thread_data[10],
                "forum": thread_data[1],
                "id": thread_data[0],
                "isClosed": bool(thread_data[3]),
                "isDeleted": bool(thread_data[8]),
                "likes": thread_data[9],
                "message": thread_data[6],
                "points": (thread_data[9] - thread_data[10]),
                "posts": thread_data[11],
                "slug": thread_data[7],
                "title": thread_data[2],
                "user": thread_data[4]
            }
        else:
            thread_info = post_data[12]
        if post_data[1] == 0:
            parent = None
        else:
            parent = post_data[1]

        return_data = {
            "date": post_data[6].strftime("%Y-%m-%d %H:%M:%S"),
            "dislikes": post_data[10],
            "forum": forum_info,
            "id": post_data[0],
            "isApproved": bool(post_data[2]),
            "isDeleted": bool(post_data[5]),
            "isEdited": bool(post_data[3]),
            "isHighlighted": bool(post_data[13]),
            "isSpam": bool(post_data[4]),
            "likes": post_data[11],
            "message": post_data[7],
            "parent": parent,
            "points": (post_data[11] - post_data[10]),
            "thread": thread_info,
            "user": user_info
        }
        ListPosts.append(return_data)
    db.close()
    return jsonify({"code": 0, "response": ListPosts})


@app.route('/db/api/forum/listThreads/', methods=['GET'])
def forum_listThreads():
    """Get threads from this forum"""
    db = db_connect()
    cursor = db.cursor()
    forum = request.args.get('forum')
    if not forum:
        return_data = {"code": 3, "response": "bad syntax"}
        db.close()
        return ujson.dumps(return_data)
    related = request.args.getlist('related')
    order = request.args.get('order', 'desc')
    limit = request.args.get('limit', False)
    since = request.args.get('since', False)
    query_stmt = """
        SELECT *
        FROM forums
        WHERE short_name = '%s'
        """ % forum
    if cursor.execute(query_stmt) == 0:
        return_data = {"code": 1, "response": "FORUM NOT FOUND"}
        db.close()
        return ujson.dumps(return_data)
    forum_data = cursor.fetchone()
    query_stmt = """
        SELECT *
        FROM threads
        WHERE forum = '%s'
        """ % forum
    if since:
        query_stmt += " AND date >= '%s' " % since
    query_stmt += " ORDER BY  date %s " % order
    if limit:
        query_stmt += " LIMIT %d" % (int(limit))
    cursor.execute(query_stmt)
    thread_datas = cursor.fetchall()
    if 'forum' in related:
        forum_info = {
            "id": forum_data[3],
            "name": forum_data[0],
            "short_name": forum_data[1],
            "user": forum_data[2]
        }
    else:
        forum_info = forum
    threads_list = []
    for thread_data in thread_datas:
        if 'user' in related:
            query_stmt = """
                SELECT *
                FROM users
                WHERE email = '%s'
                """ % thread_data[4]
            cursor.execute(query_stmt)
            user_data = cursor.fetchone()
            if user_data[2] == 'None':
                about = None
            else:
                about = user_data[2]
            if user_data[1] == 'None':
                username = None
            else:
                username = user_data[1]
            if user_data[3] == 'None':
                name = None
            else:
                name = user_data[3]
            query_stmt = """
                SELECT who_user
                FROM followers
                WHERE whom_user = '%s'
                """ % user_data[4]
            cursor.execute(query_stmt)
            followers = cursor.fetchall()
            query_stmt = """
                SELECT whom_user
                FROM followers
                WHERE who_user = '%s'
                """ % user_data[4]
            cursor.execute(query_stmt)
            following = cursor.fetchall()
            query_stmt = """
                SELECT thread_id
                FROM subscriptions
                WHERE user = '%s'
                """ % user_data[4]
            cursor.execute(query_stmt)
            subs = cursor.fetchall()
            user_info = {
                "about": about,
                "email": user_data[4],
                "followers": [x[0] for x in followers],
                "following": [x[0] for x in following],
                "id": user_data[0],
                "isAnonymous": bool(user_data[5]),
                "name": name,
                "subscriptions": [x[0] for x in subs],
                "username": username
            }
        else:
            user_info = thread_data[4]

        return_data = {
            "date": thread_data[5].strftime("%Y-%m-%d %H:%M:%S"),
            "dislikes": thread_data[10],
            "forum": forum_info,
            "id": thread_data[0],
            "isClosed": bool(thread_data[3]),
            "isDeleted": bool(thread_data[8]),
            "likes": thread_data[9],
            "message": thread_data[6],
            "points": (thread_data[9] - thread_data[10]),
            "posts": thread_data[11],
            "slug": thread_data[7],
            "title": thread_data[2],
            "user": user_info
        }
        threads_list.append(return_data)
    db.close()
    return jsonify({"code": 0, "response": threads_list})


@app.route('/db/api/forum/listUsers/', methods=['GET'])
def forum_listUsers():
    db = db_connect()
    cursor = db.cursor()
    forum = request.args.get('forum')
    if not forum:
        return_data = {"code": 3, "response": "bad syntax"}
        db.close()
        return ujson.dumps(return_data)
    order = request.args.get('order', 'desc')
    limit = request.args.get('limit', False)
    since = request.args.get('since_id', False)
    query_stmt = """
        SELECT *
        FROM forums
        WHERE short_name = '%s'
        """ % forum
    if cursor.execute(query_stmt) == 0:
        return_data = {"code": 1, "response": "FORUM NOT FOUND"}
        db.close()
        return ujson.dumps(return_data)

    query_stmt = """
        SELECT *
        FROM users
        WHERE email IN (SELECT DISTINCT user FROM posts WHERE forum = '%s')
        """ % forum
    if since:
        query_stmt += " AND user_id >= %d " % (int(since))
    query_stmt += " ORDER BY  name %s " % order
    if limit:
        query_stmt += " LIMIT %d" % (int(limit))

    cursor.execute(query_stmt)
    user_datas = cursor.fetchall()

    user_list = []
    for user_data in user_datas:
        if user_data[2] == 'None':
            about = None
        else:
            about = user_data[2]
        if user_data[1] == 'None':
            username = None
        else:
            username = user_data[1]
        if user_data[3] == 'None':
            name = None
        else:
            name = user_data[3]
        query_stmt = """
            SELECT who_user
            FROM followers
            WHERE whom_user = '%s'
            """ % user_data[4]
        cursor.execute(query_stmt)
        followers = cursor.fetchall()
        query_stmt = """
            SELECT whom_user
            FROM followers
            WHERE who_user = '%s'
            """ % user_data[4]
        cursor.execute(query_stmt)
        following = cursor.fetchall()
        query_stmt = """
            SELECT thread_id
            FROM subscriptions
            WHERE user = '%s'
            """ % user_data[4]
        cursor.execute(query_stmt)
        subs = cursor.fetchall()
        user_info = {
            "about": about,
            "email": user_data[4],
            "followers": [x[0] for x in followers],
            "following": [x[0] for x in following],
            "id": user_data[0],
            "isAnonymous": bool(user_data[5]),
            "name": name,
            "subscriptions": [x[0] for x in subs],
            "username": username
        }
        user_list.append(user_info)
    db.close()
    return jsonify({"code": 0, "response": user_list})


# POST


@app.route('/db/api/post/create/', methods=['POST'])
def post_create():
    db = db_connect()
    cursor = db.cursor()
    try:
        data = request.get_json()
        date = data['date']
        thread = data['thread']
        message = data['message']
        user = data['user']
        forum = data['forum']
        isDeleted = data.get('isDeleted', False)
        isSpam = data.get('isSpam', False)
        isEdit = data.get('isEdited', False)
        isHighlighted = data.get('isHighlighted', False)
        isApproved = data.get('isApproved', False)
        parent = data.get('parent', 0)
        if parent == None:
            parent = 0
        query_stmt = """
            INSERT INTO posts (parent, isApproved, isEdited, isSpam, isDeleted, date, message, user, forum,
         thread, isHighlited)
            VALUES (%d, %d, %d, %d, %d, '%s', '%s', '%s', '%s', %d, %d)
            """ % (parent, isApproved, isEdit, isSpam,
                   isDeleted, date, message, user, forum, thread, isHighlighted)
        cursor.execute(query_stmt)
        if parent == 0:
            parent = None
        return_data = {
            "code": 0,
            "response": {
                "date": date,
                "forum": forum,
                "id": cursor.lastrowid,
                "isApproved": isApproved,
                "isEdited": isEdit,
                "isHighlited": isHighlighted,
                "isSpam": isSpam,
                "message": message,
                "parent": parent,
                "thread": thread,
                "user": user
            }
        }
        db.commit()
        query_stmt = """
            UPDATE threads set posts = posts + 1
            WHERE thread_id = %d
            """ % thread
        cursor.execute(query_stmt)
        db.commit()
        db.close()
        return ujson.dumps(return_data)
    except KeyError:
        return_data = {"code": 2, "response": "invalid json format"}
        db.close()
        return ujson.dumps(return_data)


@app.route('/db/api/post/details/', methods=['GET'])
def post_details():
    db = db_connect()
    cursor = db.cursor()
    post = request.args.get('post', '')
    related = request.args.getlist('related')
    query_stmt = """
        SELECT * FROM posts
        WHERE post_id = '%s'
        """ % post
    if cursor.execute(query_stmt) == 0:
        return_data = {"code": 1, "response": "POST NOT FOUND"}
        db.close()
        return ujson.dumps(return_data)
    post_data = cursor.fetchone()
    if 'user' in related:
        query_stmt = """
            SELECT *
            FROM users
            WHERE email = '%s'
            """ % (post_data[8])
        cursor.execute(query_stmt)
        user_data = cursor.fetchone()
        if user_data[2] == 'None':
            about = None
        else:
            about = user_data[2]
        if user_data[1] == 'None':
            username = None
        else:
            username = user_data[1]
        if user_data[3] == 'None':
            name = None
        else:
            name = user_data[3]
        query_stmt = """
            SELECT who_user
            FROM followers
            WHERE whom_user = '%s'
            """ % (user_data[4])
        cursor.execute(query_stmt)
        followers = cursor.fetchall()
        query_stmt = """
            SELECT whom_user
            FROM followers
            WHERE who_user = '%s'
            """ % (user_data[4])
        cursor.execute(query_stmt)
        following = cursor.fetchall()
        query_stmt = """
            SELECT thread_id
            FROM subscriptions
            WHERE user = '%s'
            """ % (user_data[4])
        cursor.execute(query_stmt)
        subs = cursor.fetchall()
        user_info = {
            "about": about,
            "email": user_data[4],
            "followers": [x[0] for x in followers],
            "following": [x[0] for x in following],
            "id": user_data[0],
            "isAnonymous": bool(user_data[5]),
            "name": name,
            "subscriptions": [x[0] for x in subs],
            "username": username
        }
    else:
        user_info = post_data[8]
    if 'forum' in related:
        query_stmt = """
            SELECT *
            FROM forums
            WHERE short_name = '%s'
            """ % (post_data[9])
        cursor.execute(query_stmt)
        forum_data = cursor.fetchone()
        forum_info = {
            "id": forum_data[3],
            "name": forum_data[0],
            "short_name": forum_data[1],
            "user": forum_data[2]
        }
    else:
        forum_info = post_data[9]
    if 'thread' in related:
        query_stmt = """
            SELECT *
            FROM threads
            WHERE thread_id = '%s'
            """ % (post_data[12])
        cursor.execute(query_stmt)
        thread_data = cursor.fetchone()
        thread_info = {
            "date": thread_data[5].strftime("%Y-%m-%d %H:%M:%S"),
            "dislikes": thread_data[10],
            "forum": thread_data[1],
            "id": thread_data[0],
            "isClosed": bool(thread_data[3]),
            "isDeleted": bool(thread_data[8]),
            "likes": thread_data[9],
            "message": thread_data[6],
            "points": (thread_data[9] - thread_data[10]),
            "posts": thread_data[11],
            "slug": thread_data[7],
            "title": thread_data[2],
            "user": thread_data[4]
        }
    else:
        thread_info = post_data[12]
    if post_data[1] == 0:
        parent = None
    else:
        parent = post_data[1]

    return_data = {
        "code": 0,
        "response": {
            "date": post_data[6].strftime("%Y-%m-%d %H:%M:%S"),
            "dislikes": post_data[10],
            "forum": forum_info,
            "id": post_data[0],
            "isApproved": bool(post_data[2]),
            "isDeleted": bool(post_data[5]),
            "isEdited": bool(post_data[3]),
            "isHighlighted": bool(post_data[13]),
            "isSpam": bool(post_data[4]),
            "likes": post_data[11],
            "message": post_data[7],
            "parent": parent,
            "points": (post_data[11] - post_data[10]),
            "thread": thread_info,
            "user": user_info
        }
    }
    db.close()
    return ujson.dumps(return_data)


@app.route('/db/api/post/list/', methods=['GET'])
def post_list():
    db = db_connect()
    cursor = db.cursor()
    thread = request.args.get('thread', False)
    forum = request.args.get('forum', False)
    if thread and forum:
        return_data = {"code": 3, "response": "bad syntax"}
        db.close()
        return ujson.dumps(return_data)
    limit = request.args.get('limit', False)
    since = request.args.get('since', False)
    order = request.args.get('order', False)
    query_stmt = """
        SELECT *
        FROM posts
        WHERE
        """
    if thread:
        query_stmt += "thread =  %d" % (int(thread))
    else:
        query_stmt += "forum = '%s' " % forum
    if since:
        query_stmt += " AND date >= '%s' " % since
    if order:
        query_stmt += " ORDER BY date %s " % order
    if limit:
        query_stmt += " LIMIT %d" % (int(limit))
    cursor.execute(query_stmt)
    post_datas = cursor.fetchall()
    returnposts = []
    for post_data in post_datas:
        if post_data[1] == 0:
            parent = None
        else:
            parent = post_data[1]
        returnposts.append({
            "date": post_data[6].strftime("%Y-%m-%d %H:%M:%S"),
            "dislikes": post_data[10],
            "forum": post_data[9],
            "id": post_data[0],
            "isApproved": bool(post_data[2]),
            "isDeleted": bool(post_data[5]),
            "isEdited": bool(post_data[3]),
            "isHighlighted": bool(post_data[13]),
            "isSpam": bool(post_data[4]),
            "likes": post_data[11],
            "message": post_data[7],
            "parent": parent,
            "points": (post_data[11] - post_data[10]),
            "thread": post_data[12],
            "user": post_data[8]
        })
    return_data = {"code": 0, "response": returnposts}
    db.close()
    return ujson.dumps(return_data)


@app.route('/db/api/post/remove/', methods=['POST'])
def post_remove():
    db = db_connect()
    cursor = db.cursor()
    try:
        data = request.get_json()
        post = data['post']
    except KeyError:
        return_data = {"code": 2, "response": "invalid json format"}
        db.close()
        return ujson.dumps(return_data)
    query_stmt = """
        SELECT *
        FROM posts
        WHERE post_id = %d
        """ % (int(post))
    cursor.execute(query_stmt)
    post_data = cursor.fetchone()
    if post_data:
        if post_data[5]:
            if post_data[1] == 0:
                parent = None
            else:
                parent = post_data[1]
            returnpost = {
                "date": post_data[6].strftime("%Y-%m-%d %H:%M:%S"),
                "dislikes": post_data[10],
                "forum": post_data[9],
                "id": post_data[0],
                "isApproved": bool(post_data[2]),
                "isDeleted": bool(post_data[5]),
                "isEdited": bool(post_data[3]),
                "isHighlighted": bool(post_data[13]),
                "isSpam": bool(post_data[4]),
                "likes": post_data[11],
                "message": post_data[7],
                "parent": parent,
                "points": (post_data[11] - post_data[10]),
                "thread": post_data[12],
                "user": post_data[8]
            }
            return_data = {"code": 0, "response": returnpost}
            db.close()
            return ujson.dumps(return_data)
        else:
            query_stmt = """
                UPDATE posts set isDeleted = True
                WHERE post_id = %d
                """ % post
            cursor.execute(query_stmt)
            db.commit()
            query_stmt = """
                UPDATE threads set posts = posts - 1
                WHERE thread_id = %d
                """ % (post_data[12])
            cursor.execute(query_stmt)
            db.commit()
            return_data = {"code": 0, "response": {"post": post}}
            return ujson.dumps(return_data)
    else:
        return_data = {"code": 1, "response": "FORUM NOT FOUND"}
        db.close()
        return ujson.dumps(return_data)


@app.route('/db/api/post/restore/', methods=['POST'])
def post_restore():
    db = db_connect()
    cursor = db.cursor()
    try:
        data = request.get_json()
        post = data['post']
    except KeyError:
        return_data = {"code": 2, "response": "invalid json format"}
        db.close()
        return ujson.dumps(return_data)
    query_stmt = """
        SELECT *
        FROM posts
        WHERE post_id = %d
        """ % (int(post))
    cursor.execute(query_stmt)
    post_data = cursor.fetchone()
    if post_data:
        if not post_data[5]:
            if post_data[1] == 0:
                parent = None
            else:
                parent = post_data[1]
            returnpost = {
                "date": post_data[6].strftime("%Y-%m-%d %H:%M:%S"),
                "dislikes": post_data[10],
                "forum": post_data[9],
                "id": post_data[0],
                "isApproved": bool(post_data[2]),
                "isDeleted": bool(post_data[5]),
                "isEdited": bool(post_data[3]),
                "isHighlighted": bool(post_data[13]),
                "isSpam": bool(post_data[4]),
                "likes": post_data[11],
                "message": post_data[7],
                "parent": parent,
                "points": (post_data[11] - post_data[10]),
                "thread": post_data[12],
                "user": post_data[8]}
            return_data = {"code": 0, "response": returnpost}
            db.close()
            return ujson.dumps(return_data)
        else:
            query_stmt = """
                UPDATE posts set isDeleted = False
                WHERE post_id = %d
                """ % post
            cursor.execute(query_stmt)
            db.commit()
            query_stmt = """
                UPDATE threads set posts = posts + 1
                WHERE thread_id = %d
                """ % (post_data[12])
            cursor.execute(query_stmt)
            db.commit()
            return_data = {"code": 0, "response": {"post": post}}
            db.close()
            return ujson.dumps(return_data)
    else:
        return_data = {"code": 1, "response": "POST NOT FOUND"}
        db.close()
        return ujson.dumps(return_data)


@app.route('/db/api/post/update/', methods=['POST'])
def post_update():
    db = db_connect()
    cursor = db.cursor()
    try:
        data = request.get_json()
        post = data['post']
        message = data['message']
        query_stmt = """
            SELECT *
            FROM posts
            WHERE post_id = %d
            """ % (int(post))
        cursor.execute(query_stmt)
        post_data = cursor.fetchone()
        if post_data:
            if not post_data[7] == message:
                query_stmt = """
                    UPDATE posts set message = '%s'
                    WHERE post_id = %d
                    """ % (message, post)
                cursor.execute(query_stmt)
                db.commit()
                query_stmt = """
                    UPDATE posts set isEdited = True
                    WHERE post_id = %d
                    """ % post
                cursor.execute(query_stmt)
                db.commit()
                if post_data[1] == 0:
                    parent = None
                else:
                    parent = post_data[1]
                returnpost = {
                    "date": post_data[6].strftime("%Y-%m-%d %H:%M:%S"),
                    "dislikes": post_data[10],
                    "forum": post_data[9],
                    "id": post_data[0],
                    "isApproved": bool(post_data[2]),
                    "isDeleted": bool(post_data[5]),
                    "isEdited": True,
                    "isHighlighted": bool(post_data[13]),
                    "isSpam": bool(post_data[4]),
                    "likes": post_data[11],
                    "message": message,
                    "parent": parent,
                    "points": (post_data[11] - post_data[10]),
                    "thread": post_data[12],
                    "user": post_data[8]
                }
                return_data = {"code": 0, "response": returnpost}
                db.close()
                return ujson.dumps(return_data)
            else:
                if post_data[1] == 0:
                    parent = None
                else:
                    parent = post_data[1]
                returnpost = {
                    "date": post_data[6].strftime("%Y-%m-%d %H:%M:%S"),
                    "dislikes": post_data[10],
                    "forum": post_data[9],
                    "id": post_data[0],
                    "isApproved": bool(post_data[2]),
                    "isDeleted": bool(post_data[5]),
                    "isEdited": bool(post_data[3]),
                    "isHighlighted": bool(post_data[13]),
                    "isSpam": bool(post_data[4]),
                    "likes": post_data[11],
                    "message": post_data[7],
                    "parent": parent,
                    "points": (post_data[11] - post_data[10]),
                    "thread": post_data[12],
                    "user": post_data[8]
                }
                return_data = {"code": 0, "response": returnpost}
                db.close()
                return ujson.dumps(return_data)
        else:
            return_data = {"code": 1, "response": "POST NOT FOUND"}
            db.close()
            return ujson.dumps(return_data)
    except KeyError:
        return_data = {"code": 2, "response": "invalid json format"}
        db.close()
        return ujson.dumps(return_data)


@app.route('/db/api/post/vote/', methods=['POST'])
def post_vote():
    db = db_connect()
    cursor = db.cursor()
    try:
        data = request.get_json()
        vote = data['vote']
        post = data['post']
        query_stmt = """
            SELECT *
            FROM posts
            WHERE post_id = %d
            """ % (int(post))
        cursor.execute(query_stmt)
        post_data = cursor.fetchone()
        if post_data:
            if vote == 1:
                query_stmt = """
                    UPDATE posts set likes = likes + 1
                    WHERE post_id = %d
                    """ % (int(post))
                likes = post_data[11] + 1
                dislikes = post_data[10]
            elif vote == -1:
                query_stmt = """
                    UPDATE posts set dislikes = dislikes + 1
                    WHERE post_id = %d
                    """ % (int(post))
                likes = post_data[11]
                dislikes = post_data[10] + 1
            else:
                return_data = {"code": 3, "response": "invalid syntax"}
                db.close()
                return ujson.dumps(return_data)
            cursor.execute(query_stmt)
            db.commit()
            if post_data[1] == 0:
                parent = None
            else:
                parent = post_data[1]
            returnpost = {
                "date": post_data[6].strftime("%Y-%m-%d %H:%M:%S"),
                "dislikes": dislikes,
                "forum": post_data[9],
                "id": post_data[0],
                "isApproved": bool(post_data[2]),
                "isDeleted": bool(post_data[5]),
                "isEdited": bool(post_data[3]),
                "isHighlighted": bool(post_data[13]),
                "isSpam": bool(post_data[4]),
                "likes": likes,
                "message": post_data[7],
                "parent": parent,
                "points": (likes - dislikes),
                "thread": post_data[12],
                "user": post_data[8]
            }
            return_data = {"code": 0, "response": returnpost}
            db.close()
            return ujson.dumps(return_data)
        else:
            return_data = {"code": 1, "response": "POST NOT FOUND"}
            db.close()
            return ujson.dumps(return_data)
    except KeyError:
        return_data = {"code": 2, "response": "invalid json format"}
        db.close()
        return ujson.dumps(return_data)


# USERS
@app.route('/db/api/user/create/', methods=['POST'])
def user_create():
    db = db_connect()
    cursor = db.cursor()
    try:
        data = request.get_json()
        about = data['about']
        email = data['email']
        username = data['username']
        name = data['name']
        isAnonymous = data.get('isAnonymous', False)
        if name != None:
            query_stmt = """
                INSERT INTO users (username, about, name, email, isAnonymous)
                VALUES('%s','%s','%s','%s',%d)""" % (username, about, name, email, isAnonymous)
        else:
            query_stmt = """
                INSERT INTO users (username, about, name, email, isAnonymous)
                VALUES('%s','%s',Null,'%s',%d)""" % (username, about, email, isAnonymous)
        cursor.execute(query_stmt)
        return_data = {
            "code": 0,
            "response": {
                "about": about,
                "email": email,
                "id": cursor.lastrowid,
                "isAnonymous": isAnonymous,
                "name": name,
                "username": username
            }
        }
        db.commit()
        db.close()
        return ujson.dumps(return_data)
    except IntegrityError, e:
        if e[0] == 1062:
            return_data = {"code": 5, "response": "duplicate user"}
            db.close()
            return ujson.dumps(return_data)
    except KeyError:
        return_data = {"code": 2, "response": "invalid json format"}
        db.close()
        return ujson.dumps(return_data)


@app.route('/db/api/user/details/', methods=['GET'])
def user_details():
    db = db_connect()
    cursor = db.cursor()
    user = request.args.get('user', '')
    query_stmt = """
        SELECT *
        FROM users
        WHERE email = '%s'
        """ % user
    if cursor.execute(query_stmt) == 0:
        return_data = {"code": 1, "response": "USER NOT FOUND"}
        db.close()
        return ujson.dumps(return_data)
    else:
        user_data = cursor.fetchone()
        query_stmt = """
            SELECT who_user
            FROM followers
            WHERE whom_user = '%s'
            """ % user_data[4]
        cursor.execute(query_stmt)
        followers = cursor.fetchall()
        query_stmt = """
            SELECT whom_user
            FROM followers
            WHERE who_user = '%s'
            """ % (user_data[4])
        cursor.execute(query_stmt)
        following = cursor.fetchall()
        query_stmt = """
            SELECT thread_id
            FROM subscriptions
            WHERE user = '%s'
            """ % (user_data[4])
        cursor.execute(query_stmt)
        subs = cursor.fetchall()
        if user_data[2] == 'None':
            about = None
        else:
            about = user_data[2]
        if user_data[1] == 'None':
            username = None
        else:
            username = user_data[1]
        if user_data[3] == 'None':
            name = None
        else:
            name = user_data[3]

        user_info = {
            "about": about,
            "email": user_data[4],
            "followers": [x[0] for x in followers],
            "following": [x[0] for x in following],
            "id": user_data[0],
            "isAnonymous": bool(user_data[5]),
            "name": name,
            "subscriptions": [x[0] for x in subs],
            "username": username
        }
        return_data = {"code": 0, "response": user_info}
        db.close()
        return ujson.dumps(return_data)


@app.route('/db/api/user/follow/', methods=['POST'])
def user_follow():
    db = db_connect()
    cursor = db.cursor()
    try:
        data = request.get_json()
        follower = data['follower']  
        followee = data['followee']  
        if followee == follower:
            return_data = {"code": 3, "response": "WTF!"}
            db.close()
            return ujson.dumps(return_data)
        query_stmt = """
            SELECT *
            FROM users
            WHERE email = '%s'
            """ % followee
        cursor.execute(query_stmt)
        user_datawhom = cursor.fetchone()
        if user_datawhom:
            query_stmt = """
                SELECT *
                FROM followers
                WHERE who_user = '%s' AND whom_user = '%s'
                """ % (follower, followee)
            cursor.execute(query_stmt)
            if not cursor.fetchone():
                query_stmt = """
                    SELECT *
                    FROM users
                    WHERE email = '%s'
                    """ % follower
                cursor.execute(query_stmt)
                user_data = cursor.fetchone()
                if user_data:
                    query_stmt = """
                        INSERT into followers (who_user, whom_user)
                        VALUES ('%s', '%s')
                        """ % (follower, followee)
                    cursor.execute(query_stmt)
                    db.commit()
                    query_stmt = """
                        SELECT who_user
                        FROM followers
                        WHERE whom_user = '%s'
                        """ % (user_data[4])
                    cursor.execute(query_stmt)
                    followers = cursor.fetchall()
                    query_stmt = """
                        SELECT whom_user
                        FROM followers
                        WHERE who_user = '%s'
                        """ % (user_data[4])
                    cursor.execute(query_stmt)
                    following = cursor.fetchall()
                    query_stmt = """
                        SELECT thread_id
                        FROM subscriptions
                        WHERE user = '%s'
                        """ % (user_data[4])
                    cursor.execute(query_stmt)
                    subs = cursor.fetchall()
                    if user_data[2] == 'None':
                        about = None
                    else:
                        about = user_data[2]
                    if user_data[1] == 'None':
                        username = None
                    else:
                        username = user_data[1]
                    if user_data[3] == 'None':
                        name = None
                    else:
                        name = user_data[3]

                    user_info = {
                        "about": about,
                        "email": user_data[4],
                        "followers": [x[0] for x in followers],
                        "following": [x[0] for x in following],
                        "id": user_data[0],
                        "isAnonymous": bool(user_data[5]),
                        "name": name,
                        "subscriptions": [x[0] for x in subs],
                        "username": username
                    }
                    return_data = {"code": 0, "response": user_info}
                    db.close()
                    return ujson.dumps(return_data)
                else:
                    return_data = {"code": 1, "response": "USER NOT FOUND"}
                    db.close()
                    return ujson.dumps(return_data)
            else:
                query_stmt = """
                    SELECT *
                    FROM users
                    WHERE email = '%s'
                    """ % follower
                cursor.execute(query_stmt)
                user_data = cursor.fetchone()
                query_stmt = """
                    SELECT who_user
                    FROM followers
                    WHERE whom_user = '%s'
                    """ % (user_data[4])
                cursor.execute(query_stmt)
                followers = cursor.fetchall()
                query_stmt = """
                    SELECT whom_user
                    FROM followers
                    WHERE who_user = '%s'
                    """ % (user_data[4])
                cursor.execute(query_stmt)
                following = cursor.fetchall()
                query_stmt = """
                    SELECT thread_id
                    FROM subscriptions
                    WHERE user = '%s'
                    """ % (user_data[4])
                cursor.execute(query_stmt)
                subs = cursor.fetchall()
                if user_data[2] == 'None':
                    about = None
                else:
                    about = user_data[2]
                if user_data[1] == 'None':
                    username = None
                else:
                    username = user_data[1]
                if user_data[3] == 'None':
                    name = None
                else:
                    name = user_data[3]

                user_info = {
                    "about": about,
                    "email": user_data[4],
                    "followers": [x[0] for x in followers],
                    "following": [x[0] for x in following],
                    "id": user_data[0],
                    "isAnonymous": bool(user_data[5]),
                    "name": name,
                    "subscriptions": [x[0] for x in subs],
                    "username": username
                }
                return_data = {"code": 0, "response": user_info}
                db.close()
                return ujson.dumps(return_data)

        else:
            return_data = {"code": 1, "response": "USER NOT FOUND"}
            db.close()
            return ujson.dumps(return_data)
    except KeyError:
        return_data = {"code": 2, "response": "invalid json format"}
        db.close()
        return ujson.dumps(return_data)


@app.route('/db/api/user/listFollowers/', methods=['GET'])
def user_listFollowers():
    db = db_connect()
    cursor = db.cursor()
    user = request.args.get('user', False)
    if not user:
        return_data = {"code": 3, "response": "bad syntax"}
        db.close()
        return ujson.dumps(return_data)
    limit = request.args.get('limit', False)
    since_id = request.args.get('since_id', False)
    order = request.args.get('order', 'desc')
    query_stmt = "SELECT * FROM users WHERE email = '%s'" % (user)
    cursor.execute(query_stmt)
    user_data = cursor.fetchone()
    if user_data:
        query_stmt = """
            SELECT straight_join user_id, username, about, name, email, isAnonymous
            FROM followers join users ON users.email = followers.who_user
            WHERE whom_user = '%s'
            """ % user
        if since_id:
            query_stmt += " AND user_id >= %d " % (int(since_id))
        query_stmt += " ORDER BY name %s" % order
        if limit:
            query_stmt += " LIMIT %d" % (int(limit))
        cursor.execute(query_stmt)
        followers = cursor.fetchall()
        followers_list = []
        for user_data in followers:
            query_stmt = """
                SELECT who_user
                FROM followers
                WHERE whom_user = '%s'
                """ % (user_data[4])
            cursor.execute(query_stmt)
            followers = cursor.fetchall()
            query_stmt = """
                SELECT whom_user
                FROM followers
                WHERE who_user = '%s'
                """ % (user_data[4])
            cursor.execute(query_stmt)
            following = cursor.fetchall()
            query_stmt = """
                SELECT thread_id
                FROM subscriptions
                WHERE user = '%s'
                """ % (user_data[4])
            cursor.execute(query_stmt)
            subs = cursor.fetchall()
            if user_data[2] == 'None':
                about = None
            else:
                about = user_data[2]
            if user_data[1] == 'None':
                username = None
            else:
                username = user_data[1]
            if user_data[3] == 'None':
                name = None
            else:
                name = user_data[3]
            user_info = {
                "about": about,
                "email": user_data[4],
                "followers": [x[0] for x in followers],
                "following": [x[0] for x in following],
                "id": user_data[0],
                "isAnonymous": bool(user_data[5]),
                "name": name,
                "subscriptions": [x[0] for x in subs],
                "username": username
            }
            followers_list.append(user_info)
        return_data = {"code": 0, "response": followers_list}
        db.close()
        return ujson.dumps(return_data)
    else:
        return_data = {"code": 1, "response": "USER NOT FOUND"}
        db.close()
        return ujson.dumps(return_data)


@app.route('/db/api/user/listFollowing/', methods=['GET'])
def user_listFollowing():
    db = db_connect()
    cursor = db.cursor()
    user = request.args.get('user', False)
    if not user:
        return_data = {"code": 3, "response": "bad syntax"}
        db.close()
        return ujson.dumps(return_data)
    limit = request.args.get('limit', False)
    since_id = request.args.get('since_id', False)
    order = request.args.get('order', 'desc')
    query_stmt = """
        SELECT *
        FROM users
        WHERE email = '%s'
        """ % user
    cursor.execute(query_stmt)
    user_data = cursor.fetchone()
    if user_data:
        query_stmt = """
            SELECT straight_join user_id, username, about, name, email, isAnonymous
            FROM followers join users ON users.email = followers.whom_user
            WHERE who_user = '%s'
            """ % user
        if since_id:
            query_stmt += " AND user_id >= %d " % (int(since_id))
        query_stmt += " ORDER BY name %s" % order
        if limit:
            query_stmt += " LIMIT %d" % (int(limit))
        cursor.execute(query_stmt)
        all_following = cursor.fetchall()
        following_list = []
        for user_data in all_following:
            query_stmt = """
                SELECT who_user
                FROM followers
                WHERE whom_user = '%s'
                """ % (user_data[4])
            cursor.execute(query_stmt)
            followers = cursor.fetchall()
            query_stmt = """
                SELECT whom_user
                FROM followers
                WHERE who_user = '%s'
                """ % (user_data[4])
            cursor.execute(query_stmt)
            following = cursor.fetchall()
            query_stmt = """
                SELECT thread_id
                FROM subscriptions
                WHERE user = '%s'
                """ % (user_data[4])
            cursor.execute(query_stmt)
            subs = cursor.fetchall()
            if user_data[2] == 'None':
                about = None
            else:
                about = user_data[2]
            if user_data[1] == 'None':
                username = None
            else:
                username = user_data[1]
            if user_data[3] == 'None':
                name = None
            else:
                name = user_data[3]
            user_info = {
                "about": about,
                "email": user_data[4],
                "followers": [x[0] for x in followers],
                "following": [x[0] for x in following],
                "id": user_data[0],
                "isAnonymous": bool(user_data[5]),
                "name": name,
                "subscriptions": [x[0] for x in subs],
                "username": username
            }
            following_list.append(user_info)
        return_data = {"code": 0, "response": following_list}
        db.close()
        return ujson.dumps(return_data)
    else:
        return_data = {"code": 1, "response": "USER NOT FOUND"}
        db.close()
        return ujson.dumps(return_data)


@app.route('/db/api/user/listPosts/', methods=['GET'])
def user_listPosts():
    db = db_connect()
    cursor = db.cursor()
    user = request.args.get('user', False)
    if not user:
        return_data = {"code": 3, "response": "bad syntax"}
        db.close()
        return ujson.dumps(return_data)
    limit = request.args.get('limit', False)
    since = request.args.get('since', False)
    order = request.args.get('order', 'desc')
    query_stmt = """
        SELECT *
        FROM users
        WHERE email = '%s'
        """ % user
    cursor.execute(query_stmt)
    user_data = cursor.fetchone()
    if user_data:
        query_stmt = """
            SELECT *
            FROM posts
            WHERE user = '%s'
            """ % user
        if since:
            query_stmt += " AND date >= '%s' " % (since)
        query_stmt += " ORDER BY date %s " % (order)
        if limit:
            query_stmt += " LIMIT %d" % (int(limit))
        cursor.execute(query_stmt)
        post_datas = cursor.fetchall()
        post_list = []

        for post_data in post_datas:
            if post_data[1] == 0:
                parent = None
            else:
                parent = post_data[1]
            post_list.append({
                "date": post_data[6].strftime("%Y-%m-%d %H:%M:%S"),
                "dislikes": post_data[10],
                "forum": post_data[9],
                "id": post_data[0],
                "isApproved": bool(post_data[2]),
                "isDeleted": bool(post_data[5]),
                "isEdited": bool(post_data[3]),
                "isHighlighted": bool(post_data[13]),
                "isSpam": bool(post_data[4]),
                "likes": post_data[11],
                "message": post_data[7],
                "parent": parent,
                "points": (post_data[11] - post_data[10]),
                "thread": post_data[12],
                "user": post_data[8]
            })
        return_data = {"code": 0, "response": post_list}
        db.close()
        return ujson.dumps(return_data)

    else:
        return_data = {"code": 1, "response": "USER NOT FOUND"}
        db.close()
        return ujson.dumps(return_data)


@app.route('/db/api/user/unfollow/', methods=['POST'])
def user_unfollow():
    db = db_connect()
    cursor = db.cursor()
    try:
        data = request.get_json()
        follower = data['follower']  # who
        followee = data['followee']  # whom
        if followee == follower:
            return_data = {"code": 3, "response": "WTF!"}
            db.close()
            return ujson.dumps(return_data)
        query_stmt = """
            SELECT *
            FROM users
            WHERE email = '%s'
            """ % followee
        cursor.execute(query_stmt)
        user_datawhom = cursor.fetchone()
        if user_datawhom:
            query_stmt = """
                SELECT *
                FROM followers
                WHERE who_user = '%s' AND whom_user = '%s'
                """ % (follower, followee)
            cursor.execute(query_stmt)
            if cursor.fetchone():
                query_stmt = """
                    SELECT *
                    FROM users
                    WHERE email = '%s'
                    """ % follower
                cursor.execute(query_stmt)
                user_data = cursor.fetchone()
                if user_data:
                    query_stmt = """
                        DELETE
                        FROM followers
                        WHERE who_user = '%s' AND whom_user = '%s'
                        """ % (follower, followee)
                    cursor.execute(query_stmt)
                    db.commit()
                    query_stmt = """
                        SELECT who_user
                        FROM followers
                        WHERE whom_user = '%s'
                        """ % (user_data[4])
                    cursor.execute(query_stmt)
                    followers = cursor.fetchall()
                    query_stmt = """
                        SELECT whom_user
                        FROM followers
                        WHERE who_user = '%s'
                        """ % (user_data[4])
                    cursor.execute(query_stmt)
                    following = cursor.fetchall()
                    query_stmt = """
                        SELECT thread_id
                        FROM subscriptions
                        WHERE user = '%s'
                        """ % (user_data[4])
                    cursor.execute(query_stmt)
                    subs = cursor.fetchall()
                    if user_data[2] == 'None':
                        about = None
                    else:
                        about = user_data[2]
                    if user_data[1] == 'None':
                        username = None
                    else:
                        username = user_data[1]
                    if user_data[3] == 'None':
                        name = None
                    else:
                        name = user_data[3]

                    user_info = {
                        "about": about,
                        "email": user_data[4],
                        "followers": [x[0] for x in followers],
                        "following": [x[0] for x in following],
                        "id": user_data[0],
                        "isAnonymous": bool(user_data[5]),
                        "name": name,
                        "subscriptions": [x[0] for x in subs],
                        "username": username
                    }
                    return_data = {"code": 0, "response": user_info}
                    db.close()
                    return ujson.dumps(return_data)
                else:
                    return_data = {"code": 1, "response": "USER NOT FOUND"}
                    db.close()
                    return ujson.dumps(return_data)
            else:
                query_stmt = """
                    SELECT *
                    FROM users
                    WHERE email = '%s'
                    """ % follower
                cursor.execute(query_stmt)
                user_data = cursor.fetchone()
                query_stmt = """
                    SELECT who_user
                    FROM followers
                    WHERE whom_user = '%s'
                    """ % (user_data[4])
                cursor.execute(query_stmt)
                followers = cursor.fetchall()
                query_stmt = """
                    SELECT whom_user
                    FROM followers
                    WHERE who_user = '%s'
                    """ % (user_data[4])
                cursor.execute(query_stmt)
                following = cursor.fetchall()
                query_stmt = """
                    SELECT thread_id
                    FROM subscriptions
                    WHERE user = '%s'
                    """ % (user_data[4])
                cursor.execute(query_stmt)
                subs = cursor.fetchall()
                if user_data[2] == 'None':
                    about = None
                else:
                    about = user_data[2]
                if user_data[1] == 'None':
                    username = None
                else:
                    username = user_data[1]
                if user_data[3] == 'None':
                    name = None
                else:
                    name = user_data[3]
                user_info = {
                    "about": about,
                    "email": user_data[4],
                    "followers": [x[0] for x in followers],
                    "following": [x[0] for x in following],
                    "id": user_data[0],
                    "isAnonymous": bool(user_data[5]),
                    "name": name,
                    "subscriptions": [x[0] for x in subs],
                    "username": username
                }
                return_data = {"code": 0, "response": user_info}
                db.close()
                return ujson.dumps(return_data)
        else:
            return_data = {"code": 1, "response": "USER NOT FOUND"}
            db.close()
            return ujson.dumps(return_data)
    except KeyError:
        return_data = {"code": 2, "response": "invalid json format"}
        db.close()
        return ujson.dumps(return_data)


@app.route('/db/api/user/updateProfile/', methods=['POST'])
def user_updateProfile():
    db = db_connect()
    cursor = db.cursor()
    try:
        data = request.get_json()
        user = data['user']
        about = data['about']
        name = data['name']
        query_stmt = """
            SELECT *
            FROM users
            WHERE email = '%s'
            """ % user
        cursor.execute(query_stmt)
        user_data = cursor.fetchone()
        if user_data:
            if (user_data[2] != about) or (user_data[3] != name):
                query_stmt = """
                    UPDATE users set about = '%s'
                    WHERE email = '%s'
                    """ % (about, user)
                cursor.execute(query_stmt)
                query_stmt = """
                    UPDATE users set name = '%s'
                    WHERE email = '%s'
                    """ % (name, user)
                cursor.execute(query_stmt)
                db.commit()
                query_stmt = """
                    SELECT who_user
                    FROM followers
                    WHERE whom_user = '%s'
                    """ % (user_data[4])
                cursor.execute(query_stmt)
                followers = cursor.fetchall()
                query_stmt = """
                    SELECT whom_user
                    FROM followers
                    WHERE who_user = '%s'
                    """ % (user_data[4])
                cursor.execute(query_stmt)
                following = cursor.fetchall()
                query_stmt = """
                    SELECT thread_id
                    FROM subscriptions
                    WHERE user = '%s'
                    """ % (user_data[4])
                cursor.execute(query_stmt)
                subs = cursor.fetchall()
                if about == 'None':
                    about = None
                if user_data[1] == 'None':
                    username = None
                else:
                    username = user_data[1]
                if name == 'None':
                    name = None
                user_info = {
                    "about": about,
                    "email": user_data[4],
                    "followers": [x[0] for x in followers],
                    "following": [x[0] for x in following],
                    "id": user_data[0],
                    "isAnonymous": bool(user_data[5]),
                    "name": name,
                    "subscriptions": [x[0] for x in subs],
                    "username": username
                }
                return_data = {"code": 0, "response": user_info}
                db.close()
                return ujson.dumps(return_data)
            else:

                query_stmt = """
                    SELECT who_user
                    FROM followers
                    WHERE whom_user = '%s'
                    """ % (user_data[4])
                cursor.execute(query_stmt)
                followers = cursor.fetchall()
                query_stmt = """
                    SELECT whom_user
                    FROM followers
                    WHERE who_user = '%s'
                    """ % (user_data[4])
                cursor.execute(query_stmt)
                following = cursor.fetchall()
                query_stmt = """
                    SELECT thread_id
                    FROM subscriptions
                    WHERE user = '%s'
                    """ % (user_data[4])
                cursor.execute(query_stmt)
                subs = cursor.fetchall()
                if user_data[2] == 'None':
                    about = None
                else:
                    about = user_data[2]
                if user_data[1] == 'None':
                    username = None
                else:
                    username = user_data[1]
                if user_data[3] == 'None':
                    name = None
                else:
                    name = user_data[3]

                user_info = {
                    "about": about,
                    "email": user_data[4],
                    "followers": [x[0] for x in followers],
                    "following": [x[0] for x in following],
                    "id": user_data[0],
                    "isAnonymous": bool(user_data[5]),
                    "name": name,
                    "subscriptions": [x[0] for x in subs],
                    "username": username
                }
                return_data = {"code": 0, "response": user_info}
                db.close()
                return ujson.dumps(return_data)
        else:
            return_data = {"code": 1, "response": "USER NOT FOUND"}
            db.close()
            return ujson.dumps(return_data)
    except KeyError:
        return_data = {"code": 2, "response": "invalid json format"}
        db.close()
        return ujson.dumps(return_data)


# THREADS

@app.route('/db/api/thread/close/', methods=['POST'])
def thread_close():
    try:
        data = request.get_json()
        thread = data['thread']
        db = db_connect()
        cursor = db.cursor()
        query_stmt = """
            SELECT *
            FROM threads
            WHERE thread_id = %d
            """ % (int(thread))
        cursor.execute(query_stmt)
        thread_data = cursor.fetchone()
        if thread_data:
            if not thread_data[3]:
                query_stmt = """
                    UPDATE threads set isClosed = True
                    WHERE thread_id = %d
                    """ % (int(thread))
                cursor.execute(query_stmt)
                db.commit()
                return_data = {"code": 0, "response": {"thread": thread}}
                db.close()
                return ujson.dumps(return_data)
            else:
                return_data = {
                    "code": 0,
                    "response": {
                        "date": thread_data[5].strftime("%Y-%m-%d %H:%M:%S"),
                        "dislikes": thread_data[10],
                        "forum": thread_data[1],
                        "id": thread_data[0],
                        "isClosed": bool(thread_data[3]),
                        "isDeleted": bool(thread_data[8]),
                        "likes": thread_data[9],
                        "message": thread_data[6],
                        "points": (thread_data[9] - thread_data[10]),
                        "posts": thread_data[11],
                        "slug": thread_data[7],
                        "title": thread_data[2],
                        "user": thread_data[4]
                    }
                }
                db.close()
                return ujson.dumps(return_data)
        else:
            return_data = {"code": 1, "response": "THREAD NOT FOUND"}
            db.close()
            return ujson.dumps(return_data)
    except KeyError:
        return_data = {"code": 2, "response": "invalid json format"}
        db.close()
        return ujson.dumps(return_data)


@app.route('/db/api/thread/create/', methods=['POST'])
def thread_create():
    db = db_connect()
    cursor = db.cursor()
    try:
        data = request.get_json()
        forum = data['forum']
        title = data['title']
        isClosed = data['isClosed']
        user = data['user']
        date = data['date']
        message = data['message']
        slug = data['slug']
        isDeleted = data.get('isDeleted', False)
        query_stmt = """
            INSERT INTO threads (forum, title, isClosed, user, date, message,slug, isDeleted)
            VALUES('%s', '%s', %d, '%s', '%s', '%s', '%s', %d)""" % (
            forum, title, isClosed, user, date, message, slug, isDeleted)
        cursor.execute(query_stmt)
        db.commit()
        return_data = {
            'code': 0,
            'response': {
                'date': date,
                'forum': forum,
                'id': cursor.lastrowid,
                'isClosed': isClosed, 'isDeleted': isDeleted,
                'message': message,
                'slug': slug,
                'title': title,
                'user': user
            }
        }
        db.close()
        return ujson.dumps(return_data)
    except KeyError:
        return_data = {"code": 2, "response": "invalid json format"}
        db.close()
        return ujson.dumps(return_data)


@app.route('/db/api/thread/details/', methods=['GET'])
def thread_details():
    db = db_connect()
    cursor = db.cursor()
    thread = request.args.get('thread', '')
    related = request.args.getlist('related')
    query_stmt = """
        SELECT *
        FROM threads
        WHERE thread_id = '%s'
        """ % thread
    if cursor.execute(query_stmt) == 0:
        return_data = {"code": 1, "response": "THREAD NOT FOUND"}
        db.close()
        return ujson.dumps(return_data)
    thread_data = cursor.fetchone()
    if 'user' in related:
        query_stmt = """
            SELECT *
            FROM users
            WHERE email = '%s'
            """ % (thread_data[4])
        related.remove('user')
        cursor.execute(query_stmt)
        user_data = cursor.fetchone()
        if user_data[2] == 'None':
            about = None
        else:
            about = user_data[2]
        if user_data[1] == 'None':
            username = None
        else:
            username = user_data[1]
        if user_data[3] == 'None':
            name = None
        else:
            name = user_data[3]
        query_stmt = """
            SELECT who_user
            FROM followers
            WHERE whom_user = '%s'
            """ % (user_data[4])
        cursor.execute(query_stmt)
        followers = cursor.fetchall()
        query_stmt = """
            SELECT whom_user
            FROM followers
            WHERE who_user = '%s'
            """ % (user_data[4])
        cursor.execute(query_stmt)
        following = cursor.fetchall()
        query_stmt = """
            SELECT thread_id
            FROM subscriptions
            WHERE user = '%s'
            """ % (user_data[4])
        cursor.execute(query_stmt)
        subs = cursor.fetchall()
        user_info = {
            "about": about,
            "email": user_data[4],
            "followers": [x[0] for x in followers],
            "following": [x[0] for x in following],
            "id": user_data[0],
            "isAnonymous": bool(user_data[5]),
            "name": name,
            "subscriptions": [x[0] for x in subs],
            "username": username
        }
    else:
        user_info = thread_data[4]
    if 'forum' in related:
        related.remove('forum')
        query_stmt = """
            SELECT *
            FROM forums
            WHERE short_name = '%s'
            """ % (thread_data[1])
        cursor.execute(query_stmt)
        forum_data = cursor.fetchone()
        forum_info = {
            "id": forum_data[3],
            "name": forum_data[0],
            "short_name": forum_data[1],
            "user": forum_data[2]
        }
    else:
        forum_info = thread_data[1]
    if related:
        return_data = {"code": 3, "response": "invalid syntax"}
        db.close()
        return ujson.dumps(return_data)
    return_data = {
        "code": 0,
        "response": {
            "date": thread_data[5].strftime("%Y-%m-%d %H:%M:%S"),
            "dislikes": thread_data[10],
            "forum": forum_info,
            "id": thread_data[0],
            "isClosed": bool(thread_data[3]),
            "isDeleted": bool(thread_data[8]),
            "likes": thread_data[9],
            "message": thread_data[6],
            "points": (thread_data[9] - thread_data[10]),
            "posts": thread_data[11],
            "slug": thread_data[7],
            "title": thread_data[2],
            "user": user_info
        }
    }
    db.close()
    return ujson.dumps(return_data)


@app.route("/db/api/thread/list/", methods=["GET"])
def thread_list():
    db = db_connect()
    cursor = db.cursor()
    user = request.args.get('user', False)
    forum = request.args.get('forum', False)
    if user and forum:
        return_data = {"code": 3, "response": "bad syntax"}
        db.close()
        return ujson.dumps(return_data)
    limit = request.args.get('limit', False)
    since = request.args.get('since', False)
    order = request.args.get('order', False)
    query_stmt = """
        SELECT *
        FROM threads
        WHERE
        """
    if user:
        query_stmt += "user =  '%s'" % user
    else:
        query_stmt += "forum = '%s' " % forum
    if since:
        query_stmt += " AND date >= '%s' " % since
    if order:
        query_stmt += " ORDER BY date %s " % order
    if limit:
        query_stmt += " LIMIT %d" % (int(limit))
    cursor.execute(query_stmt)
    threads = cursor.fetchall()
    returnthreads = []
    for thread_data in threads:
        returnthreads.append({
            "date": thread_data[5].strftime("%Y-%m-%d %H:%M:%S"),
            "dislikes": thread_data[10],
            "forum": thread_data[1],
            "id": thread_data[0],
            "isClosed": bool(thread_data[3]),
            "isDeleted": bool(thread_data[8]),
            "likes": thread_data[9],
            "message": thread_data[6],
            "points": (thread_data[9] - thread_data[10]),
            "posts": thread_data[11],
            "slug": thread_data[7],
            "title": thread_data[2],
            "user": thread_data[4]
        })
    return_data = {"code": 0, "response": returnthreads}
    db.close()
    return ujson.dumps(return_data)


@app.route('/db/api/thread/listPosts/', methods=['GET'])
def thread_listpost():
    db = db_connect()
    cursor = db.cursor()
    thread = request.args.get('thread', False)
    if not thread:
        return_data = {"code": 3, "response": "bad syntax"}
        db.close()
        return ujson.dumps(return_data)
    limit = request.args.get('limit', False)
    since = request.args.get('since', False)
    order = request.args.get('order', 'desc')
    query_stmt = """
        SELECT *
        FROM threads
        WHERE thread_id = %d
        """ % (int(thread))
    cursor.execute(query_stmt)
    thread_data = cursor.fetchone()
    if thread_data:
        query_stmt = """
            SELECT *
            FROM posts
            WHERE thread = %d
            """ % (int(thread))
        if since:
            query_stmt += " AND date >= '%s' " % since
        query_stmt += " ORDER BY date %s " % order
        if limit:
            query_stmt += " LIMIT %d" % (int(limit))
        cursor.execute(query_stmt)
        post_datas = cursor.fetchall()
        post_list = []
        for post_data in post_datas:
            if post_data[1] == 0:
                parent = None
            else:
                parent = post_data[1]
            post_list.append({
                "date": post_data[6].strftime("%Y-%m-%d %H:%M:%S"),
                "dislikes": post_data[10],
                "forum": post_data[9],
                "id": post_data[0],
                "isApproved": bool(post_data[2]),
                "isDeleted": bool(post_data[5]),
                "isEdited": bool(post_data[3]),
                "isHighlighted": bool(post_data[13]),
                "isSpam": bool(post_data[4]),
                "likes": post_data[11],
                "message": post_data[7],
                "parent": parent,
                "points": (post_data[11] - post_data[10]),
                "thread": post_data[12],
                "user": post_data[8]
            })
        return_data = {"code": 0, "response": post_list}
        db.close()
        return ujson.dumps(return_data)

    else:
        return_data = {"code": 1, "response": "THREAD NOT FOUND"}
        db.close()
        return ujson.dumps(return_data)


@app.route('/db/api/thread/open/', methods=['POST'])
def thread_open():
    db = db_connect()
    cursor = db.cursor()
    try:
        data = request.get_json()
        thread = data['thread']
        query_stmt = """
            SELECT *
            FROM threads
            WHERE thread_id = %d
            """ % (int(thread))
        cursor.execute(query_stmt)
        thread_data = cursor.fetchone()
        if thread_data:
            if thread_data[3]:
                query_stmt = """
                    UPDATE threads set isClosed = False
                    WHERE thread_id = %d
                    """ % (int(thread))
                cursor.execute(query_stmt)
                db.commit()
                return_data = {"code": 0, "response": {"thread": thread}}
                db.close()
                return ujson.dumps(return_data)
            else:
                return_data = {
                    "code": 0,
                    "response": {
                        "date": thread_data[5].strftime("%Y-%m-%d %H:%M:%S"),
                        "dislikes": thread_data[10],
                        "forum": thread_data[1],
                        "id": thread_data[0],
                        "isClosed": bool(thread_data[3]),
                        "isDeleted": bool(thread_data[8]),
                        "likes": thread_data[9],
                        "message": thread_data[6],
                        "points": (thread_data[9] - thread_data[10]),
                        "posts": thread_data[11],
                        "slug": thread_data[7],
                        "title": thread_data[2],
                        "user": thread_data[4]
                    }
                }
                db.close()
                return ujson.dumps(return_data)
        else:
            return_data = {"code": 1, "response": "THREAD NOT FOUND"}
            db.close()
            return ujson.dumps(return_data)
    except KeyError:
        return_data = {"code": 2, "response": "invalid json format"}
        db.close()
        return ujson.dumps(return_data)


@app.route('/db/api/thread/remove/', methods=['POST'])
def thread_remove():
    db = db_connect()
    cursor = db.cursor()
    try:
        data = request.get_json()
        thread = data['thread']
        query_stmt = """
            SELECT *
            FROM threads
            WHERE thread_id = %d
            """ % (int(thread))
        cursor.execute(query_stmt)
        thread_data = cursor.fetchone()
        if thread_data:
            if not thread_data[8]:
                query_stmt = """
                    UPDATE threads set isDeleted = True
                    WHERE thread_id = %d
                    """ % (int(thread))
                cursor.execute(query_stmt)
                db.commit()
                query_stmt = """
                    UPDATE threads set posts = 0
                    WHERE thread_id = %d
                    """ % (int(thread))
                cursor.execute(query_stmt)
                db.commit()
                query_stmt = """
                    UPDATE posts set isDeleted = True
                    WHERE thread = %d
                    """ % (int(thread))
                cursor.execute(query_stmt)
                db.commit()
                return_data = {"code": 0, "response": {"thread": thread}}
                db.close()
                return ujson.dumps(return_data)
            else:
                query_stmt = """
                    UPDATE threads set posts = 0
                    WHERE thread_id = %d
                    """ % (int(thread))
                cursor.execute(query_stmt)
                db.commit()
                query_stmt = """
                    UPDATE posts set isDeleted = True
                    WHERE thread = %d
                    """ % (int(thread))
                cursor.execute(query_stmt)
                db.commit()
                return_data = {
                    "code": 0,
                    "response": {
                        "date": thread_data[5].strftime("%Y-%m-%d %H:%M:%S"),
                        "dislikes": thread_data[10],
                        "forum": thread_data[1],
                        "id": thread_data[0],
                        "isClosed": bool(thread_data[3]),
                        "isDeleted": bool(thread_data[8]),
                        "likes": thread_data[9],
                        "message": thread_data[6],
                        "points": (thread_data[9] - thread_data[10]),
                        "posts": 0,
                        "slug": thread_data[7],
                        "title": thread_data[2],
                        "user": thread_data[4]
                    }
                }
                db.close()
                return ujson.dumps(return_data)
        else:
            return_data = {"code": 1, "response": "THREAD NOT FOUND"}
            db.close()
            return ujson.dumps(return_data)
    except KeyError:
        return_data = {"code": 2, "response": "invalid json format"}
        db.close()
        return ujson.dumps(return_data)


@app.route('/db/api/thread/restore/', methods=['POST'])
def thread_restore():
    db = db_connect()
    cursor = db.cursor()
    try:
        data = request.get_json()
        thread = data['thread']
        query_stmt = """
            SELECT *
            FROM threads
            WHERE thread_id = %d
            """ % (int(thread))
        cursor.execute(query_stmt)
        thread_data = cursor.fetchone()
        if thread_data:
            if thread_data[8]:
                query_stmt = """
                    UPDATE threads set isDeleted = False
                    WHERE thread_id = %d
                    """ % (int(thread))
                cursor.execute(query_stmt)
                db.commit()
                query_stmt = """
                    UPDATE posts set isDeleted = False
                    WHERE thread = %d
                    """ % (int(thread))
                cursor.execute(query_stmt)
                db.commit()
                query_stmt = """
                    SELECT count(*)
                    FROM posts
                    WHERE  thread = %d
                    """ % (int(thread))
                cursor.execute(query_stmt)
                postcount = cursor.fetchone()
                query_stmt = """
                    UPDATE threads set posts = %d
                    WHERE thread_id = %d
                    """ % (int(postcount[0]), int(thread))
                cursor.execute(query_stmt)
                db.commit()
                return_data = {"code": 0, "response": {"thread": thread}}
                db.close()
                return ujson.dumps(return_data)
            else:
                return_data = {
                    "code": 0,
                    "response": {
                        "date": thread_data[5].strftime("%Y-%m-%d %H:%M:%S"),
                        "dislikes": thread_data[10],
                        "forum": thread_data[1],
                        "id": thread_data[0],
                        "isClosed": bool(thread_data[3]),
                        "isDeleted": bool(thread_data[8]),
                        "likes": thread_data[9],
                        "message": thread_data[6],
                        "points": (thread_data[9] - thread_data[10]),
                        "posts": thread_data[11],
                        "slug": thread_data[7],
                        "title": thread_data[2],
                        "user": thread_data[4]
                    }
                }
                db.close()
                return ujson.dumps(return_data)
        else:
            return_data = {"code": 1, "response": "THREAD NOT FOUND"}
            db.close()
            return ujson.dumps(return_data)
    except KeyError:
        return_data = {"code": 2, "response": "invalid json format"}
        db.close()
        return ujson.dumps(return_data)


@app.route('/db/api/thread/subscribe/', methods=['POST'])
def thread_subscribe():
    db = db_connect()
    cursor = db.cursor()
    try:
        data = request.get_json()
        user = data['user']
        thread = data['thread']
        query_stmt = """
            SELECT *
            FROM threads
            WHERE thread_id = %d
            """ % (int(thread))
        cursor.execute(query_stmt)
        thread_data = cursor.fetchone()
        query_stmt = """
            SELECT *
            FROM users
            WHERE email = '%s'
            """ % user
        cursor.execute(query_stmt)
        user_data = cursor.fetchone()
        if (not thread_data) or (not user_data):
            return_data = {"code": 1, "response": "THREAD or USER NOT FOUND"}
            db.close()
            return ujson.dumps(return_data)
        else:
            query_stmt = """
                SELECT *
                FROM subscriptions
                WHERE user = '%s' AND thread_id = %d
                """ % (user, int(thread))
            cursor.execute(query_stmt)
            sub = cursor.fetchone()
            if not sub:
                query_stmt = """
                    INSERT into subscriptions (user, thread_id)
                    VALUES ('%s', %d)
                    """ % (user, thread)
                cursor.execute(query_stmt)
                db.commit()
                return_data = {"code": 0, "response": {"thread": thread, "user": user}}
                db.close()
                return ujson.dumps(return_data)
            else:
                return_data = {"code": 0, "response": {"thread": thread, "user": user}}
                db.close()
                return ujson.dumps(return_data)
    except KeyError:
        return_data = {"code": 2, "response": "invalid json format"}
        return ujson.dumps(return_data)


@app.route('/db/api/thread/unsubscribe/', methods=['POST'])
def thread_unsubscribe():
    db = db_connect()
    cursor = db.cursor()
    try:
        data = request.get_json()
        user = data['user']
        thread = data['thread']
        query_stmt = """
            SELECT *
            FROM threads
            WHERE thread_id = %d
            """ % (int(thread))
        cursor.execute(query_stmt)
        thread_data = cursor.fetchone()
        query_stmt = """
            SELECT *
            FROM users
            WHERE email = '%s'
            """ % user
        cursor.execute(query_stmt)
        user_data = cursor.fetchone()
        if (not thread_data) or (not user_data):
            return_data = {"code": 1, "response": "THREAD or USER NOT FOUND"}
            db.close()
            return ujson.dumps(return_data)
        else:
            query_stmt = """
                SELECT *
                FROM subscriptions
                WHERE user = '%s' AND thread_id = %d
                """ % (user, int(thread))
            cursor.execute(query_stmt)
            sub = cursor.fetchone()
            if sub:
                query_stmt = """
                    DELETE
                    FROM subscriptions
                    WHERE user = '%s' AND thread_id = %d
                    """ % (user, thread)
                cursor.execute(query_stmt)
                db.commit()
                return_data = {"code": 0, "response": {"thread": thread, "user": user}}
                db.close()
                return ujson.dumps(return_data)
            else:
                return_data = {"code": 0, "response": {"thread": thread, "user": user}}
                db.close()
                return ujson.dumps(return_data)
    except KeyError:
        return_data = {"code": 2, "response": "invalid json format"}
        db.close()
        return ujson.dumps(return_data)


@app.route('/db/api/thread/update/', methods=['POST'])
def thread_update():
    db = db_connect()
    cursor = db.cursor()
    try:
        data = request.get_json()
        thread = data['thread']
        message = data['message']
        slug = data['slug']
        query_stmt = """
            SELECT *
            FROM threads
            WHERE thread_id = %d
            """ % (int(thread))
        cursor.execute(query_stmt)
        thread_data = cursor.fetchone()
        if thread_data:
            if (thread_data[6] != message) or (thread_data[7] != slug):
                query_stmt = """
                    UPDATE threads set message = '%s'
                    WHERE thread_id = %d
                    """ % (message, thread)
                cursor.execute(query_stmt)
                query_stmt = """
                    UPDATE threads set slug = '%s'
                    WHERE thread_id = %d
                    """ % (slug, thread)
                cursor.execute(query_stmt)
                db.commit()
                return_data = {
                    "code": 0,
                    "response": {
                        "date": thread_data[5].strftime("%Y-%m-%d %H:%M:%S"),
                        "dislikes": thread_data[10],
                        "forum": thread_data[1],
                        "id": thread_data[0],
                        "isClosed": bool(thread_data[3]),
                        "isDeleted": bool(thread_data[8]),
                        "likes": thread_data[9],
                        "message": message,
                        "points": (thread_data[9] - thread_data[10]),
                        "posts": thread_data[11],
                        "slug": slug,
                        "title": thread_data[2],
                        "user": thread_data[4]
                    }
                }
                db.close()
                return ujson.dumps(return_data)
            else:
                return_data = {
                    "code": 0,
                    "response": {
                        "date": thread_data[5].strftime("%Y-%m-%d %H:%M:%S"),
                        "dislikes": thread_data[10],
                        "forum": thread_data[1],
                        "id": thread_data[0],
                        "isClosed": bool(thread_data[3]),
                        "isDeleted": bool(thread_data[8]),
                        "likes": thread_data[9],
                        "message": thread_data[6],
                        "points": (thread_data[9] - thread_data[10]),
                        "posts": thread_data[11],
                        "slug": thread_data[7],
                        "title": thread_data[2],
                        "user": thread_data[4]
                    }
                }
                db.close()
                return ujson.dumps(return_data)
        else:
            return_data = {"code": 1, "response": "THREAD NOT FOUND"}
            db.close()
            return ujson.dumps(return_data)
    except KeyError:
        return_data = {"code": 2, "response": "invalid json format"}
        db.close()
        return ujson.dumps(return_data)


@app.route('/db/api/thread/vote/', methods=['POST'])
def thread_vote():
    db = db_connect()
    cursor = db.cursor()
    try:
        data = request.get_json()
        vote = data['vote']
        thread = data['thread']
        query_stmt = """
            SELECT *
            FROM threads
            WHERE thread_id = %d
            """ % (int(thread))
        cursor.execute(query_stmt)
        thread_data = cursor.fetchone()
        if thread_data:
            if vote == 1:
                query_stmt = """
                    UPDATE threads set likes = likes + 1
                    WHERE thread_id = %d
                    """ % (int(thread))
                likes = thread_data[9] + 1
                dislikes = thread_data[10]
            elif vote == -1:
                query_stmt = """
                    UPDATE threads set dislikes = dislikes + 1
                    WHERE thread_id = %d
                    """ % (int(thread))
                likes = thread_data[9]
                dislikes = thread_data[10] + 1
            else:
                return_data = {"code": 3, "response": "invalid syntax"}
                return ujson.dumps(return_data)
            cursor.execute(query_stmt)
            db.commit()
            return_data = {
                "code": 0,
                "response": {
                    "date": thread_data[5].strftime("%Y-%m-%d %H:%M:%S"),
                    "dislikes": dislikes,
                    "forum": thread_data[1],
                    "id": thread_data[0],
                    "isClosed": bool(thread_data[3]),
                    "isDeleted": bool(thread_data[8]),
                    "likes": likes,
                    "message": thread_data[6],
                    "points": (likes - dislikes),
                    "posts": thread_data[11],
                    "slug": thread_data[7],
                    "title": thread_data[2],
                    "user": thread_data[4]
                }
            }
            db.close()
            return ujson.dumps(return_data)
        else:
            return_data = {"code": 1, "response": "THREAD NOT FOUND"}
            db.close()
            return ujson.dumps(return_data)
    except KeyError:
        return_data = {"code": 2, "response": "invalid json format"}
        db.close()
        return ujson.dumps(return_data)


if __name__ == '__main__':
    app.run()
