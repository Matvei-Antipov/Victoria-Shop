from googletrans import Translator

def translate(array):
    translator = Translator()
    result = []
    for element in array:
        translated = translator.translate(element, dest='en')
        result.append(translated.text)
    return result