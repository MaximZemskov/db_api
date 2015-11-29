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
        return_data = {
            "code": code,
            "response": {
                'id': cursor.lastrowid,
                "name": data['name'],
                "short_name": data['short_name'],
                "user": data['user']
            }
        }
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
    if not forum:
        code = 3
        err_msg = "wrong"
        return_data = {"code": code, "response": err_msg}
        return jsonify(return_data)
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
        user_about = {
            "about": user_about_field,
            "email": user_email_field,
            "followers": [x[0] for x in followers_data],
            "following": [x[0] for x in following_data],
            "id": user_id_field,
            "isAnonymous": bool(user_isAnonymous_field),
            "name": user_name_field,
            "subscriptions": [x[0] for x in subscriptions_data],
            "username": user_username_field
        }
    else:
        user_about = forum_data[2]

    code = 0
    return_data = {
        "code": code,
        "response": {
            "id": forum_id_field,
            "name": forum_name_field,
            "short_name": forum_shortname_field,
            "user": user_about
        }
    }
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
    # fetching forum data
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
        forum_info = {
            "id": forum_id_field,
            "name": forum_name_field,
            "short_name": forum_shortname_field,
            "user": forum_user_field
        }
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
            user_info = {
                "about": about,
                "email": user_data[4],
                "followers": [x[0] for x in followers_data],
                "following": [x[0] for x in following_data],
                "id": user_data[0],
                "isAnonymous": bool(user_data[5]),
                "name": name,
                "subscriptions": [x[0] for x in subscriptions_data],
                "username": username
            }
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
            thread_info = {
                "date": thread_data[5].strftime("%Y-%m-%d %H:%M:%S"),
                "dislikes": thread_data[10],
                "forum": thread_data[1],
                "id": thread_data[0], "isClosed": bool(thread_data[3]),
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
            thread_info = post[12]
        if post[1] == 0:
            parent = None
        else:
            parent = post[1]

        return_data = {
            "date": post[6].strftime("%Y-%m-%d %H:%M:%S"),
            "dislikes": post[10],
            "forum": forum_info,
            "id": post[0],
            "isApproved": bool(post[2]),
            "isDeleted": bool(post[5]),
            "isEdited": bool(post[3]),
            "isHighlighted": bool(post[13]),
            "isSpam": bool(post[4]),
            "likes": post[11],
            "message": post[7],
            "parent": parent,
            "points": (post[11] - post[10]),
            "thread": thread_info,
            "user": user_info
        }
        posts_list.append(return_data)
    return jsonify({"code": 0, "response": posts_list})


@app.route('/db/api/forum/listThreads/', methods=['GET'])
def forum_listThreads():
    """Get threads from this forum"""
    # open connection
    db = db_connect()
    cursor = db.cursor()
    # fetching args
    args = fetch_listthreads_forum_args()
    query_stmt = (
                     "SELECT * "
                     "FROM forums "
                     "WHERE short_name = '%s'"
                 ) % args['forum']
    if cursor.execute(query_stmt) == 0:
        code = 1
        err_msg = "forum not found"
        return_data = {"code": code, "response": err_msg}
        return jsonify(return_data)
    forum_data = cursor.fetchone()
    query_stmt = (
                     "SELECT * "
                     "FROM threads "
                     "WHERE forum = '%s' "
                 ) % args['forum']
    if args['since']:
        query_stmt += " AND date >= '%s' " % args['since']
    query_stmt += " ORDER BY  date %s " % args['order']
    if args['limit']:
        query_stmt += " LIMIT %d" % (int(args['limit']))
    cursor.execute(query_stmt)
    threads_data = cursor.fetchall()
    if 'forum' in args['related']:
        forum_info = {
            "id": forum_data[3],
            "name": forum_data[0],
            "short_name": forum_data[1],
            "user": forum_data[2]
        }
    else:
        forum_info = args['forum']
    threads_list = []
    for thread in threads_data:
        if 'user' in args['related']:
            query_stmt = (
                             "SELECT * "
                             "FROM users "
                             "WHERE email = '%s'"
                         ) % (thread[4])
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
            user_info = {
                "about": about,
                "email": user_data[4],
                "followers": [x[0] for x in followers_data],
                "following": [x[0] for x in following_data],
                "id": user_data[0],
                "isAnonymous": bool(user_data[5]),
                "name": name,
                "subscriptions": [x[0] for x in subscriptions_data],
                "username": username
            }
        else:
            user_info = thread[4]

        return_data = {
            "date": thread[5].strftime("%Y-%m-%d %H:%M:%S"),
            "dislikes": thread[10],
            "forum": forum_info,
            "id": thread[0],
            "isClosed": bool(thread[3]),
            "isDeleted": bool(thread[8]),
            "likes": thread[9],
            "message": thread[6],
            "points": (thread[9] - thread[10]),
            "posts": thread[11],
            "slug": thread[7],
            "title": thread[2], "user": user_info
        }
        threads_list.append(return_data)
    return jsonify({"code": 0, "response": threads_list})


@app.route('/db/api/forum/listUsers/', methods=['GET'])
def forum_listUsers():
    """Get user with posts on this forum"""
    args = fetch_listusers_forum_args()
    db = db_connect()
    cursor = db.cursor()
    query_stmt = (
                     "SELECT * "
                     "FROM forums "
                     "WHERE short_name = '%s'"
                 ) % args['forum']
    if cursor.execute(query_stmt) == 0:
        code = 1
        err_msg = "forum not found"
        return_data = {"code": code, "response": err_msg}
        return jsonify(return_data)
    query_stmt = (
                     "SELECT DISTINCT email ,user_id, username, about,name, isAnonymous, IF(name = 'None', 0, 1) AS qwer "
                     "FROM posts INNER JOIN users "
                     "on posts.user = users.email "
                     "WHERE forum = '%s' "
                 ) % args['forum']
    if args['since']:
        query_stmt += " AND user_id >= %d " % (int(args['since']))
    query_stmt += " ORDER BY qwer %s, name %s " % (args['order'], args['order'])
    if args['limit']:
        query_stmt += " LIMIT %d" % (int(args['limit']))
    cursor.execute(query_stmt)
    users_data = cursor.fetchall()
    users_list = []
    for user in users_data:
        if user[2] == 'None':
            username = None
        else:
            username = user[2]
        if user[3] == 'None':
            about = None
        else:
            about = user[3]
        if user[4] == 'None':
            name = None
        else:
            name = user[4]
        query_stmt = (
                         "SELECT who_user "
                         "FROM followers "
                         "WHERE whom_user = '%s'"
                     ) % (user[0])
        cursor.execute(query_stmt)
        followers_data = cursor.fetchall()
        query_stmt = (
                         "SELECT whom_user "
                         "FROM followers "
                         "WHERE who_user = '%s'"
                     ) % (user[0])
        cursor.execute(query_stmt)
        following_data = cursor.fetchall()
        query_stmt = (
                         "SELECT thread_id "
                         "FROM subscriptions "
                         "WHERE user = '%s'"
                     ) % (user[0])
        cursor.execute(query_stmt)
        subscriptions_data = cursor.fetchall()
        user_info = {
            "about": about,
            "email": user[0],
            "followers": [x[0] for x in followers_data],
            "following": [x[0] for x in following_data],
            "id": user[1],
            "isAnonymous": bool(user[5]),
            "name": name,
            "subscriptions": [x[0] for x in subscriptions_data],
            "username": username
        }
        users_list.append(user_info)
    return jsonify({"code": 0, "response": users_list})


# POST


@app.route('/db/api/post/create/', methods=['POST'])
def post_create():
    """Create new post"""
    try:
        db = db_connect()
        cursor = db.cursor()
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
        query_str = (
                        "INSERT INTO posts (parent, isApproved, isEdited, isSpam, isDeleted, date, message, "
                        "user, forum, thread, isHighlited) "
                        "VALUES (%d, %d, %d, %d, %d, '%s', '%s', '%s', '%s', %d, %d)"
                    ) % (parent, isApproved, isEdit, isSpam, isDeleted, date, message,
                         user, forum, thread, isHighlighted)
        cursor.execute(query_str)
        if parent == 0:
            parent = None
        code = 0
        return_data = {
            "code": code,
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
        query_str = (
                        "UPDATE threads "
                        "SET posts = posts + 1 "
                        "WHERE thread_id = %d"
                    ) % thread
        cursor.execute(query_str)
        db.commit()
        db.close()
        return jsonify(return_data)
    except KeyError:
        code = 2
        err_msg = "invalid format"
        return_data = {"code": code, "response": err_msg}
        return jsonify(return_data)


@app.route('/db/api/post/details/', methods=['GET'])
def post_details():
    """Get post details"""
    db = db_connect()
    cursor = db.cursor()
    post = request.args.get('post', '')
    related = request.args.getlist('related')
    query_stmt = (
                     "SELECT * "
                     "FROM posts "
                     "WHERE post_id = '%s'"
                 ) % post
    if cursor.execute(query_stmt) == 0:
        code = 1
        err_msg = "not found"
        return_data = {"code": code, "response": err_msg}
        return jsonify(return_data)
    post_data = cursor.fetchone()
    if 'user' in related:
        query_stmt = (
                         "SELECT * "
                         "FROM users "
                         "WHERE email = '%s'"
                     ) % (post_data[8])
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
        subscriptions = cursor.fetchall()
        user_info = {
            "about": about,
            "email": user_data[4],
            "followers": [x[0] for x in followers_data],
            "following": [x[0] for x in following_data],
            "id": user_data[0],
            "isAnonymous": bool(user_data[5]),
            "name": name,
            "subscriptions": [x[0] for x in subscriptions],
            "username": username
        }
    else:
        user_info = post_data[8]

    if 'forum' in related:
        query_stmt = (
                         "SELECT * "
                         "FROM forums "
                         "WHERE short_name = '%s'"
                     ) % (post_data[9])
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
        query_stmt = (
                         "SELECT * "
                         "FROM threads "
                         "WHERE thread_id = '%s'"
                     ) % (post_data[12])
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
            "user": thread_data[4]}
    else:
        thread_info = post_data[12]
    if post_data[1] == 0:
        parent = None
    else:
        parent = post_data[1]
    code = 0
    return_data = {
        "code": code,
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
            "thread": thread_info, "user": user_info
        }
    }
    return jsonify(return_data)


