import time

from domains.auth import tokens

SECRET = 's' * 40


def test_round_trip():
    token = tokens.sign({'sub': '123', 'exp': time.time() + 60}, SECRET)
    assert tokens.verify(token, SECRET)['sub'] == '123'


def test_rejects_expired():
    token = tokens.sign({'sub': '123', 'exp': time.time() - 1}, SECRET)
    assert tokens.verify(token, SECRET) is None


def test_rejects_wrong_secret():
    token = tokens.sign({'sub': '123', 'exp': time.time() + 60}, SECRET)
    assert tokens.verify(token, 'o' * 40) is None


def test_rejects_tampered_payload():
    token = tokens.sign({'sub': '123', 'exp': time.time() + 60}, SECRET)
    forged = tokens.sign({'sub': '999', 'exp': time.time() + 60}, SECRET)
    spliced = '.'.join([token.split('.')[0], forged.split('.')[1], token.split('.')[2]])
    assert tokens.verify(spliced, SECRET) is None


def test_rejects_legacy_and_garbage_tokens():
    assert tokens.verify('discord_123_1700000000', SECRET) is None
    assert tokens.verify('', SECRET) is None
    assert tokens.verify('gf1.a.b', SECRET) is None


def test_rejects_non_numeric_subject():
    token = tokens.sign({'sub': '../x', 'exp': time.time() + 60}, SECRET)
    assert tokens.verify(token, SECRET) is None
