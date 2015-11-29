# -*- coding: utf-8 -*-
from flask import Flask
from _mysql_exceptions import IntegrityError
from func import *

app = Flask(__name__)


# API

# GENERAL


@app.route('/db/api/clear/', methods=['POST'])
def clear():
    """Truncate all tables"""
    # open connection
    db = db_connect()
    cursor = db.cursor()

    # clear executing
    clear_execute(cursor)

    # close connection
    db.commit()
    db.close()
    code = 0
    return_data = {"code": code, "response": "OK"}
    return jsonify(return_data)


@app.route('/db/api/status/', methods=['GET'])
def status():
    """Show status info: maps table name to number of rows in that table"""
    db = db_connect()
    cursor = db.cursor()
    return_data = status_execute(cursor)
    return return_data


# FORUMS


@app.route('/db/api/forum/create/', methods=['POST'])
def forum_create():
    """Create new forum"""
    try:
        # open connection
        db = db_connect()
        cursor = db.cursor()
        # get data
        data = request.get_json()
        # execution
        forum_create_execute(cursor, data)
        code = 0
        return_data = {"code": code, "response": {'id': cursor.lastrowid,
                                                  "name": data['name'],
                                                  "short_name": data['short_name'],
                                                  "user": data['user']}}
        # close db
        db.commit()
        db.close()
        return jsonify(return_data)
    except IntegrityError, e:
        data = request.get_json()
        if e[0] == 1062:
            return jsonify(integrity_err_action(e, data))
    except KeyError:
        return_data = {"code": 2, "response": "invalid json format"}
        return jsonify(return_data)


@app.route('/db/api/forum/details/', methods=['GET'])
def forum_details():
    """Get forum details"""
    # open connection
    db = db_connect()
    cursor = db.cursor()
    # get data
    forum = request.args.get('forum', '')
    related = request.args.getlist('related')
    # executing
    query_stmt = (
                     "SELECT * "
                     "FROM forums "
                     "WHERE short_name = '%s'"
                 ) % forum
    if cursor.execute(query_stmt) == 0:
        code = 1
        err_msg = "not found"
        return_data = {"code": code, "response": err_msg}
        return jsonify(return_data)
    # fetching a single row from table on current cursor position
    forum_data = cursor.fetchone()
    forum_name_field = forum_data[0]
    forum_shortname_field = forum_data[1]
    forum_email_field = forum_data[2]
    forum_id_field = forum_data[3]
    if 'user' in related:
        query_stmt = (
                         "SELECT * "
                         "FROM users "
                         "WHERE email = '%s'"
                     ) % forum_email_field
        cursor.execute(query_stmt)
        user_data = cursor.fetchone()
        # data
        if user_data[1] == 'None':
            user_username_field = None
        else:
            user_username_field = user_data[1]
        if user_data[2] == 'None':
            user_about_field = None
        else:
            user_about_field = user_data[2]
        if user_data[3] == 'None':
            user_name_field = None
        else:
            user_name_field = user_data[3]
        user_id_field = user_data[0]  # id
        user_email_field = user_data[4]  # email
        user_isAnonymous_field = user_data[5]  # isAnonymous
        query_stmt = (
                         "SELECT who_user "
                         "FROM followers "
                         "WHERE whom_user = '%s'"
                     ) % (user_data[4])
        #
        cursor.execute(query_stmt)
        # fetching all followers rows from current cursor position
        followers_data = cursor.fetchall()
        query_stmt = (
                         "SELECT whom_user "
                         "FROM followers "
                         "WHERE who_user = '%s'"
                     ) % user_email_field
        #
        cursor.execute(query_stmt)
        following_data = cursor.fetchall()
        query_stmt = (
                         "SELECT thread_id "
                         "FROM subscriptions "
                         "WHERE user = '%s'"
                     ) % user_email_field
        cursor.execute(query_stmt)
        subscriptions_data = cursor.fetchall()
        user_about = {"about": user_about_field, "email": user_email_field, "followers": [x[0] for x in followers_data],
                      "following": [x[0] for x in following_data],
                      "id": user_id_field, "isAnonymous": bool(user_isAnonymous_field),
                      "name": user_name_field, "subscriptions": [x[0] for x in subscriptions_data],
                      "username": user_username_field}
    else:
        user_about = forum_data[2]

    code = 0
    return_data = {"code": code,
                   "response": {"id": forum_id_field, "name": forum_name_field, "short_name": forum_shortname_field,
                                "user": user_about}}
    return jsonify(return_data)


@app.route('/db/api/forum/listPosts/', methods=['GET'])
def forum_listPosts():
    """Get posts from this forum"""
    db = db_connect()
    cursor = db.cursor()
    # fetching required and optional args. forum, related, order, limit, since, data
    args = fetch_listpost_forum_args()
    query_stmt = (
                     "SELECT * "
                     "FROM forums "
                     "WHERE short_name = '%s'"
                 ) % args['forum']
    # if not found
    if cursor.execute(query_stmt) == 0:
        code = 1
        err_msg = "forum not found"
        return_data = {"code": code, "response": err_msg}
        return jsonify(return_data)
    forum_data = cursor.fetchone()
    query_stmt = (
                     "SELECT * "
                     "FROM posts "
                     "WHERE forum = '%s' "
                 ) % args['forum']
    if args['since']:
        query_stmt += " AND date >= '%s' " % args['since']
    query_stmt += " ORDER BY  date %s " % args['order']
    if args['limit']:
        query_stmt += " LIMIT %d" % (int(args['limit']))
    cursor.execute(query_stmt)
    posts_data = cursor.fetchall()
    if 'forum' in args['related']:
        args['related'].remove('forum')
        forum_name_field = forum_data[0]
        forum_shortname_field = forum_data[1]
        forum_user_field = forum_data[2]
        forum_id_field = forum_data[3]
        forum_info = {"id": forum_id_field, "name": forum_name_field, "short_name": forum_shortname_field,
                      "user": forum_user_field}
    else:
        forum_info = args['forum']
    posts_list = []
    for post in posts_data:
        if 'user' in args['related']:
            query_stmt = (
                             "SELECT * "
                             "FROM users "
                             "WHERE email = '%s'"
                         ) % (post[8])
            cursor.execute(query_stmt)
            user_data = cursor.fetchone()
            if user_data[1] == 'None':
                username = None
            else:
                username = user_data[1]
            if user_data[2] == 'None':
                about = None
            else:
                about = user_data[2]
            if user_data[3] == 'None':
                name = None
            else:
                name = user_data[3]
            query_stmt = (
                             "SELECT who_user "
                             "FROM followers "
                             "WHERE whom_user = '%s'"
                         ) % (user_data[4])
            cursor.execute(query_stmt)
            followers_data = cursor.fetchall()
            query_stmt = (
                             "SELECT whom_user "
                             "FROM followers "
                             "WHERE who_user = '%s'"
                         ) % (user_data[4])
            cursor.execute(query_stmt)
            following_data = cursor.fetchall()
            query_stmt = (
                             "SELECT thread_id "
                             "FROM subscriptions "
                             "WHERE user = '%s'"
                         ) % (user_data[4])
            cursor.execute(query_stmt)
            subscriptions_data = cursor.fetchall()
            user_info = {"about": about, "email": user_data[4], "followers": [x[0] for x in followers_data],
                         "following": [x[0] for x in following_data],
                         "id": user_data[0], "isAnonymous": bool(user_data[5]),
                         "name": name, "subscriptions": [x[0] for x in subscriptions_data],
                         "username": username}
        else:
            user_info = post[8]

        if 'thread' in args['related']:
            query_stmt = (
                             "SELECT * "
                             "FROM threads "
                             "WHERE thread_id = '%s'"
                         ) % (post[12])
            cursor.execute(query_stmt)
            thread_data = cursor.fetchone()
            thread_info = {"date": thread_data[5].strftime("%Y-%m-%d %H:%M:%S"), "dislikes": thread_data[10],
                           "forum": thread_data[1], "id": thread_data[0], "isClosed": bool(thread_data[3]),
                           "isDeleted": bool(thread_data[8]),
                           "likes": thread_data[9], "message": thread_data[6],
                           "points": (thread_data[9] - thread_data[10]),
                           "posts": thread_data[11], "slug": thread_data[7], "title": thread_data[2],
                           "user": thread_data[4]}
        else:
            thread_info = post[12]
        if post[1] == 0:
            parent = None
        else:
            parent = post[1]

        return_data = {"date": post[6].strftime("%Y-%m-%d %H:%M:%S"), "dislikes": post[10],
                       "forum": forum_info, "id": post[0], "isApproved": bool(post[2]),
                       "isDeleted": bool(post[5]), "isEdited": bool(post[3]),
                       "isHighlighted": bool(post[13]), "isSpam": bool(post[4]),
                       "likes": post[11], "message": post[7], "parent": parent,
                       "points": (post[11] - post[10]), "thread": thread_info, "user": user_info}
        posts_list.append(return_data)
    return jsonify({"code": 0, "response": posts_list})


