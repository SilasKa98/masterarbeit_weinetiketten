import os
from glob import glob
from difflib import SequenceMatcher
from collections import Counter
from rapidfuzz import fuzz


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
    def create_keywords_of_scentence(input_text, lang, keyword_nums, max_ngram_size, deduplication_threshold):
        import yake
        custom_kw_extractor = yake.KeywordExtractor(lan=lang, n=max_ngram_size, dedupLim=deduplication_threshold, top=keyword_nums, features=None)
        keywords = custom_kw_extractor.extract_keywords(input_text)
        all_keywords = []
        for kw in keywords:
            all_keywords.append(kw)
        return all_keywords

    @staticmethod
    def find_text_intersections(text1, text2, image_path):
        import nltk
        from nltk.tokenize import word_tokenize

        tokens1 = set(word_tokenize(text1.lower()))
        tokens2 = set(word_tokenize(text2.lower()))

        intersection = tokens1.intersection(tokens2)

        if len(intersection) > 0:
            return intersection, image_path

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
