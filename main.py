import json
import random
import secrets
from flask_cors import CORS
from idlelib.rpc import request_queue

from flask import Flask, abort, request

with open("database.json", "r") as f:
    database = json.load(f)

app = Flask(__name__)

CORS(app)

@app.route('/')
def hello():
    return 'Hello World!'


def save_database():
    with open('database.json', 'w', encoding='utf-8') as file:
        json.dump(database, file, ensure_ascii=False, indent=4)


def find_user(email):
    for key in database['users'].keys():
        if database['users'][key]['email'] == email:
            return key

    return -1


logged_in_users = {}
tokens = {}


@app.route('/login', methods=['POST'])
def login():
    request_json = request.get_json()
    if request_json.keys() != {'email', 'password_hash'}:
        return 'Payload must be {}, not {}'.format({'email', 'password_hash'}, request_json.keys()), 400

    user_id = find_user(request_json['email'])
    if user_id == -1:
        abort(404)

    if database['users'][user_id]['password_hash'] != request_json['password_hash']:
        abort(401)

    if user_id in logged_in_users:
        return logged_in_users[user_id], 200

    token = secrets.token_hex(32)
    tokens[token] = user_id
    logged_in_users[user_id] = token
    return token, 200


@app.route('/logout', methods=['POST'])
def logout():
    request_json = request.get_json()
    if request_json.keys() != {'auth_token'}:
        return 'Payload must be {}, not {}'.format({'auth_token'}, request_json.keys()), 400

    if request_json["auth_token"] not in tokens:
        abort(404)

    user_id = tokens[request_json["auth_token"]]
    del logged_in_users[user_id]
    del tokens[request_json["auth_token"]]

    return 'Logged out successfully', 200


### GET ALL ENTRIES METHODS ###

def all_entries(name):
    return [dict({'id': key}, **database[name][key]) for key in database[name].keys()]


@app.route('/users')
def get_users():
    return all_entries('users')


@app.route('/houses')
def get_houses():
    return all_entries('houses')


@app.route('/devices')
def get_devices():
    return all_entries('devices')


@app.route('/schedules')
def get_schedules():
    return all_entries('schedules')


@app.route('/usage_records')
def get_usage_records():
    return all_entries('usage_records')


@app.route('/tariffs')
def get_tariffs():
    return all_entries('tariffs')


@app.route('/photovoltaic_systems')
def get_photovoltaic_systems():
    return all_entries('photovoltaic_systems')


@app.route('/batteries')
def get_batteries():
    return all_entries('batteries')


@app.route('/production_records')
def get_production_records():
    return all_entries('production_records')


### GET SINGLE ENTRY METHODS ###

def get_entry(name, _id, user_id):
    if 'auth_token' not in request.get_json():
        return 'auth_token needed in payload', 400
    token = request.get_json()['auth_token']
    if user_id not in logged_in_users or logged_in_users[user_id] != token:
        abort(401)

    return database[name][_id]


@app.route('/user/<string:_id>')
def get_user(_id):
    if _id not in database['users']:
        abort(404)
    return get_entry('users', _id, _id)


@app.route('/house/<string:_id>')
def get_house(_id):
    if _id not in database['houses']:
        abort(404)

    user_id = database['houses'][_id]['user_id']
    return get_entry('houses', _id, user_id)


@app.route('/device/<string:_id>')
def get_device(_id):
    if _id not in database['devices']:
        abort(404)

    house_id = database['devices'][_id]['house_id']
    user_id = database['houses'][house_id]['user_id']
    return get_entry('devices', _id, user_id)


@app.route('/schedule/<string:_id>')
def get_schedule(_id):
    if _id not in database['schedules']:
        abort(404)

    device_id = database['schedules'][_id]['device_id']
    house_id = database['devices'][device_id]['house_id']
    user_id = database['houses'][house_id]['user_id']
    return get_entry('schedules', _id, user_id)


@app.route('/usage_record/<string:_id>')
def get_usage_record(_id):
    if _id not in database['usage_records']:
        abort(404)

    device_id = database['usage_records'][_id]['device_id']
    house_id = database['devices'][device_id]['house_id']
    user_id = database['houses'][house_id]['user_id']
    return get_entry('usage_records', _id, user_id)


@app.route('/tariff/<string:_id>')
def get_tariff(_id):
    if _id not in database['tariffs']:
        abort(404)

    if 'auth_token' not in request.get_json():
        return 'auth_token needed in payload', 400
    token = request.get_json()['auth_token']
    return get_entry('tariffs', _id, tokens[token])