@app.route('/db/api/forum/listThreads/', methods=['GET'])
def forum_listThreads():
    forum = request.args.get('forum')
    if not forum:
        return_data = {"code": 3, "response": "bad syntax"}
        return jsonify(return_data)
    related = request.args.getlist('related')
    order = request.args.get('order', 'desc')
    limit = request.args.get('limit', False)
    since = request.args.get('since', False)
    db = db_connect()
    cursor = db.cursor()
    query_str = "SELECT * FROM forums WHERE short_name = '%s'" % (forum)
    if cursor.execute(query_str) == 0:
        return_data = {"code": 1, "response": "FORUM NOT FOUND"}
        return jsonify(return_data)
    myforum = cursor.fetchone()
    query_str = "SELECT * FROM threads WHERE forum = '%s' " % (forum)
    if since:
        query_str += " AND date >= '%s' " % (since)
    query_str += " ORDER BY  date %s " % (order)
    if limit:
        query_str += " limit %d" % (int(limit))
    cursor.execute(query_str)
    threads_data = cursor.fetchall()
    if 'forum' in related:
        forum_info = {"id": myforum[3], "name": myforum[0], "short_name": myforum[1],
                     "user": myforum[2]}
    else:
        forum_info = forum
    threads_list = []
    for thread in threads_data:
        if 'user' in related:
            query_str = "SELECT * FROM users WHERE email = '%s'" % (thread[4])
            cursor.execute(query_str)
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
            query_str = "SELECT who_user FROM followers WHERE whom_user = '%s'" % (user_data[4])
            cursor.execute(query_str)
            myfollowers = cursor.fetchall()
            query_str = "SELECT whom_user FROM followers WHERE who_user = '%s'" % (user_data[4])
            cursor.execute(query_str)
            myfollowing = cursor.fetchall()
            query_str = "SELECT thread_id FROM subscriptions WHERE user = '%s'" % (user_data[4])
            cursor.execute(query_str)
            mysubs = cursor.fetchall()
            userinfo = {"about": about, "email": user_data[4], "followers": [x[0] for x in myfollowers],
                        "following": [x[0] for x in myfollowing],
                        "id": user_data[0], "isAnonymous": bool(user_data[5]),
                        "name": name, "subscriptions": [x[0] for x in mysubs],
                        "username": username}
        else:
            userinfo = thread[4]

        return_data = {"date": thread[5].strftime("%Y-%m-%d %H:%M:%S"), "dislikes": thread[10],
                       "forum": forum_info, "id": thread[0], "isClosed": bool(thread[3]),
                       "isDeleted": bool(thread[8]),
                       "likes": thread[9], "message": thread[6], "points": (thread[9] - thread[10]),
                       "posts": thread[11], "slug": thread[7], "title": thread[2], "user": userinfo}
        threads_list.append(return_data)
    return jsonify({"code": 0, "response": threads_list})


@app.route('/db/api/forum/listUsers/', methods=['GET'])
def forum_listUsers():
    forum = request.args.get('forum')
    if not forum:
        return_data = {"code": 3, "response": "bad syntax"}
        return jsonify(return_data)
    order = request.args.get('order', 'desc')
    limit = request.args.get('limit', False)
    since = request.args.get('since_id', False)
    db = db_connect()
    cursor = db.cursor()
    query_str = "SELECT * FROM forums WHERE short_name = '%s'" % (forum)
    if cursor.execute(query_str) == 0:
        return_data = {"code": 1, "response": "FORUM NOT FOUND"}
        return jsonify(return_data)
    query_str = "SELECT  distinct email ,user_id, username, about,name, isAnonymous, IF(name ='None', 0, 1) as qwer   FROM posts join users " \
                "on posts.user = users.email WHERE forum = '%s' " % (forum)
    if since:
        query_str += " AND user_id >= %d " % (int(since))
    query_str += " ORDER BY qwer %s, name %s " % (order, order)
    if limit:
        query_str += " limit %d" % (int(limit))
    cursor.execute(query_str)
    myusers = cursor.fetchall()
    ListUsers = []
    for myuser in myusers:
        if myuser[3] == 'None':
            about = None
        else:
            about = myuser[3]
        if myuser[2] == 'None':
            username = None
        else:
            username = myuser[2]
        if myuser[4] == 'None':
            name = None
        else:
            name = myuser[4]
        query_str = "SELECT who_user FROM followers WHERE whom_user = '%s'" % (myuser[0])
        cursor.execute(query_str)
        myfollowers = cursor.fetchall()
        query_str = "SELECT whom_user FROM followers WHERE who_user = '%s'" % (myuser[0])
        cursor.execute(query_str)
        myfollowing = cursor.fetchall()
        query_str = "SELECT thread_id FROM subscriptions WHERE user = '%s'" % (myuser[0])
        cursor.execute(query_str)
        mysubs = cursor.fetchall()
        userinfo = {"about": about, "email": myuser[0], "followers": [x[0] for x in myfollowers],
                    "following": [x[0] for x in myfollowing],
                    "id": myuser[1], "isAnonymous": bool(myuser[5]),
                    "name": name, "subscriptions": [x[0] for x in mysubs],
                    "username": username}
        ListUsers.append(userinfo)
    return jsonify({"code": 0, "response": ListUsers})


# USERS
@app.route('/db/api/user/create/', methods=['POST'])
def user_create():
    try:
        data = request.get_json()
        about = data['about']
        email = data['email']
        username = data['username']
        name = data['name']
        isAnonymous = data.get('isAnonymous', False)
        query_str = """INSERT INTO users (username, about, name, email, isAnonymous) values
        ('%s','%s','%s','%s',%d)""" % (username, about, name, email, isAnonymous)
        db = db_connect()
        cursor = db.cursor()
        cursor.execute(query_str)
        return_data = {"code": 0, "response": {"about": about, "email": email, "id": cursor.lastrowid,
                                               "isAnonymous": isAnonymous, "name": name, "username": username}}
        db.commit()
        db.close()
        return jsonify(return_data)
    except IntegrityError, e:
        if e[0] == 1062:
            return_data = {"code": 5, "response": "duplicate user"}
            return jsonify(return_data)
    except KeyError:
        return_data = {"code": 2, "response": "invalid json format"}
        return jsonify(return_data)


@app.route('/db/api/user/details/', methods=['GET'])
def user_details():
    user = request.args.get('user', '')
    db = db_connect()
    cursor = db.cursor()
    query_str = "SELECT * FROM users WHERE email = '%s'" % (user)
    if cursor.execute(query_str) == 0:
        return_data = {"code": 1, "response": "USER NOT FOUND"}
        return jsonify(return_data)
    else:
        myuser = cursor.fetchone()
        query_str = "SELECT who_user FROM followers WHERE whom_user = '%s'" % (myuser[4])
        cursor.execute(query_str)
        myfollowers = cursor.fetchall()
        query_str = "SELECT whom_user FROM followers WHERE who_user = '%s'" % (myuser[4])
        cursor.execute(query_str)
        myfollowing = cursor.fetchall()
        query_str = "SELECT thread_id FROM subscriptions WHERE user = '%s'" % (myuser[4])
        cursor.execute(query_str)
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

        userinfo = {"about": about, "email": myuser[4], "followers": [x[0] for x in myfollowers],
                    "following": [x[0] for x in myfollowing],
                    "id": myuser[0], "isAnonymous": bool(myuser[5]),
                    "name": name, "subscriptions": [x[0] for x in mysubs],
                    "username": username}
        return_data = {"code": 0, "response": userinfo}
        return jsonify(return_data)


