# -*- coding: utf-8 -*-
from flask import Flask, jsonify, request
import MySQLdb
from _mysql_exceptions import IntegrityError

app = Flask(__name__)

# FUNCTIONS

# MAIN
app.config['JSON_SORT_KEYS'] = False
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False



@app.route('/db/api/clear/', methods=['POST'])
def clear():
    db = MySQLdb.connect(host='localhost', user="db_api_user", passwd="passwd", db="db_perf_test", charset='utf8')
    cursor = db.cursor()
    cursor.execute("truncate table forums")
    cursor.execute("truncate table users")
    cursor.execute("truncate table threads")
    cursor.execute("truncate table posts")
    cursor.execute("truncate table followers")
    cursor.execute("truncate table subscriptions")
    db.commit()

    returnData = {"code": 0, "response": "OK"}
    return jsonify(returnData)


@app.route('/db/api/status/', methods=['GET'])
def status():
    db = MySQLdb.connect(host='localhost', user="db_api_user", passwd="passwd", db="db_perf_test", charset='utf8')
    cursor = db.cursor()
    cursor.execute("select count(*) from users")
    users = cursor.fetchone()
    cursor.execute("select count(*) from threads")
    threads = cursor.fetchone()
    cursor.execute("select count(*) from forums")
    forums = cursor.fetchone()
    cursor.execute("select count(*) from posts")
    posts = cursor.fetchone()
    returnData = {"code": 0, "response": {"user": users[0], "thread": threads[0], "forum": forums[0], "post": posts[0]}}
    return jsonify(returnData)


# FORUMS


@app.route('/db/api/forum/create/', methods=['POST'])
def forum_create():
    try:
        data = request.get_json()    
        name = data['name']
        short_name = data['short_name']
        user = data['user']
        q = "INSERT INTO forums (name,short_name,user) values ('%s','%s','%s')" % (name, short_name, user)
        db = MySQLdb.connect(host='localhost', user="db_api_user", passwd="passwd", db="db_perf_test", charset='utf8')
        cursor = db.cursor()
        cursor.execute(q)
        returnData = {"code": 0, "response": {'id': cursor.lastrowid, "name": name, "short_name": short_name,
                                              "user": user}}
        db.commit()

        return jsonify(returnData)
    except IntegrityError, e:
        if e[0] == 1062:
            if 'short_name_UNIQUE' in e[1]:
                q = "SELECT * from forums where short_name = '%s'" % (short_name)
            else:
                q = "SELECT * from forums where name = '%s'" % (name)
            db = MySQLdb.connect(host='localhost', user="db_api_user", passwd="passwd", db="db_perf_test", charset='utf8')
            cursor = db.cursor()
            cursor.execute(q)
            myforum = cursor.fetchone()
            returnData = {"code":0, "response": {"id": myforum[3], "name": myforum[0], "short_name": myforum[1],
                                                "user": myforum[2]}}
            return jsonify(returnData)
    except KeyError:
        returnData = {"code": 2, "response": "invalid json format"}
        return jsonify(returnData)


@app.route('/db/api/forum/details/', methods=['GET'])
def forum_details():
    forum = request.args.get('forum', '')
    related = request.args.getlist('related')
    db = MySQLdb.connect(host='localhost', user="db_api_user", passwd="passwd", db="db_perf_test", charset='utf8')
    cursor = db.cursor()
    q = "SELECT * FROM forums where short_name = '%s'" % (forum)
    if cursor.execute(q) == 0:
        returnData = {"code": 1, "response": "FORUM NOT FOUND"}
        return  jsonify(returnData)
    myforum = cursor.fetchone()
    if 'user' in related:
        q = "SELECT * FROM users where email = '%s'" % (myforum[2])
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
        q = "Select who_user from followers where whom_user = '%s'" % (myuser[4])
        cursor.execute(q)
        myfollowers = cursor.fetchall()
        q = "Select whom_user from followers where who_user = '%s'" % (myuser[4])
        cursor.execute(q)
        myfollowing = cursor.fetchall()
        q = "Select thread_id from subscriptions where user = '%s'" % (myuser[4])
        cursor.execute(q)
        mysubs = cursor.fetchall()
        userinfo = {"about": about, "email": myuser[4], "followers":  [x[0] for x in myfollowers],
                    "following": [x[0] for x in myfollowing],
                    "id": myuser[0], "isAnonymous": bool(myuser[5]),
                    "name": name, "subscriptions": [x[0] for x in mysubs],
                    "username": username}
    else:
        userinfo = myforum[2]
    returnData = {"code": 0, "response": {"id": myforum[3], "name": myforum[0], "short_name": myforum[1],
                                          "user": userinfo}}
    return jsonify(returnData)

@app.route('/db/api/forum/listPosts/', methods=['GET'])
def forum_listPosts():
    forum = request.args.get('forum')
    if not forum:
        returnData = {"code": 3, "response": "bad syntax"}
        return jsonify(returnData)
    related = request.args.getlist('related')
    order = request.args.get('order', 'desc')
    limit = request.args.get('limit', False)
    since = request.args.get('since', False)
    db = MySQLdb.connect(host='localhost', user="db_api_user", passwd="passwd", db="db_perf_test", charset='utf8')
    cursor = db.cursor()
    q = "SELECT * FROM forums where short_name = '%s'" % (forum)
    if cursor.execute(q) == 0:
        returnData = {"code": 1, "response": "FORUM NOT FOUND"}
        return  jsonify(returnData)
    myforum = cursor.fetchone()
    q = "select * from posts where forum = '%s' " % (forum)
    if since:
        q += " and date >= '%s' " % (since)
    q += " order by  date %s " % (order)
    if limit:
        q += " limit %d" % (int(limit))
    cursor.execute(q)
    myposts = cursor.fetchall()
    if 'forum' in related:
         related.remove('forum')
         foruminfo = {"id": myforum[3], "name": myforum[0], "short_name": myforum[1],
                                          "user": myforum[2]}
    else:
         foruminfo = forum
    ListPosts = []
    for mypost in myposts:
        if 'user' in related:
            q = "SELECT * FROM users where email = '%s'" % (mypost[8])
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
            q = "Select who_user from followers where whom_user = '%s'" % (myuser[4])
            cursor.execute(q)
            myfollowers = cursor.fetchall()
            q = "Select whom_user from followers where who_user = '%s'" % (myuser[4])
            cursor.execute(q)
            myfollowing = cursor.fetchall()
            q = "Select thread_id from subscriptions where user = '%s'" % (myuser[4])
            cursor.execute(q)
            mysubs = cursor.fetchall()
            userinfo = {"about": about, "email": myuser[4], "followers":  [x[0] for x in myfollowers],
                        "following": [x[0] for x in myfollowing],
                        "id": myuser[0], "isAnonymous": bool(myuser[5]),
                        "name": name, "subscriptions": [x[0] for x in mysubs],
                        "username": username}
        else:
            userinfo = mypost[8]

        if 'thread' in related:
            q = "SELECT * FROM threads where thread_id = '%s'" % (mypost[12])
            cursor.execute(q)
            mythread = cursor.fetchone()
            threadinfo = {"date": mythread[5].strftime("%Y-%m-%d %H:%M:%S"), "dislikes": mythread[10],
                      "forum": mythread[1], "id": mythread[0], "isClosed": bool(mythread[3]), "isDeleted": bool(mythread[8]),
                      "likes": mythread[9], "message": mythread[6], "points": (mythread[9] - mythread[10]),
                      "posts": mythread[11], "slug": mythread[7], "title": mythread[2], "user": mythread[4]}
        else:
            threadinfo = mypost[12]
        if mypost[1] == 0:
            parent = None
        else:
            parent = mypost[1]

        returnData = {"date": mypost[6].strftime("%Y-%m-%d %H:%M:%S"), "dislikes": mypost[10],
                                          "forum": foruminfo, "id": mypost[0], "isApproved": bool(mypost[2]),
                                          "isDeleted": bool(mypost[5]), "isEdited": bool(mypost[3]),
                                          "isHighlighted": bool(mypost[13]), "isSpam": bool(mypost[4]),
                                          "likes": mypost[11], "message": mypost[7], "parent": parent,
                                          "points": (mypost[11]-mypost[10]), "thread": threadinfo, "user": userinfo}
        ListPosts.append(returnData)
    return jsonify({"code": 0, "response": ListPosts})


