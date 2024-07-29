import os
import re
from glob import glob
from difflib import SequenceMatcher
from collections import Counter

from nltk import RegexpTokenizer
from rapidfuzz import process, fuzz
from nltk.tokenize import word_tokenize

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
    def find_text_intersections(text1, text2, threshold=90):
        def filter_short_tokens(tokens, min_length=4):
            return [token for token in tokens if len(token) >= min_length]

        search_tokens = filter_short_tokens(word_tokenize(text1.lower()))
        doc_tokens = filter_short_tokens(word_tokenize(text2.lower()))

        intersection = {}
        # general matching for string tokens
        for t in search_tokens:
            # find best match for both texts/tokens
            matches = process.extract(t, doc_tokens, scorer=fuzz.partial_ratio, limit=5)
            for match in matches:
                token_match, score, _ = match
                if score >= threshold:
                    if t not in intersection:
                        intersection[t] = list(set())
                    intersection[t].append(token_match)

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

        return intersection if intersection else None

    @staticmethod
    def similar(a, b):
        return SequenceMatcher(None, a, b).ratio()

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
            print(f"Extrahierte Wörter wurden in die Datei {output_file} geschrieben.")
        except Exception as e:
            print(f"Fehler beim Parsen der XML-Datei: {e}")





