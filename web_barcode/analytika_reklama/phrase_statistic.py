from analytika_reklama.models import KeywordPhrase


def add_keyphrase_to_db(phrase: str):
    """
    Записывает ключевую фразу в базу данных и возвращает ее объект
    А если есть - возвращает ее объект
    """
    phrase_obj, created = KeywordPhrase.objects.get_or_create(phrase=phrase)
    if created:
        return phrase_obj
    else:
        return phrase_obj
