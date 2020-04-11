from flask import Flask, request, jsonify
import json

NAMES = []# im create an List what i called Names for save names
app = Flask(__name__)

#init the route /names, when the mothod is GET his return the list o Names in json format
@app.route('/names')
def get_names():
    return jsonify(NAMES)

#get a name by an identifier
@app.route('/names/<int:identifier>')
def get_name_by_id(identifier):
    return jsonify(NAMES[identifier]), 200

#when the method is POST, i create a name and save into the List    
@app.route('/names', methods = ['POST'])
def insert_names():
    name = request.get_json()#get data from body in the request
    NAMES.append(name)#(append): method for save in the last position of List
    return {"Name": "the names has been insert"}, 200

#when the name update, he get data from body and replace the name  by id
@app.route('/names/<int:identifier>', methods = ['PUT'])
def update_names(identifier):
    name = request.get_json()    
    NAMES[identifier] = name
    return {"message": 'name has been update'}, 200

#Delete a name 
@app.route('/names/<int:identifier>', methods = ['DELETE'])
def delete_name(identifier):
    NAMES.pop(identifier)#(pop): method for delete a data by identifier
    return {"message":"the names has been delete"}, 200

if __name__ == '__main__':
    app.run(debug=True)