@app.route('/db/api/post/list/', methods=['GET'])
def post_list():
    """List posts"""
    db = db_connect()
    cursor = db.cursor()
    thread = request.args.get('thread', False)
    forum = request.args.get('forum', False)
    limit = request.args.get('limit', False)
    since = request.args.get('since', False)
    order = request.args.get('order', False)
    if thread and forum:
        code = 3
        err_msg = "wrong request"
        return_data = {"code": code, "response": err_msg}
        return jsonify(return_data)
    query_stmt = (
        "SELECT * "
        "FROM posts "
        "WHERE "
    )
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
    posts_data = cursor.fetchall()

    post_response = []

    for post in posts_data:
        if post[1] == 0:
            parent = None
        else:
            parent = post[1]
        post_response.append({
            "date": post[6].strftime("%Y-%m-%d %H:%M:%S"),
            "dislikes": post[10],
            "forum": post[9],
            "id": post[0],
            "isApproved": bool(post[2]),
            "isDeleted": bool(post[5]),
            "isEdited": bool(post[3]),
            "isHighlighted": bool(post[13]),
            "isSpam": bool(post[4]),
            "likes": post[11],
            "message": post[7],
            "parent": parent,
            "points": (post[11] - post[10]),
            "thread": post[12], "user": post[8]
        })
    code = 0
    return_data = {"code": code, "response": post_response}
    return jsonify(return_data)


