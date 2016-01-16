# -*- coding: utf-8 -*-
from flask import Flask, jsonify, request
import MySQLdb
from _mysql_exceptions import IntegrityError

app = Flask(__name__)

# CONFIG
app.config['JSON_SORT_KEYS'] = False
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False


@app.route('/db/api/clear/', methods=['POST'])
def clear():
    """Truncate all tables"""
    db = MySQLdb.connect(host='localhost', user="db_api_user", passwd="passwd", db="db_func_test", charset='utf8')
    cursor = db.cursor()
    query_str = 'TRUNCATE TABLE '
    names_array = ['forums', 'users', 'threads', 'posts', 'followers', 'subscriptions']
    for name in names_array:
        cursor.execute(query_str + name)
    db.commit()
    return_data = {"code": 0, "response": "OK"}
    return jsonify(return_data)


@app.route('/db/api/status/', methods=['GET'])
def status():
    """Show status info: maps table name to number of rows in that table"""
    db = MySQLdb.connect(host='localhost', user="db_api_user", passwd="passwd", db="db_func_test", charset='utf8')
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
    return jsonify(return_data)


# FORUMS


@app.route('/db/api/forum/create/', methods=['POST'])
def forum_create():
    """Create new forum"""
    try:
        db = MySQLdb.connect(host='localhost', user="db_api_user", passwd="passwd", db="db_func_test", charset='utf8')
        cursor = db.cursor()
        data = request.get_json()
        name = data['name']
        short_name = data['short_name']
        user = data['user']
        q = """
            INSERT INTO forums (name,short_name,user)
            VALUES ('%s','%s','%s')
            """ % (name, short_name, user)
        cursor.execute(q)
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
        return jsonify(return_data)
    except IntegrityError, e:
        if e[0] == 1062:
            if 'short_name_UNIQUE' in e[1]:
                q = """
                    SELECT *
                    FROM forums
                    WHERE short_name = '%s'
                    """ % short_name
            else:
                q = """
                    SELECT *
                    FROM forums
                    WHERE name = '%s'
                    """ % name
            db = MySQLdb.connect(host='localhost', user="db_api_user", passwd="passwd", db="db_func_test",
                                 charset='utf8')
            cursor = db.cursor()
            cursor.execute(q)
            myforum = cursor.fetchone()
            return_data = {
                "code": 0,
                "response": {
                    "id": myforum[3],
                    "name": myforum[0],
                    "short_name": myforum[1],
                    "user": myforum[2]
                }
            }
            return jsonify(return_data)
    except KeyError:
        return_data = {"code": 2, "response": "invalid json format"}
        return jsonify(return_data)


@app.route('/db/api/forum/details/', methods=['GET'])
def forum_details():
    """Get forum details"""
    db = MySQLdb.connect(host='localhost', user="db_api_user", passwd="passwd", db="db_func_test", charset='utf8')
    cursor = db.cursor()
    forum = request.args.get('forum', '')
    related = request.args.getlist('related')
    q = """
        SELECT *
        FROM forums
        WHERE short_name = '%s'
        """ % forum
    if cursor.execute(q) == 0:
        return_data = {"code": 1, "response": "FORUM NOT FOUND"}
        return jsonify(return_data)
    myforum = cursor.fetchone()
    if 'user' in related:
        q = """
            SELECT *
            FROM users
            WHERE email = '%s'
            """ % myforum[2]
        cursor.execute(q)
        myuser = cursor.fetchone()
        if myuser[2] == 'None':
            about = None
        else:
            about = myuser[2]
        if myuser[1] == 'None':
            username = None
        else:
            username = myuser[1]
        if myuser[3] == 'None':
            name = None
        else:
            name = myuser[3]
        q = """
            SELECT who_user
            FROM followers
            WHERE whom_user = '%s'
            """ % myuser[4]
        cursor.execute(q)
        myfollowers = cursor.fetchall()
        q = """
            SELECT whom_user
            FROM followers
            WHERE who_user = '%s'
            """ % myuser[4]
        cursor.execute(q)
        myfollowing = cursor.fetchall()
        q = """
            SELECT thread_id
            FROM subscriptions
            WHERE user = '%s'
            """ % myuser[4]
        cursor.execute(q)
        mysubs = cursor.fetchall()
        userinfo = {
            "about": about,
            "email": myuser[4],
            "followers": [x[0] for x in myfollowers],
            "following": [x[0] for x in myfollowing],
            "id": myuser[0],
            "isAnonymous": bool(myuser[5]),
            "name": name,
            "subscriptions": [x[0] for x in mysubs],
            "username": username
        }
    else:
        userinfo = myforum[2]
    return_data = {
        "code": 0,
        "response": {
            "id": myforum[3],
            "name": myforum[0],
            "short_name": myforum[1],
            "user": userinfo
        }
    }
    return jsonify(return_data)


@app.route('/db/api/forum/listPosts/', methods=['GET'])
def forum_listPosts():
    """Get posts from this forum"""
    db = MySQLdb.connect(host='localhost', user="db_api_user", passwd="passwd", db="db_func_test", charset='utf8')
    cursor = db.cursor()
    forum = request.args.get('forum')
    if not forum:
        return_data = {"code": 3, "response": "bad syntax"}
        return jsonify(return_data)
    related = request.args.getlist('related')
    order = request.args.get('order', 'desc')
    limit = request.args.get('limit', False)
    since = request.args.get('since', False)
    q = """
        SELECT *
        FROM forums
        WHERE short_name = '%s'
        """ % forum
    if cursor.execute(q) == 0:
        return_data = {"code": 1, "response": "FORUM NOT FOUND"}
        return jsonify(return_data)
    myforum = cursor.fetchone()
    q = """
        SELECT *
        FROM posts
        WHERE forum = '%s'
        """ % forum
    if since:
        q += " AND date >= '%s' " % since
    q += " ORDER BY  date %s " % order
    if limit:
        q += " LIMIT %d" % (int(limit))
    cursor.execute(q)
    myposts = cursor.fetchall()
    if 'forum' in related:
        related.remove('forum')
        foruminfo = {
            "id": myforum[3],
            "name": myforum[0],
            "short_name": myforum[1],
            "user": myforum[2]
        }
    else:
        foruminfo = forum
    ListPosts = []
    for mypost in myposts:
        if 'user' in related:
            q = """
                SELECT *
                FROM users
                WHERE email = '%s'
                """ % mypost[8]
            cursor.execute(q)
            myuser = cursor.fetchone()
            if myuser[2] == 'None':
                about = None
            else:
                about = myuser[2]
            if myuser[1] == 'None':
                username = None
            else:
                username = myuser[1]
            if myuser[3] == 'None':
                name = None
            else:
                name = myuser[3]
            q = """
                SELECT who_user
                FROM followers
                WHERE whom_user = '%s'
                """ % myuser[4]
            cursor.execute(q)
            myfollowers = cursor.fetchall()
            q = """
                SELECT whom_user
                FROM followers
                WHERE who_user = '%s'
                """ % myuser[4]
            cursor.execute(q)
            myfollowing = cursor.fetchall()
            q = """
                SELECT thread_id
                FROM subscriptions
                WHERE user = '%s'
                """ % myuser[4]
            cursor.execute(q)
            mysubs = cursor.fetchall()
            userinfo = {
                "about": about,
                "email": myuser[4],
                "followers": [x[0] for x in myfollowers],
                "following": [x[0] for x in myfollowing],
                "id": myuser[0],
                "isAnonymous": bool(myuser[5]),
                "name": name,
                "subscriptions": [x[0] for x in mysubs],
                "username": username
            }
        else:
            userinfo = mypost[8]

        if 'thread' in related:
            q = """
            SELECT *
            FROM threads
            WHERE thread_id = '%s'
            """ % mypost[12]
            cursor.execute(q)
            mythread = cursor.fetchone()
            threadinfo = {
                "date": mythread[5].strftime("%Y-%m-%d %H:%M:%S"),
                "dislikes": mythread[10],
                "forum": mythread[1],
                "id": mythread[0],
                "isClosed": bool(mythread[3]),
                "isDeleted": bool(mythread[8]),
                "likes": mythread[9],
                "message": mythread[6],
                "points": (mythread[9] - mythread[10]),
                "posts": mythread[11],
                "slug": mythread[7],
                "title": mythread[2],
                "user": mythread[4]
            }
        else:
            threadinfo = mypost[12]
        if mypost[1] == 0:
            parent = None
        else:
            parent = mypost[1]

        return_data = {
            "date": mypost[6].strftime("%Y-%m-%d %H:%M:%S"),
            "dislikes": mypost[10],
            "forum": foruminfo,
            "id": mypost[0],
            "isApproved": bool(mypost[2]),
            "isDeleted": bool(mypost[5]),
            "isEdited": bool(mypost[3]),
            "isHighlighted": bool(mypost[13]),
            "isSpam": bool(mypost[4]),
            "likes": mypost[11],
            "message": mypost[7],
            "parent": parent,
            "points": (mypost[11] - mypost[10]),
            "thread": threadinfo,
            "user": userinfo
        }
        ListPosts.append(return_data)
    return jsonify({"code": 0, "response": ListPosts})


