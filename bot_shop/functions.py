from translate import Translator

#translator

def translate_text(text, target_language='ru'):
    translator= Translator(to_lang=target_language)
    translation = translator.translate(text)
    return translation