from flask import Flask, render_template, redirect, url_for, request, current_app, flash, send_file, make_response,jsonify
import MySQLdb
import MySQLdb.cursors
import json
import config
import datetime

app = Flask(__name__)


def init_db():
	db = MySQLdb.connect(host=config.host,user=config.user,passwd=config.passwd,db=config.db, cursorclass=MySQLdb.cursors.DictCursor)
	return db

def user_exists(email):
	db = init_db()
	if (db == None):
		return None

	cur = db.cursor()
	cur.execute("SELECT COUNT(*) FROM accounts WHERE email='"+email+"'")
	found = cur.fetchall()[0][0]
	db.close()
	return found

def get_user(email, password):
	db = init_db()
	if (db == None):
		return None

	cur = db.cursor()
	cur.execute("SELECT * FROM accounts WHERE email='"+email+"' AND password='"+password+"'")
	try:
		user = cur.fetchall()[0]
	except:
		user = None
	db.close()
	return user
	#get user's data and return them.

def add_user(firstname, lastname, phone, email, password):
	db = init_db()
	if (db == None):
		return False

	if (user_exists(email)):
		return False

	cur = db.cursor()
	cur.execute("INSERT INTO accounts(firstname,lastname,phone,email,password) VALUES ('"+firstname+"','"+lastname+"',"+phone+",'"+email+"','"+password+"')")
	db.commit()
	db.close()
	return True
	#create user

def update_user(email, car_type, color, plate):
	db = init_db()
	if (db == None):
		return False

	if not(user_exists(email)):
		return False

	cur = db.cursor()
	cur.execute("UPDATE accounts SET is_driver=1, car_type='"+car_type+"', color='"+color+"', plate='"+plate+"' WHERE email='"+email+"'")
	db.commit()
	db.close()
	return True
	#update driver


def add_ride(driver_id, departure, from_lng, from_lat, to_lng, to_lat, fare, seats_available, comment):
	db = init_db()
	if (db == None):
		return False

	cur = db.cursor()
	cur.execute("INSERT INTO rides(driver_id, departure, from_lng, from_lat, to_lng, to_lat, fare, seats_available, comment) VALUES ("+str(driver_id)+",'"+departure+"',"+str(from_lng)+",'"+str(from_lat)+"','"+str(to_lng)+"','"+str(to_lat)+"',"+str(fare)+","+str(seats_available)+",'"+comment+"')")
	db.commit()
	db.close()
	return True


def delete_ride(ride_id):
	db = init_db()
	if (db == None):
		return False

	cur = db.cursor()
	cur.execute("SELECT COUNT(*) FROM rides WHERE id="+str(ride_id))
	if (int(cur.fetchall()[0][0]) == 0):
		return False;

	cur.execute("DELETE from rides WHERE id="+str(ride_id))
	db.commit()
	db.close()
	return True


def check_rides(departure, from_lng, from_lat, to_lng, to_lat):
	db = init_db()
	if (db == None):
		return None

	cur = db.cursor()

	cur.execute("""SELECT * FROM rides INNER JOIN accounts ON accounts.id=rides.driver_id 
		 WHERE departure >= %(min)s AND departure <= %(max)s 
		AND from_lng >= %(min_from_lng)s AND from_lat >= %(min_from_lat)s AND from_lng <= %(max_from_lng)s AND from_lat <= %(max_from_lat)s
		AND to_lng >= %(min_to_lng)s AND to_lat >= %(min_to_lat)s AND to_lng <= %(max_to_lng)s AND to_lat <= %(max_to_lat)s"""

		, {'min': datetime.datetime.strptime(departure, '%Y-%m-%d %H:%M:%S') - datetime.timedelta(hours=1),'max': datetime.datetime.strptime(departure, '%Y-%m-%d %H:%M:%S') + datetime.timedelta(hours=1)
		,'min_from_lng': from_lng-config.lng_clearance,'min_from_lat': from_lat-config.lat_clearance
		,'max_from_lng': from_lng+config.lng_clearance,'max_from_lat': from_lat+config.lat_clearance
		,'min_to_lng': to_lng-config.lng_clearance,'min_to_lat': to_lat-config.lat_clearance
		,'max_to_lng': to_lng+config.lng_clearance,'max_to_lat': to_lat+config.lat_clearance})

	rides = cur.fetchall()
	db.close()

	rides = list(rides)

	for ride in rides:
		ride["departure"] = str(ride["departure"])
		ride["from_lng"] = str(ride["from_lng"])
		ride["from_lat"] = str(ride["from_lat"])
		ride["to_lng"] = str(ride["to_lng"])
		ride["to_lat"] = str(ride["to_lat"])

	return rides