@app.route('/db/api/forum/listThreads/', methods=['GET'])
def forum_listThreads():
    forum = request.args.get('forum')
    if not forum:
        returnData = {"code": 3, "response": "bad syntax"}
        return jsonify(returnData)
    related = request.args.getlist('related')
    order = request.args.get('order', 'desc')
    limit = request.args.get('limit', False)
    since = request.args.get('since', False)
    db = MySQLdb.connect(host='localhost', user="db_api_user", passwd="passwd", db="db_perf_test", charset='utf8')
    cursor = db.cursor()
    q = "SELECT * FROM forums where short_name = '%s'" % (forum)
    if cursor.execute(q) == 0:
        returnData = {"code": 1, "response": "FORUM NOT FOUND"}
        return  jsonify(returnData)
    myforum = cursor.fetchone()
    q = "select * from threads where forum = '%s' " % (forum)
    if since:
        q += " and date >= '%s' " % (since)
    q += " order by  date %s " % (order)
    if limit:
        q += " limit %d" % (int(limit))
    cursor.execute(q)
    mythreads = cursor.fetchall()
    if 'forum' in related:
         foruminfo = {"id": myforum[3], "name": myforum[0], "short_name": myforum[1],
                                          "user": myforum[2]}
    else:
         foruminfo = forum
    ListThreads = []
    for mythread in mythreads:
        if 'user' in related:
            q = "SELECT * FROM users where email = '%s'" % (mythread[4])
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
            q = "Select who_user from followers where whom_user = '%s'" % (myuser[4])
            cursor.execute(q)
            myfollowers = cursor.fetchall()
            q = "Select whom_user from followers where who_user = '%s'" % (myuser[4])
            cursor.execute(q)
            myfollowing = cursor.fetchall()
            q = "Select thread_id from subscriptions where user = '%s'" % (myuser[4])
            cursor.execute(q)
            mysubs = cursor.fetchall()
            userinfo = {"about": about, "email": myuser[4], "followers":  [x[0] for x in myfollowers],
                        "following": [x[0] for x in myfollowing],
                        "id": myuser[0], "isAnonymous": bool(myuser[5]),
                        "name": name, "subscriptions": [x[0] for x in mysubs],
                        "username": username}
        else:
            userinfo = mythread[4]

        returnData = {"date": mythread[5].strftime("%Y-%m-%d %H:%M:%S"), "dislikes": mythread[10],
                  "forum": foruminfo, "id": mythread[0], "isClosed": bool(mythread[3]), "isDeleted": bool(mythread[8]),
                  "likes": mythread[9], "message": mythread[6], "points": (mythread[9] - mythread[10]),
                  "posts": mythread[11], "slug": mythread[7], "title": mythread[2], "user": userinfo}
        ListThreads.append(returnData)
    return jsonify({"code": 0, "response": ListThreads})

@app.route('/db/api/forum/listUsers/', methods=['GET'])
def forum_listUsers():
    forum = request.args.get('forum')
    if not forum:
        returnData = {"code": 3, "response": "bad syntax"}
        return jsonify(returnData)
    order = request.args.get('order', 'desc')
    limit = request.args.get('limit', False)
    since = request.args.get('since_id', False)
    db = MySQLdb.connect(host='localhost', user="db_api_user", passwd="passwd", db="db_perf_test", charset='utf8')
    cursor = db.cursor()
    q = "SELECT * FROM forums where short_name = '%s'" % (forum)
    if cursor.execute(q) == 0:
        returnData = {"code": 1, "response": "FORUM NOT FOUND"}
        return  jsonify(returnData)




    q =  """SELECT * FROM users
        WHERE email IN (SELECT DISTINCT user FROM posts WHERE forum = '%s') """ % (forum)
    if since:
        q += " and user_id >= %d " % (int(since))
    q += " order by  name %s " % (order)
    if limit:
        q += " limit %d" % (int(limit))



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
        q = "Select who_user from followers where whom_user = '%s'" % (myuser[4])
        cursor.execute(q)
        myfollowers = cursor.fetchall()
        q = "Select whom_user from followers where who_user = '%s'" % (myuser[4])
        cursor.execute(q)
        myfollowing = cursor.fetchall()
        q = "Select thread_id from subscriptions where user = '%s'" % (myuser[4])
        cursor.execute(q)
        mysubs = cursor.fetchall()
        userinfo = {"about": about, "email": myuser[4], "followers":  [x[0] for x in myfollowers],
                        "following": [x[0] for x in myfollowing],
                        "id": myuser[0], "isAnonymous": bool(myuser[5]),
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
        if name != None:
            q = """INSERT INTO users (username, about, name, email, isAnonymous) values
            ('%s','%s','%s','%s',%d)""" % (username, about, name, email, isAnonymous)
        else:
            q = """INSERT INTO users (username, about, name, email, isAnonymous) values
            ('%s','%s',Null,'%s',%d)""" % (username, about, email, isAnonymous)
        db = MySQLdb.connect(host='localhost', user="db_api_user", passwd="passwd", db="db_perf_test", charset='utf8')
        cursor = db.cursor()
        cursor.execute(q)
        returnData = {"code": 0, "response": {"about": about, "email": email, "id": cursor.lastrowid,
                                              "isAnonymous": isAnonymous, "name": name, "username": username}}
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
    user = request.args.get('user', '')
    db = MySQLdb.connect(host='localhost', user="db_api_user", passwd="passwd", db="db_perf_test", charset='utf8')
    cursor = db.cursor()
    q = "SELECT * FROM users where email = '%s'" % (user)
    if cursor.execute(q) == 0:
        returnData = {"code": 1, "response": "USER NOT FOUND"}
        return jsonify(returnData)
    else:
        myuser = cursor.fetchone()
        q = "Select who_user from followers where whom_user = '%s'" % (myuser[4])
        cursor.execute(q)
        myfollowers = cursor.fetchall()
        q = "Select whom_user from followers where who_user = '%s'" % (myuser[4])
        cursor.execute(q)
        myfollowing = cursor.fetchall()
        q = "Select thread_id from subscriptions where user = '%s'" % (myuser[4])
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

        userinfo = {"about": about, "email": myuser[4], "followers":  [x[0] for x in myfollowers],
                    "following": [x[0] for x in myfollowing],
                    "id": myuser[0], "isAnonymous": bool(myuser[5]),
                    "name": name, "subscriptions": [x[0] for x in mysubs],
                    "username": username}
        returnData = {"code": 0, "response": userinfo}
        return jsonify(returnData)


@app.route('/db/api/user/listPosts/', methods=['GET'])
def user_listPosts():
    user = request.args.get('user', False)
    if not user:
        returnData = {"code": 3, "response": "bad syntax"}
        return jsonify(returnData)
    limit = request.args.get('limit', False)
    since = request.args.get('since', False)
    order = request.args.get('order', 'desc')
    db = MySQLdb.connect(host='localhost', user="db_api_user", passwd="passwd", db="db_perf_test", charset='utf8')
    cursor = db.cursor()
    q = "select * from users where email = '%s'" % (user)
    cursor.execute(q)
    myuser = cursor.fetchone()
    if myuser:
        q = "select * from posts where user = '%s'" % (user)
        if since:
            q += " and date >= '%s' " % (since)
        q += " order by date %s " % (order)
        if limit:
            q += " limit %d" % (int(limit))
        cursor.execute(q)
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
                                              "points": (mypost[11]-mypost[10]), "thread": mypost[12],
                                              "user": mypost[8]})
        returnData = {"code": 0, "response": postlist}
        return jsonify(returnData)

    else:
        returnData = {"code": 1, "response": "USER NOT FOUND"}
        return jsonify(returnData)