@app.route('/db/api/forum/listThreads/', methods=['GET'])
def forum_listThreads():
    """Get threads from this forum"""
    db = MySQLdb.connect(host='localhost', user="db_api_user", passwd="passwd", db="db_func_test", charset='utf8')
    cursor = db.cursor()
    forum = request.args.get('forum')
    if not forum:
        return_data = {"code": 3, "response": "bad syntax"}
        return jsonify(return_data)
    related = request.args.getlist('related')
    order = request.args.get('order', 'desc')
    limit = request.args.get('limit', False)
    since = request.args.get('since', False)
    q = """
        SELECT *
        FROM forums
        WHERE short_name = '%s'
        """ % forum
    if cursor.execute(q) == 0:
        return_data = {"code": 1, "response": "FORUM NOT FOUND"}
        return jsonify(return_data)
    myforum = cursor.fetchone()
    q = """
        SELECT *
        FROM threads
        WHERE forum = '%s'
        """ % forum
    if since:
        q += " AND date >= '%s' " % since
    q += " ORDER BY  date %s " % order
    if limit:
        q += " LIMIT %d" % (int(limit))
    cursor.execute(q)
    mythreads = cursor.fetchall()
    if 'forum' in related:
        foruminfo = {
            "id": myforum[3],
            "name": myforum[0],
            "short_name": myforum[1],
            "user": myforum[2]
        }
    else:
        foruminfo = forum
    ListThreads = []
    for mythread in mythreads:
        if 'user' in related:
            q = """
                SELECT *
                FROM users
                WHERE email = '%s'
                """ % mythread[4]
            cursor.execute(q)
            myuser = cursor.fetchone()
            if myuser[2] == 'None':
                about = None
            else:
                about = myuser[2]
            if myuser[1] == 'None':
                username = None
            else:
                username = myuser[1]
            if myuser[3] == 'None':
                name = None
            else:
                name = myuser[3]
            q = """
                SELECT who_user
                FROM followers
                WHERE whom_user = '%s'
                """ % myuser[4]
            cursor.execute(q)
            myfollowers = cursor.fetchall()
            q = """
                SELECT whom_user
                FROM followers
                WHERE who_user = '%s'
                """ % myuser[4]
            cursor.execute(q)
            myfollowing = cursor.fetchall()
            q = """
                SELECT thread_id
                FROM subscriptions
                WHERE user = '%s'
                """ % myuser[4]
            cursor.execute(q)
            mysubs = cursor.fetchall()
            userinfo = {
                "about": about,
                "email": myuser[4],
                "followers": [x[0] for x in myfollowers],
                "following": [x[0] for x in myfollowing],
                "id": myuser[0],
                "isAnonymous": bool(myuser[5]),
                "name": name,
                "subscriptions": [x[0] for x in mysubs],
                "username": username
            }
        else:
            userinfo = mythread[4]

        return_data = {
            "date": mythread[5].strftime("%Y-%m-%d %H:%M:%S"),
            "dislikes": mythread[10],
            "forum": foruminfo,
            "id": mythread[0],
            "isClosed": bool(mythread[3]),
            "isDeleted": bool(mythread[8]),
            "likes": mythread[9],
            "message": mythread[6],
            "points": (mythread[9] - mythread[10]),
            "posts": mythread[11],
            "slug": mythread[7],
            "title": mythread[2],
            "user": userinfo
        }
        ListThreads.append(return_data)
    return jsonify({"code": 0, "response": ListThreads})


@app.route('/db/api/forum/listUsers/', methods=['GET'])
def forum_listUsers():
    db = MySQLdb.connect(host='localhost', user="db_api_user", passwd="passwd", db="db_func_test", charset='utf8')
    cursor = db.cursor()
    forum = request.args.get('forum')
    if not forum:
        return_data = {"code": 3, "response": "bad syntax"}
        return jsonify(return_data)
    order = request.args.get('order', 'desc')
    limit = request.args.get('limit', False)
    since = request.args.get('since_id', False)
    q = """
        SELECT *
        FROM forums
        WHERE short_name = '%s'
        """ % forum
    if cursor.execute(q) == 0:
        return_data = {"code": 1, "response": "FORUM NOT FOUND"}
        return jsonify(return_data)

    q = """
        SELECT *
        FROM users
        WHERE email IN (SELECT DISTINCT user FROM posts WHERE forum = '%s')
        """ % forum
    if since:
        q += " AND user_id >= %d " % (int(since))
    q += " ORDER BY  name %s " % order
    if limit:
        q += " LIMIT %d" % (int(limit))

    cursor.execute(q)
    myusers = cursor.fetchall()

    ListUsers = []
    for myuser in myusers:
        if myuser[2] == 'None':
            about = None
        else:
            about = myuser[2]
        if myuser[1] == 'None':
            username = None
        else:
            username = myuser[1]
        if myuser[3] == 'None':
            name = None
        else:
            name = myuser[3]
        q = """
            SELECT who_user
            FROM followers
            WHERE whom_user = '%s'
            """ % myuser[4]
        cursor.execute(q)
        myfollowers = cursor.fetchall()
        q = """
            SELECT whom_user
            FROM followers
            WHERE who_user = '%s'
            """ % myuser[4]
        cursor.execute(q)
        myfollowing = cursor.fetchall()
        q = """
            SELECT thread_id
            FROM subscriptions
            WHERE user = '%s'
            """ % myuser[4]
        cursor.execute(q)
        mysubs = cursor.fetchall()
        userinfo = {
            "about": about,
            "email": myuser[4],
            "followers": [x[0] for x in myfollowers],
            "following": [x[0] for x in myfollowing],
            "id": myuser[0],
            "isAnonymous": bool(myuser[5]),
            "name": name,
            "subscriptions": [x[0] for x in mysubs],
            "username": username
        }
        ListUsers.append(userinfo)
    return jsonify({"code": 0, "response": ListUsers})