@app.route('/db/api/user/listPosts/', methods=['GET'])
def user_listPosts():
    user = request.args.get('user', False)
    if not user:
        return_data = {"code": 3, "response": "bad syntax"}
        return jsonify(return_data)
    limit = request.args.get('limit', False)
    since = request.args.get('since', False)
    order = request.args.get('order', 'desc')
    db = db_connect()
    cursor = db.cursor()
    query_str = "SELECT * FROM users WHERE email = '%s'" % (user)
    cursor.execute(query_str)
    myuser = cursor.fetchone()
    if myuser:
        query_str = "SELECT * FROM posts WHERE user = '%s'" % (user)
        if since:
            query_str += " AND date >= '%s' " % (since)
        query_str += " ORDER BY date %s " % (order)
        if limit:
            query_str += " limit %d" % (int(limit))
        cursor.execute(query_str)
        myposts = cursor.fetchall()
        postlist = []

        for mypost in myposts:
            if mypost[1] == 0:
                parent = None
            else:
                parent = mypost[1]
            postlist.append({"date": mypost[6].strftime("%Y-%m-%d %H:%M:%S"), "dislikes": mypost[10],
                             "forum": mypost[9], "id": mypost[0], "isApproved": bool(mypost[2]),
                             "isDeleted": bool(mypost[5]), "isEdited": bool(mypost[3]),
                             "isHighlighted": bool(mypost[13]), "isSpam": bool(mypost[4]),
                             "likes": mypost[11], "message": mypost[7], "parent": parent,
                             "points": (mypost[11] - mypost[10]), "thread": mypost[12],
                             "user": mypost[8]})
        return_data = {"code": 0, "response": postlist}
        return jsonify(return_data)

    else:
        return_data = {"code": 1, "response": "USER NOT FOUND"}
        return jsonify(return_data)


@app.route('/db/api/user/updateProfile/', methods=['POST'])
def user_updateProfile():
    try:
        data = request.get_json()
        user = data['user']
        about = data['about']
        name = data['name']
        db = db_connect()
        cursor = db.cursor()
        query_str = "SELECT * FROM users WHERE email = '%s' " % (user)
        cursor.execute(query_str)
        myuser = cursor.fetchone()
        if myuser:
            if (myuser[2] != about) or (myuser[3] != name):
                query_str = "update users set about = '%s' WHERE email = '%s'" % (about, user)
                cursor.execute(query_str)
                query_str = "update users set name = '%s' WHERE email = '%s'" % (name, user)
                cursor.execute(query_str)
                db.commit()
                query_str = "SELECT who_user FROM followers WHERE whom_user = '%s'" % (myuser[4])
                cursor.execute(query_str)
                myfollowers = cursor.fetchall()
                query_str = "SELECT whom_user FROM followers WHERE who_user = '%s'" % (myuser[4])
                cursor.execute(query_str)
                myfollowing = cursor.fetchall()
                query_str = "SELECT thread_id FROM subscriptions WHERE user = '%s'" % (myuser[4])
                cursor.execute(query_str)
                mysubs = cursor.fetchall()
                if about == 'None':
                    about = None
                if myuser[1] == 'None':
                    username = None
                else:
                    username = myuser[1]
                if name == 'None':
                    name = None
                userinfo = {"about": about, "email": myuser[4], "followers": [x[0] for x in myfollowers],
                            "following": [x[0] for x in myfollowing],
                            "id": myuser[0], "isAnonymous": bool(myuser[5]),
                            "name": name, "subscriptions": [x[0] for x in mysubs],
                            "username": username}
                return_data = {"code": 0, "response": userinfo}
                return jsonify(return_data)
            else:

                query_str = "SELECT who_user FROM followers WHERE whom_user = '%s'" % (myuser[4])
                cursor.execute(query_str)
                myfollowers = cursor.fetchall()
                query_str = "SELECT whom_user FROM followers WHERE who_user = '%s'" % (myuser[4])
                cursor.execute(query_str)
                myfollowing = cursor.fetchall()
                query_str = "SELECT thread_id FROM subscriptions WHERE user = '%s'" % (myuser[4])
                cursor.execute(query_str)
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

                userinfo = {"about": about, "email": myuser[4], "followers": [x[0] for x in myfollowers],
                            "following": [x[0] for x in myfollowing],
                            "id": myuser[0], "isAnonymous": bool(myuser[5]),
                            "name": name, "subscriptions": [x[0] for x in mysubs],
                            "username": username}
                return_data = {"code": 0, "response": userinfo}
                return jsonify(return_data)
        else:
            return_data = {"code": 1, "response": "USER NOT FOUND"}
            db.close()
            return jsonify(return_data)
    except KeyError:
        return_data = {"code": 2, "response": "invalid json format"}
        return jsonify(return_data)


@app.route('/db/api/user/follow/', methods=['POST'])
def user_follow():
    try:
        data = request.get_json()
        follower = data['follower']  # who
        followee = data['followee']  # whom
        if followee == follower:
            return_data = {"code": 3, "response": "WTF!"}
            return jsonify(return_data)
        db = db_connect()
        cursor = db.cursor()
        query_str = "SELECT * FROM users WHERE email = '%s' " % (followee)
        cursor.execute(query_str)
        myuserwhom = cursor.fetchone()
        if myuserwhom:
            query_str = "SELECT * FROM followers WHERE who_user = '%s' AND whom_user = '%s'" % (follower, followee)
            cursor.execute(query_str)
            if not cursor.fetchone():
                query_str = "SELECT * FROM users WHERE email = '%s' " % (follower)
                cursor.execute(query_str)
                myuser = cursor.fetchone()
                if myuser:
                    query_str = "insert into followers (who_user, whom_user) values ('%s', '%s')" % (follower, followee)
                    cursor.execute(query_str)
                    db.commit()
                    query_str = "SELECT who_user FROM followers WHERE whom_user = '%s'" % (myuser[4])
                    cursor.execute(query_str)
                    myfollowers = cursor.fetchall()
                    query_str = "SELECT whom_user FROM followers WHERE who_user = '%s'" % (myuser[4])
                    cursor.execute(query_str)
                    myfollowing = cursor.fetchall()
                    query_str = "SELECT thread_id FROM subscriptions WHERE user = '%s'" % (myuser[4])
                    cursor.execute(query_str)
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

                    userinfo = {"about": about, "email": myuser[4], "followers": [x[0] for x in myfollowers],
                                "following": [x[0] for x in myfollowing],
                                "id": myuser[0], "isAnonymous": bool(myuser[5]),
                                "name": name, "subscriptions": [x[0] for x in mysubs],
                                "username": username}
                    return_data = {"code": 0, "response": userinfo}
                    return jsonify(return_data)
                else:
                    return_data = {"code": 1, "response": "USER NOT FOUND"}
                    db.close()
                    return jsonify(return_data)
            else:
                query_str = "SELECT * FROM users WHERE email = '%s' " % (follower)
                cursor.execute(query_str)
                myuser = cursor.fetchone()
                query_str = "SELECT who_user FROM followers WHERE whom_user = '%s'" % (myuser[4])
                cursor.execute(query_str)
                myfollowers = cursor.fetchall()
                query_str = "SELECT whom_user FROM followers WHERE who_user = '%s'" % (myuser[4])
                cursor.execute(query_str)
                myfollowing = cursor.fetchall()
                query_str = "SELECT thread_id FROM subscriptions WHERE user = '%s'" % (myuser[4])
                cursor.execute(query_str)
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

                userinfo = {"about": about, "email": myuser[4], "followers": [x[0] for x in myfollowers],
                            "following": [x[0] for x in myfollowing],
                            "id": myuser[0], "isAnonymous": bool(myuser[5]),
                            "name": name, "subscriptions": [x[0] for x in mysubs],
                            "username": username}
                return_data = {"code": 0, "response": userinfo}
                return jsonify(return_data)

        else:
            return_data = {"code": 1, "response": "USER NOT FOUND"}
            db.close()
            return jsonify(return_data)
    except KeyError:
        return_data = {"code": 2, "response": "invalid json format"}
        return jsonify(return_data)