@app.route('/db/api/user/updateProfile/', methods=['POST'])
def user_updateProfile():
    try:
        data = request.get_json()
        user = data['user']
        about = data['about']
        name = data['name']
        db = MySQLdb.connect(host='localhost', user="db_api_user", passwd="passwd", db="db_perf_test", charset='utf8')
        cursor = db.cursor()
        q = "SELECT * FROM users where email = '%s' " % (user)
        cursor.execute(q)
        myuser = cursor.fetchone()
        if myuser:
            if (myuser[2] != about) or (myuser[3] != name):
                q = "update users set about = '%s' where email = '%s'" % (about, user)
                cursor.execute(q)
                q = "update users set name = '%s' where email = '%s'" % (name, user)
                cursor.execute(q)
                db.commit()
                q = "Select who_user from followers where whom_user = '%s'" % (myuser[4])
                cursor.execute(q)
                myfollowers = cursor.fetchall()
                q = "Select whom_user from followers where who_user = '%s'" % (myuser[4])
                cursor.execute(q)
                myfollowing = cursor.fetchall()
                q = "Select thread_id from subscriptions where user = '%s'" % (myuser[4])
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
                userinfo = {"about": about, "email": myuser[4], "followers":  [x[0] for x in myfollowers],
                            "following": [x[0] for x in myfollowing],
                            "id": myuser[0], "isAnonymous": bool(myuser[5]),
                            "name": name, "subscriptions": [x[0] for x in mysubs],
                            "username": username}
                returnData = {"code": 0, "response": userinfo}
                return jsonify(returnData)
            else:

                q = "Select who_user from followers where whom_user = '%s'" % (myuser[4])
                cursor.execute(q)
                myfollowers = cursor.fetchall()
                q = "Select whom_user from followers where who_user = '%s'" % (myuser[4])
                cursor.execute(q)
                myfollowing = cursor.fetchall()
                q = "Select thread_id from subscriptions where user = '%s'" % (myuser[4])
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

                userinfo = {"about": about, "email": myuser[4], "followers":  [x[0] for x in myfollowers],
                            "following": [x[0] for x in myfollowing],
                            "id": myuser[0], "isAnonymous": bool(myuser[5]),
                            "name": name, "subscriptions": [x[0] for x in mysubs],
                            "username": username}
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
    try:
        data = request.get_json()
        follower = data['follower'] # who
        followee = data['followee'] # whom
        if followee == follower:
            returnData = {"code": 3, "response": "WTF!"}
            return jsonify(returnData)
        db = MySQLdb.connect(host='localhost', user="db_api_user", passwd="passwd", db="db_perf_test", charset='utf8')
        cursor = db.cursor()
        q = "SELECT * FROM users where email = '%s' " % (followee)
        cursor.execute(q)
        myuserwhom = cursor.fetchone()
        if myuserwhom:
            q = "select * from followers where who_user = '%s' and whom_user = '%s'" % (follower, followee)
            cursor.execute(q)
            if not cursor.fetchone():
                q = "SELECT * FROM users where email = '%s' " % (follower)
                cursor.execute(q)
                myuser = cursor.fetchone()
                if myuser:
                    q = "insert into followers (who_user, whom_user) values ('%s', '%s')" % (follower, followee)
                    cursor.execute(q)
                    db.commit()
                    q = "Select who_user from followers where whom_user = '%s'" % (myuser[4])
                    cursor.execute(q)
                    myfollowers = cursor.fetchall()
                    q = "Select whom_user from followers where who_user = '%s'" % (myuser[4])
                    cursor.execute(q)
                    myfollowing = cursor.fetchall()
                    q = "Select thread_id from subscriptions where user = '%s'" % (myuser[4])
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

                    userinfo = {"about": about, "email": myuser[4], "followers":  [x[0] for x in myfollowers],
                                "following": [x[0] for x in myfollowing],
                                "id": myuser[0], "isAnonymous": bool(myuser[5]),
                                "name": name, "subscriptions": [x[0] for x in mysubs],
                                "username": username}
                    returnData = {"code": 0, "response": userinfo}
                    return jsonify(returnData)
                else:
                    returnData = {"code": 1, "response": "USER NOT FOUND"}

                    return jsonify(returnData)
            else:
                q = "SELECT * FROM users where email = '%s' " % (follower)
                cursor.execute(q)
                myuser = cursor.fetchone()
                q = "Select who_user from followers where whom_user = '%s'" % (myuser[4])
                cursor.execute(q)
                myfollowers = cursor.fetchall()
                q = "Select whom_user from followers where who_user = '%s'" % (myuser[4])
                cursor.execute(q)
                myfollowing = cursor.fetchall()
                q = "Select thread_id from subscriptions where user = '%s'" % (myuser[4])
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

                userinfo = {"about": about, "email": myuser[4], "followers":  [x[0] for x in myfollowers],
                                "following": [x[0] for x in myfollowing],
                                "id": myuser[0], "isAnonymous": bool(myuser[5]),
                                "name": name, "subscriptions": [x[0] for x in mysubs],
                                "username": username}
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
    user = request.args.get('user', False)
    if not user:
        returnData = {"code": 3, "response": "bad syntax"}
        return jsonify(returnData)
    limit = request.args.get('limit', False)
    since_id = request.args.get('since_id', False)
    order = request.args.get('order', 'desc')
    db = MySQLdb.connect(host='localhost', user="db_api_user", passwd="passwd", db="db_perf_test", charset='utf8')
    cursor = db.cursor()
    q = "select * from users where email = '%s'" % (user)
    cursor.execute(q)
    myuser = cursor.fetchone()
    if myuser:





        q = "select straight_join user_id, username, about, name, email, isAnonymous from followers join users on users.email = followers.who_user where whom_user = '%s' " % (user)

        if since_id:
            q += " and user_id >= %d " % (int(since_id))
        q += " order by name %s" % (order)
        if limit:
            q += " limit %d" % (int(limit))
        cursor.execute(q)
        myfollowers = cursor.fetchall()
        followersList = []
        for myuser in myfollowers:
                    q = "Select who_user from followers where whom_user = '%s'" % (myuser[4])
                    cursor.execute(q)
                    myfollowers = cursor.fetchall()
                    q = "Select whom_user from followers where who_user = '%s'" % (myuser[4])
                    cursor.execute(q)
                    myfollowing = cursor.fetchall()
                    q = "Select thread_id from subscriptions where user = '%s'" % (myuser[4])
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

                    userinfo = {"about": about, "email": myuser[4], "followers":  [x[0] for x in myfollowers],
                                    "following": [x[0] for x in myfollowing],
                                    "id": myuser[0], "isAnonymous": bool(myuser[5]),
                                    "name": name, "subscriptions": [x[0] for x in mysubs],
                                    "username": username}

                    followersList.append(userinfo)

        returnData = {"code": 0, "response": followersList}
        return jsonify(returnData)


    else:
        returnData = {"code": 1, "response": "USER NOT FOUND"}

        return jsonify(returnData)


