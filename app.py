from flask import Flask, jsonify, request
import MySQLdb
from _mysql_exceptions import IntegrityError
from func import *

app = Flask(__name__)


@app.route('/db/api/clear/', methods=['POST'])
def clear():
    db = db_connect()
    cursor = db.cursor()
    clear_execute(cursor)
    db.commit()
    db.close()
    code = 0
    return_data = {"code": code, "response": "OK"}
    return jsonify(return_data)


@app.route('/db/api/status/', methods=['GET'])
def status():
    db = db_connect()
    cursor = db.cursor()
    return_data = status_execute(cursor)
    return return_data


if __name__ == '__main__':
    app.run()