@app.route('/photovoltaic_system/<string:_id>')
def get_photovoltaic_system(_id):
    if _id not in database['photovoltaic_systems']:
        abort(404)

    house_id = database['photovoltaic_systems'][_id]['house_id']
    user_id = database['houses'][house_id]['user_id']
    return get_entry('photovoltaic_systems', _id, user_id)


@app.route('/battery/<string:_id>')
def get_battery(_id):
    if _id not in database['batteries']:
        abort(404)

    photovoltaic_system_id = database['batteries'][_id]['photovoltaic_system_id']
    house_id = database['photovoltaic_systems'][photovoltaic_system_id]['house_id']
    user_id = database['houses'][house_id]['user_id']
    return get_entry('batteries', _id, user_id)


@app.route('/production_record/<string:_id>')
def get_production_record(_id):
    if _id not in database['production_records']:
        abort(404)

    photovoltaic_system_id = database['production_records'][_id]['photovoltaic_system_id']
    house_id = database['photovoltaic_systems'][photovoltaic_system_id]['house_id']
    user_id = database['houses'][house_id]['user_id']
    return get_entry("production_records", _id, user_id)


### DELETE METHODS ###

def del_entry(name, _id, user_id):
    if 'auth_token' not in request.get_json():
        return 'auth_token needed in payload', 400
    token = request.get_json()['auth_token']
    if user_id not in logged_in_users or logged_in_users[user_id] != token:
        abort(401)

    del database[name][_id]
    save_database()
    return '', 204


@app.route('/user/<string:_id>', methods=['DELETE'])
def del_user(_id):
    if _id not in database['users']:
        abort(404)
    return del_entry('users', _id, _id)


@app.route('/house/<string:_id>', methods=['DELETE'])
def del_house(_id):
    if _id not in database['houses']:
        abort(404)

    user_id = database['houses'][_id]['user_id']
    return del_entry('houses', _id, user_id)


@app.route('/device/<string:_id>', methods=['DELETE'])
def del_device(_id):
    if _id not in database['devices']:
        abort(404)

    house_id = database['devices'][_id]['house_id']
    user_id = database['houses'][house_id]['user_id']
    return del_entry('devices', _id, user_id)


@app.route('/schedule/<string:_id>', methods=['DELETE'])
def del_schedule(_id):
    if _id not in database['schedules']:
        abort(404)

    device_id = database['schedules'][_id]['device_id']
    house_id = database['devices'][device_id]['house_id']
    user_id = database['houses'][house_id]['user_id']
    return del_entry('schedules', _id, user_id)


@app.route('/usage_record/<string:_id>', methods=['DELETE'])
def del_usage_record(_id):
    if _id not in database['usage_records']:
        abort(404)

    device_id = database['usage_records'][_id]['device_id']
    house_id = database['devices'][device_id]['house_id']
    user_id = database['houses'][house_id]['user_id']
    return del_entry('usage_records', _id, user_id)


@app.route('/tariff/<string:_id>', methods=['DELETE'])
def del_tariff(_id):
    if _id not in database['tariffs']:
        abort(404)

    if 'auth_token' not in request.get_json():
        return 'auth_token needed in payload', 400
    token = request.get_json()['auth_token']
    return del_entry('tariffs', _id, tokens[token])


@app.route('/photovoltaic_system/<string:_id>', methods=['DELETE'])
def del_photovoltaic_system(_id):
    if _id not in database['photovoltaic_systems']:
        abort(404)

    house_id = database['photovoltaic_systems'][_id]['house_id']
    user_id = database['houses'][house_id]['user_id']
    return del_entry('photovoltaic_systems', _id, user_id)


@app.route('/battery/<string:_id>', methods=['DELETE'])
def del_battery(_id):
    if _id not in database['batteries']:
        abort(404)

    photovoltaic_system_id = database['batteries'][_id]['photovoltaic_system_id']
    house_id = database['photovoltaic_systems'][photovoltaic_system_id]['house_id']
    user_id = database['houses'][house_id]['user_id']
    return del_entry('batteries', _id, user_id)


@app.route('/production_record/<string:_id>', methods=['DELETE'])
def del_production_record(_id):
    if _id not in database['production_records']:
        abort(404)

    photovoltaic_system_id = database['production_records'][_id]['photovoltaic_system_id']
    house_id = database['photovoltaic_systems'][photovoltaic_system_id]['house_id']
    user_id = database['houses'][house_id]['user_id']
    return del_entry("production_records", _id, user_id)


### PATCH METHODS ###