@app.route('/db/api/user/listFollowing/', methods=['GET'])
def user_listFollowing():
    user = request.args.get('user', False)
    if not user:
        returnData = {"code": 3, "response": "bad syntax"}
        return jsonify(returnData)
    limit = request.args.get('limit', False)
    since_id = request.args.get('since_id', False)
    order = request.args.get('order', 'desc')
    db = MySQLdb.connect(host='localhost', user="db_api_user", passwd="passwd", db="db_perf_test", charset='utf8')
    cursor = db.cursor()
    q = "select * from users where email = '%s'" % (user)
    cursor.execute(q)
    myuser = cursor.fetchone()
    if myuser:

        q = "select straight_join user_id, username, about, name, email, isAnonymous  from followers join users on users.email = followers.whom_user where who_user = '%s' " % (user)

        if since_id:
            q += " and user_id >= %d " % (int(since_id))
        q += " order by name %s" % (order)
        if limit:
            q += " limit %d" % (int(limit))
        cursor.execute(q)
        allmyfollowing = cursor.fetchall()
        myfollowingList = []
        for myuser in allmyfollowing:
                    q = "Select who_user from followers where whom_user = '%s'" % (myuser[4])
                    cursor.execute(q)
                    myfollowers = cursor.fetchall()
                    q = "Select whom_user from followers where who_user = '%s'" % (myuser[4])
                    cursor.execute(q)
                    myfollowing = cursor.fetchall()
                    q = "Select thread_id from subscriptions where user = '%s'" % (myuser[4])
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

                    userinfo = {"about": about, "email": myuser[4], "followers":  [x[0] for x in myfollowers],
                                    "following": [x[0] for x in myfollowing],
                                    "id": myuser[0], "isAnonymous": bool(myuser[5]),
                                    "name": name, "subscriptions": [x[0] for x in mysubs],
                                    "username": username}

                    myfollowingList.append(userinfo)

        returnData = {"code": 0, "response": myfollowingList}
        return jsonify(returnData)


    else:
        returnData = {"code": 1, "response": "USER NOT FOUND"}

        return jsonify(returnData)

@app.route('/db/api/user/unfollow/', methods=['POST'])
def uesr_unfollow():
    try:
        data = request.get_json()
        follower = data['follower'] # who
        followee = data['followee'] # whom
        if followee == follower:
            returnData = {"code": 3, "response": "WTF!"}
            return jsonify(returnData)
        db = MySQLdb.connect(host='localhost', user="db_api_user", passwd="passwd", db="db_perf_test", charset='utf8')
        cursor = db.cursor()
        q = "SELECT * FROM users where email = '%s' " % (followee)
        cursor.execute(q)
        myuserwhom = cursor.fetchone()
        if myuserwhom:
            q = "select * from followers where who_user = '%s' and whom_user = '%s'" % (follower, followee)
            cursor.execute(q)
            if cursor.fetchone():
                q = "SELECT * FROM users where email = '%s' " % (follower)
                cursor.execute(q)
                myuser = cursor.fetchone()
                if myuser:
                    q = "delete from followers where who_user = '%s' and whom_user = '%s'" % (follower, followee)
                    cursor.execute(q)
                    db.commit()
                    q = "Select who_user from followers where whom_user = '%s'" % (myuser[4])
                    cursor.execute(q)
                    myfollowers = cursor.fetchall()
                    q = "Select whom_user from followers where who_user = '%s'" % (myuser[4])
                    cursor.execute(q)
                    myfollowing = cursor.fetchall()
                    q = "Select thread_id from subscriptions where user = '%s'" % (myuser[4])
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

                    userinfo = {"about": about, "email": myuser[4], "followers":  [x[0] for x in myfollowers],
                                "following": [x[0] for x in myfollowing],
                                "id": myuser[0], "isAnonymous": bool(myuser[5]),
                                "name": name, "subscriptions": [x[0] for x in mysubs],
                                "username": username}
                    returnData = {"code": 0, "response": userinfo}
                    return jsonify(returnData)
                else:
                    returnData = {"code": 1, "response": "USER NOT FOUND"}

                    return jsonify(returnData)
            else:
                q = "SELECT * FROM users where email = '%s' " % (follower)
                cursor.execute(q)
                myuser = cursor.fetchone()
                q = "Select who_user from followers where whom_user = '%s'" % (myuser[4])
                cursor.execute(q)
                myfollowers = cursor.fetchall()
                q = "Select whom_user from followers where who_user = '%s'" % (myuser[4])
                cursor.execute(q)
                myfollowing = cursor.fetchall()
                q = "Select thread_id from subscriptions where user = '%s'" % (myuser[4])
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

                userinfo = {"about": about, "email": myuser[4], "followers":  [x[0] for x in myfollowers],
                                "following": [x[0] for x in myfollowing],
                                "id": myuser[0], "isAnonymous": bool(myuser[5]),
                                "name": name, "subscriptions": [x[0] for x in mysubs],
                                "username": username}
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
        q = """INSERT INTO threads (forum, title, isClosed, user, date, message,slug, isDeleted) values
        ('%s', '%s', %d, '%s', '%s', '%s', '%s', %d)""" % (forum, title, isClosed, user, date, message, slug, isDeleted)
        db = MySQLdb.connect(host='localhost', user="db_api_user", passwd="passwd", db="db_perf_test", charset='utf8')
        cursor = db.cursor()
        cursor.execute(q)
        db.commit()

        returnData = {'code': 0, 'response': {'date': date, 'forum': forum, 'id': cursor.lastrowid,
                                              'isClosed': isClosed, 'isDeleted': isDeleted,
                                              'message': message, 'slug': slug, 'title': title, 'user': user}}
        return jsonify(returnData)
    except KeyError:
        returnData = {"code": 2, "response": "invalid json format"}
        return jsonify(returnData)


