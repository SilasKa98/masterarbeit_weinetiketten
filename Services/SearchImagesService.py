import re

from Services.DataProcessService import DataProcessService
from ActionProcessor import ActionProcessor
from Services.DatabaseService import DatabaseService

from transformers import BertTokenizer, BertModel
from annoy import AnnoyIndex
import numpy as np
import spacy
from spacy.matcher import PhraseMatcher

class SearchImagesService:

    def __init__(self):
        self.database_service = DatabaseService()

    @staticmethod
    def named_entity_recognition(search_text):
        nlp_de = spacy.load('de_core_news_md')
        nlp_en = spacy.load('en_core_web_md')

        # add wine types to spacy for better results
        matcher = PhraseMatcher(nlp_de.vocab)
        wine_types = []
        with open("C:\\Masterarbeit_ocr_env\\dictionary_files\\wine_types.txt", "r") as file:
            for item in file:
                wine_types.append(item.strip())

        patterns = [nlp_de(text) for text in wine_types]
        matcher.add("WEINSORTEN", patterns)

        doc_de = nlp_de(search_text)
        matches = matcher(doc_de)
        wine_type_matches = [doc_de[start:end].text for match_id, start, end in matches]

        doc_en = nlp_en(search_text)
        found_dates = [ent.text for ent in doc_en.ents if ent.label_ == "DATE"]

        #regex date finding fallback
        date_pattern = re.compile(r'\b\d{1,4}\b')
        dates_from_regex = date_pattern.findall(search_text)

        found_dates.extend(dates_from_regex)
        found_dates = list(set(found_dates))

        entitie_dict = {"wine_types": wine_type_matches}
        print(doc_de.ents)
        for ent in doc_de.ents:
            if ent.label_ in ["LOC", "GPE"]:
                if "loc" not in entitie_dict:
                    entitie_dict["loc"] = []
                entitie_dict["loc"].append(ent.text)
        if found_dates:
            entitie_dict["date"] = found_dates

        return entitie_dict

    def text_based_keyword_search(self, search_text, used_ocrs=["easyocr", "tesseract", "doctr"], sub_search=False, sub_search_paths=[]):

        search_entitys = self.named_entity_recognition(search_text)
        search_text_keywords = list(set())
        if search_entitys:
            for k,v in search_entitys.items():
                search_text_keywords.extend(v)
        else:
            search_text_keywords = DataProcessService.create_keywords_of_scentence(search_text, "de", 4, 6, 0.9)[0].split()

        print(search_text_keywords)

        db_results_all = []
        for ocr in used_ocrs:
            if not sub_search:
                db_result = self.database_service.select_from_table(ocr, "*", as_dict=True)
                db_results_all.append(db_result)
            else:
                for item in sub_search_paths:
                    db_result = self.database_service.select_from_table(ocr, "*", condition="path =%s", params=[item], as_dict=True)
                    db_results_all.append(db_result)

        print(db_results_all)

        path_text_dict = {}
        for inner_list in db_results_all:
            for item in inner_list:
                for key, value in item.items():
                    if key == "path":
                        current_path = value
                    else:
                        if current_path in path_text_dict:
                            path_text_dict[current_path] = path_text_dict[current_path] + " " + value
                        else:
                            path_text_dict[current_path] = value

        intersection_dict = {}
        for key, text in path_text_dict.items():
            for keyword in search_text_keywords:
                text_intersection = DataProcessService.find_text_intersections(keyword, text)
                if text_intersection is not None:
                    text_intersection_str = next(iter(text_intersection))
                    if text_intersection_str in intersection_dict:
                        intersection_dict[text_intersection_str].add(key)
                    else:
                        intersection_dict[text_intersection_str] = {key}

        return intersection_dict

    def semantic_search(self, search_text, used_ocrs=["doctr"]):
        # Initialisierung des BERT-Modells und Tokenizers
        tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
        model = BertModel.from_pretrained('bert-base-uncased')

        def encode_text(text, tokenizer_inner, model_inner):
            inputs = tokenizer_inner(text, return_tensors='pt', truncation=True, padding=True, max_length=512)
            outputs = model_inner(**inputs)
            return outputs.last_hidden_state.mean(dim=1).squeeze().detach().numpy()

        def split_text(text, tokenizer_inner, max_length=512):
            tokens = tokenizer_inner.tokenize(text)
            chunks = [tokens[i:i + max_length] for i in range(0, len(tokens), max_length)]
            return [tokenizer_inner.convert_tokens_to_string(chunk) for chunk in chunks if chunk]

        def aggregate_text_vector(text, tokenizer_inner, model_inner):
            chunks = split_text(text, tokenizer_inner)
            if not chunks:  # Sicherstellen, dass es keine leeren Chunks gibt
                return np.zeros(model_inner.config.hidden_size)  # Standardwert für leere Texte
            vectors = [encode_text(chunk, tokenizer_inner, model_inner) for chunk in chunks]
            if not vectors:  # Sicherstellen, dass die Vektorliste nicht leer ist
                return np.zeros(model_inner.config.hidden_size)
            return np.mean(vectors, axis=0)

        # read in db label infos
        db_results_all = []
        for ocr in used_ocrs:
            db_result = self.database_service.select_from_table(ocr, "path, text_final", as_dict=True)
            db_results_all.append(db_result)

        path_text_dict = {}
        for inner_list in db_results_all:
            for item in inner_list:
                for key, value in item.items():
                    if key == "path":
                        current_path = value
                    else:
                        if current_path in path_text_dict:
                            path_text_dict[current_path] = path_text_dict[current_path] + " " + value
                        else:
                            path_text_dict[current_path] = value

        print(path_text_dict)
        texts_to_search_in = []
        text_keys = []
        for k, v in path_text_dict.items():
            texts_to_search_in.append(v)
            text_keys.append(k)

        # Beispielhafte Vektorisierung
        #texts = ["fruchtiger Rotwein", "trockener Weißwein", "süßer Rosé", "Riesling", "bollinger"]
        vectors = np.array([aggregate_text_vector(text, tokenizer, model) for text in texts_to_search_in])

        # Erstelle Annoy-Index
        f = vectors.shape[1]  # Länge der Vektoren
        t = AnnoyIndex(f, 'angular')  # 'angular' verwendet den Winkelabstand (cosine similarity)

        # Füge Vektoren zum Index hinzu
        for i, vector in enumerate(vectors):
            t.add_item(i, vector)

        t.build(10)  # 10 Bäume erstellen

        # Beispielhafte Abfrage
        query = search_text
        query_vector = encode_text(query, tokenizer, model)
        indices = t.get_nns_by_vector(query_vector, 50)  # Finde die 3 nächsten Nachbarn
        print(indices)  # Gibt die Indizes der ähnlichsten Weinetiketten zurück
        found_paths = []
        for i in indices:
            found_paths.append(text_keys[i])
            print(text_keys[i])

        sub_search = self.text_based_keyword_search(search_text, sub_search=True,sub_search_paths=found_paths)
        print("subset: ")
        print(sub_search)

        sub_search_values_list = []
        for value_set in sub_search.values():
            sub_search_values_list.extend(value_set)

        second_choice_hits = list(filter(lambda x: x not in sub_search_values_list, found_paths))

        print("second_choice_hits: ")
        print(second_choice_hits)

        return sub_search, second_choice_hits

