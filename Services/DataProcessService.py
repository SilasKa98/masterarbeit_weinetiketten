import math
import os
import re
from glob import glob
from difflib import SequenceMatcher
from collections import Counter

import nltk
from nltk import RegexpTokenizer
from rapidfuzz import process, fuzz
from nltk.tokenize import word_tokenize

class DataProcessService:

    @staticmethod
    def iterate_directory(directory):

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
    def limit_dict_items(d, limit=24):
        new_dict = {}
        for key, values in d.items():
            if len(values) > limit:
                new_dict[key] = set(list(values)[:limit])
            else:
                new_dict[key] = values
        return new_dict

    @staticmethod
    def remove_duplicate_val_from_dict(d):
        seen_values = set()
        for key, values in d.items():
            if isinstance(values, set):
                d[key] = {value for value in values if value not in seen_values}
                seen_values.update(d[key])
            else:
                d[key] = [value for value in values if value not in seen_values]
                seen_values.update(d[key])
        return d

    @staticmethod
    def find_text_intersections(text1, doc_tokens, wine_names, wine_types, blacklisted_words, threshold=90):
        def filter_short_tokens(tokens, min_length):
            # Filter tokens based on a minimum length.
            return [token for token in tokens if len(token) >= min_length]

        normalized_text1 = text1.strip().lower()
        if normalized_text1 in wine_names or normalized_text1 in wine_types:
            search_tokens = {normalized_text1}
        else:
            # Tokenize text1 and filter short tokens, use set for faster membership checks and removing duplicates
            search_tokens = set(filter_short_tokens(nltk.word_tokenize(normalized_text1), 3))

        intersection = {}
        # general matching for string tokens
        for t in search_tokens:
            # if searchword is blacklisted skip this itteration and dont search for matches (e.g. wine)
            if t in blacklisted_words:
                continue
            # find best match for both texts/tokens
            matches = process.extract(t, doc_tokens, scorer=fuzz.partial_ratio, limit=1)
            for match in matches:
                token_match, score, _ = match
                if score >= threshold and token_match.lower() not in blacklisted_words:
                    intersection.setdefault(text1, set()).add(token_match)

        # Regex to find year spans (e.g. "1900-2000")
        year_range_regex = r'\b(\d{4})-(\d{4})\b'
        # search for year spans in the search_tokens
        year_ranges = []
        for token in search_tokens:
            ranges = re.findall(year_range_regex, token)
            for start, end in ranges:
                year_ranges.append(f'{start}-{end}')

        # matching for century tokens
        for year_range in year_ranges:
            start, end = map(int, year_range.split('-'))
            valid_years = set()
            year_matches = []
            for token in doc_tokens:
                # prio to numbers with "er" at the end --> common on wine labels for year info
                if re.match(r'^\d{4}\s?er$', token):
                    try:
                        year = int(token.replace(' er', '').replace('er', ''))
                        if start <= year <= end:
                            year_matches.append((year, token))
                    except ValueError:
                        continue
                else:
                    try:
                        year = int(token)
                        if start <= year <= end:
                            valid_years.add(year)
                    except ValueError:
                        continue
            if year_matches:
                best_match = max(year_matches, key=lambda x: x[0])
                if year_range not in intersection:
                    intersection[year_range] = list(set())
                intersection[year_range].append(best_match[1])
            elif valid_years:
                if year_range not in intersection:
                    intersection[year_range] = list(set())
                for year in valid_years:
                    intersection[year_range].append(str(year))

        if intersection:
            print("match found: ", intersection)

        return intersection if intersection else None

    @staticmethod
    def is_similar(word1, word2, threshold=80):
        return fuzz.ratio(word1, word2) > threshold

    def convert_set_to_list(self, obj):
        # rekursiv transform sets to lists
        if isinstance(obj, dict):
            return {key: self.convert_set_to_list(value) for key, value in obj.items()}
        elif isinstance(obj, set):
            return list(obj)
        elif isinstance(obj, list):
            return [self.convert_set_to_list(item) for item in obj]
        else:
            return obj

    @staticmethod
    def find_similar_images_by_sentence(strings_list, paths, threshold=85):
        similar_pairs = []
        checked_pairs = set()
        cleaned_string_list = [result[0] for result in strings_list]
        for i, sentence in enumerate(cleaned_string_list):
            for j, other_sentence in enumerate(cleaned_string_list):
                if i != j and (j, i) not in checked_pairs:
                    # check if both strings are "" or None
                    if not (sentence is None and other_sentence is None) and not (sentence == "" and other_sentence == ""):
                        if "empty" not in sentence and "empty" not in other_sentence:
                            similarity = fuzz.ratio(sentence, other_sentence)
                            if similarity >= threshold:
                                similar_pairs.append((sentence, other_sentence, similarity, paths[i], paths[j]))
                            checked_pairs.add((i, j))

        return similar_pairs

    @staticmethod
    def remove_accent_chars(input_word):
        accents = {
            'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
            'á': 'a', 'à': 'a', 'â': 'a',
            'í': 'i', 'ì': 'i', 'î': 'i', 'ï': 'i',
            'ó': 'o', 'ò': 'o', 'ô': 'o',
            'ú': 'u', 'ù': 'u', 'û': 'u',
            'ç': 'c', 'ñ': 'n'
        }
        for accented_char, normal_char in accents.items():
            input_word = input_word.replace(accented_char, normal_char)

        return input_word

    @staticmethod
    def create_txt_from_wikimedia(file_path, output_file, max_words, language="de"):
        from bigxml import Parser, xml_handle_element
        import re

        # wikipedia text decorator
        @xml_handle_element("mediawiki", "page", "revision", "text")
        def handler(node):
            yield node.text

        def clean_text(text):
            # Entfernt Wiki-Syntax und HTML-Tags mit regulären Ausdrücken
            text = re.sub(r'\[\[.*?\]\]', '', text)  # Entfernt [[wikilinks]]
            text = re.sub(r'<.*?>', '', text)  # Entfernt HTML-Tags
            text = re.sub(r'==.*?==', '', text)  # Entfernt Überschriften
            text = re.sub(r'\{\{.*?\}\}', '', text)  # Entfernt Vorlagen
            return text

        def extract_words(text):
            if language == "de":
                regex = r'\b[A-Za-zäöüÄÖÜß-]{5,}\b'
            elif language == "fr":
                regex = r'\b[A-Za-zàâçéèêëîïôûùüÿæœ-]{5,}\b'
            elif language == "it":
                regex = r'\b[A-Za-zàèéìòù-]{5,}\b'
            else:
                regex = r'\b[A-Za-z-]{5,}\b'
            words = re.findall(regex, text.lower())  # only words with at least 5 chars
            unique_words = set(words)  # Entfernt Duplikate durch Umwandlung in ein Set
            return list(unique_words)  # Rückgabe als Liste von eindeutigen Wörtern


        try:
            with open(file_path, "rb") as f, open(output_file, 'w', encoding='utf-8') as out_file:
                count = 0
                for item in Parser(f).iter_from(handler):
                    # Bereinigen des Textes und Extrahieren der Wörter
                    cleaned_text = clean_text(item)
                    words = extract_words(cleaned_text)

                    # Schreibe jedes Wort in die Ausgabedatei
                    for word in words:
                        out_file.write(word + '\n')
                        count += 1
                        if count >= max_words:
                            break
                    if count >= max_words:
                        break
            print(f"extracted words have been written in file: {output_file}.")
        except Exception as e:
            print(f"Error while parsing XML-File: {e}")

    # clean word and check if it contains vocals and has a min length
    @staticmethod
    def word_is_meaningful(word):

        if word.isdigit():
            year = int(word)
            if 1600 <= year <= 2100:
                return True

        clean_word = re.sub(r'[^a-zA-ZäöüÄÖÜ]', '', word)
        has_vowel = bool(re.search(r'[aeiouäöüAEIOUÄÖÜ]', clean_word))
        unique_letters = len(set(clean_word)) >= 3
        min_length = len(clean_word) >= 3
        return has_vowel and unique_letters and min_length

    def generate_google_search_query_from_ent_dict(self, dict_input):
        dict_input = self.remove_duplicate_val_from_dict(dict_input)
        search_query = ""
        used_keys = set()

        if 'wine_types' in dict_input:
            search_query += ' '.join(dict_input['wine_types']) + ' '
            used_keys.add('wine_types')

        if 'wine_names' in dict_input:
            search_query += ' '.join(dict_input['wine_names']) + ' '
            used_keys.add('wine_names')

        if 'wine_attributes' in dict_input:
            search_query += ' '.join(dict_input['wine_attributes']) + ' '
            used_keys.add('wine_attributes')

        if 'loc' in dict_input:
            search_query += ' '.join([f'"{loc}"' for loc in dict_input['loc']]) + ' '
            used_keys.add('loc')

        if 'date' in dict_input:
            search_query += ' '.join(dict_input['date']) + ' '
            used_keys.add('date')

        search_query = search_query.strip().replace('"', '')

        cleaned_search_query = [item for item in search_query.split() if self.word_is_meaningful(item)]

        # remove similar words (also uses some tolerance, so words doesn't need 1:1)
        seen = []
        unique_words = []
        for word in cleaned_search_query:
            if not any(self.is_similar(word, seen_word) for seen_word in seen):
                unique_words.append(word)
                seen.append(word)

        cleaned_search_query = ' '.join(unique_words)

        # only return query string if values of 3 different categorys are in it
        if len(used_keys) >= 3:
            return cleaned_search_query
        else:
            return ""