@app.route('/db/api/thread/details/', methods=['GET'])
def thread_details():
    thread = request.args.get('thread', '')
    related = request.args.getlist('related')
    db = MySQLdb.connect(host='localhost', user="db_api_user", passwd="passwd", db="db_perf_test", charset='utf8')
    cursor = db.cursor()
    q = "SELECT * FROM threads where thread_id = '%s'" % (thread)
    if cursor.execute(q) == 0:
        returnData = {"code": 1, "response": "THREAD NOT FOUND"}
        return  jsonify(returnData)
    mythread = cursor.fetchone()
    if 'user' in related:
        q = "SELECT * FROM users where email = '%s'" % (mythread[4])
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
        q = "Select who_user from followers where whom_user = '%s'" % (myuser[4])
        cursor.execute(q)
        myfollowers = cursor.fetchall()
        q = "Select whom_user from followers where who_user = '%s'" % (myuser[4])
        cursor.execute(q)
        myfollowing = cursor.fetchall()
        q = "Select thread_id from subscriptions where user = '%s'" % (myuser[4])
        cursor.execute(q)
        mysubs = cursor.fetchall()
        userinfo = {"about": about, "email": myuser[4], "followers":  [x[0] for x in myfollowers],
                    "following": [x[0] for x in myfollowing],
                    "id": myuser[0], "isAnonymous": bool(myuser[5]),
                    "name": name, "subscriptions": [x[0] for x in mysubs],
                    "username": username}
    else:
        userinfo = mythread[4]
    if 'forum' in related:
         related.remove('forum')
         q = "SELECT * FROM forums where short_name = '%s'" % (mythread[1])
         cursor.execute(q)
         myforum = cursor.fetchone()
         foruminfo = {"id": myforum[3], "name": myforum[0], "short_name": myforum[1],
                                          "user": myforum[2]}
    else:
         foruminfo = mythread[1]
    if related:
        returnData = {"code": 3, "response": "invalid syntax"}
        return jsonify(returnData)
    returnData = {"code": 0, "response": {"date": mythread[5].strftime("%Y-%m-%d %H:%M:%S"), "dislikes": mythread[10],
                  "forum": foruminfo, "id": mythread[0], "isClosed": bool(mythread[3]), "isDeleted": bool(mythread[8]),
                  "likes": mythread[9], "message": mythread[6], "points": (mythread[9] - mythread[10]),
                  "posts": mythread[11], "slug": mythread[7], "title": mythread[2], "user": userinfo}}
    return jsonify(returnData)


@app.route("/db/api/thread/list/", methods = ["GET"])
def thread_list():
    user = request.args.get('user', False)
    forum = request.args.get('forum', False)
    if user and forum:
        returnData = {"code": 3, "response": "bad syntax"}
        return jsonify(returnData)
    limit = request.args.get('limit', False)
    since = request.args.get('since', False)
    order = request.args.get('order', False)
    db = MySQLdb.connect(host='localhost', user="db_api_user", passwd="passwd", db="db_perf_test", charset='utf8')
    cursor = db.cursor()
    q = "SELECT * FROM threads where "
    if user:
        q += "user =  '%s'" % (user)
    else:
        q += "forum = '%s' " % (forum)
    if since:
        q += " and date >= '%s' " % (since)
    if order:
        q += " order by date %s " % (order)
    if limit:
        q += " limit %d" % (int(limit))

    cursor.execute(q)
    threads = cursor.fetchall()

    returnthreads = []

    for mythread in threads:
        returnthreads.append({"date": mythread[5].strftime("%Y-%m-%d %H:%M:%S"), "dislikes": mythread[10],
                  "forum": mythread[1], "id": mythread[0], "isClosed": bool(mythread[3]), "isDeleted": bool(mythread[8]),
                  "likes": mythread[9], "message": mythread[6], "points": (mythread[9] - mythread[10]),
                  "posts": mythread[11], "slug": mythread[7], "title": mythread[2], "user": mythread[4]})
    returnData = {"code": 0, "response": returnthreads}
    return jsonify(returnData)


@app.route('/db/api/thread/listPosts/', methods = ['GET'])
def thread_listpost():
    thread = request.args.get('thread', False)
    if not thread:
        returnData = {"code": 3, "response": "bad syntax"}
        return jsonify(returnData)
    limit = request.args.get('limit', False)
    since = request.args.get('since', False)
    order = request.args.get('order', 'desc')
    db = MySQLdb.connect(host='localhost', user="db_api_user", passwd="passwd", db="db_perf_test", charset='utf8')
    cursor = db.cursor()
    q = "select * from threads where thread_id = %d" % (int(thread))
    cursor.execute(q)
    mythread = cursor.fetchone()
    if mythread:
        q = "select * from posts where thread = %d" % (int(thread))
        if since:
            q += " and date >= '%s' " % (since)
        q += " order by date %s " % (order)
        if limit:
            q += " limit %d" % (int(limit))
        cursor.execute(q)
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
                                              "points": (mypost[11]-mypost[10]), "thread": mypost[12],
                                              "user": mypost[8]})
        returnData = {"code": 0, "response": postlist}
        return jsonify(returnData)

    else:
        returnData = {"code": 1, "response": "THREAD NOT FOUND"}
        return jsonify(returnData)


@app.route('/db/api/thread/remove/', methods=['POST'])
def thread_remove():
    try:
        data = request.get_json()
        thread = data['thread']
        db = MySQLdb.connect(host='localhost', user="db_api_user", passwd="passwd", db="db_perf_test", charset='utf8')
        cursor = db.cursor()
        q = "select * from threads where thread_id = %d" % (int(thread))
        cursor.execute(q)
        mythread = cursor.fetchone()
        if mythread:
            if not mythread[8]:
                q = "update threads set isDeleted = True where thread_id = %d" % (int(thread))
                cursor.execute(q)
                db.commit()
                q = "update threads set posts = 0 where thread_id = %d" % (int(thread))
                cursor.execute(q)
                db.commit()
                q = "update posts set isDeleted = True where thread = %d" % (int(thread))
                cursor.execute(q)
                db.commit()

                returnData = {"code": 0, "response": {"thread": thread}}
                return jsonify(returnData)
            else:
                q = "update threads set posts = 0 where thread_id = %d" % (int(thread))
                cursor.execute(q)
                db.commit()
                q = "update posts set isDeleted = True where thread = %d" % (int(thread))
                cursor.execute(q)
                db.commit()

                returnData = {"code": 0, "response":{"date": mythread[5].strftime("%Y-%m-%d %H:%M:%S"), "dislikes": mythread[10],
                "forum": mythread[1], "id": mythread[0], "isClosed": bool(mythread[3]), "isDeleted": bool(mythread[8]),
                "likes": mythread[9], "message": mythread[6], "points": (mythread[9] - mythread[10]),
                "posts": 0, "slug": mythread[7], "title": mythread[2], "user": mythread[4]}}
                return jsonify(returnData)
        else:
            returnData = {"code": 1, "response": "THREAD NOT FOUND"}
            return jsonify(returnData)
    except KeyError:
        returnData = {"code": 2, "response": "invalid json format"}
        return jsonify(returnData)