# USERS
@app.route('/db/api/user/create/', methods=['POST'])
def user_create():
    db = MySQLdb.connect(host='localhost', user="db_api_user", passwd="passwd", db="db_func_test", charset='utf8')
    cursor = db.cursor()
    try:
        data = request.get_json()
        about = data['about']
        email = data['email']
        username = data['username']
        name = data['name']
        isAnonymous = data.get('isAnonymous', False)
        if name != None:
            q = """
                INSERT INTO users (username, about, name, email, isAnonymous)
                VALUES('%s','%s','%s','%s',%d)""" % (username, about, name, email, isAnonymous)
        else:
            q = """
                INSERT INTO users (username, about, name, email, isAnonymous)
                VALUES('%s','%s',Null,'%s',%d)""" % (username, about, email, isAnonymous)
        cursor.execute(q)
        returnData = {
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
        return jsonify(returnData)
    except IntegrityError, e:
        if e[0] == 1062:
            returnData = {"code": 5, "response": "duplicate user"}
            return jsonify(returnData)
    except KeyError:
        returnData = {"code": 2, "response": "invalid json format"}
        return jsonify(returnData)


@app.route('/db/api/user/details/', methods=['GET'])
def user_details():
    db = MySQLdb.connect(host='localhost', user="db_api_user", passwd="passwd", db="db_func_test", charset='utf8')
    cursor = db.cursor()
    user = request.args.get('user', '')
    q = """
        SELECT *
        FROM users
        WHERE email = '%s'
        """ % user
    if cursor.execute(q) == 0:
        returnData = {"code": 1, "response": "USER NOT FOUND"}
        return jsonify(returnData)
    else:
        myuser = cursor.fetchone()
        q = """
            SELECT who_user
            FROM followers
            WHERE whom_user = '%s'
            """ % myuser[4]
        cursor.execute(q)
        myfollowers = cursor.fetchall()
        q = """
            SELECT whom_user
            FROM followers
            WHERE who_user = '%s'
            """ % (myuser[4])
        cursor.execute(q)
        myfollowing = cursor.fetchall()
        q = """
            SELECT thread_id
            FROM subscriptions
            WHERE user = '%s'
            """ % (myuser[4])
        cursor.execute(q)
        mysubs = cursor.fetchall()
        if myuser[2] == 'None':
            about = None
        else:
            about = myuser[2]
        if myuser[1] == 'None':
            username = None
        else:
            username = myuser[1]
        if myuser[3] == 'None':
            name = None
        else:
            name = myuser[3]

        userinfo = {
            "about": about,
            "email": myuser[4],
            "followers": [x[0] for x in myfollowers],
            "following": [x[0] for x in myfollowing],
            "id": myuser[0],
            "isAnonymous": bool(myuser[5]),
            "name": name,
            "subscriptions": [x[0] for x in mysubs],
            "username": username
        }
        returnData = {"code": 0, "response": userinfo}
        return jsonify(returnData)


@app.route('/db/api/user/listPosts/', methods=['GET'])
def user_listPosts():
    db = MySQLdb.connect(host='localhost', user="db_api_user", passwd="passwd", db="db_func_test", charset='utf8')
    cursor = db.cursor()
    user = request.args.get('user', False)
    if not user:
        returnData = {"code": 3, "response": "bad syntax"}
        return jsonify(returnData)
    limit = request.args.get('limit', False)
    since = request.args.get('since', False)
    order = request.args.get('order', 'desc')
    q = """
        SELECT *
        FROM users
        WHERE email = '%s'
        """ % user
    cursor.execute(q)
    myuser = cursor.fetchone()
    if myuser:
        q = """
            SELECT *
            FROM posts
            WHERE user = '%s'
            """ % user
        if since:
            q += " AND date >= '%s' " % (since)
        q += " ORDER BY date %s " % (order)
        if limit:
            q += " LIMIT %d" % (int(limit))
        cursor.execute(q)
        myposts = cursor.fetchall()
        postlist = []

        for mypost in myposts:
            if mypost[1] == 0:
                parent = None
            else:
                parent = mypost[1]
            postlist.append({
                "date": mypost[6].strftime("%Y-%m-%d %H:%M:%S"),
                "dislikes": mypost[10],
                "forum": mypost[9],
                "id": mypost[0],
                "isApproved": bool(mypost[2]),
                "isDeleted": bool(mypost[5]),
                "isEdited": bool(mypost[3]),
                "isHighlighted": bool(mypost[13]),
                "isSpam": bool(mypost[4]),
                "likes": mypost[11],
                "message": mypost[7],
                "parent": parent,
                "points": (mypost[11] - mypost[10]),
                "thread": mypost[12],
                "user": mypost[8]
            })
        returnData = {"code": 0, "response": postlist}
        return jsonify(returnData)

    else:
        returnData = {"code": 1, "response": "USER NOT FOUND"}
        return jsonify(returnData)


@app.route('/db/api/user/updateProfile/', methods=['POST'])
def user_updateProfile():
    db = MySQLdb.connect(host='localhost', user="db_api_user", passwd="passwd", db="db_func_test", charset='utf8')
    cursor = db.cursor()
    try:
        data = request.get_json()
        user = data['user']
        about = data['about']
        name = data['name']
        q = """
            SELECT *
            FROM users
            WHERE email = '%s'
            """ % user
        cursor.execute(q)
        myuser = cursor.fetchone()
        if myuser:
            if (myuser[2] != about) or (myuser[3] != name):
                q = """
                    UPDATE users set about = '%s'
                    WHERE email = '%s'
                    """ % (about, user)
                cursor.execute(q)
                q = """
                    UPDATE users set name = '%s'
                    WHERE email = '%s'
                    """ % (name, user)
                cursor.execute(q)
                db.commit()
                q = """
                    SELECT who_user
                    FROM followers
                    WHERE whom_user = '%s'
                    """ % (myuser[4])
                cursor.execute(q)
                myfollowers = cursor.fetchall()
                q = """
                    SELECT whom_user
                    FROM followers
                    WHERE who_user = '%s'
                    """ % (myuser[4])
                cursor.execute(q)
                myfollowing = cursor.fetchall()
                q = """
                    SELECT thread_id
                    FROM subscriptions
                    WHERE user = '%s'
                    """ % (myuser[4])
                cursor.execute(q)
                mysubs = cursor.fetchall()
                if about == 'None':
                    about = None
                if myuser[1] == 'None':
                    username = None
                else:
                    username = myuser[1]
                if name == 'None':
                    name = None
                userinfo = {
                    "about": about,
                    "email": myuser[4],
                    "followers": [x[0] for x in myfollowers],
                    "following": [x[0] for x in myfollowing],
                    "id": myuser[0],
                    "isAnonymous": bool(myuser[5]),
                    "name": name,
                    "subscriptions": [x[0] for x in mysubs],
                    "username": username
                }
                returnData = {"code": 0, "response": userinfo}
                return jsonify(returnData)
            else:

                q = """
                    SELECT who_user
                    FROM followers
                    WHERE whom_user = '%s'
                    """ % (myuser[4])
                cursor.execute(q)
                myfollowers = cursor.fetchall()
                q = """
                    SELECT whom_user
                    FROM followers
                    WHERE who_user = '%s'
                    """ % (myuser[4])
                cursor.execute(q)
                myfollowing = cursor.fetchall()
                q = """
                    SELECT thread_id
                    FROM subscriptions
                    WHERE user = '%s'
                    """ % (myuser[4])
                cursor.execute(q)
                mysubs = cursor.fetchall()
                if myuser[2] == 'None':
                    about = None
                else:
                    about = myuser[2]
                if myuser[1] == 'None':
                    username = None
                else:
                    username = myuser[1]
                if myuser[3] == 'None':
                    name = None
                else:
                    name = myuser[3]

                userinfo = {
                    "about": about,
                    "email": myuser[4],
                    "followers": [x[0] for x in myfollowers],
                    "following": [x[0] for x in myfollowing],
                    "id": myuser[0],
                    "isAnonymous": bool(myuser[5]),
                    "name": name,
                    "subscriptions": [x[0] for x in mysubs],
                    "username": username
                }
                returnData = {"code": 0, "response": userinfo}
                return jsonify(returnData)
        else:
            returnData = {"code": 1, "response": "USER NOT FOUND"}
            return jsonify(returnData)
    except KeyError:
        returnData = {"code": 2, "response": "invalid json format"}
        return jsonify(returnData)


@app.route('/db/api/user/follow/', methods=['POST'])
def user_follow():
    db = MySQLdb.connect(host='localhost', user="db_api_user", passwd="passwd", db="db_func_test", charset='utf8')
    cursor = db.cursor()
    try:
        data = request.get_json()
        follower = data['follower']  # who
        followee = data['followee']  # whom
        if followee == follower:
            returnData = {"code": 3, "response": "WTF!"}
            return jsonify(returnData)
        q = """
            SELECT *
            FROM users
            WHERE email = '%s'
            """ % followee
        cursor.execute(q)
        myuserwhom = cursor.fetchone()
        if myuserwhom:
            q = """
                SELECT *
                FROM followers
                WHERE who_user = '%s' AND whom_user = '%s'
                """ % (follower, followee)
            cursor.execute(q)
            if not cursor.fetchone():
                q = """
                    SELECT *
                    FROM users
                    WHERE email = '%s'
                    """ % follower
                cursor.execute(q)
                myuser = cursor.fetchone()
                if myuser:
                    q = """
                        INSERT into followers (who_user, whom_user)
                        VALUES ('%s', '%s')
                        """ % (follower, followee)
                    cursor.execute(q)
                    db.commit()
                    q = """
                        SELECT who_user
                        FROM followers
                        WHERE whom_user = '%s'
                        """ % (myuser[4])
                    cursor.execute(q)
                    myfollowers = cursor.fetchall()
                    q = """
                        SELECT whom_user
                        FROM followers
                        WHERE who_user = '%s'
                        """ % (myuser[4])
                    cursor.execute(q)
                    myfollowing = cursor.fetchall()
                    q = """
                        SELECT thread_id
                        FROM subscriptions
                        WHERE user = '%s'
                        """ % (myuser[4])
                    cursor.execute(q)
                    mysubs = cursor.fetchall()
                    if myuser[2] == 'None':
                        about = None
                    else:
                        about = myuser[2]
                    if myuser[1] == 'None':
                        username = None
                    else:
                        username = myuser[1]
                    if myuser[3] == 'None':
                        name = None
                    else:
                        name = myuser[3]

                    userinfo = {
                        "about": about,
                        "email": myuser[4],
                        "followers": [x[0] for x in myfollowers],
                        "following": [x[0] for x in myfollowing],
                        "id": myuser[0],
                        "isAnonymous": bool(myuser[5]),
                        "name": name,
                        "subscriptions": [x[0] for x in mysubs],
                        "username": username
                    }
                    returnData = {"code": 0, "response": userinfo}
                    return jsonify(returnData)
                else:
                    returnData = {"code": 1, "response": "USER NOT FOUND"}

                    return jsonify(returnData)
            else:
                q = """
                    SELECT *
                    FROM users
                    WHERE email = '%s'
                    """ % follower
                cursor.execute(q)
                myuser = cursor.fetchone()
                q = """
                    SELECT who_user
                    FROM followers
                    WHERE whom_user = '%s'
                    """ % (myuser[4])
                cursor.execute(q)
                myfollowers = cursor.fetchall()
                q = """
                    SELECT whom_user
                    FROM followers
                    WHERE who_user = '%s'
                    """ % (myuser[4])
                cursor.execute(q)
                myfollowing = cursor.fetchall()
                q = """
                    SELECT thread_id
                    FROM subscriptions
                    WHERE user = '%s'
                    """ % (myuser[4])
                cursor.execute(q)
                mysubs = cursor.fetchall()
                if myuser[2] == 'None':
                    about = None
                else:
                    about = myuser[2]
                if myuser[1] == 'None':
                    username = None
                else:
                    username = myuser[1]
                if myuser[3] == 'None':
                    name = None
                else:
                    name = myuser[3]

                userinfo = {
                    "about": about,
                    "email": myuser[4],
                    "followers": [x[0] for x in myfollowers],
                    "following": [x[0] for x in myfollowing],
                    "id": myuser[0],
                    "isAnonymous": bool(myuser[5]),
                    "name": name,
                    "subscriptions": [x[0] for x in mysubs],
                    "username": username
                }
                returnData = {"code": 0, "response": userinfo}
                return jsonify(returnData)

        else:
            returnData = {"code": 1, "response": "USER NOT FOUND"}

            return jsonify(returnData)
    except KeyError:
        returnData = {"code": 2, "response": "invalid json format"}
        return jsonify(returnData)


@app.route('/db/api/user/listFollowers/', methods=['GET'])
def user_listFollowers():
    db = MySQLdb.connect(host='localhost', user="db_api_user", passwd="passwd", db="db_func_test", charset='utf8')
    cursor = db.cursor()
    user = request.args.get('user', False)
    if not user:
        returnData = {"code": 3, "response": "bad syntax"}
        return jsonify(returnData)
    limit = request.args.get('limit', False)
    since_id = request.args.get('since_id', False)
    order = request.args.get('order', 'desc')
    q = "SELECT * FROM users WHERE email = '%s'" % (user)
    cursor.execute(q)
    myuser = cursor.fetchone()
    if myuser:
        q = """
            SELECT straight_join user_id, username, about, name, email, isAnonymous
            FROM followers join users ON users.email = followers.who_user
            WHERE whom_user = '%s'
            """ % user
        if since_id:
            q += " AND user_id >= %d " % (int(since_id))
        q += " ORDER BY name %s" % order
        if limit:
            q += " LIMIT %d" % (int(limit))
        cursor.execute(q)
        myfollowers = cursor.fetchall()
        followersList = []
        for myuser in myfollowers:
            q = """
                SELECT who_user
                FROM followers
                WHERE whom_user = '%s'
                """ % (myuser[4])
            cursor.execute(q)
            myfollowers = cursor.fetchall()
            q = """
                SELECT whom_user
                FROM followers
                WHERE who_user = '%s'
                """ % (myuser[4])
            cursor.execute(q)
            myfollowing = cursor.fetchall()
            q = """
                SELECT thread_id
                FROM subscriptions
                WHERE user = '%s'
                """ % (myuser[4])
            cursor.execute(q)
            mysubs = cursor.fetchall()
            if myuser[2] == 'None':
                about = None
            else:
                about = myuser[2]
            if myuser[1] == 'None':
                username = None
            else:
                username = myuser[1]
            if myuser[3] == 'None':
                name = None
            else:
                name = myuser[3]
            userinfo = {
                "about": about,
                "email": myuser[4],
                "followers": [x[0] for x in myfollowers],
                "following": [x[0] for x in myfollowing],
                "id": myuser[0],
                "isAnonymous": bool(myuser[5]),
                "name": name,
                "subscriptions": [x[0] for x in mysubs],
                "username": username
            }
            followersList.append(userinfo)
        returnData = {"code": 0, "response": followersList}
        return jsonify(returnData)
    else:
        returnData = {"code": 1, "response": "USER NOT FOUND"}
        return jsonify(returnData)


@app.route('/db/api/user/listFollowing/', methods=['GET'])
def user_listFollowing():
    db = MySQLdb.connect(host='localhost', user="db_api_user", passwd="passwd", db="db_func_test", charset='utf8')
    cursor = db.cursor()
    user = request.args.get('user', False)
    if not user:
        returnData = {"code": 3, "response": "bad syntax"}
        return jsonify(returnData)
    limit = request.args.get('limit', False)
    since_id = request.args.get('since_id', False)
    order = request.args.get('order', 'desc')
    q = """
        SELECT *
        FROM users
        WHERE email = '%s'
        """ % user
    cursor.execute(q)
    myuser = cursor.fetchone()
    if myuser:
        q = """
            SELECT straight_join user_id, username, about, name, email, isAnonymous
            FROM followers join users ON users.email = followers.whom_user
            WHERE who_user = '%s'
            """ % user
        if since_id:
            q += " AND user_id >= %d " % (int(since_id))
        q += " ORDER BY name %s" % order
        if limit:
            q += " LIMIT %d" % (int(limit))
        cursor.execute(q)
        allmyfollowing = cursor.fetchall()
        myfollowingList = []
        for myuser in allmyfollowing:
            q = """
                SELECT who_user
                FROM followers
                WHERE whom_user = '%s'
                """ % (myuser[4])
            cursor.execute(q)
            myfollowers = cursor.fetchall()
            q = """
                SELECT whom_user
                FROM followers
                WHERE who_user = '%s'
                """ % (myuser[4])
            cursor.execute(q)
            myfollowing = cursor.fetchall()
            q = """
                SELECT thread_id
                FROM subscriptions
                WHERE user = '%s'
                """ % (myuser[4])
            cursor.execute(q)
            mysubs = cursor.fetchall()
            if myuser[2] == 'None':
                about = None
            else:
                about = myuser[2]
            if myuser[1] == 'None':
                username = None
            else:
                username = myuser[1]
            if myuser[3] == 'None':
                name = None
            else:
                name = myuser[3]
            userinfo = {
                "about": about,
                "email": myuser[4],
                "followers": [x[0] for x in myfollowers],
                "following": [x[0] for x in myfollowing],
                "id": myuser[0],
                "isAnonymous": bool(myuser[5]),
                "name": name,
                "subscriptions": [x[0] for x in mysubs],
                "username": username
            }
            myfollowingList.append(userinfo)
        returnData = {"code": 0, "response": myfollowingList}
        return jsonify(returnData)
    else:
        returnData = {"code": 1, "response": "USER NOT FOUND"}
        return jsonify(returnData)


@app.route('/db/api/user/unfollow/', methods=['POST'])
def uesr_unfollow():
    db = MySQLdb.connect(host='localhost', user="db_api_user", passwd="passwd", db="db_func_test", charset='utf8')
    cursor = db.cursor()
    try:
        data = request.get_json()
        follower = data['follower']  # who
        followee = data['followee']  # whom
        if followee == follower:
            returnData = {"code": 3, "response": "WTF!"}
            return jsonify(returnData)
        q = """
            SELECT *
            FROM users
            WHERE email = '%s'
            """ % followee
        cursor.execute(q)
        myuserwhom = cursor.fetchone()
        if myuserwhom:
            q = """
                SELECT *
                FROM followers
                WHERE who_user = '%s' AND whom_user = '%s'
                """ % (follower, followee)
            cursor.execute(q)
            if cursor.fetchone():
                q = """
                    SELECT *
                    FROM users
                    WHERE email = '%s'
                    """ % follower
                cursor.execute(q)
                myuser = cursor.fetchone()
                if myuser:
                    q = """
                        DELETE
                        FROM followers
                        WHERE who_user = '%s' AND whom_user = '%s'
                        """ % (follower, followee)
                    cursor.execute(q)
                    db.commit()
                    q = """
                        SELECT who_user
                        FROM followers
                        WHERE whom_user = '%s'
                        """ % (myuser[4])
                    cursor.execute(q)
                    myfollowers = cursor.fetchall()
                    q = """
                        SELECT whom_user
                        FROM followers
                        WHERE who_user = '%s'
                        """ % (myuser[4])
                    cursor.execute(q)
                    myfollowing = cursor.fetchall()
                    q = """
                        SELECT thread_id
                        FROM subscriptions
                        WHERE user = '%s'
                        """ % (myuser[4])
                    cursor.execute(q)
                    mysubs = cursor.fetchall()
                    if myuser[2] == 'None':
                        about = None
                    else:
                        about = myuser[2]
                    if myuser[1] == 'None':
                        username = None
                    else:
                        username = myuser[1]
                    if myuser[3] == 'None':
                        name = None
                    else:
                        name = myuser[3]

                    userinfo = {
                        "about": about,
                        "email": myuser[4],
                        "followers": [x[0] for x in myfollowers],
                        "following": [x[0] for x in myfollowing],
                        "id": myuser[0],
                        "isAnonymous": bool(myuser[5]),
                        "name": name,
                        "subscriptions": [x[0] for x in mysubs],
                        "username": username
                    }
                    returnData = {"code": 0, "response": userinfo}
                    return jsonify(returnData)
                else:
                    returnData = {"code": 1, "response": "USER NOT FOUND"}

                    return jsonify(returnData)
            else:
                q = """
                    SELECT *
                    FROM users
                    WHERE email = '%s'
                    """ % follower
                cursor.execute(q)
                myuser = cursor.fetchone()
                q = """
                    SELECT who_user
                    FROM followers
                    WHERE whom_user = '%s'
                    """ % (myuser[4])
                cursor.execute(q)
                myfollowers = cursor.fetchall()
                q = """
                    SELECT whom_user
                    FROM followers
                    WHERE who_user = '%s'
                    """ % (myuser[4])
                cursor.execute(q)
                myfollowing = cursor.fetchall()
                q = """
                    SELECT thread_id
                    FROM subscriptions
                    WHERE user = '%s'
                    """ % (myuser[4])
                cursor.execute(q)
                mysubs = cursor.fetchall()
                if myuser[2] == 'None':
                    about = None
                else:
                    about = myuser[2]
                if myuser[1] == 'None':
                    username = None
                else:
                    username = myuser[1]
                if myuser[3] == 'None':
                    name = None
                else:
                    name = myuser[3]
                userinfo = {
                    "about": about,
                    "email": myuser[4],
                    "followers": [x[0] for x in myfollowers],
                    "following": [x[0] for x in myfollowing],
                    "id": myuser[0],
                    "isAnonymous": bool(myuser[5]),
                    "name": name,
                    "subscriptions": [x[0] for x in mysubs],
                    "username": username
                }
                returnData = {"code": 0, "response": userinfo}
                return jsonify(returnData)
        else:
            returnData = {"code": 1, "response": "USER NOT FOUND"}
            return jsonify(returnData)
    except KeyError:
        returnData = {"code": 2, "response": "invalid json format"}
        return jsonify(returnData)


# THREADS
@app.route('/db/api/thread/create/', methods=['POST'])
def thread_create():
    db = MySQLdb.connect(host='localhost', user="db_api_user", passwd="passwd", db="db_func_test", charset='utf8')
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
        q = """
            INSERT INTO threads (forum, title, isClosed, user, date, message,slug, isDeleted)
            VALUES('%s', '%s', %d, '%s', '%s', '%s', '%s', %d)""" % (
            forum, title, isClosed, user, date, message, slug, isDeleted)
        cursor.execute(q)
        db.commit()
        returnData = {
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
        return jsonify(returnData)
    except KeyError:
        returnData = {"code": 2, "response": "invalid json format"}
        return jsonify(returnData)


@app.route('/db/api/thread/details/', methods=['GET'])
def thread_details():
    db = MySQLdb.connect(host='localhost', user="db_api_user", passwd="passwd", db="db_func_test", charset='utf8')
    cursor = db.cursor()
    thread = request.args.get('thread', '')
    related = request.args.getlist('related')
    q = """
        SELECT *
        FROM threads
        WHERE thread_id = '%s'
        """ % thread
    if cursor.execute(q) == 0:
        returnData = {"code": 1, "response": "THREAD NOT FOUND"}
        return jsonify(returnData)
    mythread = cursor.fetchone()
    if 'user' in related:
        q = """
            SELECT *
            FROM users
            WHERE email = '%s'
            """ % (mythread[4])
        related.remove('user')
        cursor.execute(q)
        myuser = cursor.fetchone()
        if myuser[2] == 'None':
            about = None
        else:
            about = myuser[2]
        if myuser[1] == 'None':
            username = None
        else:
            username = myuser[1]
        if myuser[3] == 'None':
            name = None
        else:
            name = myuser[3]
        q = """
            SELECT who_user
            FROM followers
            WHERE whom_user = '%s'
            """ % (myuser[4])
        cursor.execute(q)
        myfollowers = cursor.fetchall()
        q = """
            SELECT whom_user
            FROM followers
            WHERE who_user = '%s'
            """ % (myuser[4])
        cursor.execute(q)
        myfollowing = cursor.fetchall()
        q = """
            SELECT thread_id
            FROM subscriptions
            WHERE user = '%s'
            """ % (myuser[4])
        cursor.execute(q)
        mysubs = cursor.fetchall()
        userinfo = {
            "about": about,
            "email": myuser[4],
            "followers": [x[0] for x in myfollowers],
            "following": [x[0] for x in myfollowing],
            "id": myuser[0],
            "isAnonymous": bool(myuser[5]),
            "name": name,
            "subscriptions": [x[0] for x in mysubs],
            "username": username
        }
    else:
        userinfo = mythread[4]
    if 'forum' in related:
        related.remove('forum')
        q = """
            SELECT *
            FROM forums
            WHERE short_name = '%s'
            """ % (mythread[1])
        cursor.execute(q)
        myforum = cursor.fetchone()
        foruminfo = {
            "id": myforum[3],
            "name": myforum[0],
            "short_name": myforum[1],
            "user": myforum[2]
        }
    else:
        foruminfo = mythread[1]
    if related:
        returnData = {"code": 3, "response": "invalid syntax"}
        return jsonify(returnData)
    returnData = {
        "code": 0,
        "response": {
            "date": mythread[5].strftime("%Y-%m-%d %H:%M:%S"),
            "dislikes": mythread[10],
            "forum": foruminfo,
            "id": mythread[0],
            "isClosed": bool(mythread[3]),
            "isDeleted": bool(mythread[8]),
            "likes": mythread[9],
            "message": mythread[6],
            "points": (mythread[9] - mythread[10]),
            "posts": mythread[11],
            "slug": mythread[7],
            "title": mythread[2],
            "user": userinfo
        }
    }
    return jsonify(returnData)


@app.route("/db/api/thread/list/", methods=["GET"])
def thread_list():
    db = MySQLdb.connect(host='localhost', user="db_api_user", passwd="passwd", db="db_func_test", charset='utf8')
    cursor = db.cursor()
    user = request.args.get('user', False)
    forum = request.args.get('forum', False)
    if user and forum:
        returnData = {"code": 3, "response": "bad syntax"}
        return jsonify(returnData)
    limit = request.args.get('limit', False)
    since = request.args.get('since', False)
    order = request.args.get('order', False)
    q = """
        SELECT *
        FROM threads
        WHERE
        """
    if user:
        q += "user =  '%s'" % user
    else:
        q += "forum = '%s' " % forum
    if since:
        q += " AND date >= '%s' " % since
    if order:
        q += " ORDER BY date %s " % order
    if limit:
        q += " LIMIT %d" % (int(limit))
    cursor.execute(q)
    threads = cursor.fetchall()
    returnthreads = []
    for mythread in threads:
        returnthreads.append({
            "date": mythread[5].strftime("%Y-%m-%d %H:%M:%S"),
            "dislikes": mythread[10],
            "forum": mythread[1],
            "id": mythread[0],
            "isClosed": bool(mythread[3]),
            "isDeleted": bool(mythread[8]),
            "likes": mythread[9],
            "message": mythread[6],
            "points": (mythread[9] - mythread[10]),
            "posts": mythread[11],
            "slug": mythread[7],
            "title": mythread[2],
            "user": mythread[4]
        })
    returnData = {"code": 0, "response": returnthreads}
    return jsonify(returnData)


@app.route('/db/api/thread/listPosts/', methods=['GET'])
def thread_listpost():
    db = MySQLdb.connect(host='localhost', user="db_api_user", passwd="passwd", db="db_func_test", charset='utf8')
    cursor = db.cursor()
    thread = request.args.get('thread', False)
    if not thread:
        returnData = {"code": 3, "response": "bad syntax"}
        return jsonify(returnData)
    limit = request.args.get('limit', False)
    since = request.args.get('since', False)
    order = request.args.get('order', 'desc')
    q = """
        SELECT *
        FROM threads
        WHERE thread_id = %d
        """ % (int(thread))
    cursor.execute(q)
    mythread = cursor.fetchone()
    if mythread:
        q = """
            SELECT *
            FROM posts
            WHERE thread = %d
            """ % (int(thread))
        if since:
            q += " AND date >= '%s' " % since
        q += " ORDER BY date %s " % order
        if limit:
            q += " LIMIT %d" % (int(limit))
        cursor.execute(q)
        myposts = cursor.fetchall()
        postlist = []
        for mypost in myposts:
            if mypost[1] == 0:
                parent = None
            else:
                parent = mypost[1]
            postlist.append({
                "date": mypost[6].strftime("%Y-%m-%d %H:%M:%S"),
                "dislikes": mypost[10],
                "forum": mypost[9],
                "id": mypost[0],
                "isApproved": bool(mypost[2]),
                "isDeleted": bool(mypost[5]),
                "isEdited": bool(mypost[3]),
                "isHighlighted": bool(mypost[13]),
                "isSpam": bool(mypost[4]),
                "likes": mypost[11],
                "message": mypost[7],
                "parent": parent,
                "points": (mypost[11] - mypost[10]),
                "thread": mypost[12],
                "user": mypost[8]
            })
        returnData = {"code": 0, "response": postlist}
        return jsonify(returnData)

    else:
        returnData = {"code": 1, "response": "THREAD NOT FOUND"}
        return jsonify(returnData)


@app.route('/db/api/thread/remove/', methods=['POST'])
def thread_remove():
    db = MySQLdb.connect(host='localhost', user="db_api_user", passwd="passwd", db="db_func_test", charset='utf8')
    cursor = db.cursor()
    try:
        data = request.get_json()
        thread = data['thread']
        q = """
            SELECT *
            FROM threads
            WHERE thread_id = %d
            """ % (int(thread))
        cursor.execute(q)
        mythread = cursor.fetchone()
        if mythread:
            if not mythread[8]:
                q = """
                    UPDATE threads set isDeleted = True
                    WHERE thread_id = %d
                    """ % (int(thread))
                cursor.execute(q)
                db.commit()
                q = """
                    UPDATE threads set posts = 0
                    WHERE thread_id = %d
                    """ % (int(thread))
                cursor.execute(q)
                db.commit()
                q = """
                    UPDATE posts set isDeleted = True
                    WHERE thread = %d
                    """ % (int(thread))
                cursor.execute(q)
                db.commit()
                returnData = {"code": 0, "response": {"thread": thread}}
                return jsonify(returnData)
            else:
                q = """
                    UPDATE threads set posts = 0
                    WHERE thread_id = %d
                    """ % (int(thread))
                cursor.execute(q)
                db.commit()
                q = """
                    UPDATE posts set isDeleted = True
                    WHERE thread = %d
                    """ % (int(thread))
                cursor.execute(q)
                db.commit()
                returnData = {
                    "code": 0,
                    "response": {
                        "date": mythread[5].strftime("%Y-%m-%d %H:%M:%S"),
                        "dislikes": mythread[10],
                        "forum": mythread[1],
                        "id": mythread[0],
                        "isClosed": bool(mythread[3]),
                        "isDeleted": bool(mythread[8]),
                        "likes": mythread[9],
                        "message": mythread[6],
                        "points": (mythread[9] - mythread[10]),
                        "posts": 0,
                        "slug": mythread[7],
                        "title": mythread[2],
                        "user": mythread[4]
                    }
                }
                return jsonify(returnData)
        else:
            returnData = {"code": 1, "response": "THREAD NOT FOUND"}
            return jsonify(returnData)
    except KeyError:
        returnData = {"code": 2, "response": "invalid json format"}
        return jsonify(returnData)


@app.route('/db/api/thread/restore/', methods=['POST'])
def thread_restore():
    db = MySQLdb.connect(host='localhost', user="db_api_user", passwd="passwd", db="db_func_test", charset='utf8')
    cursor = db.cursor()
    try:
        data = request.get_json()
        thread = data['thread']
        q = """
            SELECT *
            FROM threads
            WHERE thread_id = %d
            """ % (int(thread))
        cursor.execute(q)
        mythread = cursor.fetchone()
        if mythread:
            if mythread[8]:
                q = """
                    UPDATE threads set isDeleted = False
                    WHERE thread_id = %d
                    """ % (int(thread))
                cursor.execute(q)
                db.commit()
                q = """
                    UPDATE posts set isDeleted = False
                    WHERE thread = %d
                    """ % (int(thread))
                cursor.execute(q)
                db.commit()
                q = """
                    SELECT count(*)
                    FROM posts
                    WHERE  thread = %d
                    """ % (int(thread))
                cursor.execute(q)
                postcount = cursor.fetchone()
                q = """
                    UPDATE threads set posts = %d
                    WHERE thread_id = %d
                    """ % (int(postcount[0]), int(thread))
                cursor.execute(q)
                db.commit()
                returnData = {"code": 0, "response": {"thread": thread}}
                return jsonify(returnData)
            else:
                returnData = {
                    "code": 0,
                    "response": {
                        "date": mythread[5].strftime("%Y-%m-%d %H:%M:%S"),
                        "dislikes": mythread[10],
                        "forum": mythread[1],
                        "id": mythread[0],
                        "isClosed": bool(mythread[3]),
                        "isDeleted": bool(mythread[8]),
                        "likes": mythread[9],
                        "message": mythread[6],
                        "points": (mythread[9] - mythread[10]),
                        "posts": mythread[11],
                        "slug": mythread[7],
                        "title": mythread[2],
                        "user": mythread[4]
                    }
                }
                return jsonify(returnData)
        else:
            returnData = {"code": 1, "response": "THREAD NOT FOUND"}
            return jsonify(returnData)
    except KeyError:
        returnData = {"code": 2, "response": "invalid json format"}
        return jsonify(returnData)


@app.route('/db/api/thread/close/', methods=['POST'])
def thread_close():
    try:
        data = request.get_json()
        thread = data['thread']
        db = MySQLdb.connect(host='localhost', user="db_api_user", passwd="passwd", db="db_func_test", charset='utf8')
        cursor = db.cursor()
        q = """
            SELECT *
            FROM threads
            WHERE thread_id = %d
            """ % (int(thread))
        cursor.execute(q)
        mythread = cursor.fetchone()
        if mythread:
            if not mythread[3]:
                q = """
                    UPDATE threads set isClosed = True
                    WHERE thread_id = %d
                    """ % (int(thread))
                cursor.execute(q)
                db.commit()
                returnData = {"code": 0, "response": {"thread": thread}}
                return jsonify(returnData)
            else:
                returnData = {
                    "code": 0,
                    "response": {
                        "date": mythread[5].strftime("%Y-%m-%d %H:%M:%S"),
                        "dislikes": mythread[10],
                        "forum": mythread[1],
                        "id": mythread[0],
                        "isClosed": bool(mythread[3]),
                        "isDeleted": bool(mythread[8]),
                        "likes": mythread[9],
                        "message": mythread[6],
                        "points": (mythread[9] - mythread[10]),
                        "posts": mythread[11],
                        "slug": mythread[7],
                        "title": mythread[2],
                        "user": mythread[4]
                    }
                }
                return jsonify(returnData)
        else:
            returnData = {"code": 1, "response": "THREAD NOT FOUND"}
            return jsonify(returnData)
    except KeyError:
        returnData = {"code": 2, "response": "invalid json format"}
        return jsonify(returnData)


@app.route('/db/api/thread/open/', methods=['POST'])
def thread_open():
    db = MySQLdb.connect(host='localhost', user="db_api_user", passwd="passwd", db="db_func_test", charset='utf8')
    cursor = db.cursor()
    try:
        data = request.get_json()
        thread = data['thread']
        q = """
            SELECT *
            FROM threads
            WHERE thread_id = %d
            """ % (int(thread))
        cursor.execute(q)
        mythread = cursor.fetchone()
        if mythread:
            if mythread[3]:
                q = """
                    UPDATE threads set isClosed = False
                    WHERE thread_id = %d
                    """ % (int(thread))
                cursor.execute(q)
                db.commit()
                returnData = {"code": 0, "response": {"thread": thread}}
                return jsonify(returnData)
            else:
                returnData = {
                    "code": 0,
                    "response": {
                        "date": mythread[5].strftime("%Y-%m-%d %H:%M:%S"),
                        "dislikes": mythread[10],
                        "forum": mythread[1],
                        "id": mythread[0],
                        "isClosed": bool(mythread[3]),
                        "isDeleted": bool(mythread[8]),
                        "likes": mythread[9],
                        "message": mythread[6],
                        "points": (mythread[9] - mythread[10]),
                        "posts": mythread[11],
                        "slug": mythread[7],
                        "title": mythread[2],
                        "user": mythread[4]
                    }
                }
                return jsonify(returnData)
        else:
            returnData = {"code": 1, "response": "THREAD NOT FOUND"}
            return jsonify(returnData)
    except KeyError:
        returnData = {"code": 2, "response": "invalid json format"}
        return jsonify(returnData)


@app.route('/db/api/thread/update/', methods=['POST'])
def thread_update():
    db = MySQLdb.connect(host='localhost', user="db_api_user", passwd="passwd", db="db_func_test", charset='utf8')
    cursor = db.cursor()
    try:
        data = request.get_json()
        thread = data['thread']
        message = data['message']
        slug = data['slug']
        q = """
            SELECT *
            FROM threads
            WHERE thread_id = %d
            """ % (int(thread))
        cursor.execute(q)
        mythread = cursor.fetchone()
        if mythread:
            if (mythread[6] != message) or (mythread[7] != slug):
                q = """
                    UPDATE threads set message = '%s'
                    WHERE thread_id = %d
                    """ % (message, thread)
                cursor.execute(q)
                q = """
                    UPDATE threads set slug = '%s'
                    WHERE thread_id = %d
                    """ % (slug, thread)
                cursor.execute(q)
                db.commit()
                returnData = {
                    "code": 0,
                    "response": {
                        "date": mythread[5].strftime("%Y-%m-%d %H:%M:%S"),
                        "dislikes": mythread[10],
                        "forum": mythread[1],
                        "id": mythread[0],
                        "isClosed": bool(mythread[3]),
                        "isDeleted": bool(mythread[8]),
                        "likes": mythread[9],
                        "message": message,
                        "points": (mythread[9] - mythread[10]),
                        "posts": mythread[11],
                        "slug": slug,
                        "title": mythread[2],
                        "user": mythread[4]
                    }
                }
                return jsonify(returnData)
            else:
                returnData = {
                    "code": 0,
                    "response": {
                        "date": mythread[5].strftime("%Y-%m-%d %H:%M:%S"),
                        "dislikes": mythread[10],
                        "forum": mythread[1],
                        "id": mythread[0],
                        "isClosed": bool(mythread[3]),
                        "isDeleted": bool(mythread[8]),
                        "likes": mythread[9],
                        "message": mythread[6],
                        "points": (mythread[9] - mythread[10]),
                        "posts": mythread[11],
                        "slug": mythread[7],
                        "title": mythread[2],
                        "user": mythread[4]
                    }
                }
                return jsonify(returnData)
        else:
            returnData = {"code": 1, "response": "THREAD NOT FOUND"}
            return jsonify(returnData)
    except KeyError:
        returnData = {"code": 2, "response": "invalid json format"}
        return jsonify(returnData)


@app.route('/db/api/thread/vote/', methods=['POST'])
def thread_vote():
    db = MySQLdb.connect(host='localhost', user="db_api_user", passwd="passwd", db="db_func_test", charset='utf8')
    cursor = db.cursor()
    try:
        data = request.get_json()
        vote = data['vote']
        thread = data['thread']
        q = """
            SELECT *
            FROM threads
            WHERE thread_id = %d
            """ % (int(thread))
        cursor.execute(q)
        mythread = cursor.fetchone()
        if mythread:
            if vote == 1:
                q = """
                    UPDATE threads set likes = likes + 1
                    WHERE thread_id = %d
                    """ % (int(thread))
                mylikes = mythread[9] + 1
                mydislikes = mythread[10]
            elif vote == -1:
                q = """
                    UPDATE threads set dislikes = dislikes + 1
                    WHERE thread_id = %d
                    """ % (int(thread))
                mylikes = mythread[9]
                mydislikes = mythread[10] + 1
            else:
                returnData = {"code": 3, "response": "invalid syntax"}
                return jsonify(returnData)
            cursor.execute(q)
            db.commit()
            returnData = {
                "code": 0,
                "response": {
                    "date": mythread[5].strftime("%Y-%m-%d %H:%M:%S"),
                    "dislikes": mydislikes,
                    "forum": mythread[1],
                    "id": mythread[0],
                    "isClosed": bool(mythread[3]),
                    "isDeleted": bool(mythread[8]),
                    "likes": mylikes,
                    "message": mythread[6],
                    "points": (mylikes - mydislikes),
                    "posts": mythread[11],
                    "slug": mythread[7],
                    "title": mythread[2],
                    "user": mythread[4]
                }
            }
            return jsonify(returnData)
        else:
            returnData = {"code": 1, "response": "THREAD NOT FOUND"}
            return jsonify(returnData)
    except KeyError:
        returnData = {"code": 2, "response": "invalid json format"}
        return jsonify(returnData)


@app.route('/db/api/thread/subscribe/', methods=['POST'])
def thread_subscribe():
    db = MySQLdb.connect(host='localhost', user="db_api_user", passwd="passwd", db="db_func_test", charset='utf8')
    cursor = db.cursor()
    try:
        data = request.get_json()
        user = data['user']
        thread = data['thread']
        q = """
            SELECT *
            FROM threads
            WHERE thread_id = %d
            """ % (int(thread))
        cursor.execute(q)
        mythread = cursor.fetchone()
        q = """
            SELECT *
            FROM users
            WHERE email = '%s'
            """ % user
        cursor.execute(q)
        myuser = cursor.fetchone()
        if (not mythread) or (not myuser):
            returnData = {"code": 1, "response": "THREAD or USER NOT FOUND"}
            return jsonify(returnData)
        else:
            q = """
                SELECT *
                FROM subscriptions
                WHERE user = '%s' AND thread_id = %d
                """ % (user, int(thread))
            cursor.execute(q)
            mysub = cursor.fetchone()
            if not mysub:
                q = """
                    INSERT into subscriptions (user, thread_id)
                    VALUES ('%s', %d)
                    """ % (user, thread)
                cursor.execute(q)
                db.commit()
                returnData = {"code": 0, "response": {"thread": thread, "user": user}}
                return jsonify(returnData)
            else:
                returnData = {"code": 0, "response": {"thread": thread, "user": user}}
                return jsonify(returnData)
    except KeyError:
        returnData = {"code": 2, "response": "invalid json format"}
        return jsonify(returnData)


@app.route('/db/api/thread/unsubscribe/', methods=['POST'])
def thread_unsubscribe():
    db = MySQLdb.connect(host='localhost', user="db_api_user", passwd="passwd", db="db_func_test", charset='utf8')
    cursor = db.cursor()
    try:
        data = request.get_json()
        user = data['user']
        thread = data['thread']
        q = """
            SELECT *
            FROM threads
            WHERE thread_id = %d
            """ % (int(thread))
        cursor.execute(q)
        mythread = cursor.fetchone()
        q = """
            SELECT *
            FROM users
            WHERE email = '%s'
            """ % user
        cursor.execute(q)
        myuser = cursor.fetchone()
        if (not mythread) or (not myuser):
            returnData = {"code": 1, "response": "THREAD or USER NOT FOUND"}
            return jsonify(returnData)
        else:
            q = """
                SELECT *
                FROM subscriptions
                WHERE user = '%s' AND thread_id = %d
                """ % (user, int(thread))
            cursor.execute(q)
            mysub = cursor.fetchone()
            if mysub:
                q = """
                    DELETE
                    FROM subscriptions
                    WHERE user = '%s' AND thread_id = %d
                    """ % (user, thread)
                cursor.execute(q)
                db.commit()
                returnData = {"code": 0, "response": {"thread": thread, "user": user}}
                return jsonify(returnData)
            else:
                returnData = {"code": 0, "response": {"thread": thread, "user": user}}
                return jsonify(returnData)
    except KeyError:
        returnData = {"code": 2, "response": "invalid json format"}
        return jsonify(returnData)


# POST


@app.route('/db/api/post/create/', methods=['POST'])
def post_create():
    db = MySQLdb.connect(host='localhost', user="db_api_user", passwd="passwd", db="db_func_test", charset='utf8')
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
        q = """
            INSERT INTO posts (parent, isApproved, isEdited, isSpam, isDeleted, date, message, user, forum,
         thread, isHighlited)
            VALUES (%d, %d, %d, %d, %d, '%s', '%s', '%s', '%s', %d, %d)
            """ % (parent, isApproved, isEdit, isSpam,
                   isDeleted, date, message, user, forum, thread, isHighlighted)
        cursor.execute(q)
        if parent == 0:
            parent = None
        returnData = {
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
        q = """
            UPDATE threads set posts = posts + 1
            WHERE thread_id = %d
            """ % thread
        cursor.execute(q)
        db.commit()
        return jsonify(returnData)
    except KeyError:
        returnData = {"code": 2, "response": "invalid json format"}
        return jsonify(returnData)


@app.route('/db/api/post/details/', methods=['GET'])
def post_details():
    db = MySQLdb.connect(host='localhost', user="db_api_user", passwd="passwd", db="db_func_test", charset='utf8')
    cursor = db.cursor()
    post = request.args.get('post', '')
    related = request.args.getlist('related')
    q = """
        SELECT * FROM posts
        WHERE post_id = '%s'
        """ % post
    if cursor.execute(q) == 0:
        returnData = {"code": 1, "response": "POST NOT FOUND"}
        return jsonify(returnData)
    mypost = cursor.fetchone()
    if 'user' in related:
        q = """
            SELECT *
            FROM users
            WHERE email = '%s'
            """ % (mypost[8])
        cursor.execute(q)
        myuser = cursor.fetchone()
        if myuser[2] == 'None':
            about = None
        else:
            about = myuser[2]
        if myuser[1] == 'None':
            username = None
        else:
            username = myuser[1]
        if myuser[3] == 'None':
            name = None
        else:
            name = myuser[3]
        q = """
            SELECT who_user
            FROM followers
            WHERE whom_user = '%s'
            """ % (myuser[4])
        cursor.execute(q)
        myfollowers = cursor.fetchall()
        q = """
            SELECT whom_user
            FROM followers
            WHERE who_user = '%s'
            """ % (myuser[4])
        cursor.execute(q)
        myfollowing = cursor.fetchall()
        q = """
            SELECT thread_id
            FROM subscriptions
            WHERE user = '%s'
            """ % (myuser[4])
        cursor.execute(q)
        mysubs = cursor.fetchall()
        userinfo = {
            "about": about,
            "email": myuser[4],
            "followers": [x[0] for x in myfollowers],
            "following": [x[0] for x in myfollowing],
            "id": myuser[0],
            "isAnonymous": bool(myuser[5]),
            "name": name,
            "subscriptions": [x[0] for x in mysubs],
            "username": username
        }
    else:
        userinfo = mypost[8]
    if 'forum' in related:
        q = """
            SELECT *
            FROM forums
            WHERE short_name = '%s'
            """ % (mypost[9])
        cursor.execute(q)
        myforum = cursor.fetchone()
        foruminfo = {
            "id": myforum[3],
            "name": myforum[0],
            "short_name": myforum[1],
            "user": myforum[2]
        }
    else:
        foruminfo = mypost[9]
    if 'thread' in related:
        q = """
            SELECT *
            FROM threads
            WHERE thread_id = '%s'
            """ % (mypost[12])
        cursor.execute(q)
        mythread = cursor.fetchone()
        threadinfo = {
            "date": mythread[5].strftime("%Y-%m-%d %H:%M:%S"),
            "dislikes": mythread[10],
            "forum": mythread[1],
            "id": mythread[0],
            "isClosed": bool(mythread[3]),
            "isDeleted": bool(mythread[8]),
            "likes": mythread[9],
            "message": mythread[6],
            "points": (mythread[9] - mythread[10]),
            "posts": mythread[11],
            "slug": mythread[7],
            "title": mythread[2],
            "user": mythread[4]
        }
    else:
        threadinfo = mypost[12]
    if mypost[1] == 0:
        parent = None
    else:
        parent = mypost[1]

    returnData = {
        "code": 0,
        "response": {
            "date": mypost[6].strftime("%Y-%m-%d %H:%M:%S"),
            "dislikes": mypost[10],
            "forum": foruminfo,
            "id": mypost[0],
            "isApproved": bool(mypost[2]),
            "isDeleted": bool(mypost[5]),
            "isEdited": bool(mypost[3]),
            "isHighlighted": bool(mypost[13]),
            "isSpam": bool(mypost[4]),
            "likes": mypost[11],
            "message": mypost[7],
            "parent": parent,
            "points": (mypost[11] - mypost[10]),
            "thread": threadinfo,
            "user": userinfo
        }
    }
    return jsonify(returnData)


@app.route('/db/api/post/list/', methods=['GET'])
def post_list():
    db = MySQLdb.connect(host='localhost', user="db_api_user", passwd="passwd", db="db_func_test", charset='utf8')
    cursor = db.cursor()
    thread = request.args.get('thread', False)
    forum = request.args.get('forum', False)
    if thread and forum:
        returnData = {"code": 3, "response": "bad syntax"}
        return jsonify(returnData)
    limit = request.args.get('limit', False)
    since = request.args.get('since', False)
    order = request.args.get('order', False)
    q = """
        SELECT *
        FROM posts
        WHERE
        """
    if thread:
        q += "thread =  %d" % (int(thread))
    else:
        q += "forum = '%s' " % forum
    if since:
        q += " AND date >= '%s' " % since
    if order:
        q += " ORDER BY date %s " % order
    if limit:
        q += " LIMIT %d" % (int(limit))
    cursor.execute(q)
    myposts = cursor.fetchall()
    returnposts = []
    for mypost in myposts:
        if mypost[1] == 0:
            parent = None
        else:
            parent = mypost[1]
        returnposts.append({
            "date": mypost[6].strftime("%Y-%m-%d %H:%M:%S"),
            "dislikes": mypost[10],
            "forum": mypost[9],
            "id": mypost[0],
            "isApproved": bool(mypost[2]),
            "isDeleted": bool(mypost[5]),
            "isEdited": bool(mypost[3]),
            "isHighlighted": bool(mypost[13]),
            "isSpam": bool(mypost[4]),
            "likes": mypost[11],
            "message": mypost[7],
            "parent": parent,
            "points": (mypost[11] - mypost[10]),
            "thread": mypost[12],
            "user": mypost[8]
        })
    returnData = {"code": 0, "response": returnposts}
    return jsonify(returnData)


@app.route('/db/api/post/remove/', methods=['POST'])
def post_remove():
    db = MySQLdb.connect(host='localhost', user="db_api_user", passwd="passwd", db="db_func_test", charset='utf8')
    cursor = db.cursor()
    try:
        data = request.get_json()
        post = data['post']
    except KeyError:
        returnData = {"code": 2, "response": "invalid json format"}
        return jsonify(returnData)
    q = """
        SELECT *
        FROM posts
        WHERE post_id = %d
        """ % (int(post))
    cursor.execute(q)
    mypost = cursor.fetchone()
    if mypost:
        if mypost[5]:
            if mypost[1] == 0:
                parent = None
            else:
                parent = mypost[1]
            returnpost = {
                "date": mypost[6].strftime("%Y-%m-%d %H:%M:%S"),
                "dislikes": mypost[10],
                "forum": mypost[9],
                "id": mypost[0],
                "isApproved": bool(mypost[2]),
                "isDeleted": bool(mypost[5]),
                "isEdited": bool(mypost[3]),
                "isHighlighted": bool(mypost[13]),
                "isSpam": bool(mypost[4]),
                "likes": mypost[11],
                "message": mypost[7],
                "parent": parent,
                "points": (mypost[11] - mypost[10]),
                "thread": mypost[12],
                "user": mypost[8]
            }
            returnData = {"code": 0, "response": returnpost}
            return jsonify(returnData)
        else:
            q = """
                UPDATE posts set isDeleted = True
                WHERE post_id = %d
                """ % post
            cursor.execute(q)
            db.commit()
            q = """
                UPDATE threads set posts = posts - 1
                WHERE thread_id = %d
                """ % (mypost[12])
            cursor.execute(q)
            db.commit()
            returnData = {"code": 0, "response": {"post": post}}
            return jsonify(returnData)
    else:
        returnData = {"code": 1, "response": "FORUM NOT FOUND"}
        return jsonify(returnData)


@app.route('/db/api/post/restore/', methods=['POST'])
def post_restore():
    db = MySQLdb.connect(host='localhost', user="db_api_user", passwd="passwd", db="db_func_test", charset='utf8')
    cursor = db.cursor()
    try:
        data = request.get_json()
        post = data['post']
    except KeyError:
        returnData = {"code": 2, "response": "invalid json format"}
        return jsonify(returnData)
    q = """
        SELECT *
        FROM posts
        WHERE post_id = %d
        """ % (int(post))
    cursor.execute(q)
    mypost = cursor.fetchone()
    if mypost:
        if not mypost[5]:
            if mypost[1] == 0:
                parent = None
            else:
                parent = mypost[1]
            returnpost = {
                "date": mypost[6].strftime("%Y-%m-%d %H:%M:%S"),
                "dislikes": mypost[10],
                "forum": mypost[9],
                "id": mypost[0],
                "isApproved": bool(mypost[2]),
                "isDeleted": bool(mypost[5]),
                "isEdited": bool(mypost[3]),
                "isHighlighted": bool(mypost[13]),
                "isSpam": bool(mypost[4]),
                "likes": mypost[11],
                "message": mypost[7],
                "parent": parent,
                "points": (mypost[11] - mypost[10]),
                "thread": mypost[12],
                "user": mypost[8]}
            returnData = {"code": 0, "response": returnpost}
            return jsonify(returnData)
        else:
            q = """
                UPDATE posts set isDeleted = False
                WHERE post_id = %d
                """ % post
            cursor.execute(q)
            db.commit()
            q = """
                UPDATE threads set posts = posts + 1
                WHERE thread_id = %d
                """ % (mypost[12])
            cursor.execute(q)
            db.commit()
            returnData = {"code": 0, "response": {"post": post}}
            return jsonify(returnData)
    else:
        returnData = {"code": 1, "response": "POST NOT FOUND"}
        return jsonify(returnData)


@app.route('/db/api/post/update/', methods=['POST'])
def post_update():
    db = MySQLdb.connect(host='localhost', user="db_api_user", passwd="passwd", db="db_func_test", charset='utf8')
    cursor = db.cursor()
    try:
        data = request.get_json()
        post = data['post']
        message = data['message']
        q = """
            SELECT *
            FROM posts
            WHERE post_id = %d
            """ % (int(post))
        cursor.execute(q)
        mypost = cursor.fetchone()
        if mypost:
            if not mypost[7] == message:
                q = """
                    UPDATE posts set message = '%s'
                    WHERE post_id = %d
                    """ % (message, post)
                cursor.execute(q)
                db.commit()
                q = """
                    UPDATE posts set isEdited = True
                    WHERE post_id = %d
                    """ % post
                cursor.execute(q)
                db.commit()
                if mypost[1] == 0:
                    parent = None
                else:
                    parent = mypost[1]
                returnpost = {
                    "date": mypost[6].strftime("%Y-%m-%d %H:%M:%S"),
                    "dislikes": mypost[10],
                    "forum": mypost[9],
                    "id": mypost[0],
                    "isApproved": bool(mypost[2]),
                    "isDeleted": bool(mypost[5]),
                    "isEdited": True,
                    "isHighlighted": bool(mypost[13]),
                    "isSpam": bool(mypost[4]),
                    "likes": mypost[11],
                    "message": message,
                    "parent": parent,
                    "points": (mypost[11] - mypost[10]),
                    "thread": mypost[12],
                    "user": mypost[8]
                }
                returnData = {"code": 0, "response": returnpost}
                return jsonify(returnData)
            else:
                if mypost[1] == 0:
                    parent = None
                else:
                    parent = mypost[1]
                returnpost = {
                    "date": mypost[6].strftime("%Y-%m-%d %H:%M:%S"),
                    "dislikes": mypost[10],
                    "forum": mypost[9],
                    "id": mypost[0],
                    "isApproved": bool(mypost[2]),
                    "isDeleted": bool(mypost[5]),
                    "isEdited": bool(mypost[3]),
                    "isHighlighted": bool(mypost[13]),
                    "isSpam": bool(mypost[4]),
                    "likes": mypost[11],
                    "message": mypost[7],
                    "parent": parent,
                    "points": (mypost[11] - mypost[10]),
                    "thread": mypost[12],
                    "user": mypost[8]
                }
                returnData = {"code": 0, "response": returnpost}
                return jsonify(returnData)
        else:
            returnData = {"code": 1, "response": "POST NOT FOUND"}
            return jsonify(returnData)
    except KeyError:
        returnData = {"code": 2, "response": "invalid json format"}
        return jsonify(returnData)


@app.route('/db/api/post/vote/', methods=['POST'])
def post_vote():
    db = MySQLdb.connect(host='localhost', user="db_api_user", passwd="passwd", db="db_func_test", charset='utf8')
    cursor = db.cursor()
    try:
        data = request.get_json()
        vote = data['vote']
        post = data['post']
        q = """
            SELECT *
            FROM posts
            WHERE post_id = %d
            """ % (int(post))
        cursor.execute(q)
        mypost = cursor.fetchone()
        if mypost:
            if vote == 1:
                q = """
                    UPDATE posts set likes = likes + 1
                    WHERE post_id = %d
                    """ % (int(post))
                mylikes = mypost[11] + 1
                mydislikes = mypost[10]
            elif vote == -1:
                q = """
                    UPDATE posts set dislikes = dislikes + 1
                    WHERE post_id = %d
                    """ % (int(post))
                mylikes = mypost[11]
                mydislikes = mypost[10] + 1
            else:
                returnData = {"code": 3, "response": "invalid syntax"}
                return jsonify(returnData)
            cursor.execute(q)
            db.commit()
            if mypost[1] == 0:
                parent = None
            else:
                parent = mypost[1]
            returnpost = {
                "date": mypost[6].strftime("%Y-%m-%d %H:%M:%S"),
                "dislikes": mydislikes,
                "forum": mypost[9],
                "id": mypost[0],
                "isApproved": bool(mypost[2]),
                "isDeleted": bool(mypost[5]),
                "isEdited": bool(mypost[3]),
                "isHighlighted": bool(mypost[13]),
                "isSpam": bool(mypost[4]),
                "likes": mylikes,
                "message": mypost[7],
                "parent": parent,
                "points": (mylikes - mydislikes),
                "thread": mypost[12],
                "user": mypost[8]
            }
            returnData = {"code": 0, "response": returnpost}
            return jsonify(returnData)
        else:
            returnData = {"code": 1, "response": "POST NOT FOUND"}
            return jsonify(returnData)
    except KeyError:
        returnData = {"code": 2, "response": "invalid json format"}
        return jsonify(returnData)


if __name__ == '__main__':
    app.run()