@app.route('/db/api/post/remove/', methods=['POST'])
def post_remove():
    """Mark post as removed"""
    db = db_connect()
    cursor = db.cursor()
    try:
        data = request.get_json()
        post = data['post']
    except KeyError:
        code = 2
        err_msg = "invalid format"
        return_data = {"code": code, "response": err_msg}
        return jsonify(return_data)
    query_stmt = (
                     "SELECT * "
                     "FROM posts "
                     "WHERE post_id = %d "
                 ) % (int(post))
    cursor.execute(query_stmt)
    post_data = cursor.fetchone()
    if post_data:
        if post_data[5]:
            if post_data[1] == 0:
                parent = None
            else:
                parent = post_data[1]
            post_response = {
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
            code = 0
            return_data = {"code": code, "response": post_response}
            return jsonify(return_data)
        else:
            query_stmt = (
                             "UPDATE posts "
                             "SET isDeleted = True "
                             "WHERE post_id = %d"
                         ) % post
            cursor.execute(query_stmt)
            db.commit()
            query_stmt = (
                             "UPDATE threads "
                             "SET posts = posts - 1 "
                             "WHERE thread_id = %d"
                         ) % (post_data[12])
            cursor.execute(query_stmt)
            db.commit()
            db.close()
            code = 0
            return_data = {"code": code, "response": {"post": post}}
            return jsonify(return_data)
    else:
        code = 1
        err_msg = "forum not found"
        return_data = {"code": code, "response": err_msg}
        db.close()
        return jsonify(return_data)


@app.route('/db/api/post/restore/', methods=['POST'])
def post_restore():
    """Cancel removal"""
    db = db_connect()
    cursor = db.cursor()
    try:
        data = request.get_json()
        post = data['post']
    except KeyError:
        code = 2
        err_msg = "invalid format"
        return_data = {"code": code, "response": err_msg}
        return jsonify(return_data)
    query_stmt = (
                     "SELECT * "
                     "FROM posts "
                     "WHERE post_id = %d "
                 ) % (int(post))
    cursor.execute(query_stmt)
    post_data = cursor.fetchone()
    if post_data:
        if not post_data[5]:
            if post_data[1] == 0:
                parent = None
            else:
                parent = post_data[1]
            response_post = {
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
            code = 0
            return_data = {"code": code, "response": response_post}
            return jsonify(return_data)
        else:
            query_stmt = (
                             "UPDATE posts "
                             "SET isDeleted = False "
                             "WHERE post_id = %d"
                         ) % post
            cursor.execute(query_stmt)
            db.commit()
            query_stmt = (
                             "UPDATE threads "
                             "SET posts = posts + 1 "
                             "WHERE thread_id = %d"
                         ) % (post_data[12])
            cursor.execute(query_stmt)
            db.commit()
            db.close()
            code = 0
            return_data = {
                "code": code,
                "response": {
                    "post": post
                }
            }
            return jsonify(return_data)
    else:
        code = 1
        err_msg = "not found"
        return_data = {"code": code, "response": err_msg}
        db.close()
        return jsonify(return_data)


@app.route('/db/api/post/update/', methods=['POST'])
def post_update():
    """Edit post"""
    try:
        db = db_connect()
        cursor = db.cursor()
        data = request.get_json()
        post = data['post']
        message = data['message']
        query_stmt = (
                         "SELECT * "
                         "FROM posts "
                         "WHERE post_id = %d "
                     ) % (int(post))
        cursor.execute(query_stmt)
        post_data = cursor.fetchone()
        if post_data:
            if not post_data[7] == message:
                query_stmt = (
                                 "UPDATE posts "
                                 "SET message = '%s' "
                                 "WHERE post_id = %d"
                             ) % (message, post)
                cursor.execute(query_stmt)
                db.commit()
                query_stmt = (
                                 "UPDATE posts "
                                 "SET isEdited = True "
                                 "WHERE post_id = %d"
                             ) % post
                cursor.execute(query_stmt)
                db.commit()
                db.close()
                if post_data[1] == 0:
                    parent = None
                else:
                    parent = post_data[1]
                post_response = {
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
                code = 0
                return_data = {"code": code, "response": post_response}
                return jsonify(return_data)
            else:
                if post_data[1] == 0:
                    parent = None
                else:
                    parent = post_data[1]
                post_response = {
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
                code = 0
                return_data = {"code": code, "response": post_response}
                return jsonify(return_data)
        else:
            code = 1
            err_msg = "not found"
            return_data = {"code": code, "response": err_msg}
            db.close()
            return jsonify(return_data)
    except KeyError:
        code = 2
        err_msg = "invalid format"
        return_data = {"code": code, "response": err_msg}
        return jsonify(return_data)


@app.route('/db/api/post/vote/', methods=['POST'])
def post_vote():
    """like/dislike post"""
    try:
        db = db_connect()
        cursor = db.cursor()
        data = request.get_json()
        vote = data['vote']
        post = data['post']
        query_stmt = (
                         "SELECT * "
                         "FROM posts "
                         "WHERE post_id = %d "
                     ) % (int(post))
        cursor.execute(query_stmt)
        post_data = cursor.fetchone()
        if post_data:
            if vote == 1:
                query_stmt = (
                                 "UPDATE posts "
                                 "SET likes = likes + 1 "
                                 "WHERE post_id = %d"
                             ) % (int(post))
                likes = post_data[11] + 1
                dislikes = post_data[10]
            elif vote == -1:
                query_stmt = (
                                 "UPDATE posts "
                                 "SET dislikes = dislikes + 1 "
                                 "WHERE post_id = %d"
                             ) % (int(post))
                likes = post_data[11]
                dislikes = post_data[10] + 1
            else:
                code = 3
                err_msg = "invalid request"
                return_data = {"code": code, "response": err_msg}
                return jsonify(return_data)
            cursor.execute(query_stmt)
            db.commit()
            db.close()
            if post_data[1] == 0:
                parent = None
            else:
                parent = post_data[1]
            response_post = {
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
            code = 0
            return_data = {"code": code, "response": response_post}
            return jsonify(return_data)
        else:
            code = 1
            err_msg = "not found"
            return_data = {"code": code, "response": err_msg}
            db.close()
            return jsonify(return_data)
    except KeyError:
        code = 2
        err_msg = "invalid format"
        return_data = {"code": code, "response": err_msg}
        return jsonify(return_data)


# USERS
@app.route('/db/api/user/create/', methods=['POST'])
def user_create():
    """Create new user"""
    try:
        db = db_connect()
        cursor = db.cursor()
        # get request data
        data = request.get_json()
        about = data['about']
        email = data['email']
        username = data['username']
        name = data['name']
        isAnonymous = data.get('isAnonymous', False)
        query_stmt = (
                         "INSERT INTO users (username, about, name, email, isAnonymous) "
                         "VALUES ('%s','%s','%s','%s',%d)"
                     ) % (username, about, name, email, isAnonymous)
        cursor.execute(query_stmt)
        code = 0
        return_data = {
            "code": code, "response": {
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
        return jsonify(return_data)
    except IntegrityError, e:
        if e[0] == 1062:
            code = 5
            err_msg = "user exist"
            return_data = {"code": code, "response": err_msg}
            return jsonify(return_data)
    except KeyError:
        code = 2
        err_msg = "invalid request"
        return_data = {"code": code, "response": err_msg}
        return jsonify(return_data)


@app.route('/db/api/user/details/', methods=['GET'])
def user_details():
    """Get user details"""
    db = db_connect()
    cursor = db.cursor()
    # fetch args
    user = request.args.get('user', '')
    query_stmt = (
                     "SELECT * "
                     "FROM users "
                     "WHERE email = '%s'"
                 ) % user
    if cursor.execute(query_stmt) == 0:
        return_data = {"code": 1, "response": "USER NOT FOUND"}
        return jsonify(return_data)
    else:
        user_data = cursor.fetchone()
        if user_data[1] == 'None':
            users_username_field = None
        else:
            users_username_field = user_data[1]
        if user_data[2] == 'None':
            users_about_field = None
        else:
            users_about_field = user_data[2]
        if user_data[3] == 'None':
            users_name_field = None
        else:
            users_name_field = user_data[3]

        users_email_field = user_data[4]
        users_isAnonymous_field = user_data[5]
        query_stmt = (
                         "SELECT who_user "
                         "FROM followers "
                         "WHERE whom_user = '%s'"
                     ) % users_email_field
        cursor.execute(query_stmt)
        followers_data = cursor.fetchall()
        query_stmt = (
                         "SELECT whom_user "
                         "FROM followers "
                         "WHERE who_user = '%s'"
                     ) % users_email_field
        cursor.execute(query_stmt)
        following_data = cursor.fetchall()
        query_stmt = (
                         "SELECT thread_id "
                         "FROM subscriptions "
                         "WHERE user = '%s'"
                     ) % users_email_field
        cursor.execute(query_stmt)
        subscriptions_data = cursor.fetchall()

        user_info = {
            "about": users_about_field,
            "email": users_email_field,
            "followers": [x[0] for x in followers_data],
            "following": [x[0] for x in following_data],
            "id": user_data[0],
            "isAnonymous": bool(users_isAnonymous_field),
            "name": users_name_field,
            "subscriptions": [x[0] for x in subscriptions_data],
            "username": users_username_field
        }
        code = 0
        return_data = {"code": code, "response": user_info}
        return jsonify(return_data)


@app.route('/db/api/user/follow/', methods=['POST'])
def user_follow():
    """Mark one user as folowing other user"""
    try:
        data = request.get_json()
        follower = data['follower']  # who
        followee = data['followee']  # whom
        # if followee == follower:
        #     return_data = {"code": 3, "response": "WTF!"}
        #     return jsonify(return_data)
        db = db_connect()
        cursor = db.cursor()
        query_stmt = (
                         "SELECT * "
                         "FROM users "
                         "WHERE email = '%s' "
                     ) % followee
        cursor.execute(query_stmt)
        user_whom_data = cursor.fetchone()
        if user_whom_data:
            query_stmt = (
                             "SELECT * "
                             "FROM followers "
                             "WHERE who_user = '%s' AND whom_user = '%s'"
                         ) % (follower, followee)
            cursor.execute(query_stmt)
            if not cursor.fetchone():
                query_stmt = (
                                 "SELECT * "
                                 "FROM users "
                                 "WHERE email = '%s' "
                             ) % follower
                cursor.execute(query_stmt)
                user_data = cursor.fetchone()
                if user_data:
                    query_stmt = (
                                     "INSERT INTO followers (who_user, whom_user) "
                                     "VALUES ('%s', '%s')"
                                 ) % (follower, followee)
                    cursor.execute(query_stmt)
                    db.commit()
                    query_stmt = (
                                     "SELECT who_user "
                                     "FROM followers "
                                     "WHERE whom_user = '%s'"
                                 ) % (user_data[4])
                    cursor.execute(query_stmt)
                    followers_data = cursor.fetchall()
                    query_stmt = (
                                     "SELECT whom_user "
                                     "FROM followers WHERE "
                                     "who_user = '%s'"
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

                    user_info = {
                        "about": about,
                        "email": user_data[4],
                        "followers": [x[0] for x in followers_data],
                        "following": [x[0] for x in following_data],
                        "id": user_data[0],
                        "isAnonymous": bool(user_data[5]),
                        "name": name,
                        "subscriptions": [x[0] for x in subscriptions_data],
                        "username": username
                    }
                    code = 0
                    return_data = {"code": code, "response": user_info}
                    return jsonify(return_data)
                else:
                    code = 1
                    err_msg = "not found"
                    return_data = {"code": code, "response": err_msg}
                    db.close()
                    return jsonify(return_data)
            else:
                query_stmt = (
                                 "SELECT * "
                                 "FROM users "
                                 "WHERE email = '%s' "
                             ) % follower
                cursor.execute(query_stmt)
                user_data = cursor.fetchone()
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

                user_info = {
                    "about": about,
                    "email": user_data[4],
                    "followers": [x[0] for x in followers_data],
                    "following": [x[0] for x in following_data],
                    "id": user_data[0],
                    "isAnonymous": bool(user_data[5]),
                    "name": name,
                    "subscriptions": [x[0] for x in subscriptions_data],
                    "username": username
                }
                code = 0
                return_data = {"code": code, "response": user_info}
                return jsonify(return_data)

        else:
            code = 1
            err_msg = "not found"
            return_data = {"code": code, "response": err_msg}
            db.close()
            return jsonify(return_data)
    except KeyError:
        code = 2
        err_msg = "invalid"
        return_data = {"code": code, "response": err_msg}
        return jsonify(return_data)


@app.route('/db/api/user/listFollowers/', methods=['GET'])
def user_listFollowers():
    """Get followers of this user"""
    db = db_connect()
    cursor = db.cursor()
    args = fetch_args_user_followers()
    # if not args['user']:
    #     return_data = {"code": 3, "response": "bad syntax"}
    #     return jsonify(return_data)
    query_stmt = (
                     "SELECT * "
                     "FROM users "
                     "WHERE email = '%s'"
                 ) % args['user']
    cursor.execute(query_stmt)
    user = cursor.fetchone()
    if user:

        query_stmt = (
                         "SELECT * "
                         "FROM users INNER JOIN followers "
                         "ON users.email = followers.who_user "
                         "WHERE whom_user = '%s' "
                     ) % args['user']
        if args['since_id']:
            query_stmt += " AND user_id >= %d " % (int(args['since_id']))
        query_stmt += " ORDER BY name %s" % args['order']
        if args['limit']:
            query_stmt += " LIMIT %d" % (int(args['limit']))
        cursor.execute(query_stmt)
        followers_data = cursor.fetchall()
        followers_list = []
        for user in followers_data:
            query_stmt = (
                             "SELECT who_user "
                             "FROM followers "
                             "WHERE whom_user = '%s'"
                         ) % (user[4])
            cursor.execute(query_stmt)
            followers_data = cursor.fetchall()
            query_stmt = (
                             "SELECT whom_user "
                             "FROM followers "
                             "WHERE who_user = '%s'"
                         ) % (user[4])
            cursor.execute(query_stmt)
            following_data = cursor.fetchall()
            query_stmt = (
                             "SELECT thread_id "
                             "FROM subscriptions "
                             "WHERE user = '%s'"
                         ) % (user[4])
            cursor.execute(query_stmt)
            subscriptions_data = cursor.fetchall()
            if user[1] == 'None':
                username = None
            else:
                username = user[1]
            if user[2] == 'None':
                about = None
            else:
                about = user[2]
            if user[3] == 'None':
                name = None
            else:
                name = user[3]

            user_info = {
                "about": about,
                "email": user[4],
                "followers": [x[0] for x in followers_data],
                "following": [x[0] for x in following_data],
                "id": user[0],
                "isAnonymous": bool(user[5]),
                "name": name,
                "subscriptions": [x[0] for x in subscriptions_data],
                "username": username
            }

            followers_list.append(user_info)

        code = 0
        return_data = {"code": code, "response": followers_list}
        return jsonify(return_data)
    else:
        code = 1
        err_msg = "not found"
        return_data = {"code": code, "response": err_msg}
        db.close()
        return jsonify(return_data)


@app.route('/db/api/user/listFollowing/', methods=['GET'])
def user_listFollowing():
    """Get followees of this user"""
    db = db_connect()
    cursor = db.cursor()
    args = fetch_args_user_followers()
    # if not user:
    #     return_data = {"code": 3, "response": "bad syntax"}
    #     return jsonify(return_data)
    query_stmt = (
                     "SELECT * "
                     "FROM users "
                     "WHERE email = '%s'"
                 ) % args['user']
    cursor.execute(query_stmt)
    user_data = cursor.fetchone()
    if user_data:
        query_stmt = (
                         "SELECT * "
                         "FROM users INNER JOIN followers "
                         "ON users.email = followers.whom_user "
                         "WHERE who_user = '%s' "
                     ) % args['user']
        if args['since_id']:
            query_stmt += " AND user_id >= %d " % (int(args['since_id']))
        query_stmt += " ORDER BY name %s" % args['order']
        if args['limit']:
            query_stmt += " LIMIT %d" % (int(args['limit']))
        cursor.execute(query_stmt)
        all_following = cursor.fetchall()
        following_list = []
        for user_data in all_following:
            query_stmt = (
                             "SELECT who_user "
                             "FROM followers "
                             "WHERE whom_user = '%s'"
                         ) % user_data[4]
            cursor.execute(query_stmt)
            followers_data = cursor.fetchall()
            query_stmt = (
                             "SELECT whom_user "
                             "FROM followers "
                             "WHERE who_user = '%s'"
                         ) % user_data[4]
            cursor.execute(query_stmt)
            following_data = cursor.fetchall()
            query_stmt = (
                             "SELECT thread_id "
                             "FROM subscriptions "
                             "WHERE user = '%s'"
                         ) % user_data[4]
            cursor.execute(query_stmt)
            subscriptions_data = cursor.fetchall()
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

            user_info = {
                "about": about,
                "email": user_data[4],
                "followers": [x[0] for x in followers_data],
                "following": [x[0] for x in following_data],
                "id": user_data[0],
                "isAnonymous": bool(user_data[5]),
                "name": name,
                "subscriptions": [x[0] for x in subscriptions_data],
                "username": username
            }

            following_list.append(user_info)

        code = 0
        return_data = {"code": code, "response": following_list}
        return jsonify(return_data)
    else:
        code = 1
        err_msg = "not found"
        return_data = {"code": code, "response": err_msg}
        db.close()
        return jsonify(return_data)


@app.route('/db/api/user/listPosts/', methods=['GET'])
def user_listPosts():
    """Get user details"""
    db = db_connect()
    cursor = db.cursor()
    args = fetch_args_user()
    if not args['user']:
        code = 3
        err_msg = "bad shit"
        return_data = {"code": code, "response": err_msg}
        return jsonify(return_data)
    query_stmt = (
                     "SELECT * "
                     "FROM users "
                     "WHERE email = '%s'"
                 ) % args['user']
    cursor.execute(query_stmt)
    user_data = cursor.fetchone()
    if user_data:
        query_stmt = (
                         "SELECT * "
                         "FROM posts "
                         "WHERE user = '%s'"
                     ) % args['user']
        if args['since']:
            query_stmt += " AND date >= '%s' " % args['since']
        query_stmt += " ORDER BY date %s " % args['order']
        if args['limit']:
            query_stmt += " LIMIT %d" % (int(args['limit']))
        cursor.execute(query_stmt)
        posts_data = cursor.fetchall()
        posts_list = []
        for post in posts_data:
            if post[1] == 0:
                parent = None
            else:
                parent = post[1]
            posts_list.append({
                "date": post[6].strftime("%Y-%m-%d %H:%M:%S"),
                "dislikes": post[10],
                "forum": post[9],
                "id": post[0],
                "isApproved": bool(post[2]),
                "isDeleted": bool(post[5]),
                "isEdited": bool(post[3]),
                "isHighlighted": bool(post[13]),
                "isSpam": bool(post[4]),
                "likes": post[11],
                "message": post[7],
                "parent": parent,
                "points": (post[11] - post[10]),
                "thread": post[12],
                "user": post[8]
            })
        code = 0
        return_data = {"code": code, "response": posts_list}
        return jsonify(return_data)

    else:
        code = 1
        err_msg = "not found"
        return_data = {"code": code, "response": err_msg}
        return jsonify(return_data)


@app.route('/db/api/user/unfollow/', methods=['POST'])
def user_unfollow():
    """Mark one user as not folowing other user anymore"""
    try:
        db = db_connect()
        cursor = db.cursor()
        data = request.get_json()
        follower = data['follower']  # who
        followee = data['followee']  # whom
        # if followee == follower:
        #     return_data = {"code": 3, "response": "WTF!"}
        #     return jsonify(return_data)
        query_stmt = (
                         "SELECT * "
                         "FROM users "
                         "WHERE email = '%s' "
                     ) % followee
        cursor.execute(query_stmt)
        user_whom = cursor.fetchone()
        if user_whom:
            query_stmt = (
                             "SELECT * "
                             "FROM followers "
                             "WHERE who_user = '%s' "
                             "AND whom_user = '%s'"
                         ) % (follower, followee)
            cursor.execute(query_stmt)
            if cursor.fetchone():
                query_stmt = (
                                 "SELECT * "
                                 "FROM users "
                                 "WHERE email = '%s' "
                             ) % follower
                cursor.execute(query_stmt)
                user_data = cursor.fetchone()
                if user_data:
                    query_stmt = (
                                     "DELETE "
                                     "FROM followers "
                                     "WHERE who_user = '%s' AND whom_user = '%s'"
                                 ) % (follower, followee)
                    cursor.execute(query_stmt)
                    db.commit()
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
                                 ) % user_data[4]
                    cursor.execute(query_stmt)
                    following_data = cursor.fetchall()
                    query_stmt = (
                                     "SELECT thread_id "
                                     "FROM subscriptions "
                                     "WHERE user = '%s'"
                                 ) % user_data[4]
                    cursor.execute(query_stmt)
                    subscriptions_data = cursor.fetchall()
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

                    user_info = {
                        "about": about,
                        "email": user_data[4],
                        "followers": [x[0] for x in followers_data],
                        "following": [x[0] for x in following_data],
                        "id": user_data[0],
                        "isAnonymous": bool(user_data[5]),
                        "name": name,
                        "subscriptions": [x[0] for x in subscriptions_data],
                        "username": username
                    }
                    code = 1
                    return_data = {"code": code, "response": user_info}
                    return jsonify(return_data)
                else:
                    code = 1
                    err_msg = "not found"
                    return_data = {"code": code, "response": err_msg}
                    db.close()
                    return jsonify(return_data)
            else:
                query_stmt = (
                                 "SELECT * "
                                 "FROM users "
                                 "WHERE email = '%s' "
                             ) % follower
                cursor.execute(query_stmt)
                user_data = cursor.fetchone()
                query_stmt = (
                                 "SELECT who_user "
                                 "FROM followers "
                                 "WHERE whom_user = '%s'"
                             ) % user_data[4]
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

                user_info = {
                    "about": about,
                    "email": user_data[4],
                    "followers": [x[0] for x in followers_data],
                    "following": [x[0] for x in following_data],
                    "id": user_data[0],
                    "isAnonymous": bool(user_data[5]),
                    "name": name,
                    "subscriptions": [x[0] for x in subscriptions_data],
                    "username": username
                }
                code = 0
                return_data = {"code": code, "response": user_info}
                return jsonify(return_data)

        else:
            code = 1
            err_msg = "not found"
            return_data = {"code": code, "response": err_msg}
            db.close()
            return jsonify(return_data)
    except KeyError:
        code = 2
        err_msg = "invalid"
        return_data = {"code": code, "response": err_msg}
        return jsonify(return_data)


@app.route('/db/api/user/updateProfile/', methods=['POST'])
def user_updateProfile():
    """Update profile"""
    try:
        db = db_connect()
        cursor = db.cursor()
        data = request.get_json()
        about = data['about']  # user info
        user = data['user']  # user email
        name = data['name']  # user name
        query_stmt = (
                         "SELECT * "
                         "FROM users "
                         "WHERE email = '%s' "
                     ) % user
        cursor.execute(query_stmt)
        user_data = cursor.fetchone()
        if user_data:
            if (user_data[2] != about) or (user_data[3] != name):
                query_stmt = (
                                 "UPDATE users "
                                 "SET about = '%s' "
                                 "WHERE email = '%s'"
                             ) % (about, user)
                cursor.execute(query_stmt)
                query_stmt = (
                                 "UPDATE users "
                                 "SET name = '%s' "
                                 "WHERE email = '%s'"
                             ) % (name, user)
                cursor.execute(query_stmt)
                db.commit()
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
                    "followers": [x[0] for x in followers_data],
                    "following": [x[0] for x in following_data],
                    "id": user_data[0],
                    "isAnonymous": bool(user_data[5]),
                    "name": name,
                    "subscriptions": [x[0] for x in subscriptions_data],
                    "username": username
                }
                return_data = {"code": 0, "response": user_info}
                return jsonify(return_data)
            else:
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

                user_info = {
                    "about": about,
                    "email": user_data[4],
                    "followers": [x[0] for x in followers_data],
                    "following": [x[0] for x in following_data],
                    "id": user_data[0],
                    "isAnonymous": bool(user_data[5]),
                    "name": name,
                    "subscriptions": [x[0] for x in subscriptions_data],
                    "username": username}
                return_data = {"code": 0, "response": user_info}
                return jsonify(return_data)
        else:
            code = 1
            err_msg = "not found"
            return_data = {"code": code, "response": err_msg}
            db.close()
            return jsonify(return_data)
    except KeyError:
        code = 2
        err_msg = "invalid"
        return_data = {"code": code, "response": err_msg}
        return jsonify(return_data)


# THREADS
@app.route('/db/api/thread/create/', methods=['POST'])
def thread_create():
    """Create new thread"""
    try:
        db = db_connect()
        cursor = db.cursor()
        data = request.get_json()
        forum = data['forum']
        title = data['title']
        isClosed = data['isClosed']
        user = data['user']
        date = data['date']
        message = data['message']
        slug = data['slug']
        isDeleted = data.get('isDeleted', False)
        query_str = (
                        "INSERT INTO threads (forum, title, isClosed, user, date, message,slug, isDeleted) "
                        "VALUES ('%s', '%s', %d, '%s', '%s', '%s', '%s', %d)"
                    ) % (forum, title, isClosed, user, date, message, slug, isDeleted)
        cursor.execute(query_str)
        db.commit()
        db.close()
        return_data = {
            'code': 0, 'response': {
                'date': date,
                'forum': forum,
                'id': cursor.lastrowid,
                'isClosed': isClosed,
                'isDeleted': isDeleted,
                'message': message,
                'slug': slug, 'title': title, 'user': user}}
        return jsonify(return_data)
    except KeyError:
        code = 2
        err_msg = "invalid"
        return_data = {"code": code, "response": err_msg}
        return jsonify(return_data)


@app.route('/db/api/thread/details/', methods=['GET'])
def thread_details():
    """Get thread details"""
    db = db_connect()
    cursor = db.cursor()
    thread = request.args.get('thread', '')
    related = request.args.getlist('related')
    query_str = (
                    "SELECT * "
                    "FROM threads "
                    "WHERE thread_id = '%s'"
                ) % thread
    if cursor.execute(query_str) == 0:
        code = 1
        err_msg = "not found"
        return_data = {"code": code, "response": err_msg}
        return jsonify(return_data)
    thread_data = cursor.fetchone()
    if 'user' in related:
        query_str = (
                        "SELECT * "
                        "FROM users "
                        "WHERE email = '%s'"
                    ) % thread_data[4]
        related.remove('user')
        cursor.execute(query_str)
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
        query_str = (
                        "SELECT who_user "
                        "FROM followers "
                        "WHERE whom_user = '%s'"
                    ) % user_data[4]
        cursor.execute(query_str)
        followers_data = cursor.fetchall()
        query_str = (
                        "SELECT whom_user "
                        "FROM followers "
                        "WHERE who_user = '%s'"
                    ) % user_data[4]
        cursor.execute(query_str)
        following_data = cursor.fetchall()
        query_str = (
                        "SELECT thread_id "
                        "FROM subscriptions "
                        "WHERE user = '%s'"
                    ) % user_data[4]
        cursor.execute(query_str)
        subscriptions_data = cursor.fetchall()
        user_info = {
            "about": about,
            "email": user_data[4],
            "followers": [x[0] for x in followers_data],
            "following": [x[0] for x in following_data],
            "id": user_data[0],
            "isAnonymous": bool(user_data[5]),
            "name": name,
            "subscriptions": [x[0] for x in subscriptions_data],
            "username": username
        }
    else:
        user_info = thread_data[4]
    if 'forum' in related:
        related.remove('forum')
        query_str = (
                        "SELECT * "
                        "FROM forums "
                        "WHERE short_name = '%s'"
                    ) % (thread_data[1])
        cursor.execute(query_str)
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
        code = 3
        err_msg = "invalid syntax"
        return_data = {"code": code, "response": err_msg}
        return jsonify(return_data)
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
    return jsonify(return_data)


@app.route("/db/api/thread/list/", methods=["GET"])
def thread_list():
    """List threads"""
    db = db_connect()
    cursor = db.cursor()
    user = request.args.get('user', False)
    forum = request.args.get('forum', False)
    limit = request.args.get('limit', False)
    since = request.args.get('since', False)
    order = request.args.get('order', False)
    if user and forum:
        code = 3
        err_msg = "wrong request"
        return_data = {"code": code, "response": err_msg}
        return jsonify(return_data)
    query_stmt = (
        "SELECT * "
        "FROM threads "
        "WHERE "
    )
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

    threads_list = []

    for thread in threads:
        threads_list.append({
            "date": thread[5].strftime("%Y-%m-%d %H:%M:%S"),
            "dislikes": thread[10],
            "forum": thread[1],
            "id": thread[0],
            "isClosed": bool(thread[3]),
            "isDeleted": bool(thread[8]),
            "likes": thread[9],
            "message": thread[6],
            "points": (thread[9] - thread[10]),
            "posts": thread[11],
            "slug": thread[7],
            "title": thread[2],
            "user": thread[4]
        })
    code = 0
    return_data = {"code": code, "response": threads_list}
    return jsonify(return_data)


@app.route('/db/api/thread/listPosts/', methods=['GET'])
def thread_listPost():
    """Get posts from this thread"""
    db = db_connect()
    cursor = db.cursor()
    thread = request.args.get('thread', False)
    limit = request.args.get('limit', False)
    since = request.args.get('since', False)
    order = request.args.get('order', 'desc')
    if not thread:
        code = 3
        err_msg = "wrong request"
        return_data = {"code": code, "response": err_msg}
        return jsonify(return_data)
    query_stmt = (
                     "SELECT * "
                     "FROM threads "
                     "WHERE thread_id = %d"
                 ) % (int(thread))
    cursor.execute(query_stmt)
    thread_data = cursor.fetchone()
    if thread_data:
        query_stmt = (
                         "SELECT * "
                         "FROM posts "
                         "WHERE thread = %d"
                     ) % (int(thread))
        if since:
            query_stmt += " AND date >= '%s' " % since
        query_stmt += " ORDER BY date %s " % order
        if limit:
            query_stmt += " LIMIT %d" % (int(limit))
        cursor.execute(query_stmt)
        posts_data = cursor.fetchall()
        post_list = []

        for post in posts_data:
            if post[1] == 0:
                parent = None
            else:
                parent = post[1]
            post_list.append({
                "date": post[6].strftime("%Y-%m-%d %H:%M:%S"),
                "dislikes": post[10],
                "forum": post[9],
                "id": post[0],
                "isApproved": bool(post[2]),
                "isDeleted": bool(post[5]),
                "isEdited": bool(post[3]),
                "isHighlighted": bool(post[13]),
                "isSpam": bool(post[4]),
                "likes": post[11],
                "message": post[7],
                "parent": parent,
                "points": (post[11] - post[10]),
                "thread": post[12],
                "user": post[8]
            })
        code = 0
        return_data = {"code": code, "response": post_list}
        return jsonify(return_data)

    else:
        code = 1
        err_msg = "thread not found"
        return_data = {"code": code, "response": err_msg}
        return jsonify(return_data)


@app.route('/db/api/thread/remove/', methods=['POST'])
def thread_remove():
    """Mark thread as removed"""
    try:
        db = db_connect()
        cursor = db.cursor()
        data = request.get_json()
        thread = data['thread']
        query_stmt = (
                         "SELECT * "
                         "FROM threads "
                         "WHERE thread_id = %d"
                     ) % (int(thread))
        cursor.execute(query_stmt)
        thread_data = cursor.fetchone()
        if thread_data:
            if not thread_data[8]:
                query_stmt = (
                                 "UPDATE threads "
                                 "SET isDeleted = True "
                                 "WHERE thread_id = %d"
                             ) % (int(thread))
                cursor.execute(query_stmt)
                db.commit()
                query_stmt = (
                                 "UPDATE threads "
                                 "SET posts = 0 "
                                 "WHERE thread_id = %d"
                             ) % (int(thread))
                cursor.execute(query_stmt)
                db.commit()
                query_stmt = (
                                 "UPDATE posts "
                                 "SET isDeleted = True "
                                 "WHERE thread = %d"
                             ) % (int(thread))
                cursor.execute(query_stmt)
                db.commit()
                db.close()
                code = 0
                return_data = {
                    "code": code, "response": {
                        "thread": thread
                    }
                }
                return jsonify(return_data)
            else:
                query_stmt = (
                                 "UPDATE threads "
                                 "SET posts = 0 "
                                 "WHERE thread_id = %d"
                             ) % (int(thread))
                cursor.execute(query_stmt)
                db.commit()
                query_stmt = (
                                 "UPDATE posts "
                                 "SET isDeleted = True "
                                 "WHERE thread = %d"
                             ) % (int(thread))
                cursor.execute(query_stmt)
                db.commit()
                db.close()
                return_data = {"code": 0,
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
                                   "user": thread_data[4]}}
                return jsonify(return_data)
        else:
            code = 1
            err_msg = "not found"
            return_data = {"code": code, "response": err_msg}
            return jsonify(return_data)
    except KeyError:
        code = 2
        err_msg = "invalid json"
        return_data = {"code": code, "response": err_msg}
        return jsonify(return_data)


@app.route('/db/api/thread/restore/', methods=['POST'])
def thread_restore():
    """Cancel removal"""
    try:
        db = db_connect()
        cursor = db.cursor()
        data = request.get_json()
        thread = data['thread']
        query_stmt = (
                         "SELECT * "
                         "FROM threads "
                         "WHERE thread_id = %d"
                     ) % (int(thread))
        cursor.execute(query_stmt)
        thread_data = cursor.fetchone()
        if thread_data:
            if thread_data[8]:
                query_stmt = (
                                 "UPDATE threads "
                                 "SET isDeleted = False "
                                 "WHERE thread_id = %d"
                             ) % (int(thread))
                cursor.execute(query_stmt)
                db.commit()
                query_stmt = (
                                 "UPDATE posts "
                                 "SET isDeleted = False "
                                 "WHERE thread = %d"
                             ) % (int(thread))
                cursor.execute(query_stmt)
                db.commit()
                query_stmt = (
                                 "SELECT count(*) "
                                 "FROM posts "
                                 "WHERE thread = %d"
                             ) % (int(thread))
                cursor.execute(query_stmt)
                post_count = cursor.fetchone()
                query_stmt = (
                                 "UPDATE threads "
                                 "SET posts = %d "
                                 "WHERE thread_id = %d"
                             ) % (int(post_count[0]), int(thread))
                cursor.execute(query_stmt)
                db.commit()
                db.close()
                code = 0
                return_data = {
                    "code": code,
                    "response": {
                        "thread": thread
                    }
                }
                return jsonify(return_data)
            else:
                code = 0
                return_data = {
                    "code": code,
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
                return jsonify(return_data)

        else:
            code = 1
            err_msg = "not found"
            return_data = {"code": code, "response": err_msg}
            return jsonify(return_data)
    except KeyError:
        code = 2
        err_msg = "invalid json"
        return_data = {"code": code, "response": err_msg}
        return jsonify(return_data)


@app.route('/db/api/thread/close/', methods=['POST'])
def thread_close():
    """Mark thread as closed"""
    try:
        db = db_connect()
        cursor = db.cursor()
        data = request.get_json()
        thread = data['thread']
        query_stmt = (
                         "SELECT * "
                         "FROM threads "
                         "WHERE thread_id = %d"
                     ) % (int(thread))
        cursor.execute(query_stmt)
        thread_data = cursor.fetchone()
        if thread_data:
            if not thread_data[3]:
                query_stmt = (
                                 "UPDATE threads "
                                 "SET isClosed = True "
                                 "WHERE thread_id = %d"
                             ) % (int(thread))
                cursor.execute(query_stmt)
                db.commit()
                db.close()
                code = 0
                return_data = {
                    "code": code,
                    "response": {
                        "thread": thread
                    }
                }
                return jsonify(return_data)
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
                        "user": thread_data[4]}}

                return jsonify(return_data)
        else:
            code = 1
            err_msg = "not found"
            return_data = {"code": code, "response": err_msg}
            return jsonify(return_data)
    except KeyError:
        code = 2
        err_msg = "invalid format"
        return_data = {"code": code, "response": err_msg}
        return jsonify(return_data)


@app.route('/db/api/thread/open/', methods=['POST'])
def thread_open():
    """Mark thread as opened"""
    try:
        db = db_connect()
        cursor = db.cursor()
        data = request.get_json()
        thread = data['thread']
        query_str = (
                        "SELECT * "
                        "FROM threads "
                        "WHERE thread_id = %d"
                    ) % (int(thread))
        cursor.execute(query_str)
        thread_data = cursor.fetchone()
        if thread_data:
            if thread_data[3]:
                query_str = (
                                "UPDATE threads "
                                "SET isClosed = False "
                                "WHERE thread_id = %d"
                            ) % (int(thread))
                cursor.execute(query_str)
                db.commit()
                db.close()
                code = 0
                return_data = {
                    "code": code,
                    "response": {
                        "thread": thread
                    }
                }
                return jsonify(return_data)
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
                return jsonify(return_data)
        else:
            code = 1
            err_msg = "not found"
            return_data = {"code": code, "response": err_msg}
            return jsonify(return_data)
    except KeyError:
        code = 2
        err_msg = "invalid format"
        return_data = {"code": code, "response": err_msg}
        return jsonify(return_data)


@app.route('/db/api/thread/update/', methods=['POST'])
def thread_update():
    """Edit thread"""
    try:
        db = db_connect()
        cursor = db.cursor()
        data = request.get_json()
        thread = data['thread']
        message = data['message']
        slug = data['slug']
        query_str = (
                        "SELECT * "
                        "FROM threads "
                        "WHERE thread_id = %d "
                    ) % (int(thread))
        cursor.execute(query_str)
        thread_data = cursor.fetchone()
        if thread_data:
            if (thread_data[6] != message) or (thread_data[7] != slug):
                query_str = (
                                "UPDATE threads "
                                "SET message = '%s' "
                                "WHERE thread_id = %d"
                            ) % (message, thread)
                cursor.execute(query_str)
                query_str = (
                                "UPDATE threads "
                                "SET slug = '%s' "
                                "WHERE thread_id = %d"
                            ) % (slug, thread)
                cursor.execute(query_str)
                db.commit()
                db.close()
                code = 0
                return_data = {
                    "code": code,
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
                return jsonify(return_data)
            else:
                code = 0
                return_data = {
                    "code": code,
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
                return jsonify(return_data)
        else:
            code = 1
            err_msg = "not found"
            return_data = {"code": code, "response": err_msg}
            db.close()
            return jsonify(return_data)
    except KeyError:
        code = 2
        err_msg = "invalid format"
        return_data = {"code": code, "response": err_msg}
        return jsonify(return_data)


@app.route('/db/api/thread/vote/', methods=['POST'])
def thread_vote():
    """like/dislike thread"""
    try:
        db = db_connect()
        cursor = db.cursor()
        data = request.get_json()
        vote = data['vote']
        thread = data['thread']
        query_str = (
                        "SELECT * "
                        "FROM threads "
                        "WHERE thread_id = %d "
                    ) % (int(thread))
        cursor.execute(query_str)
        thread_data = cursor.fetchone()
        if thread_data:
            if vote == 1:
                query_str = (
                                "UPDATE threads "
                                "SET likes = likes + 1 "
                                "WHERE thread_id = %d"
                            ) % (int(thread))
                likes = thread_data[9] + 1
                dislikes = thread_data[10]
            elif vote == -1:
                query_str = (
                                "UPDATE threads "
                                "SET dislikes = dislikes + 1 "
                                "WHERE thread_id = %d"
                            ) % (int(thread))
                likes = thread_data[9]
                dislikes = thread_data[10] + 1
            else:
                code = 3
                err_msg = "wrong syntax"
                return_data = {"code": code, "response": err_msg}
                return jsonify(return_data)
            cursor.execute(query_str)
            db.commit()
            db.close()
            return_data = {
                "code": 0,
                "response": {
                    "date": thread_data[5].strftime("%Y-%m-%d %H:%M:%S"), "dislikes": dislikes,
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
            return jsonify(return_data)
        else:
            code = 1
            err_msg = "not found"
            return_data = {"code": code, "response": err_msg}
            db.close()
            return jsonify(return_data)
    except KeyError:
        code = 2
        err_msg = "invalid format"
        return_data = {"code": code, "response": err_msg}
        return jsonify(return_data)


@app.route('/db/api/thread/subscribe/', methods=['POST'])
def thread_subscribe():
    """Subscribe user to this thread"""
    try:
        db = db_connect()
        cursor = db.cursor()
        data = request.get_json()
        user = data['user']
        thread = data['thread']
        query_stmt = (
                         "SELECT * "
                         "FROM threads "
                         "WHERE thread_id = %d "
                     ) % (int(thread))
        cursor.execute(query_stmt)
        thread_data = cursor.fetchone()
        query_stmt = (
                         "SELECT * "
                         "FROM users "
                         "WHERE email = '%s'"
                     ) % user
        cursor.execute(query_stmt)
        user_data = cursor.fetchone()
        if (not thread_data) or (not user_data):
            code = 1
            err_msg = "not found"
            return_data = {"code": code, "response": err_msg}
            db.close()
            return jsonify(return_data)
        else:
            query_stmt = (
                             "SELECT * "
                             "FROM subscriptions "
                             "WHERE user = '%s' AND thread_id = %d"
                         ) % (user, int(thread))
            cursor.execute(query_stmt)
            subscriptions = cursor.fetchone()
            if not subscriptions:
                query_stmt = (
                                 "INSERT INTO subscriptions (user, thread_id) "
                                 "VALUES ('%s', %d)"
                             ) % (user, thread)
                cursor.execute(query_stmt)
                db.commit()
                db.close()
                code = 0
                return_data = {
                    "code": code,
                    "response": {
                        "thread": thread,
                        "user": user
                    }
                }
                return jsonify(return_data)

            else:
                code = 0
                return_data = {
                    "code": code,
                    "response": {
                        "thread": thread,
                        "user": user
                    }
                }
                return jsonify(return_data)
    except KeyError:
        code = 2
        err_msg = "invalid format"
        return_data = {"code": code, "response": err_msg}
        return jsonify(return_data)


@app.route('/db/api/thread/unsubscribe/', methods=['POST'])
def thread_unsubscribe():
    """Unsubscribe user from this thread"""
    try:
        db = db_connect()
        cursor = db.cursor()
        data = request.get_json()
        user = data['user']
        thread = data['thread']
        query_str = (
                        "SELECT * "
                        "FROM threads "
                        "WHERE thread_id = %d "
                    ) % (int(thread))
        cursor.execute(query_str)
        thread_data = cursor.fetchone()
        query_str = (
                        "SELECT * "
                        "FROM users "
                        "WHERE email = '%s'"
                    ) % user
        cursor.execute(query_str)
        user_data = cursor.fetchone()
        if (not thread_data) or (not user_data):
            code = 1
            err_msg = "not found"
            return_data = {"code": code, "response": err_msg}
            db.close()
            return jsonify(return_data)
        else:
            query_str = (
                            "SELECT * "
                            "FROM subscriptions "
                            "WHERE user = '%s' AND thread_id = %d"
                        ) % (user, int(thread))
            cursor.execute(query_str)
            subscriptions = cursor.fetchone()
            if subscriptions:
                query_str = (
                                "DELETE "
                                "FROM subscriptions "
                                "WHERE user = '%s' AND thread_id = %d"
                            ) % (user, thread)
                cursor.execute(query_str)
                db.commit()
                db.close()
                code = 0
                return_data = {
                    "code": code,
                    "response": {
                        "thread": thread,
                        "user": user
                    }
                }
                return jsonify(return_data)

            else:
                code = 0
                return_data = {
                    "code": code,
                    "response": {
                        "thread": thread,
                        "user": user
                    }
                }
                return jsonify(return_data)
    except KeyError:
        code = 2
        err_msg = "invalid format"
        return_data = {"code": code, "response": err_msg}
        return jsonify(return_data)


if __name__ == '__main__':
    app.run()
