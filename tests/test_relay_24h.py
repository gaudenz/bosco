from datetime import timedelta

from bosco.ranking import Relay24hScore
from bosco.ranking import Validator

def test_relay_24h(eventtest):
    valid = eventtest._event.validate(eventtest.getTeam('119'))

    assert valid['status'] == Validator.OK
    assert (eventtest._event.validate(eventtest.getTeam('121'))['status']
            == Validator.OK)
    assert (eventtest._event.validate(eventtest.getTeam('103'))['status']
            == Validator.OK)
    assert (eventtest._event.validate(eventtest.getTeam('104'))['status']
            == Validator.DISQUALIFIED)
    assert (eventtest._event.validate(eventtest.getTeam('105'))['status']
            == Validator.DISQUALIFIED)
    assert (eventtest._event.validate(eventtest.getTeam('106'))['status']
            == Validator.DISQUALIFIED)
    assert (eventtest._event.validate(eventtest.getTeam('109'))['status']
            == Validator.OK)

    eventtest.getTeam('105').override = Validator.OK
    # notify cache that this team has changed
    eventtest._cache.update(eventtest.getTeam('105'))
    assert (eventtest._event.validate(eventtest.getTeam('105'))['status']
            == Validator.OK)

    eventtest.getTeam('119').override = Validator.DISQUALIFIED
    eventtest._cache.update(eventtest.getTeam('119'))
    assert (eventtest._event.validate(eventtest.getTeam('119'))['status']
            == Validator.DISQUALIFIED)

    assert (eventtest._event.score(eventtest.getTeam('119'))['score']
            == Relay24hScore(41, timedelta(minutes=41*6)))
    assert (eventtest._event.score(eventtest.getTeam('121'))['score']
            == Relay24hScore(40, timedelta(minutes=40*6)))
    assert (eventtest._event.score(eventtest.getTeam('103'))['score']
            == Relay24hScore(38, timedelta(minutes=41*6)))
    assert (eventtest._event.score(eventtest.getTeam('109'))['score']
            == Relay24hScore(40, timedelta(minutes=40*6)))

    # Test greater than ordering
    assert (eventtest._event.score(eventtest.getTeam('121'))['score']
            < eventtest._event.score(eventtest.getTeam('119'))['score'])

    # Test greater than ordering
    assert (eventtest._event.score(eventtest.getTeam('109'))['score']
            > eventtest._event.score(eventtest.getTeam('103'))['score'])

    # Test equal ordering
    assert(eventtest._event.score(eventtest.getTeam('121'))['score']
           == eventtest._event.score(eventtest.getTeam('109'))['score'])
