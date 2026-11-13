"""Reject complete, predictable passwords without banning words in a passphrase."""
import re
import unicodedata

from django.core.exceptions import ValidationError

LEET={'a':'[a4]','e':'[e3]','i':'[i1]','o':'[o0]','s':'[s5]','t':'[t7]'}

def base_pattern(word):
    return ''.join(LEET.get(char,re.escape(char)) for char in word)


class PasswordPatternValidator:
    def validate(self, password, user=None):
        value = unicodedata.normalize('NFKC', password).casefold()
        normalized=value.translate(str.maketrans({'@':'a','$':'s'}))
        compact = ''.join(char for char in normalized if char.isalnum()) or value
        letters = ''.join(char for char in compact if char.isalpha())
        if any(compact == compact[:size] * (len(compact) // size)
                              for size in range(1, 5) if len(compact) >= 8 and len(compact) % size == 0):
            raise ValidationError('Sandi memakai pola berulang yang mudah ditebak. Pilih beberapa kata yang tidak berkaitan.', code='password_repeated')
        for row in ('0123456789', '1234567890', 'abcdefghijklmnopqrstuvwxyz',
                    'qwertyuiopasdfghjklzxcvbnm'):
            repeated = row * (len(compact) // len(row) + 2)
            if len(compact) >= 8 and (compact in repeated or compact in repeated[::-1]):
                raise ValidationError('Sandi memakai urutan angka, huruf, atau keyboard yang mudah ditebak.', code='password_sequence')
        weak_bases={'password','katasandi','sandi','silar','admin','administrator',
                    'operator','reporter','qwerty','letmein','welcome','iloveyou'}
        if letters in weak_bases or any(re.fullmatch(r'\d*'+base_pattern(word)+r'\d*',compact) for word in weak_bases):
            raise ValidationError('Sandi terlalu mudah ditebak, termasuk jika ditambah angka atau simbol. Pilih gabungan kata yang berbeda.', code='password_expected')
        if user is None:
            return
        identities = set()
        for raw in (getattr(user, 'full_name', ''), str(getattr(user, 'email', '')).split('@')[0]):
            raw = unicodedata.normalize('NFKC', raw).casefold()
            identities.update(re.findall(r'[^\W\d_]{3,}', raw))
            identities.add(''.join(char for char in raw if char.isalpha()))
        for identity in identities:
            if len(identity) < 3:
                continue
            pattern = base_pattern(identity)
            if letters == identity or re.fullmatch(r'\d*' + pattern + r'\d*', compact):
                raise ValidationError('Sandi masih berupa nama atau bagian email dengan tambahan angka/simbol. Gunakan beberapa kata yang tidak berkaitan.', code='password_identity_variant')

    def get_help_text(self):
        return 'Hindari nama/email dengan tambahan angka atau simbol, karakter berulang, dan urutan keyboard.'