@app.route('/db/api/thread/restore/', methods = ['POST'])
def thread_restore():
    try:
        data = request.get_json()
        thread = data['thread']
        db = MySQLdb.connect(host='localhost', user="db_api_user", passwd="passwd", db="db_perf_test", charset='utf8')
        cursor = db.cursor()
        q = "select * from threads where thread_id = %d" % (int(thread))
        cursor.execute(q)
        mythread = cursor.fetchone()
        if mythread:
            if mythread[8]:
                q = "update threads set isDeleted = False where thread_id = %d" % (int(thread))
                cursor.execute(q)
                db.commit()
                q = "update posts set isDeleted = False where thread = %d" % (int(thread))
                cursor.execute(q)
                db.commit()
                q = "select count(*) from posts where  thread = %d" % (int(thread))
                cursor.execute(q)
                postcount = cursor.fetchone()
                q = "update threads set posts = %d where thread_id = %d" % (int(postcount[0]), int(thread))
                cursor.execute(q)
                db.commit()

                returnData = {"code": 0, "response": {"thread": thread}}
                return jsonify(returnData)
            else:
                returnData = {"code": 0, "response":{"date": mythread[5].strftime("%Y-%m-%d %H:%M:%S"), "dislikes": mythread[10],
                "forum": mythread[1], "id": mythread[0], "isClosed": bool(mythread[3]), "isDeleted": bool(mythread[8]),
                "likes": mythread[9], "message": mythread[6], "points": (mythread[9] - mythread[10]),
                "posts": mythread[11], "slug": mythread[7], "title": mythread[2], "user": mythread[4]}}

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
        db = MySQLdb.connect(host='localhost', user="db_api_user", passwd="passwd", db="db_perf_test", charset='utf8')
        cursor = db.cursor()
        q = "select * from threads where thread_id = %d" % (int(thread))
        cursor.execute(q)
        mythread = cursor.fetchone()
        if mythread:
            if not mythread[3]:
                q = "update threads set isClosed = True where thread_id = %d" % (int(thread))
                cursor.execute(q)
                db.commit()

                returnData = {"code": 0, "response": {"thread": thread}}
                return jsonify(returnData)
            else:
                returnData = {"code": 0, "response":{"date": mythread[5].strftime("%Y-%m-%d %H:%M:%S"), "dislikes": mythread[10],
                "forum": mythread[1], "id": mythread[0], "isClosed": bool(mythread[3]), "isDeleted": bool(mythread[8]),
                "likes": mythread[9], "message": mythread[6], "points": (mythread[9] - mythread[10]),
                "posts": mythread[11], "slug": mythread[7], "title": mythread[2], "user": mythread[4]}}

                return jsonify(returnData)
        else:
            returnData = {"code": 1, "response": "THREAD NOT FOUND"}
            return jsonify(returnData)
    except KeyError:
        returnData = {"code": 2, "response": "invalid json format"}
        return jsonify(returnData)


@app.route('/db/api/thread/open/', methods=['POST'])
def thread_open():
    try:
        data = request.get_json()
        thread = data['thread']
        db = MySQLdb.connect(host='localhost', user="db_api_user", passwd="passwd", db="db_perf_test", charset='utf8')
        cursor = db.cursor()
        q = "select * from threads where thread_id = %d" % (int(thread))
        cursor.execute(q)
        mythread = cursor.fetchone()
        if mythread:
            if mythread[3]:
                q = "update threads set isClosed = False where thread_id = %d" % (int(thread))
                cursor.execute(q)
                db.commit()

                returnData = {"code": 0, "response": {"thread": thread}}
                return jsonify(returnData)
            else:
                returnData = {"code": 0, "response":{"date": mythread[5].strftime("%Y-%m-%d %H:%M:%S"), "dislikes": mythread[10],
                "forum": mythread[1], "id": mythread[0], "isClosed": bool(mythread[3]), "isDeleted": bool(mythread[8]),
                "likes": mythread[9], "message": mythread[6], "points": (mythread[9] - mythread[10]),
                "posts": mythread[11], "slug": mythread[7], "title": mythread[2], "user": mythread[4]}}

                return jsonify(returnData)
        else:
            returnData = {"code": 1, "response": "THREAD NOT FOUND"}
            return jsonify(returnData)
    except KeyError:
        returnData = {"code": 2, "response": "invalid json format"}
        return jsonify(returnData)


@app.route('/db/api/thread/update/', methods=['POST'])
def thread_update():
    try:
        data = request.get_json()
        thread = data['thread']
        message = data['message']
        slug = data['slug']
        db = MySQLdb.connect(host='localhost', user="db_api_user", passwd="passwd", db="db_perf_test", charset='utf8')
        cursor = db.cursor()
        q = "SELECT * FROM threads where thread_id = %d " % (int(thread))
        cursor.execute(q)
        mythread = cursor.fetchone()
        if mythread:
            if (mythread[6] != message) or (mythread[7] != slug):
                q = "update threads set message = '%s' where thread_id = %d" % (message, thread)
                cursor.execute(q)
                q = "update threads set slug = '%s' where thread_id = %d" % (slug, thread)
                cursor.execute(q)
                db.commit()

                returnData = {"code": 0, "response": {"date": mythread[5].strftime("%Y-%m-%d %H:%M:%S"), "dislikes": mythread[10],
                "forum": mythread[1], "id": mythread[0], "isClosed": bool(mythread[3]), "isDeleted": bool(mythread[8]),
                "likes": mythread[9], "message": message, "points": (mythread[9] - mythread[10]),
                "posts": mythread[11], "slug": slug, "title": mythread[2], "user": mythread[4]}}
                return jsonify(returnData)
            else:
                returnData = {"code": 0, "response":{"date": mythread[5].strftime("%Y-%m-%d %H:%M:%S"), "dislikes": mythread[10],
                "forum": mythread[1], "id": mythread[0], "isClosed": bool(mythread[3]), "isDeleted": bool(mythread[8]),
                "likes": mythread[9], "message": mythread[6], "points": (mythread[9] - mythread[10]),
                "posts": mythread[11], "slug": mythread[7], "title": mythread[2], "user": mythread[4]}}
                return jsonify(returnData)
        else:
            returnData = {"code": 1, "response": "THREAD NOT FOUND"}

            return jsonify(returnData)
    except KeyError:
        returnData = {"code": 2, "response": "invalid json format"}
        return jsonify(returnData)


