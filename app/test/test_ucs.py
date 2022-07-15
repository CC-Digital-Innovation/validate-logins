import app.validate.https.ucs as ucs

class TestUCS:
    def test_success_login(self):
        status = ucs.validate('ucs01.quokka.ninja', 'ucspe', 'ucspe')
        assert status

    def test_failed_login(self):
        status = ucs.validate('ucs01.quokka.ninja', 'ucspe', 'wrong password')
        assert not status