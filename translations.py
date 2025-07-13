#!/usr/bin/env python3
"""
Translation strings for certificate generation in multiple languages
"""

TRANSLATIONS = {
    'en': {
        'title': 'CERTIFICATE OF PARTICIPATION',
        'certify_that': 'We certify that',
        'participated_in': 'participated in the course',
        'held_at': 'held at',
        'with_duration': 'with a total duration of',
        'date_format': 'in {date}',
        'issued_by': 'Certificate issued by',
        'verification': 'Verification:',
        'nft_id': 'NFT ID:',
        'salt': 'Security Code:',
    },
    'pt': {
        'title': 'CERTIFICADO DE PARTICIPAÇÃO',
        'certify_that': 'Certificamos que',
        'participated_in': 'participou do curso',
        'held_at': 'realizado em',
        'with_duration': 'com carga horária de',
        'date_format': 'em {date}',
        'issued_by': 'Certificado emitido por',
        'verification': 'Verificação:',
        'nft_id': 'ID NFT:',
        'salt': 'Código de Segurança:',
    },
    'es': {
        'title': 'CERTIFICADO DE PARTICIPACIÓN',
        'certify_that': 'Certificamos que',
        'participated_in': 'participó en el curso',
        'held_at': 'impartido en',
        'with_duration': 'con una duración de',
        'date_format': 'en {date}',
        'issued_by': 'Certificado emitido por',
        'verification': 'Verificación:',
        'nft_id': 'ID NFT:',
        'salt': 'Código de Seguridad:',
    },
    'fr': {
        'title': 'CERTIFICAT DE PARTICIPATION',
        'certify_that': 'Nous certifions que',
        'participated_in': 'a participé au cours',
        'held_at': 'dispensé à',
        'with_duration': 'd\'une durée de',
        'date_format': 'à {date}',
        'issued_by': 'Certificat délivré par',
        'verification': 'Vérification :',
        'nft_id': 'ID NFT :',
        'salt': 'Code de Sécurité :',
    }
}

def get_translation(language: str, key: str) -> str:
    """
    Get translation for a specific key in the given language.
    Falls back to English if language or key not found.
    """
    lang_dict = TRANSLATIONS.get(language, TRANSLATIONS['en'])
    return lang_dict.get(key, TRANSLATIONS['en'].get(key, key))

def get_available_languages():
    """Return list of available language codes"""
    return list(TRANSLATIONS.keys())

def format_date_text(language: str, date: str) -> str:
    """Format date text according to language"""
    template = get_translation(language, 'date_format')
    return template.format(date=date)