@app.route('/db/api/user/listFollowers/', methods=['GET'])
def user_listFollowers():
    user = request.args.get('user', False)
    if not user:
        return_data = {"code": 3, "response": "bad syntax"}
        return jsonify(return_data)
    limit = request.args.get('limit', False)
    since_id = request.args.get('since_id', False)
    order = request.args.get('order', 'desc')
    db = db_connect()
    cursor = db.cursor()
    query_str = "SELECT * FROM users WHERE email = '%s'" % (user)
    cursor.execute(query_str)
    myuser = cursor.fetchone()
    if myuser:

        query_str = "SELECT * FROM users join followers on users.email = followers.who_user WHERE whom_user = '%s' " % (
            user)
        if since_id:
            query_str += " AND user_id >= %d " % (int(since_id))
        query_str += " ORDER BY name %s" % (order)
        if limit:
            query_str += " limit %d" % (int(limit))
        cursor.execute(query_str)
        myfollowers = cursor.fetchall()
        followersList = []
        for myuser in myfollowers:
            query_str = "SELECT who_user FROM followers WHERE whom_user = '%s'" % (myuser[4])
            cursor.execute(query_str)
            myfollowers = cursor.fetchall()
            query_str = "SELECT whom_user FROM followers WHERE who_user = '%s'" % (myuser[4])
            cursor.execute(query_str)
            myfollowing = cursor.fetchall()
            query_str = "SELECT thread_id FROM subscriptions WHERE user = '%s'" % (myuser[4])
            cursor.execute(query_str)
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

            userinfo = {"about": about, "email": myuser[4], "followers": [x[0] for x in myfollowers],
                        "following": [x[0] for x in myfollowing],
                        "id": myuser[0], "isAnonymous": bool(myuser[5]),
                        "name": name, "subscriptions": [x[0] for x in mysubs],
                        "username": username}

            followersList.append(userinfo)

        return_data = {"code": 0, "response": followersList}
        return jsonify(return_data)
    else:
        return_data = {"code": 1, "response": "USER NOT FOUND"}
        db.close()
        return jsonify(return_data)


@app.route('/db/api/user/listFollowing/', methods=['GET'])
def user_listFollowing():
    user = request.args.get('user', False)
    if not user:
        return_data = {"code": 3, "response": "bad syntax"}
        return jsonify(return_data)
    limit = request.args.get('limit', False)
    since_id = request.args.get('since_id', False)
    order = request.args.get('order', 'desc')
    db = db_connect()
    cursor = db.cursor()
    query_str = "SELECT * FROM users WHERE email = '%s'" % (user)
    cursor.execute(query_str)
    myuser = cursor.fetchone()
    if myuser:

        query_str = "SELECT * FROM users join followers on users.email = followers.whom_user WHERE who_user = '%s' " % (
            user)
        if since_id:
            query_str += " AND user_id >= %d " % (int(since_id))
        query_str += " ORDER BY name %s" % (order)
        if limit:
            query_str += " limit %d" % (int(limit))
        cursor.execute(query_str)
        allmyfollowing = cursor.fetchall()
        myfollowingList = []
        for myuser in allmyfollowing:
            query_str = "SELECT who_user FROM followers WHERE whom_user = '%s'" % (myuser[4])
            cursor.execute(query_str)
            myfollowers = cursor.fetchall()
            query_str = "SELECT whom_user FROM followers WHERE who_user = '%s'" % (myuser[4])
            cursor.execute(query_str)
            myfollowing = cursor.fetchall()
            query_str = "SELECT thread_id FROM subscriptions WHERE user = '%s'" % (myuser[4])
            cursor.execute(query_str)
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

            userinfo = {"about": about, "email": myuser[4], "followers": [x[0] for x in myfollowers],
                        "following": [x[0] for x in myfollowing],
                        "id": myuser[0], "isAnonymous": bool(myuser[5]),
                        "name": name, "subscriptions": [x[0] for x in mysubs],
                        "username": username}

            myfollowingList.append(userinfo)

        return_data = {"code": 0, "response": myfollowingList}
        return jsonify(return_data)
    else:
        return_data = {"code": 1, "response": "USER NOT FOUND"}
        db.close()
        return jsonify(return_data)


@app.route('/db/api/user/unfollow/', methods=['POST'])
def uesr_unfollow():
    try:
        data = request.get_json()
        follower = data['follower']  # who
        followee = data['followee']  # whom
        if followee == follower:
            return_data = {"code": 3, "response": "WTF!"}
            return jsonify(return_data)
        db = db_connect()
        cursor = db.cursor()
        query_str = "SELECT * FROM users WHERE email = '%s' " % (followee)
        cursor.execute(query_str)
        myuserwhom = cursor.fetchone()
        if myuserwhom:
            query_str = "SELECT * FROM followers WHERE who_user = '%s' AND whom_user = '%s'" % (follower, followee)
            cursor.execute(query_str)
            if cursor.fetchone():
                query_str = "SELECT * FROM users WHERE email = '%s' " % (follower)
                cursor.execute(query_str)
                myuser = cursor.fetchone()
                if myuser:
                    query_str = "delete FROM followers WHERE who_user = '%s' AND whom_user = '%s'" % (
                        follower, followee)
                    cursor.execute(query_str)
                    db.commit()
                    query_str = "SELECT who_user FROM followers WHERE whom_user = '%s'" % (myuser[4])
                    cursor.execute(query_str)
                    myfollowers = cursor.fetchall()
                    query_str = "SELECT whom_user FROM followers WHERE who_user = '%s'" % (myuser[4])
                    cursor.execute(query_str)
                    myfollowing = cursor.fetchall()
                    query_str = "SELECT thread_id FROM subscriptions WHERE user = '%s'" % (myuser[4])
                    cursor.execute(query_str)
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

                    userinfo = {"about": about, "email": myuser[4], "followers": [x[0] for x in myfollowers],
                                "following": [x[0] for x in myfollowing],
                                "id": myuser[0], "isAnonymous": bool(myuser[5]),
                                "name": name, "subscriptions": [x[0] for x in mysubs],
                                "username": username}
                    return_data = {"code": 0, "response": userinfo}
                    return jsonify(return_data)
                else:
                    return_data = {"code": 1, "response": "USER NOT FOUND"}
                    db.close()
                    return jsonify(return_data)
            else:
                query_str = "SELECT * FROM users WHERE email = '%s' " % (follower)
                cursor.execute(query_str)
                myuser = cursor.fetchone()
                query_str = "SELECT who_user FROM followers WHERE whom_user = '%s'" % (myuser[4])
                cursor.execute(query_str)
                myfollowers = cursor.fetchall()
                query_str = "SELECT whom_user FROM followers WHERE who_user = '%s'" % (myuser[4])
                cursor.execute(query_str)
                myfollowing = cursor.fetchall()
                query_str = "SELECT thread_id FROM subscriptions WHERE user = '%s'" % (myuser[4])
                cursor.execute(query_str)
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

                userinfo = {"about": about, "email": myuser[4], "followers": [x[0] for x in myfollowers],
                            "following": [x[0] for x in myfollowing],
                            "id": myuser[0], "isAnonymous": bool(myuser[5]),
                            "name": name, "subscriptions": [x[0] for x in mysubs],
                            "username": username}
                return_data = {"code": 0, "response": userinfo}
                return jsonify(return_data)

        else:
            return_data = {"code": 1, "response": "USER NOT FOUND"}
            db.close()
            return jsonify(return_data)
    except KeyError:
        return_data = {"code": 2, "response": "invalid json format"}
        return jsonify(return_data)


# THREADS
@app.route('/db/api/thread/create/', methods=['POST'])
def thread_create():
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
        query_str = """INSERT INTO threads (forum, title, isClosed, user, date, message,slug, isDeleted) values
        ('%s', '%s', %d, '%s', '%s', '%s', '%s', %d)""" % (forum, title, isClosed, user, date, message, slug, isDeleted)
        db = db_connect()
        cursor = db.cursor()
        cursor.execute(query_str)
        db.commit()
        db.close()
        return_data = {'code': 0, 'response': {'date': date, 'forum': forum, 'id': cursor.lastrowid,
                                               'isClosed': isClosed, 'isDeleted': isDeleted,
                                               'message': message, 'slug': slug, 'title': title, 'user': user}}
        return jsonify(return_data)
    except KeyError:
        return_data = {"code": 2, "response": "invalid json format"}
        return jsonify(return_data)