@app.route('/api/v1/login', methods=['GET'])
def login():
	if request.method == 'GET':
		try:
			received_data = json.loads(request.get_data())
			user = get_user(received_data['email'],received_data['password'])
			print(user)
			if (user == None):
				return jsonify({"authorized":False})

			return jsonify({"authorized":True,"id":user[0],"firstname":user[1],"lastname":user[2],"phone":user[3],"email":user[4],"is_driver":user[6],"car_type":user[7],"color":user[8],"plate":user[9]})
		except:
			return jsonify({"authorized":False})
	else:
		return jsonify({"authorized":False})

@app.route('/api/v1/signup', methods=['POST'])
def signup():
	if request.method == 'POST':
		try:
			received_data = json.loads(request.get_data())
			success = add_user(received_data['firstname'], received_data['lastname'], received_data['phone'], received_data['email'], received_data['password'])
			return jsonify({"success":success})
		except:
			return jsonify({"success":False})
	else:
		return jsonify({"success":False})

@app.route('/api/v1/update', methods=['POST'])
def update():
	if request.method == 'POST':
		try:
			received_data = json.loads(request.get_data())
			success = update_user(received_data['email'], received_data['car_type'], received_data['color'], received_data['plate'])
			return jsonify({"success":success})
		except:
			return jsonify({"success":False})
	else:
		return jsonify({"success":False})


@app.route('/api/v1/add', methods=['POST'])
def add():
	received_data = json.loads(request.get_data())
	#success = add_ride(received_data['driver_id'], received_data['departure'], received_data['from_lng'], received_data['from_lat'], received_data['to_lng'], received_data['to_lat'], received_data['fare'], received_data['seats_available'], received_data['comment'])
	#print(success)
	if request.method == 'POST':
		try:
			received_data = json.loads(request.get_data())
			success = add_ride(received_data['driver_id'], received_data['departure'], received_data['from_lng'], received_data['from_lat'], received_data['to_lng'], received_data['to_lat'], received_data['fare'], received_data['seats_available'], received_data['comment'])
			return jsonify({"success":success})
		except:
			return jsonify({"success":False})
	else:
		return jsonify({"success":False})

@app.route('/api/v1/delete', methods=['DELETE'])
def delete():
	if request.method == 'DELETE':
		try:
			received_data = json.loads(request.get_data())
			success = delete_ride(received_data['id'])
			return jsonify({"success":success})
		except:
			return jsonify({"success":False})
	else:
		return jsonify({"success":False})

@app.route('/api/v1/check', methods=['GET'])
def check():
	if request.method == 'GET':
		received_data = json.loads(request.get_data())

		#rides = check_rides(received_data['departure'], received_data['from_lng'], received_data['from_lat'], received_data['to_lng'], received_data['to_lat'])

		#print(json.dumps(rides))
		try:
			received_data = json.loads(request.get_data())
			#user = get_user(received_data['email'],received_data['password'])
			rides = check_rides(received_data['departure'], received_data['from_lng'], received_data['from_lat'], received_data['to_lng'], received_data['to_lat'])
			if (rides == None):
				return jsonify({})

			return json.dumps(rides)
		except:
			return jsonify({})
	else:
		return jsonify({})
	
#@app.route('/api/v1/request', methods=['POST'])
#def request():
#	return jsonify({"authorized":True})


app.run("0.0.0.0",debug = True,port=80)