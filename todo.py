from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
import jwt
import datetime
from functools import wraps

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

def token_required(f):
    @wraps(f)
    def decorated(*args,**kwargs):
        token = None

        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']
        
        if not token:
            return jsonify({'message' : 'token is missing'}) , 401
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'])
            current_user = db.db.udata.find_one({'public_id' : data['public_id']})
        except:
            return jsonify({'message' : 'token is invalid'})        

        return f(current_user,*args,**kwargs)

    return decorated


@app.route('/user', methods=['GET'])
@token_required
def get_all_user(current_user):

    if not current_user['admin']:
        return jsonify({'message' : 'you can not have access'})

    data= db.db.udata.find()
    output=[]

    for user in data:
        output.append({'public_id':user['public_id'], 'name':user['name'], 'password':user['password'], 'admin':user['admin']})   

    return jsonify({'users' : output})

@app.route('/user/<public_id>', methods=['GET'])
@token_required
def get_one_user(current_user,public_id):
    
    if not current_user['admin']:
        return jsonify({'message' : 'you can not have access'})

    data = db.db.udata.find_one({'public_id' : public_id})
    
    if not data:
        return jsonify({'message' : 'no user found'})

    return jsonify({'user' : {'public_id':data['public_id'], 'name':data['name'], 'password':data['password'], 'admin':data['admin']}})

@app.route('/user', methods=['POST'])
@token_required
def create_user(current_user):

    if not current_user['admin']:
        return jsonify({'message' : 'you can not have access'})

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

@app.route('/user/<public_id>', methods=['PUT'])
@token_required
def promote_user(current_user,public_id):

    if not current_user['admin']:
        return jsonify({'message' : 'you can not have access'})

    result=db.db.udata.update({ "public_id" : public_id } , { '$set' : { "admin" : 'True' }} )
    
    if result['nModified'] > 0:  
        return jsonify({'message' : 'user updated'})

    return jsonify({'message' : 'no user found'})
    

@app.route('/user/<public_id>', methods=['DELETE'])
@token_required
def delete_user(current_user,public_id):

    if not current_user['admin']:
        return jsonify({'message' : 'you can not have access'})

    result = db.db.udata.remove({"public_id": public_id})
    
    if result['n'] > 0:
        return jsonify({'message' : 'user deleted'})
    
    return jsonify({'message' : 'no such user found'})

@app.route('/login')
def login():
    auth =request.authorization

    if not auth and not auth.username and not auth.password:
        return make_reponse('Could not verify' , 401, {'WWW-Authntication' : 'Basic-realm="Login required"'})
    user = db.db.udata.find_one({'name':auth.username})
    
    if not user:
        return make_reponse('Could not verify' , 401, {'WWW-Authntication' : 'Basic-realm="Login required"'})
    
    if check_password_hash(user['password'] ,auth.password ):
        token = jwt.encode({ 'public_id' : user['public_id'] , 'exp' : datetime.datetime.utcnow()+ datetime.timedelta(minutes = 30) }, app.config['SECRET_KEY'])
        return jsonify({'token' : token.decode('UTF-8')})
    return make_reponse('Could not verify' , 401, {'WWW-Authntication' : 'Basic-realm="Login required"'})

@app.route('/todo', methods=['GET'])
@token_required
def get_all_todo(current_user):

    data = db.db.utodo.find({'user_id' : current_user['public_id']})
    
    if not data:
        return jsonify({'message' : 'no Todo yet'})
    
    todo=[]

    for dat in data:
        todo.append({ 'id' : dat['id'], 'text' : dat['text'], 'complete' : dat['complete']})

    return jsonify({'todo' : todo })

@app.route('/todo/<todo_id>', methods=['GET'])
@token_required
def get_todo(current_user,todo_id):
    data = db.db.utodo.find({'user_id' : current_user['public_id']})
    print(todo_id)
    if not data:
        return jsonify({'message' : 'no Todo yet'})
    
    todo=[]
    for dat in data:
        print(dat['id'])
        if int(todo_id) == dat['id']:
            todo.append({ 'id' : dat['id'], 'text' : dat['text'], 'complete' : dat['complete']})

    return jsonify({'todo' : todo})


@app.route('/todo', methods=['POST'])
@token_required
def create_todo(current_user):
    data = request.get_json()

    td= Todo()
    td.complete=False
    td.text=data['text']
    td.user_id=current_user['public_id']
    
    data=db.db.utodo.find({'user_id' : current_user['public_id']})

    if not data:
        td.id = 0
    else : 
        for dat in data:
            td.id=dat['id']
        td.id=td.id+1

    db.db.utodo.insert({'user_id' : td.user_id, 'complete': td.complete , 'text' : td.text, 'id' : td.id })

    return jsonify({'messgae' : 'todo has been added'})

@app.route('/todo/<todo_id>', methods=['DELETE'])
@token_required
def delete_todo(current_user, todo_id):

    result = db.db.utodo.remove({"user_id": current_user['public_id'] , 'id' : int(todo_id)})
    
    if result['n'] > 0:
        return jsonify({'message' : 'todo deleted'})
    
    return jsonify({'message' : 'no such todo found'})

@app.route('/todo/<todo_id>', methods=['PUT'])
@token_required
def complete_todo(current_user, todo_id):

    result=db.db.utodo.update({ "user_id" : current_user['public_id'] , 'id' : int(todo_id) } , { '$set' : { "complete" : 'True' }} )
    
    if result['nModified'] > 0:  
        return jsonify({'message' : 'todo updated'})

    return jsonify({'message' : 'no todo found'})
    

if __name__ == '__main__':
    app.run(debug=True)