@app.route('/db/api/thread/details/', methods=['GET'])
def thread_details():
    thread = request.args.get('thread', '')
    related = request.args.getlist('related')
    db = db_connect()
    cursor = db.cursor()
    query_str = "SELECT * FROM threads WHERE thread_id = '%s'" % (thread)
    if cursor.execute(query_str) == 0:
        return_data = {"code": 1, "response": "THREAD NOT FOUND"}
        return jsonify(return_data)
    mythread = cursor.fetchone()
    if 'user' in related:
        query_str = "SELECT * FROM users WHERE email = '%s'" % (mythread[4])
        related.remove('user')
        cursor.execute(query_str)
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
        query_str = "SELECT who_user FROM followers WHERE whom_user = '%s'" % (myuser[4])
        cursor.execute(query_str)
        myfollowers = cursor.fetchall()
        query_str = "SELECT whom_user FROM followers WHERE who_user = '%s'" % (myuser[4])
        cursor.execute(query_str)
        myfollowing = cursor.fetchall()
        query_str = "SELECT thread_id FROM subscriptions WHERE user = '%s'" % (myuser[4])
        cursor.execute(query_str)
        mysubs = cursor.fetchall()
        userinfo = {"about": about, "email": myuser[4], "followers": [x[0] for x in myfollowers],
                    "following": [x[0] for x in myfollowing],
                    "id": myuser[0], "isAnonymous": bool(myuser[5]),
                    "name": name, "subscriptions": [x[0] for x in mysubs],
                    "username": username}
    else:
        userinfo = mythread[4]
    if 'forum' in related:
        related.remove('forum')
        query_str = "SELECT * FROM forums WHERE short_name = '%s'" % (mythread[1])
        cursor.execute(query_str)
        myforum = cursor.fetchone()
        foruminfo = {"id": myforum[3], "name": myforum[0], "short_name": myforum[1],
                     "user": myforum[2]}
    else:
        foruminfo = mythread[1]
    if related:
        return_data = {"code": 3, "response": "invalid syntax"}
        return jsonify(return_data)
    return_data = {"code": 0, "response": {"date": mythread[5].strftime("%Y-%m-%d %H:%M:%S"), "dislikes": mythread[10],
                                           "forum": foruminfo, "id": mythread[0], "isClosed": bool(mythread[3]),
                                           "isDeleted": bool(mythread[8]),
                                           "likes": mythread[9], "message": mythread[6],
                                           "points": (mythread[9] - mythread[10]),
                                           "posts": mythread[11], "slug": mythread[7], "title": mythread[2],
                                           "user": userinfo}}
    return jsonify(return_data)


@app.route("/db/api/thread/list/", methods=["GET"])
def thread_list():
    user = request.args.get('user', False)
    forum = request.args.get('forum', False)
    if user and forum:
        return_data = {"code": 3, "response": "bad syntax"}
        return jsonify(return_data)
    limit = request.args.get('limit', False)
    since = request.args.get('since', False)
    order = request.args.get('order', False)
    db = db_connect()
    cursor = db.cursor()
    query_str = "SELECT * FROM threads WHERE "
    if user:
        query_str += "user =  '%s'" % (user)
    else:
        query_str += "forum = '%s' " % (forum)
    if since:
        query_str += " AND date >= '%s' " % (since)
    if order:
        query_str += " ORDER BY date %s " % (order)
    if limit:
        query_str += " limit %d" % (int(limit))

    cursor.execute(query_str)
    threads = cursor.fetchall()

    returnthreads = []

    for mythread in threads:
        returnthreads.append({"date": mythread[5].strftime("%Y-%m-%d %H:%M:%S"), "dislikes": mythread[10],
                              "forum": mythread[1], "id": mythread[0], "isClosed": bool(mythread[3]),
                              "isDeleted": bool(mythread[8]),
                              "likes": mythread[9], "message": mythread[6], "points": (mythread[9] - mythread[10]),
                              "posts": mythread[11], "slug": mythread[7], "title": mythread[2], "user": mythread[4]})
    return_data = {"code": 0, "response": returnthreads}
    return jsonify(return_data)


@app.route('/db/api/thread/listPosts/', methods=['GET'])
def thread_listpost():
    thread = request.args.get('thread', False)
    if not thread:
        return_data = {"code": 3, "response": "bad syntax"}
        return jsonify(return_data)
    limit = request.args.get('limit', False)
    since = request.args.get('since', False)
    order = request.args.get('order', 'desc')
    db = db_connect()
    cursor = db.cursor()
    query_str = "SELECT * FROM threads WHERE thread_id = %d" % (int(thread))
    cursor.execute(query_str)
    mythread = cursor.fetchone()
    if mythread:
        query_str = "SELECT * FROM posts WHERE thread = %d" % (int(thread))
        if since:
            query_str += " AND date >= '%s' " % (since)
        query_str += " ORDER BY date %s " % (order)
        if limit:
            query_str += " limit %d" % (int(limit))
        cursor.execute(query_str)
        myposts = cursor.fetchall()
        postlist = []

        for mypost in myposts:
            if mypost[1] == 0:
                parent = None
            else:
                parent = mypost[1]
            postlist.append({"date": mypost[6].strftime("%Y-%m-%d %H:%M:%S"), "dislikes": mypost[10],
                             "forum": mypost[9], "id": mypost[0], "isApproved": bool(mypost[2]),
                             "isDeleted": bool(mypost[5]), "isEdited": bool(mypost[3]),
                             "isHighlighted": bool(mypost[13]), "isSpam": bool(mypost[4]),
                             "likes": mypost[11], "message": mypost[7], "parent": parent,
                             "points": (mypost[11] - mypost[10]), "thread": mypost[12],
                             "user": mypost[8]})
        return_data = {"code": 0, "response": postlist}
        return jsonify(return_data)

    else:
        return_data = {"code": 1, "response": "THREAD NOT FOUND"}
        return jsonify(return_data)


@app.route('/db/api/thread/remove/', methods=['POST'])
def thread_remove():
    try:
        data = request.get_json()
        thread = data['thread']
        db = db_connect()
        cursor = db.cursor()
        query_str = "SELECT * FROM threads WHERE thread_id = %d" % (int(thread))
        cursor.execute(query_str)
        mythread = cursor.fetchone()
        if mythread:
            if not mythread[8]:
                query_str = "update threads set isDeleted = True WHERE thread_id = %d" % (int(thread))
                cursor.execute(query_str)
                db.commit()
                query_str = "update threads set posts = 0 WHERE thread_id = %d" % (int(thread))
                cursor.execute(query_str)
                db.commit()
                query_str = "update posts set isDeleted = True WHERE thread = %d" % (int(thread))
                cursor.execute(query_str)
                db.commit()
                db.close()
                return_data = {"code": 0, "response": {"thread": thread}}
                return jsonify(return_data)
            else:
                query_str = "update threads set posts = 0 WHERE thread_id = %d" % (int(thread))
                cursor.execute(query_str)
                db.commit()
                query_str = "update posts set isDeleted = True WHERE thread = %d" % (int(thread))
                cursor.execute(query_str)
                db.commit()
                db.close()
                return_data = {"code": 0,
                               "response": {"date": mythread[5].strftime("%Y-%m-%d %H:%M:%S"), "dislikes": mythread[10],
                                            "forum": mythread[1], "id": mythread[0], "isClosed": bool(mythread[3]),
                                            "isDeleted": bool(mythread[8]),
                                            "likes": mythread[9], "message": mythread[6],
                                            "points": (mythread[9] - mythread[10]),
                                            "posts": 0, "slug": mythread[7], "title": mythread[2], "user": mythread[4]}}
                return jsonify(return_data)
        else:
            return_data = {"code": 1, "response": "THREAD NOT FOUND"}
            return jsonify(return_data)
    except KeyError:
        return_data = {"code": 2, "response": "invalid json format"}
        return jsonify(return_data)


