"""2021-08-08 migration"""

name = "20200406_users_collection"
dependencies = []

def upgrade(db):
    db.create_collection('users')
    db.users.insert([
        {
           '_id': '01921092019201',
           'name': 'pollo frito',
           'email': 'test@kfc.com', 
           'avatar': 'http://imagen.png',
           'hobbys': []
        }])