'''
   Tests for Event Logger App
'''
import random
import string
from unittest.mock import patch, MagicMock
import requests as req
from eventlogger.app import app, relay_to_homeassistant

C = app.test_client()


def __random_string(length=32):
    '''Generates random string'''
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))


def test_event_returned():
    '''Sends random event data and ensures it is returned'''
    rnd_user = __random_string()
    rnd_message = __random_string()
    response = C.post("/event",
                      json={
                          "user": rnd_user,
                          "message": rnd_message})
    assert response.status_code == 201
    assert response.json["user"] == rnd_user
    assert response.json["message"] == rnd_message
    assert response.json["url"] is None
    assert response.json["platform"] is None
    response = C.get("/event")
    assert rnd_user in str(response.data)
    assert rnd_message in str(response.data)


def test_twitch_event():
    '''Sends event data with optional fields and ensures they are returned'''
    rnd_user = "tobor"
    rnd_message = "Special twitch message"
    rnd_url = "https://twitch.tv/askmartyn"
    rnd_platform = "twitch"
    response = C.post("/event",
                      json={
                          "user": rnd_user,
                          "message": rnd_message,
                          "url": rnd_url,
                          "platform": rnd_platform})
    assert response.status_code == 201
    assert response.json["user"] == "tobor"
    assert response.json["message"] == "Special twitch message"
    assert response.json["url"] == "https://twitch.tv/askmartyn"
    assert response.json["platform"] == "twitch"


def test_event_with_optional_fields():
    '''Sends event data with optional fields and ensures they are returned'''
    rnd_user = __random_string()
    rnd_message = __random_string()
    rnd_url = f'https://{__random_string(8)}.example.com'
    rnd_platform = __random_string(8)
    response = C.post("/event",
                      json={
                          "user": rnd_user,
                          "message": rnd_message,
                          "url": rnd_url,
                          "platform": rnd_platform})
    assert response.status_code == 201
    assert response.json["user"] == rnd_user
    assert response.json["message"] == rnd_message
    assert response.json["url"] == rnd_url
    assert response.json["platform"] == rnd_platform


def test_invalid_event_rejected():
    '''Sends invalid event data and ensures a 400 error is returned'''
    response = C.post("/event", json={"user": "only_user"})
    assert response.status_code == 400
    response = C.post("/event", json={})
    assert response.status_code == 400


def test_ha_relay_skipped_when_not_configured():
    '''relay_to_homeassistant does nothing when HA_URL/HA_TOKEN are absent'''
    with patch('eventlogger.app.requests.post') as mock_post:
        relay_to_homeassistant({"user": "test", "message": "hello"})
        mock_post.assert_not_called()


def test_ha_relay_sends_event():
    '''relay_to_homeassistant posts event to Home Assistant when configured'''
    event_data = {"user": "test", "message": "hello"}
    mock_response = MagicMock()
    mock_response.status_code = 200
    with patch('eventlogger.app.requests.post', return_value=mock_response) as mock_post:
        with patch('eventlogger.app.environ.get', side_effect=lambda k, *a: {
            'HA_URL': 'http://homeassistant.local:8123',
            'HA_TOKEN': 'test_token',
        }.get(k)):
            relay_to_homeassistant(event_data)
        mock_post.assert_called_once_with(
            'http://homeassistant.local:8123/api/events/event_logger',
            headers={
                'Authorization': 'Bearer test_token',
                'Content-Type': 'application/json',
            },
            json=event_data,
            timeout=10,
        )


def test_ha_relay_handles_request_failure():
    '''relay_to_homeassistant logs error and does not raise on request failure'''
    with patch('eventlogger.app.requests.post',
               side_effect=req.exceptions.RequestException('connection error')):
        with patch('eventlogger.app.environ.get', side_effect=lambda k, *a: {
            'HA_URL': 'http://homeassistant.local:8123',
            'HA_TOKEN': 'test_token',
        }.get(k)):
            # Should not raise
            relay_to_homeassistant({"user": "test", "message": "fail"})