@app.route('/db/api/thread/vote/', methods=['POST'])
def thread_vote():
    try:
        data = request.get_json()
        vote = data['vote']
        thread = data['thread']
        db = MySQLdb.connect(host='localhost', user="db_api_user", passwd="passwd", db="db_perf_test", charset='utf8')
        cursor = db.cursor()
        q = "SELECT * FROM threads where thread_id = %d " % (int(thread))
        cursor.execute(q)
        mythread = cursor.fetchone()
        if mythread:
            if vote == 1:
                q = "update threads set likes = likes + 1 where thread_id = %d" % (int(thread))
                mylikes = mythread[9] + 1
                mydislikes = mythread[10]
            elif vote == -1:
                q = "update threads set dislikes = dislikes + 1 where thread_id = %d" % (int(thread))
                mylikes = mythread[9]
                mydislikes = mythread[10] + 1
            else:
                returnData = {"code": 3, "response": "invalid syntax"}
                return jsonify(returnData)
            cursor.execute(q)
            db.commit()

            returnData = {"code": 0, "response":{"date": mythread[5].strftime("%Y-%m-%d %H:%M:%S"), "dislikes": mydislikes,
                "forum": mythread[1], "id": mythread[0], "isClosed": bool(mythread[3]), "isDeleted": bool(mythread[8]),
                "likes": mylikes, "message": mythread[6], "points": (mylikes - mydislikes),
                "posts": mythread[11], "slug": mythread[7], "title": mythread[2], "user": mythread[4]}}
            return jsonify(returnData)
        else:
            returnData = {"code": 1, "response": "THREAD NOT FOUND"}

            return jsonify(returnData)

    except KeyError:
        returnData = {"code": 2, "response": "invalid json format"}
        return jsonify(returnData)


@app.route('/db/api/thread/subscribe/', methods=['POST'])
def thread_subscribe():
    try:
        data = request.get_json()
        user = data['user']
        thread = data['thread']
        db = MySQLdb.connect(host='localhost', user="db_api_user", passwd="passwd", db="db_perf_test", charset='utf8')
        cursor = db.cursor()
        q = "SELECT * FROM threads where thread_id = %d " % (int(thread))
        cursor.execute(q)
        mythread = cursor.fetchone()
        q = "SELECT * FROM users where email = '%s'" % (user)
        cursor.execute(q)
        myuser = cursor.fetchone()
        if (not mythread) or (not myuser):
            returnData = {"code": 1, "response": "THREAD or USER NOT FOUND"}

            return jsonify(returnData)
        else:
            q = "select * from subscriptions where user = '%s' and thread_id = %d" % (user, int(thread))
            cursor.execute(q)
            mysub = cursor.fetchone()
            if not mysub:
                q = "insert into subscriptions (user, thread_id) values ('%s', %d)" % (user, thread)
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
    try:
        data = request.get_json()
        user = data['user']
        thread = data['thread']
        db = MySQLdb.connect(host='localhost', user="db_api_user", passwd="passwd", db="db_perf_test", charset='utf8')
        cursor = db.cursor()
        q = "SELECT * FROM threads where thread_id = %d " % (int(thread))
        cursor.execute(q)
        mythread = cursor.fetchone()
        q = "SELECT * FROM users where email = '%s'" % (user)
        cursor.execute(q)
        myuser = cursor.fetchone()
        if (not mythread) or (not myuser):
            returnData = {"code": 1, "response": "THREAD or USER NOT FOUND"}

            return jsonify(returnData)
        else:
            q = "select * from subscriptions where user = '%s' and thread_id = %d" % (user, int(thread))
            cursor.execute(q)
            mysub = cursor.fetchone()
            if mysub:
                q = "delete  from subscriptions where user = '%s' and thread_id = %d" % (user, thread)
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
        q = """INSERT INTO posts (parent, isApproved, isEdited, isSpam, isDeleted, date, message, user, forum,
         thread, isHighlited)
         values (%d, %d, %d, %d, %d, '%s', '%s', '%s', '%s', %d, %d)""" % (parent, isApproved, isEdit, isSpam,
                                                                           isDeleted, date, message,
                                                                           user, forum, thread, isHighlighted)
        db = MySQLdb.connect(host='localhost', user="db_api_user", passwd="passwd", db="db_perf_test", charset='utf8')
        cursor = db.cursor()
        cursor.execute(q)
        if parent == 0:
            parent = None
        returnData = {"code": 0, "response": {"date": date, "forum": forum,
                                              "id": cursor.lastrowid, "isApproved": isApproved,
                                              "isEdited": isEdit, "isHighlited": isHighlighted, "isSpam": isSpam,
                                              "message": message, "parent": parent, "thread": thread, "user": user}}
        db.commit()
        q = """update threads set posts = posts + 1 where thread_id = %d""" % (thread)
        cursor.execute(q)
        db.commit()

        return jsonify(returnData)
    except KeyError:
        returnData = {"code": 2, "response": "invalid json format"}
        return jsonify(returnData)


@app.route('/db/api/post/details/', methods=['GET'])
def post_details():
    post = request.args.get('post', '')
    related = request.args.getlist('related')
    db = MySQLdb.connect(host='localhost', user="db_api_user", passwd="passwd", db="db_perf_test", charset='utf8')
    cursor = db.cursor()
    q = "SELECT * FROM posts where post_id = '%s'" % (post)
    if cursor.execute(q) == 0:
        returnData = {"code": 1, "response": "POST NOT FOUND"}
        return  jsonify(returnData)
    mypost = cursor.fetchone()
    if 'user' in related:
        q = "SELECT * FROM users where email = '%s'" % (mypost[8])
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
        q = "Select who_user from followers where whom_user = '%s'" % (myuser[4])
        cursor.execute(q)
        myfollowers = cursor.fetchall()
        q = "Select whom_user from followers where who_user = '%s'" % (myuser[4])
        cursor.execute(q)
        myfollowing = cursor.fetchall()
        q = "Select thread_id from subscriptions where user = '%s'" % (myuser[4])
        cursor.execute(q)
        mysubs = cursor.fetchall()
        userinfo = {"about": about, "email": myuser[4], "followers":  [x[0] for x in myfollowers],
                    "following": [x[0] for x in myfollowing],
                    "id": myuser[0], "isAnonymous": bool(myuser[5]),
                    "name": name, "subscriptions": [x[0] for x in mysubs],
                    "username": username}
    else:
        userinfo = mypost[8]

    if 'forum' in related:
         q = "SELECT * FROM forums where short_name = '%s'" % (mypost[9])
         cursor.execute(q)
         myforum = cursor.fetchone()
         foruminfo = {"id": myforum[3], "name": myforum[0], "short_name": myforum[1],
                                          "user": myforum[2]}
    else:
         foruminfo = mypost[9]

    if 'thread' in related:
        q = "SELECT * FROM threads where thread_id = '%s'" % (mypost[12])
        cursor.execute(q)
        mythread = cursor.fetchone()
        threadinfo = {"date": mythread[5].strftime("%Y-%m-%d %H:%M:%S"), "dislikes": mythread[10],
                  "forum": mythread[1], "id": mythread[0], "isClosed": bool(mythread[3]), "isDeleted": bool(mythread[8]),
                  "likes": mythread[9], "message": mythread[6], "points": (mythread[9] - mythread[10]),
                  "posts": mythread[11], "slug": mythread[7], "title": mythread[2], "user": mythread[4]}
    else:
        threadinfo = mypost[12]
    if mypost[1] == 0:
        parent = None
    else:
        parent = mypost[1]

    returnData = {"code": 0, "response": {"date": mypost[6].strftime("%Y-%m-%d %H:%M:%S"), "dislikes": mypost[10],
                                          "forum": foruminfo, "id": mypost[0], "isApproved": bool(mypost[2]),
                                          "isDeleted": bool(mypost[5]), "isEdited": bool(mypost[3]),
                                          "isHighlighted": bool(mypost[13]), "isSpam": bool(mypost[4]),
                                          "likes": mypost[11], "message": mypost[7], "parent": parent,
                                          "points": (mypost[11]-mypost[10]), "thread": threadinfo, "user": userinfo}}
    return jsonify(returnData)