@app.route('/db/api/thread/restore/', methods=['POST'])
def thread_restore():
    try:
        data = request.get_json()
        thread = data['thread']
        db = db_connect()
        cursor = db.cursor()
        query_str = "SELECT * FROM threads WHERE thread_id = %d" % (int(thread))
        cursor.execute(query_str)
        mythread = cursor.fetchone()
        if mythread:
            if mythread[8]:
                query_str = "update threads set isDeleted = False WHERE thread_id = %d" % (int(thread))
                cursor.execute(query_str)
                db.commit()
                query_str = "update posts set isDeleted = False WHERE thread = %d" % (int(thread))
                cursor.execute(query_str)
                db.commit()
                query_str = "SELECT count(*) FROM posts WHERE  thread = %d" % (int(thread))
                cursor.execute(query_str)
                postcount = cursor.fetchone()
                query_str = "update threads set posts = %d WHERE thread_id = %d" % (int(postcount[0]), int(thread))
                cursor.execute(query_str)
                db.commit()
                db.close()
                return_data = {"code": 0, "response": {"thread": thread}}
                return jsonify(return_data)
            else:
                return_data = {"code": 0,
                               "response": {"date": mythread[5].strftime("%Y-%m-%d %H:%M:%S"), "dislikes": mythread[10],
                                            "forum": mythread[1], "id": mythread[0], "isClosed": bool(mythread[3]),
                                            "isDeleted": bool(mythread[8]),
                                            "likes": mythread[9], "message": mythread[6],
                                            "points": (mythread[9] - mythread[10]),
                                            "posts": mythread[11], "slug": mythread[7], "title": mythread[2],
                                            "user": mythread[4]}}

                return jsonify(return_data)


        else:
            return_data = {"code": 1, "response": "THREAD NOT FOUND"}
            return jsonify(return_data)
    except KeyError:
        return_data = {"code": 2, "response": "invalid json format"}
        return jsonify(return_data)


@app.route('/db/api/thread/close/', methods=['POST'])
def thread_close():
    try:
        data = request.get_json()
        thread = data['thread']
        db = db_connect()
        cursor = db.cursor()
        query_str = "SELECT * FROM threads WHERE thread_id = %d" % (int(thread))
        cursor.execute(query_str)
        mythread = cursor.fetchone()
        if mythread:
            if not mythread[3]:
                query_str = "update threads set isClosed = True WHERE thread_id = %d" % (int(thread))
                cursor.execute(query_str)
                db.commit()
                db.close()
                return_data = {"code": 0, "response": {"thread": thread}}
                return jsonify(return_data)
            else:
                return_data = {"code": 0,
                               "response": {"date": mythread[5].strftime("%Y-%m-%d %H:%M:%S"), "dislikes": mythread[10],
                                            "forum": mythread[1], "id": mythread[0], "isClosed": bool(mythread[3]),
                                            "isDeleted": bool(mythread[8]),
                                            "likes": mythread[9], "message": mythread[6],
                                            "points": (mythread[9] - mythread[10]),
                                            "posts": mythread[11], "slug": mythread[7], "title": mythread[2],
                                            "user": mythread[4]}}

                return jsonify(return_data)
        else:
            return_data = {"code": 1, "response": "THREAD NOT FOUND"}
            return jsonify(return_data)
    except KeyError:
        return_data = {"code": 2, "response": "invalid json format"}
        return jsonify(return_data)


@app.route('/db/api/thread/open/', methods=['POST'])
def thread_open():
    try:
        data = request.get_json()
        thread = data['thread']
        db = db_connect()
        cursor = db.cursor()
        query_str = "SELECT * FROM threads WHERE thread_id = %d" % (int(thread))
        cursor.execute(query_str)
        mythread = cursor.fetchone()
        if mythread:
            if mythread[3]:
                query_str = "update threads set isClosed = False WHERE thread_id = %d" % (int(thread))
                cursor.execute(query_str)
                db.commit()
                db.close()
                return_data = {"code": 0, "response": {"thread": thread}}
                return jsonify(return_data)
            else:
                return_data = {"code": 0,
                               "response": {"date": mythread[5].strftime("%Y-%m-%d %H:%M:%S"), "dislikes": mythread[10],
                                            "forum": mythread[1], "id": mythread[0], "isClosed": bool(mythread[3]),
                                            "isDeleted": bool(mythread[8]),
                                            "likes": mythread[9], "message": mythread[6],
                                            "points": (mythread[9] - mythread[10]),
                                            "posts": mythread[11], "slug": mythread[7], "title": mythread[2],
                                            "user": mythread[4]}}

                return jsonify(return_data)
        else:
            return_data = {"code": 1, "response": "THREAD NOT FOUND"}
            return jsonify(return_data)
    except KeyError:
        return_data = {"code": 2, "response": "invalid json format"}
        return jsonify(return_data)


@app.route('/db/api/thread/update/', methods=['POST'])
def thread_update():
    try:
        data = request.get_json()
        thread = data['thread']
        message = data['message']
        slug = data['slug']
        db = db_connect()
        cursor = db.cursor()
        query_str = "SELECT * FROM threads WHERE thread_id = %d " % (int(thread))
        cursor.execute(query_str)
        mythread = cursor.fetchone()
        if mythread:
            if (mythread[6] != message) or (mythread[7] != slug):
                query_str = "update threads set message = '%s' WHERE thread_id = %d" % (message, thread)
                cursor.execute(query_str)
                query_str = "update threads set slug = '%s' WHERE thread_id = %d" % (slug, thread)
                cursor.execute(query_str)
                db.commit()
                db.close()
                return_data = {"code": 0,
                               "response": {"date": mythread[5].strftime("%Y-%m-%d %H:%M:%S"), "dislikes": mythread[10],
                                            "forum": mythread[1], "id": mythread[0], "isClosed": bool(mythread[3]),
                                            "isDeleted": bool(mythread[8]),
                                            "likes": mythread[9], "message": message,
                                            "points": (mythread[9] - mythread[10]),
                                            "posts": mythread[11], "slug": slug, "title": mythread[2],
                                            "user": mythread[4]}}
                return jsonify(return_data)
            else:
                return_data = {"code": 0,
                               "response": {"date": mythread[5].strftime("%Y-%m-%d %H:%M:%S"), "dislikes": mythread[10],
                                            "forum": mythread[1], "id": mythread[0], "isClosed": bool(mythread[3]),
                                            "isDeleted": bool(mythread[8]),
                                            "likes": mythread[9], "message": mythread[6],
                                            "points": (mythread[9] - mythread[10]),
                                            "posts": mythread[11], "slug": mythread[7], "title": mythread[2],
                                            "user": mythread[4]}}
                return jsonify(return_data)
        else:
            return_data = {"code": 1, "response": "THREAD NOT FOUND"}
            db.close()
            return jsonify(return_data)
    except KeyError:
        return_data = {"code": 2, "response": "invalid json format"}
        return jsonify(return_data)


@app.route('/db/api/thread/vote/', methods=['POST'])
def thread_vote():
    try:
        data = request.get_json()
        vote = data['vote']
        thread = data['thread']
        db = db_connect()
        cursor = db.cursor()
        query_str = "SELECT * FROM threads WHERE thread_id = %d " % (int(thread))
        cursor.execute(query_str)
        mythread = cursor.fetchone()
        if mythread:
            if vote == 1:
                query_str = "update threads set likes = likes + 1 WHERE thread_id = %d" % (int(thread))
                mylikes = mythread[9] + 1
                mydislikes = mythread[10]
            elif vote == -1:
                query_str = "update threads set dislikes = dislikes + 1 WHERE thread_id = %d" % (int(thread))
                mylikes = mythread[9]
                mydislikes = mythread[10] + 1
            else:
                return_data = {"code": 3, "response": "invalid syntax"}
                return jsonify(return_data)
            cursor.execute(query_str)
            db.commit()
            db.close()
            return_data = {"code": 0,
                           "response": {"date": mythread[5].strftime("%Y-%m-%d %H:%M:%S"), "dislikes": mydislikes,
                                        "forum": mythread[1], "id": mythread[0], "isClosed": bool(mythread[3]),
                                        "isDeleted": bool(mythread[8]),
                                        "likes": mylikes, "message": mythread[6], "points": (mylikes - mydislikes),
                                        "posts": mythread[11], "slug": mythread[7], "title": mythread[2],
                                        "user": mythread[4]}}
            return jsonify(return_data)
        else:
            return_data = {"code": 1, "response": "THREAD NOT FOUND"}
            db.close()
            return jsonify(return_data)

    except KeyError:
        return_data = {"code": 2, "response": "invalid json format"}
        return jsonify(return_data)


