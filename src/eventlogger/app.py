'''Event Logger flask app'''
import logging
from os import environ, path
from flask import Flask, request, jsonify
import requests
import eventlogger
from eventlogger.models import Event, db

logger = logging.getLogger(__name__)

conf_file = environ.get(
    'WEBAPP_CONF') or f'{path.dirname(eventlogger.__file__)}/config.py'
print(conf_file)
GOOD_DATA = {
    "user": "<user>",
    "message": "<message>",
    "url": "<url(optional)>",
    "platform": "<platform(optional)>",
}


def relay_to_homeassistant(event_data):
    '''Relay event to Home Assistant via its REST API'''
    ha_url = environ.get('HA_URL')
    ha_token = environ.get('HA_TOKEN')
    if not ha_url or not ha_token:
        return
    try:
        response = requests.post(
            f'{ha_url}/api/events/event_logger',
            headers={
                'Authorization': f'Bearer {ha_token}',
                'Content-Type': 'application/json',
            },
            json=event_data,
            timeout=5,
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as exc:
        logger.error('Home Assistant relay failed: %s', exc)


def create_app(config_filename):
    '''App factory for Webapp'''
    new_app = Flask(__name__)
    new_app.config.from_pyfile(config_filename, silent=False)
    db.init_app(new_app)
    print(new_app.config)
    with new_app.app_context():
        db.create_all()

    @new_app.route('/event', methods=['GET'])
    def get_paginated_items():
        '''Return paginated event items based on page and per_page values'''
        page = int(request.args.get('page')) if request.args.get('page') else 1
        per_page = int(request.args.get('per_page')
                       ) if request.args.get('per_page') else 5
        items = Event.query.order_by(Event.time.desc()) \
            .paginate(page=page,
                      per_page=per_page,
                      error_out=False)
        return jsonify({
            "items": [item.to_dict() for item in items.items],
            "total": items.total,
            "page": items.page,
            "pages": items.pages,
            "next_page": f'/event?page={ page + 1 }&per_page={ per_page }'
        }), 200

    @new_app.route('/event', methods=['POST'])
    def receive_event():
        '''URL for receiving event log entries'''
        data = request.get_json()
        print(data)

        if not data or 'user' not in data or 'message' not in data:
            return jsonify({
                'error': 'Invalid input',
                'received': f'{data}',
                'expected': f'{GOOD_DATA}'}), 400

        new_event = Event(
            user=data['user'],
            message=data['message'],
            url=data.get('url'),
            platform=data.get('platform'))
        db.session.add(new_event)
        db.session.commit()

        event_dict = new_event.to_dict()
        relay_to_homeassistant(event_dict)

        return jsonify(event_dict), 201

    @new_app.route('/')
    def root():
        '''App index'''
        return get_paginated_items()
    return new_app


app = create_app(conf_file)

if __name__ == "__main__":
    app.run()
    # app.run(debug=True) #For debugging local dev issues
