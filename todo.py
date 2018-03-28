from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
import jwt

app = Flask(__name__)
app.config['SECRET_KEY']='securekey'
app.config['MONGO_DBNAME'] = 's_database'
app.config['MONGO_URI'] = "mongodb://todo:admin@ds119988.mlab.com:19988/s_database"

db = PyMongo(app) 

class Users:
    id = int()
    public_id = str()
    name= str()
    password = str()
    admin= bool()

class Todo:
    id = int()
    complete = bool()
    user_id = int()
    text = str()

@app.route('/user', methods=['GET'])
def get_all_user():

    data= db.db.udata.find()
    output=[]

    for user in data:
        output.append({'public_id':user['public_id'], 'name':user['name'], 'password':user['password'], 'admin':user['admin']})   

    return jsonify({'users' : output})

@app.route('/user/<user_id>', methods=['GET'])
def get_one_user():
    return ' '

@app.route('/user', methods=['POST'])
def create_user():
    data = request.get_json()
    hashedpass= generate_password_hash(data['password'])

    new_user=Users()
    new_user.public_id=str(uuid.uuid4())
    new_user.name=data['name']
    new_user.password= hashedpass
    new_user.admin=False

    db.db.udata.insert({'public_id' : new_user.public_id , 'name' : new_user.name, 'password' : new_user.password
                        ,'admin' : new_user.admin })

    return jsonify({'message' : 'New user added'})

@app.route('/user/<user_id>', methods=['PUT'])
def promote_user():
    return ' '

@app.route('/user/<user_id>', methods=['DELETE'])
def delete_user():
    return ' '

if __name__ == '__main__':
    app.run(debug=True)