@app.route('/db/api/thread/subscribe/', methods=['POST'])
def thread_subscribe():
    try:
        data = request.get_json()
        user = data['user']
        thread = data['thread']
        db = db_connect()
        cursor = db.cursor()
        query_str = "SELECT * FROM threads WHERE thread_id = %d " % (int(thread))
        cursor.execute(query_str)
        mythread = cursor.fetchone()
        query_str = "SELECT * FROM users WHERE email = '%s'" % (user)
        cursor.execute(query_str)
        myuser = cursor.fetchone()
        if (not mythread) or (not myuser):
            return_data = {"code": 1, "response": "THREAD or USER NOT FOUND"}
            db.close()
            return jsonify(return_data)
        else:
            query_str = "SELECT * FROM subscriptions WHERE user = '%s' AND thread_id = %d" % (user, int(thread))
            cursor.execute(query_str)
            mysub = cursor.fetchone()
            if not mysub:
                query_str = "insert into subscriptions (user, thread_id) values ('%s', %d)" % (user, thread)
                cursor.execute(query_str)
                db.commit()
                db.close()
                return_data = {"code": 0, "response": {"thread": thread, "user": user}}
                return jsonify(return_data)

            else:
                return_data = {"code": 0, "response": {"thread": thread, "user": user}}
                return jsonify(return_data)
    except KeyError:
        return_data = {"code": 2, "response": "invalid json format"}
        return jsonify(return_data)


@app.route('/db/api/thread/unsubscribe/', methods=['POST'])
def thread_unsubscribe():
    try:
        data = request.get_json()
        user = data['user']
        thread = data['thread']
        db = db_connect()
        cursor = db.cursor()
        query_str = "SELECT * FROM threads WHERE thread_id = %d " % (int(thread))
        cursor.execute(query_str)
        mythread = cursor.fetchone()
        query_str = "SELECT * FROM users WHERE email = '%s'" % (user)
        cursor.execute(query_str)
        myuser = cursor.fetchone()
        if (not mythread) or (not myuser):
            return_data = {"code": 1, "response": "THREAD or USER NOT FOUND"}
            db.close()
            return jsonify(return_data)
        else:
            query_str = "SELECT * FROM subscriptions WHERE user = '%s' AND thread_id = %d" % (user, int(thread))
            cursor.execute(query_str)
            mysub = cursor.fetchone()
            if mysub:
                query_str = "delete  FROM subscriptions WHERE user = '%s' AND thread_id = %d" % (user, thread)
                cursor.execute(query_str)
                db.commit()
                db.close()
                return_data = {"code": 0, "response": {"thread": thread, "user": user}}
                return jsonify(return_data)

            else:
                return_data = {"code": 0, "response": {"thread": thread, "user": user}}
                return jsonify(return_data)
    except KeyError:
        return_data = {"code": 2, "response": "invalid json format"}
        return jsonify(return_data)


# POST


@app.route('/db/api/post/create/', methods=['POST'])
def post_create():
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
        query_str = """INSERT INTO posts (parent, isApproved, isEdited, isSpam, isDeleted, date, message, user, forum,
         thread, isHighlited)
         values (%d, %d, %d, %d, %d, '%s', '%s', '%s', '%s', %d, %d)""" % (parent, isApproved, isEdit, isSpam,
                                                                           isDeleted, date, message,
                                                                           user, forum, thread, isHighlighted)
        db = db_connect()
        cursor = db.cursor()
        cursor.execute(query_str)
        if parent == 0:
            parent = None
        return_data = {"code": 0, "response": {"date": date, "forum": forum,
                                               "id": cursor.lastrowid, "isApproved": isApproved,
                                               "isEdited": isEdit, "isHighlited": isHighlighted, "isSpam": isSpam,
                                               "message": message, "parent": parent, "thread": thread, "user": user}}
        db.commit()
        query_str = """update threads set posts = posts + 1 WHERE thread_id = %d""" % (thread)
        cursor.execute(query_str)
        db.commit()
        db.close()
        return jsonify(return_data)
    except KeyError:
        return_data = {"code": 2, "response": "invalid json format"}
        return jsonify(return_data)


@app.route('/db/api/post/details/', methods=['GET'])
def post_details():
    post = request.args.get('post', '')
    related = request.args.getlist('related')
    db = db_connect()
    cursor = db.cursor()
    query_str = "SELECT * FROM posts WHERE post_id = '%s'" % (post)
    if cursor.execute(query_str) == 0:
        return_data = {"code": 1, "response": "POST NOT FOUND"}
        return jsonify(return_data)
    mypost = cursor.fetchone()
    if 'user' in related:
        query_str = "SELECT * FROM users WHERE email = '%s'" % (mypost[8])
        cursor.execute(query_str)
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
        query_str = "SELECT who_user FROM followers WHERE whom_user = '%s'" % (myuser[4])
        cursor.execute(query_str)
        myfollowers = cursor.fetchall()
        query_str = "SELECT whom_user FROM followers WHERE who_user = '%s'" % (myuser[4])
        cursor.execute(query_str)
        myfollowing = cursor.fetchall()
        query_str = "SELECT thread_id FROM subscriptions WHERE user = '%s'" % (myuser[4])
        cursor.execute(query_str)
        mysubs = cursor.fetchall()
        userinfo = {"about": about, "email": myuser[4], "followers": [x[0] for x in myfollowers],
                    "following": [x[0] for x in myfollowing],
                    "id": myuser[0], "isAnonymous": bool(myuser[5]),
                    "name": name, "subscriptions": [x[0] for x in mysubs],
                    "username": username}
    else:
        userinfo = mypost[8]

    if 'forum' in related:
        query_str = "SELECT * FROM forums WHERE short_name = '%s'" % (mypost[9])
        cursor.execute(query_str)
        myforum = cursor.fetchone()
        foruminfo = {"id": myforum[3], "name": myforum[0], "short_name": myforum[1],
                     "user": myforum[2]}
    else:
        foruminfo = mypost[9]

    if 'thread' in related:
        query_str = "SELECT * FROM threads WHERE thread_id = '%s'" % (mypost[12])
        cursor.execute(query_str)
        mythread = cursor.fetchone()
        threadinfo = {"date": mythread[5].strftime("%Y-%m-%d %H:%M:%S"), "dislikes": mythread[10],
                      "forum": mythread[1], "id": mythread[0], "isClosed": bool(mythread[3]),
                      "isDeleted": bool(mythread[8]),
                      "likes": mythread[9], "message": mythread[6], "points": (mythread[9] - mythread[10]),
                      "posts": mythread[11], "slug": mythread[7], "title": mythread[2], "user": mythread[4]}
    else:
        threadinfo = mypost[12]
    if mypost[1] == 0:
        parent = None
    else:
        parent = mypost[1]

    return_data = {"code": 0, "response": {"date": mypost[6].strftime("%Y-%m-%d %H:%M:%S"), "dislikes": mypost[10],
                                           "forum": foruminfo, "id": mypost[0], "isApproved": bool(mypost[2]),
                                           "isDeleted": bool(mypost[5]), "isEdited": bool(mypost[3]),
                                           "isHighlighted": bool(mypost[13]), "isSpam": bool(mypost[4]),
                                           "likes": mypost[11], "message": mypost[7], "parent": parent,
                                           "points": (mypost[11] - mypost[10]), "thread": threadinfo, "user": userinfo}}
    return jsonify(return_data)


@app.route('/db/api/post/list/', methods=['GET'])
def post_list():
    thread = request.args.get('thread', False)
    forum = request.args.get('forum', False)
    if thread and forum:
        return_data = {"code": 3, "response": "bad syntax"}
        return jsonify(return_data)
    limit = request.args.get('limit', False)
    since = request.args.get('since', False)
    order = request.args.get('order', False)
    db = db_connect()
    cursor = db.cursor()
    query_str = "SELECT * FROM posts WHERE "
    if thread:
        query_str += "thread =  %d" % (int(thread))
    else:
        query_str += "forum = '%s' " % (forum)
    if since:
        query_str += " AND date >= '%s' " % (since)
    if order:
        query_str += " ORDER BY date %s " % (order)
    if limit:
        query_str += " limit %d" % (int(limit))

    cursor.execute(query_str)
    myposts = cursor.fetchall()

    returnposts = []

    for mypost in myposts:
        if mypost[1] == 0:
            parent = None
        else:
            parent = mypost[1]
        returnposts.append({"date": mypost[6].strftime("%Y-%m-%d %H:%M:%S"), "dislikes": mypost[10],
                            "forum": mypost[9], "id": mypost[0], "isApproved": bool(mypost[2]),
                            "isDeleted": bool(mypost[5]), "isEdited": bool(mypost[3]),
                            "isHighlighted": bool(mypost[13]), "isSpam": bool(mypost[4]),
                            "likes": mypost[11], "message": mypost[7], "parent": parent,
                            "points": (mypost[11] - mypost[10]), "thread": mypost[12], "user": mypost[8]})
    return_data = {"code": 0, "response": returnposts}
    return jsonify(return_data)


