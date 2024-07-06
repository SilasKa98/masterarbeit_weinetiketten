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
    def create_txt_from_wikimedia(file_path, output_file, max_words):
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
            # Extrahiert Wörter mit regulären Ausdrücken und filtert Duplikate
            words = re.findall(r'\b[A-Za-z]{5,}\b', text.lower())  # Nur Wörter mit mindestens 4 Buchstaben
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





