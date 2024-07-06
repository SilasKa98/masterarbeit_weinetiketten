from spellchecker import SpellChecker


class SpellcheckerService:

    def __init__(self, added_dict_file, language):
        self.added_dict_file = added_dict_file
        self.language = language
        self.spell = SpellChecker(language=self.language)

    def add_words_to_spellchecker_dict(self):
        file = self.added_dict_file

        if file:
            self.spell.word_frequency.load_text_file(self.added_dict_file)

        return self.spell

    def correct_word(self, word):
        corrected_word = self.spell.correction(word)
        if corrected_word is None:
            corrected_word = word
        return corrected_word

    def is_word_correct_check(self, word):
        is_correct = self.spell.known([word])

        if is_correct:
            is_correct = True
            suggestions = {}
        else:
            is_correct = False
            suggestions = self.spell.candidates(word)

        return is_correct, suggestions