@app.route('/db/api/post/remove/', methods=['POST'])
def post_remove():
    try:
        data = request.get_json()
        post = data['post']
    except KeyError:
        return_data = {"code": 2, "response": "invalid json format"}
        return jsonify(return_data)
    db = db_connect()
    cursor = db.cursor()
    query_str = "SELECT * FROM posts WHERE post_id = %d " % (int(post))
    cursor.execute(query_str)
    mypost = cursor.fetchone()
    if mypost:
        if mypost[5]:
            if mypost[1] == 0:
                parent = None
            else:
                parent = mypost[1]
            returnpost = {"date": mypost[6].strftime("%Y-%m-%d %H:%M:%S"), "dislikes": mypost[10],
                          "forum": mypost[9], "id": mypost[0], "isApproved": bool(mypost[2]),
                          "isDeleted": bool(mypost[5]), "isEdited": bool(mypost[3]),
                          "isHighlighted": bool(mypost[13]), "isSpam": bool(mypost[4]),
                          "likes": mypost[11], "message": mypost[7], "parent": parent,
                          "points": (mypost[11] - mypost[10]), "thread": mypost[12], "user": mypost[8]}
            return_data = {"code": 0, "response": returnpost}
            return jsonify(return_data)
        else:
            query_str = "update posts set isDeleted = True WHERE post_id = %d" % (post)
            cursor.execute(query_str)
            db.commit()
            query_str = "update threads set posts = posts - 1 WHERE thread_id = %d" % (mypost[12])
            cursor.execute(query_str)
            db.commit()
            db.close()
            return_data = {"code": 0, "response": {"post": post}}
            return jsonify(return_data)
    else:
        return_data = {"code": 1, "response": "FORUM NOT FOUND"}
        db.close()
        return jsonify(return_data)


@app.route('/db/api/post/restore/', methods=['POST'])
def post_restore():
    try:
        data = request.get_json()
        post = data['post']
    except KeyError:
        return_data = {"code": 2, "response": "invalid json format"}
        return jsonify(return_data)
    db = db_connect()
    cursor = db.cursor()
    query_str = "SELECT * FROM posts WHERE post_id = %d " % (int(post))
    cursor.execute(query_str)
    mypost = cursor.fetchone()
    if mypost:
        if not mypost[5]:
            if mypost[1] == 0:
                parent = None
            else:
                parent = mypost[1]
            returnpost = {"date": mypost[6].strftime("%Y-%m-%d %H:%M:%S"), "dislikes": mypost[10],
                          "forum": mypost[9], "id": mypost[0], "isApproved": bool(mypost[2]),
                          "isDeleted": bool(mypost[5]), "isEdited": bool(mypost[3]),
                          "isHighlighted": bool(mypost[13]), "isSpam": bool(mypost[4]),
                          "likes": mypost[11], "message": mypost[7], "parent": parent,
                          "points": (mypost[11] - mypost[10]), "thread": mypost[12], "user": mypost[8]}
            return_data = {"code": 0, "response": returnpost}
            return jsonify(return_data)
        else:
            query_str = "update posts set isDeleted = False WHERE post_id = %d" % (post)
            cursor.execute(query_str)
            db.commit()
            query_str = "update threads set posts = posts + 1 WHERE thread_id = %d" % (mypost[12])
            cursor.execute(query_str)
            db.commit()
            db.close()
            return_data = {"code": 0, "response": {"post": post}}
            return jsonify(return_data)
    else:
        return_data = {"code": 1, "response": "POST NOT FOUND"}
        db.close()
        return jsonify(return_data)


@app.route('/db/api/post/update/', methods=['POST'])
def post_update():
    try:
        data = request.get_json()
        post = data['post']
        message = data['message']
        db = db_connect()
        cursor = db.cursor()
        query_str = "SELECT * FROM posts WHERE post_id = %d " % (int(post))
        cursor.execute(query_str)
        mypost = cursor.fetchone()
        if mypost:
            if not mypost[7] == message:
                query_str = "update posts set message = '%s' WHERE post_id = %d" % (message, post)
                cursor.execute(query_str)
                db.commit()
                query_str = "update posts set isEdited = True WHERE post_id = %d" % (post)
                cursor.execute(query_str)
                db.commit()
                db.close()
                if mypost[1] == 0:
                    parent = None
                else:
                    parent = mypost[1]
                returnpost = {"date": mypost[6].strftime("%Y-%m-%d %H:%M:%S"), "dislikes": mypost[10],
                              "forum": mypost[9], "id": mypost[0], "isApproved": bool(mypost[2]),
                              "isDeleted": bool(mypost[5]), "isEdited": True,
                              "isHighlighted": bool(mypost[13]), "isSpam": bool(mypost[4]),
                              "likes": mypost[11], "message": message, "parent": parent,
                              "points": (mypost[11] - mypost[10]), "thread": mypost[12], "user": mypost[8]}
                return_data = {"code": 0, "response": returnpost}
                return jsonify(return_data)
            else:
                if mypost[1] == 0:
                    parent = None
                else:
                    parent = mypost[1]
                returnpost = {"date": mypost[6].strftime("%Y-%m-%d %H:%M:%S"), "dislikes": mypost[10],
                              "forum": mypost[9], "id": mypost[0], "isApproved": bool(mypost[2]),
                              "isDeleted": bool(mypost[5]), "isEdited": bool(mypost[3]),
                              "isHighlighted": bool(mypost[13]), "isSpam": bool(mypost[4]),
                              "likes": mypost[11], "message": mypost[7], "parent": parent,
                              "points": (mypost[11] - mypost[10]), "thread": mypost[12], "user": mypost[8]}
                return_data = {"code": 0, "response": returnpost}
                return jsonify(return_data)
        else:
            return_data = {"code": 1, "response": "POST NOT FOUND"}
            db.close()
            return jsonify(return_data)
    except KeyError:
        return_data = {"code": 2, "response": "invalid json format"}
        return jsonify(return_data)


@app.route('/db/api/post/vote/', methods=['POST'])
def post_vote():
    try:
        data = request.get_json()
        vote = data['vote']
        post = data['post']
        db = db_connect()
        cursor = db.cursor()
        query_str = "SELECT * FROM posts WHERE post_id = %d " % (int(post))
        cursor.execute(query_str)
        mypost = cursor.fetchone()
        if mypost:
            if vote == 1:
                query_str = "update posts set likes = likes + 1 WHERE post_id = %d" % (int(post))
                mylikes = mypost[11] + 1
                mydislikes = mypost[10]
            elif vote == -1:
                query_str = "update posts set dislikes = dislikes + 1 WHERE post_id = %d" % (int(post))
                mylikes = mypost[11]
                mydislikes = mypost[10] + 1
            else:
                return_data = {"code": 3, "response": "invalid syntax"}
                return jsonify(return_data)
            cursor.execute(query_str)
            db.commit()
            db.close()
            if mypost[1] == 0:
                parent = None
            else:
                parent = mypost[1]
            returnpost = {"date": mypost[6].strftime("%Y-%m-%d %H:%M:%S"), "dislikes": mydislikes,
                          "forum": mypost[9], "id": mypost[0], "isApproved": bool(mypost[2]),
                          "isDeleted": bool(mypost[5]), "isEdited": bool(mypost[3]),
                          "isHighlighted": bool(mypost[13]), "isSpam": bool(mypost[4]),
                          "likes": mylikes, "message": mypost[7], "parent": parent,
                          "points": (mylikes - mydislikes), "thread": mypost[12], "user": mypost[8]}
            return_data = {"code": 0, "response": returnpost}
            return jsonify(return_data)
        else:
            return_data = {"code": 1, "response": "POST NOT FOUND"}
            db.close()
            return jsonify(return_data)

    except KeyError:
        return_data = {"code": 2, "response": "invalid json format"}
        return jsonify(return_data)


if __name__ == '__main__':
    app.run()