@app.route('/db/api/post/list/', methods=['GET'])
def post_list():
    thread = request.args.get('thread', False)
    forum = request.args.get('forum', False)
    if thread and forum:
        returnData = {"code": 3, "response": "bad syntax"}
        return jsonify(returnData)
    limit = request.args.get('limit', False)
    since = request.args.get('since', False)
    order = request.args.get('order', False)
    db = MySQLdb.connect(host='localhost', user="db_api_user", passwd="passwd", db="db_perf_test", charset='utf8')
    cursor = db.cursor()
    q = "SELECT * FROM posts where "
    if thread:
        q += "thread =  %d" % (int(thread))
    else:
        q += "forum = '%s' " % (forum)
    if since:
        q += " and date >= '%s' " % (since)
    if order:
        q += " order by date %s " % (order)
    if limit:
        q += " limit %d" % (int(limit))

    cursor.execute(q)
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
                                          "points": (mypost[11]-mypost[10]), "thread": mypost[12], "user": mypost[8]})
    returnData = {"code": 0, "response": returnposts}
    return jsonify(returnData)


@app.route('/db/api/post/remove/', methods = ['POST'])
def post_remove():
    try:
        data = request.get_json()
        post = data['post']
    except KeyError:
        returnData = {"code": 2, "response": "invalid json format"}
        return jsonify(returnData)
    db = MySQLdb.connect(host='localhost', user="db_api_user", passwd="passwd", db="db_perf_test", charset='utf8')
    cursor = db.cursor()
    q = "SELECT * FROM posts where post_id = %d " % (int(post))
    cursor.execute(q)
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
                                          "points": (mypost[11]-mypost[10]), "thread": mypost[12], "user": mypost[8]}
            returnData = {"code": 0, "response": returnpost}
            return jsonify(returnData)
        else:
            q = "update posts set isDeleted = True where post_id = %d" % (post)
            cursor.execute(q)
            db.commit()
            q = "update threads set posts = posts - 1 where thread_id = %d" % (mypost[12])
            cursor.execute(q)
            db.commit()

            returnData = {"code": 0, "response": {"post": post}}
            return jsonify(returnData)
    else:
        returnData = {"code": 1, "response": "FORUM NOT FOUND"}

        return jsonify(returnData)


@app.route('/db/api/post/restore/', methods = ['POST'])
def post_restore():
    try:
        data = request.get_json()
        post = data['post']
    except KeyError:
        returnData = {"code": 2, "response": "invalid json format"}
        return jsonify(returnData)
    db = MySQLdb.connect(host='localhost', user="db_api_user", passwd="passwd", db="db_perf_test", charset='utf8')
    cursor = db.cursor()
    q = "SELECT * FROM posts where post_id = %d " % (int(post))
    cursor.execute(q)
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
                                          "points": (mypost[11]-mypost[10]), "thread": mypost[12], "user": mypost[8]}
            returnData = {"code": 0, "response": returnpost}
            return jsonify(returnData)
        else:
            q = "update posts set isDeleted = False where post_id = %d" % (post)
            cursor.execute(q)
            db.commit()
            q = "update threads set posts = posts + 1 where thread_id = %d" % (mypost[12])
            cursor.execute(q)
            db.commit()

            returnData = {"code": 0, "response": {"post": post}}
            return jsonify(returnData)
    else:
        returnData = {"code": 1, "response": "POST NOT FOUND"}

        return jsonify(returnData)


@app.route('/db/api/post/update/', methods = ['POST'])
def post_update():
    try:
        data = request.get_json()
        post = data['post']
        message = data['message']
        db = MySQLdb.connect(host='localhost', user="db_api_user", passwd="passwd", db="db_perf_test", charset='utf8')
        cursor = db.cursor()
        q = "SELECT * FROM posts where post_id = %d " % (int(post))
        cursor.execute(q)
        mypost = cursor.fetchone()
        if mypost:
            if not mypost[7] == message:
                q = "update posts set message = '%s' where post_id = %d" % (message, post)
                cursor.execute(q)
                db.commit()
                q = "update posts set isEdited = True where post_id = %d" % (post)
                cursor.execute(q)
                db.commit()

                if mypost[1] == 0:
                    parent = None
                else:
                    parent = mypost[1]
                returnpost = {"date": mypost[6].strftime("%Y-%m-%d %H:%M:%S"), "dislikes": mypost[10],
                                              "forum": mypost[9], "id": mypost[0], "isApproved": bool(mypost[2]),
                                              "isDeleted": bool(mypost[5]), "isEdited": True,
                                              "isHighlighted": bool(mypost[13]), "isSpam": bool(mypost[4]),
                                              "likes": mypost[11], "message": message, "parent": parent,
                                              "points": (mypost[11]-mypost[10]), "thread": mypost[12], "user": mypost[8]}
                returnData = {"code": 0, "response": returnpost}
                return jsonify(returnData)
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
                                              "points": (mypost[11]-mypost[10]), "thread": mypost[12], "user": mypost[8]}
                returnData = {"code": 0, "response": returnpost}
                return jsonify(returnData)
        else:
            returnData = {"code": 1, "response": "POST NOT FOUND"}

            return jsonify(returnData)
    except KeyError:
        returnData = {"code": 2, "response": "invalid json format"}
        return jsonify(returnData)


@app.route('/db/api/post/vote/', methods = ['POST'])
def post_vote():
    try:
        data = request.get_json()
        vote = data['vote']
        post = data['post']
        db = MySQLdb.connect(host='localhost', user="db_api_user", passwd="passwd", db="db_perf_test", charset='utf8')
        cursor = db.cursor()
        q = "SELECT * FROM posts where post_id = %d " % (int(post))
        cursor.execute(q)
        mypost = cursor.fetchone()
        if mypost:
            if vote == 1:
                q = "update posts set likes = likes + 1 where post_id = %d" % (int(post))
                mylikes = mypost[11] + 1
                mydislikes = mypost[10]
            elif vote == -1:
                q = "update posts set dislikes = dislikes + 1 where post_id = %d" % (int(post))
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
            returnpost = {"date": mypost[6].strftime("%Y-%m-%d %H:%M:%S"), "dislikes": mydislikes,
                                              "forum": mypost[9], "id": mypost[0], "isApproved": bool(mypost[2]),
                                              "isDeleted": bool(mypost[5]), "isEdited": bool(mypost[3]),
                                              "isHighlighted": bool(mypost[13]), "isSpam": bool(mypost[4]),
                                              "likes": mylikes, "message": mypost[7], "parent": parent,
                                              "points": (mylikes-mydislikes), "thread": mypost[12], "user": mypost[8]}
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
