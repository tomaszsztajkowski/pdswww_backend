import json
import random
from idlelib.rpc import request_queue

from flask import Flask, abort, request

with open("database.json", "r") as f:
    database = json.load(f)

app = Flask(__name__)


@app.route('/')
def hello():
    return 'Hello World!'


def save_database():
    with open('database.json', 'w', encoding='utf-8') as file:
        json.dump(database, file, ensure_ascii=False, indent=4)


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

def get_entry(name, _id):
    if _id in database[name]:
        return database[name][_id]
    abort(404)


@app.route('/user/<string:_id>')
def get_user(_id):
    return get_entry('users', _id)


@app.route('/house/<string:_id>')
def get_house(_id):
    return get_entry('houses', _id)


@app.route('/device/<string:_id>')
def get_device(_id):
    return get_entry('devices', _id)


@app.route('/schedule/<string:_id>')
def get_schedule(_id):
    return get_entry('schedules', _id)


@app.route('/usage_record/<string:_id>')
def get_usage_record(_id):
    return get_entry('usage_records', _id)


@app.route('/tariff/<string:_id>')
def get_tariff(_id):
    return get_entry('tariffs', _id)


@app.route('/photovoltaic_system/<string:_id>')
def get_photovoltaic_system(_id):
    return get_entry('photovoltaic_systems', _id)


@app.route('/battery/<string:_id>')
def get_battery(_id):
    return get_entry('batteries', _id)


@app.route('/production_record/<string:_id>')
def get_production_record(_id):
    return get_entry("production_records", _id)


### DELETE METHODS ###

def del_entry(name, _id):
    if _id in database[name]:
        del database[name][_id]
        save_database()
        return '', 204
    else:
        abort(404)


@app.route('/user/<string:_id>', methods=['DELETE'])
def del_user(_id):
    return del_entry('users', _id)


@app.route('/house/<string:_id>', methods=['DELETE'])
def del_house(_id):
    return del_entry('houses', _id)


@app.route('/device/<string:_id>', methods=['DELETE'])
def del_device(_id):
    return del_entry('devices', _id)


@app.route('/schedule/<string:_id>', methods=['DELETE'])
def del_schedule(_id):
    return del_entry('schedules', _id)


@app.route('/usage_record/<string:_id>', methods=['DELETE'])
def del_usage_record(_id):
    return del_entry('usage_records', _id)


@app.route('/tariff/<string:_id>', methods=['DELETE'])
def del_tariff(_id):
    return del_entry('tariffs', _id)


@app.route('/photovoltaic_system/<string:_id>', methods=['DELETE'])
def del_photovoltaic_system(_id):
    return del_entry('photovoltaic_systems', _id)


@app.route('/battery/<string:_id>', methods=['DELETE'])
def del_battery(_id):
    return del_entry('batteries', _id)


@app.route('/production_record/<string:_id>', methods=['DELETE'])
def del_production_record(_id):
    return del_entry("production_records", _id)


### PATCH METHODS ###

def patch_entry(name, _id, not_allowed_keys=None, unique_keys=None):
    if unique_keys is None:
        unique_keys = set()
    if not_allowed_keys is None:
        not_allowed_keys = set()

    if _id in database[name]:
        request_json = request.get_json()
        not_common_keys = request_json.keys() - database[name][_id].keys()
        not_common_keys -= not_allowed_keys
        if len(not_common_keys) > 0:
            return "{} keys not allowed".format(not_common_keys), 400

        for key in unique_keys:
            if key in request_json and not all([request_json[key] != item[key] for item in database[name].values()]):
                return '"{}": "{}" already in different item'.format(key, request_json[key]), 403

        database[name][_id].update(request_json)
        save_database()
        return database[name][_id]
    else:
        abort(404)


@app.route('/user/<string:_id>', methods=['PATCH'])
def patch_user(_id):
    return patch_entry('users', _id, unique_keys={'email'})


@app.route('/house/<string:_id>', methods=['PATCH'])
def patch_house(_id):
    return patch_entry('houses', _id)


@app.route('/device/<string:_id>', methods=['PATCH'])
def patch_device(_id):
    return patch_entry('devices', _id)


@app.route('/schedule/<string:_id>', methods=['PATCH'])
def patch_schedule(_id):
    return patch_entry('schedules', _id)


@app.route('/usage_record/<string:_id>', methods=['PATCH'])
def patch_usage_record(_id):
    return patch_entry('usage_records', _id)


@app.route('/tariff/<string:_id>', methods=['PATCH'])
def patch_tariff(_id):
    return patch_entry('tariffs', _id)


@app.route('/photovoltaic_system/<string:_id>', methods=['PATCH'])
def patch_photovoltaic_system(_id):
    return patch_entry('photovoltaic_systems', _id)


@app.route('/battery/<string:_id>', methods=['PATCH'])
def patch_battery(_id):
    return patch_entry('batteries', _id)


@app.route('/production_record/<string:_id>', methods=['PATCH'])
def patch_production_record(_id):
    return patch_entry("production_records", _id)


### POST METHODS ###

def post_entry(name, mandatory_keys, unique_keys=None):
    if unique_keys is None:
        unique_keys = set()
    request_json = request.get_json()

    missed_keys = mandatory_keys - request_json.keys()
    if len(missed_keys) > 0:
        return "{} keys must be included".format(missed_keys), 400
    
    extra_keys = request_json.keys() - mandatory_keys
    if len(extra_keys) > 0:
        return "{} keys not allowed".format(extra_keys), 400

    for key in unique_keys:
        if key in request_json and not all([request_json[key] != item[key] for item in database[name].values()]):
            return '"{}": "{}" already in different item'.format(key, request_json[key]), 403

    new_id = str(random.randint(1, 99999999))
    while new_id in database[name]:
        new_id = str(random.randint(1, 99999999))

    database[name][new_id] = request_json
    save_database()
    return database[name][new_id]


@app.route('/user', methods=['POST'])
def post_user():
    return post_entry('users', {'email', 'password_hash', 'name'}, unique_keys={'email'})


@app.route('/house', methods=['POST'])
def post_house():
    return post_entry('houses', {'user_id', 'address', 'name'})


@app.route('/device', methods=['POST'])
def post_device():
    return post_entry('devices', {'house_id', 'name', 'nominal_power_kw'})


@app.route('/schedule', methods=['POST'])
def post_schedule():
    return post_entry('schedules', {'device_id', 'day_of_week', 'start_time', 'end_time'})


@app.route('/usage_record', methods=['POST'])
def post_usage_record():
    return post_entry('usage_records', {'device_id', 'date', 'start_time', 'end_time', 'total_consumption_kw', 'cost'})


@app.route('/tariff', methods=['POST'])
def post_tariff():
    return post_entry('tariffs', {'name', 'day_rate_kwh', 'night_rate_kwh', 'day_start', 'night_start'})


@app.route('/photovoltaic_system', methods=['POST'])
def post_photovoltaic_system():
    return post_entry('photovoltaic_systems', {'house_id', 'panel_area_m2', 'max_power_kw'})


@app.route('/battery', methods=['POST'])
def post_battery():
    return post_entry('batteries', {'photovoltaic_system_id', 'capacity_kwh', 'current_charge_kwh'})


@app.route('/production_record', methods=['POST'])
def post_production_record():
    return post_entry('production_records', {'photovoltaic_system_id', 'date', 'produced_energy_kwh'})


if __name__ == '__main__':
    app.run(debug=True)