def patch_entry(name, _id, user_id, not_allowed_keys=None, unique_keys=None):
    if unique_keys is None:
        unique_keys = set()
    if not_allowed_keys is None:
        not_allowed_keys = set()

    if 'auth_token' not in request.get_json():
        return 'auth_token needed in payload', 400
    token = request.get_json()['auth_token']
    if user_id not in logged_in_users or logged_in_users[user_id] != token:
        abort(401)

    request_json = request.get_json()
    not_common_keys = request_json.keys() - (database[name][_id].keys() | {'auth_token'})
    not_common_keys -= not_allowed_keys
    if len(not_common_keys) > 0:
        return "{} keys not allowed".format(not_common_keys), 400

    for key in unique_keys:
        if key in request_json and not all([request_json[key] != item[key] for item in database[name].values()]):
            return '"{}": "{}" already in different item'.format(key, request_json[key]), 403
    
    del request_json['auth_token']
    
    database[name][_id].update(request_json)
    save_database()
    return database[name][_id]


@app.route('/user/<string:_id>', methods=['PATCH'])
def patch_user(_id):
    if _id not in database['users']:
        abort(404)
    return patch_entry('users', _id, _id, unique_keys={'email'})


@app.route('/house/<string:_id>', methods=['PATCH'])
def patch_house(_id):
    if _id not in database['houses']:
        abort(404)

    user_id = database['houses'][_id]['user_id']
    return patch_entry('houses', _id, user_id)


@app.route('/device/<string:_id>', methods=['PATCH'])
def patch_device(_id):
    if _id not in database['devices']:
        abort(404)

    house_id = database['devices'][_id]['house_id']
    user_id = database['houses'][house_id]['user_id']
    return patch_entry('devices', _id, user_id)


@app.route('/schedule/<string:_id>', methods=['PATCH'])
def patch_schedule(_id):
    if _id not in database['schedules']:
        abort(404)

    device_id = database['schedules'][_id]['device_id']
    house_id = database['devices'][device_id]['house_id']
    user_id = database['houses'][house_id]['user_id']
    return patch_entry('schedules', _id, user_id)


@app.route('/usage_record/<string:_id>', methods=['PATCH'])
def patch_usage_record(_id):
    if _id not in database['usage_records']:
        abort(404)

    device_id = database['usage_records'][_id]['device_id']
    house_id = database['devices'][device_id]['house_id']
    user_id = database['houses'][house_id]['user_id']
    return patch_entry('usage_records', _id, user_id)


@app.route('/tariff/<string:_id>', methods=['PATCH'])
def patch_tariff(_id):
    if _id not in database['tariffs']:
        abort(404)

    if 'auth_token' not in request.get_json():
        return 'auth_token needed in payload', 400
    token = request.get_json()['auth_token']
    return patch_entry('tariffs', _id, tokens[token])


@app.route('/photovoltaic_system/<string:_id>', methods=['PATCH'])
def patch_photovoltaic_system(_id):
    if _id not in database['photovoltaic_systems']:
        abort(404)

    house_id = database['photovoltaic_systems'][_id]['house_id']
    user_id = database['houses'][house_id]['user_id']
    return patch_entry('photovoltaic_systems', _id, user_id)


@app.route('/battery/<string:_id>', methods=['PATCH'])
def patch_battery(_id):
    if _id not in database['batteries']:
        abort(404)

    photovoltaic_system_id = database['batteries'][_id]['photovoltaic_system_id']
    house_id = database['photovoltaic_systems'][photovoltaic_system_id]['house_id']
    user_id = database['houses'][house_id]['user_id']
    return patch_entry('batteries', _id, user_id)


@app.route('/production_record/<string:_id>', methods=['PATCH'])
def patch_production_record(_id):
    if _id not in database['production_records']:
        abort(404)

    photovoltaic_system_id = database['production_records'][_id]['photovoltaic_system_id']
    house_id = database['photovoltaic_systems'][photovoltaic_system_id]['house_id']
    user_id = database['houses'][house_id]['user_id']
    return patch_entry("production_records", _id, user_id)


### POST METHODS ###

def post_entry(name, mandatory_keys, unique_keys=None):
    if unique_keys is None:
        unique_keys = set()
    request_json = request.get_json()

    missed_keys = mandatory_keys - request_json.keys()
    if len(missed_keys) > 0:
        return "{} keys must be included".format(missed_keys), 400

    extra_keys = request_json.keys() - (mandatory_keys | {'auth_token'})
    if len(extra_keys) > 0:
        return "{} keys not allowed".format(extra_keys), 400

    for key in unique_keys:
        if key in request_json and not all([request_json[key] != item[key] for item in database[name].values()]):
            return '"{}": "{}" already in different item'.format(key, request_json[key]), 403

    new_id = str(random.randint(1, 99999999))
    while new_id in database[name]:
        new_id = str(random.randint(1, 99999999))

    del request_json['auth_token']

    database[name][new_id] = request_json
    save_database()
    return database[name][new_id]


