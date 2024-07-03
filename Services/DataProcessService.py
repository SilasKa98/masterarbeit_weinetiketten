import os
from glob import glob
from difflib import SequenceMatcher
from collections import Counter
from rapidfuzz import fuzz
from spellchecker import SpellChecker
import enchant

class DataProcessService:

    @staticmethod
    def iterate_directory(directory):

        # Durch das Hauptverzeichnis iterieren
        image_path = ''
        for root, dirs, files in os.walk(directory):
            for file in files:
                image_path = os.path.join(root, file)
                yield image_path

        return image_path

    @staticmethod
    def get_subdirectories(path):
        try:
            contents = os.listdir(path)
            subdirectories = [name for name in contents if os.path.isdir(os.path.join(path, name))]
            return subdirectories

        except FileNotFoundError:
            print(f"Error: The path '{path}' does not exist.")
            return []
        except PermissionError:
            print(f"Error: Permission denied for path '{path}'.")
            return []

    @staticmethod
    def create_keywords_of_scentence(input_text, lang, keyword_nums, max_ngram_size, deduplication_threshold):
        import yake
        custom_kw_extractor = yake.KeywordExtractor(lan=lang, n=max_ngram_size, dedupLim=deduplication_threshold, top=keyword_nums, features=None)
        keywords = custom_kw_extractor.extract_keywords(input_text)
        all_keywords = []
        for kw in keywords:
            all_keywords.append(kw)
        return all_keywords

    @staticmethod
    def find_text_intersections(text1, text2):
        import nltk
        from nltk.tokenize import word_tokenize

        tokens1 = set(word_tokenize(text1.lower()))
        tokens2 = set(word_tokenize(text2.lower()))

        intersection = tokens1.intersection(tokens2)

        if len(intersection) > 0:
            return intersection

    @staticmethod
    def similar(a, b):
        return SequenceMatcher(None, a, b).ratio()

    @staticmethod
    def find_similar_sentences(strings_list, paths, threshold=85):
        similar_pairs = []
        checked_pairs = set()
        cleaned_string_list = [result[0] for result in strings_list]
        for i, sentence in enumerate(cleaned_string_list):
            for j, other_sentence in enumerate(cleaned_string_list):
                if i != j and (j, i) not in checked_pairs:
                    if "empty" not in sentence and "empty" not in other_sentence:
                        similarity = fuzz.ratio(sentence, other_sentence)
                        if similarity >= threshold:
                            similar_pairs.append((sentence, other_sentence, similarity, paths[i], paths[j]))
                        checked_pairs.add((i, j))

        return similar_pairs

    @staticmethod
    def spellchecker(word, language='en'):
        if len(word) > 10:
            spell = SpellChecker(language=language, distance=1)
        else:
            spell = SpellChecker(language=language)
        corrected_word = spell.correction(word)
        #print("wrong: ", word, " corrected: ", corrected_word)
        if corrected_word is None:
            corrected_word = word
        return corrected_word

    @staticmethod
    def is_word_correct_check(word, language='en_US'):
        if language == "en":
            language = "en_US"
        elif language == "de":
            language = "de_DE"
        else:
            language = "en_US"

        d = enchant.Dict(language)
        is_correct = d.check(word)

        if not is_correct:
            suggestions = d.suggest(word)
        else:
            suggestions = []

        return is_correct, suggestions