@app.route('/user', methods=['POST'])
def post_user():
    return post_entry('users', {'email', 'password_hash', 'name'}, unique_keys={'email'})


@app.route('/house', methods=['POST'])
def post_house():
    if 'auth_token' not in request.get_json():
        return 'auth_token needed in payload', 400
    token = request.get_json()['auth_token']
    if token not in tokens:
        abort(401)

    request.get_json()['user_id'] = tokens[token]

    user_id = database['houses'][tokens[token]]['user_id']
    if tokens[token] != user_id:
        abort(401)

    return post_entry('houses', {'user_id', 'address', 'name'})


@app.route('/device', methods=['POST'])
def post_device():
    if 'auth_token' not in request.get_json():
        return 'auth_token needed in payload', 400
    token = request.get_json()['auth_token']
    if token not in tokens:
        abort(401)

    house_id = database['devices'][tokens[token]]['house_id']
    user_id = database['houses'][house_id]['user_id']
    
    if tokens[token] != user_id:
        abort(401)

    return post_entry('devices', {'house_id', 'name', 'nominal_power_kw'})


@app.route('/schedule', methods=['POST'])
def post_schedule():
    if 'auth_token' not in request.get_json():
        return 'auth_token needed in payload', 400
    token = request.get_json()['auth_token']
    if token not in tokens:
        abort(401)

    device_id = database['schedules'][tokens[token]]['device_id']
    house_id = database['devices'][device_id]['house_id']
    user_id = database['houses'][house_id]['user_id']
    
    if tokens[token] != user_id:
        abort(401)
    
    return post_entry('schedules', {'device_id', 'day_of_week', 'start_time', 'end_time'})


@app.route('/usage_record', methods=['POST'])
def post_usage_record():
    if 'auth_token' not in request.get_json():
        return 'auth_token needed in payload', 400
    token = request.get_json()['auth_token']
    if token not in tokens:
        abort(401)

    device_id = database['usage_records'][tokens[token]]['device_id']
    house_id = database['devices'][device_id]['house_id']
    user_id = database['houses'][house_id]['user_id']

    if tokens[token] != user_id:
        abort(401)

    return post_entry('usage_records', {'device_id', 'date', 'start_time', 'end_time', 'total_consumption_kw', 'cost'})


@app.route('/tariff', methods=['POST'])
def post_tariff():
    return post_entry('tariffs', {'name', 'day_rate_kwh', 'night_rate_kwh', 'day_start', 'night_start'})


@app.route('/photovoltaic_system', methods=['POST'])
def post_photovoltaic_system():
    if 'auth_token' not in request.get_json():
        return 'auth_token needed in payload', 400
    token = request.get_json()['auth_token']
    if token not in tokens:
        abort(401)

    house_id = database['photovoltaic_systems'][tokens[token]]['house_id']
    user_id = database['houses'][house_id]['user_id']

    if tokens[token] != user_id:
        abort(401)

    return post_entry('photovoltaic_systems', {'house_id', 'panel_area_m2', 'max_power_kw'})


@app.route('/battery', methods=['POST'])
def post_battery():
    if 'auth_token' not in request.get_json():
        return 'auth_token needed in payload', 400
    token = request.get_json()['auth_token']
    if token not in tokens:
        abort(401)

    photovoltaic_system_id = database['batteries'][tokens[token]]['photovoltaic_system_id']
    house_id = database['photovoltaic_systems'][photovoltaic_system_id]['house_id']
    user_id = database['houses'][house_id]['user_id']

    if tokens[token] != user_id:
        abort(401)

    return post_entry('batteries', {'photovoltaic_system_id', 'capacity_kwh', 'current_charge_kwh'})


@app.route('/production_record', methods=['POST'])
def post_production_record():
    if 'auth_token' not in request.get_json():
        return 'auth_token needed in payload', 400
    token = request.get_json()['auth_token']
    if token not in tokens:
        abort(401)

    photovoltaic_system_id = database['production_records'][tokens[token]]['photovoltaic_system_id']
    house_id = database['photovoltaic_systems'][photovoltaic_system_id]['house_id']
    user_id = database['houses'][house_id]['user_id']

    if tokens[token] != user_id:
        abort(401)

    return post_entry('production_records', {'photovoltaic_system_id', 'date', 'produced_energy_kwh'})


if __name__ == '__main__':
    app.run(debug=True)
