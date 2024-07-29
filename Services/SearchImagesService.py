import re
import os
import pickle
import numpy as np
from transformers import BertTokenizer, BertModel
from annoy import AnnoyIndex
import spacy
from spacy.matcher import PhraseMatcher
from Services.DatabaseService import DatabaseService
from Services.DataProcessService import DataProcessService

class SearchImagesService:

    def __init__(self, cache_file='vector_cache.pkl'):
        self.database_service = DatabaseService()
        self.cache_file = cache_file
        self.cache = self.load_cache()

    def load_cache(self):
        if os.path.exists(self.cache_file):
            with open(self.cache_file, 'rb') as f:
                return pickle.load(f)
        return {}

    def save_cache(self):
        with open(self.cache_file, 'wb') as f:
            pickle.dump(self.cache, f)

    def search_algorithm(self, search_text):

        entity_search_dict = self.named_entity_recognition(search_text)
        entity_search_text = " ".join(ent for ents in entity_search_dict.values() for ent in ents)

        query = entity_search_text.strip() or search_text

        found_paths_semantic = self.semantic_search(query)
        text_based_result = self.text_based_keyword_search(search_text)

        print("########################(text_based_result)##################################")
        print(text_based_result)

        found_paths_only = [path for path, _, _ in found_paths_semantic]
        top_hits = self.text_based_keyword_search(search_text, sub_search=True, sub_search_paths=found_paths_only)

        sub_search_values_list = list(set())
        for value_set in top_hits.values():
            sub_search_values_list.extend(value_set)

        second_choice_hits = list(filter(lambda x: x not in sub_search_values_list, found_paths_only))

        # remove all paths from text_based_results that are already in top hits
        for key in text_based_result:
            text_based_result[key] = {path for path in text_based_result[key] if path not in top_hits}

        print("Search DONE !")
        return top_hits, second_choice_hits, text_based_result

    @staticmethod
    def named_entity_recognition(search_text):
        nlp_de = spacy.load('de_core_news_md')
        nlp_en = spacy.load('en_core_web_md')

        matcher = PhraseMatcher(nlp_de.vocab, attr='LOWER')
        wine_types = []
        with open("C:\\Masterarbeit_ocr_env\\dictionary_files\\wine_types.txt", "r") as file:
            wine_types = [item.strip().lower() for item in file]

        patterns = [nlp_de(text) for text in wine_types]
        matcher.add("WEINSORTEN", patterns)

        doc_de = nlp_de(search_text.lower())
        matches = matcher(doc_de)
        wine_type_matches = [doc_de[start:end].text for match_id, start, end in matches]

        doc_en = nlp_en(search_text)
        found_dates = [ent.text for ent in doc_en.ents if ent.label_ == "DATE"]

        date_pattern = re.compile(r'\b\d{1,4}\b')
        dates_from_regex = date_pattern.findall(search_text)
        found_dates.extend(dates_from_regex)
        found_dates = list(set(found_dates))

        entitie_dict = {"wine_types": wine_type_matches}
        for ent in doc_de.ents:
            if ent.label_ in ["LOC", "GPE"]:
                if "loc" not in entitie_dict:
                    entitie_dict["loc"] = []
                entitie_dict["loc"].append(ent.text)
        if found_dates:
            entitie_dict["date"] = found_dates

        return entitie_dict

    # sub function for semantic search
    @staticmethod
    def encode_text(text, tokenizer, model):
        inputs = tokenizer(text, return_tensors='pt', truncation=True, padding=True, max_length=512)
        outputs = model(**inputs)
        return outputs.last_hidden_state.mean(dim=1).squeeze().detach().numpy()

    # sub function for semantic search
    @staticmethod
    def split_text(text, tokenizer, max_length=512):
        tokens = tokenizer.tokenize(text)
        chunks = [tokens[i:i + max_length] for i in range(0, len(tokens), max_length)]
        return [tokenizer.convert_tokens_to_string(chunk) for chunk in chunks if chunk]

    # sub function for semantic search
    def aggregate_text_vector(self, text, tokenizer, model):
        chunks = self.split_text(text, tokenizer)
        if not chunks:
            return np.zeros(model.config.hidden_size)
        vectors = [self.encode_text(chunk, tokenizer, model) for chunk in chunks]
        if not vectors:
            return np.zeros(model.config.hidden_size)
        return np.mean(vectors, axis=0)

    def update_cache(self, db_results):
        for result in db_results:
            key = (result['path'], result['ocr_model'], result['column'])
            text = result['text']
            if key not in self.cache:
                vector = self.aggregate_text_vector(text, self.tokenizer, self.model)
                self.cache[key] = vector
        self.save_cache()

    # sub function for semantic search
    def build_annoy_index(self):
        vectors = list(self.cache.values())
        f = len(vectors[0]) if vectors else 0
        t = AnnoyIndex(f, 'angular')

        for i, (key, vector) in enumerate(self.cache.items()):
            t.add_item(i, vector)

        t.build(10)
        return t

    def semantic_search(self, search_text, used_ocrs={"doctr": ["text_final", "text_pure_modified_images"],
                                                      "tesseract": ["text_final", "text_pure_modified_images"],
                                                      "easyocr": ["text_final", "text_pure_modified_images"],
                                                        }):
        tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
        model = BertModel.from_pretrained('bert-base-uncased')
        self.tokenizer = tokenizer
        self.model = model

        db_results_all = []
        for ocr_model, columns in used_ocrs.items():
            for column in columns:
                db_result = self.database_service.select_from_table(ocr_model, f"path, {column} as text", as_dict=True)
                for res in db_result:
                    res['ocr_model'] = ocr_model
                    res['column'] = column
                db_results_all.extend(db_result)

        self.update_cache(db_results_all)

        t = self.build_annoy_index()

        query = search_text
        query_vector = self.encode_text(query, tokenizer, model)
        indices = t.get_nns_by_vector(query_vector, 50)
        print(indices)

        found_paths = [list(self.cache.keys())[i] for i in indices]
        print(found_paths)

        return found_paths

    def text_based_keyword_search(self, search_text, used_ocrs=["easyocr", "tesseract", "doctr"], sub_search=False, sub_search_paths=[]):
        search_entitys = self.named_entity_recognition(search_text)
        search_text_keywords = list(set())
        if search_entitys:
            for k, v in search_entitys.items():
                search_text_keywords.extend(v)
        else:
            search_text_keywords = DataProcessService.create_keywords_of_scentence(search_text, "de", 4, 6, 0.9)[0].split()

        # filter for years again
        year_regex = r'\b(\d{4})\b'
        century_regex = r'(\d{1,2})\s*\.?\s*jahrhundert'
        found_years = re.findall(year_regex, search_text)
        centuries = re.findall(century_regex, search_text, re.IGNORECASE)
        for century in centuries:
            century = int(century)
            start_year = (century - 1) * 100 + 1
            end_year = century * 100
            found_years.append(f'{start_year}-{end_year}')
        search_text_keywords.extend(found_years)

        print("--------------------------SEARCH TEXT KEYWORDS (SUBSEARCH)------------------------------------")
        print(search_text_keywords)

        db_results_all = []
        for ocr in used_ocrs:
            if not sub_search:
                db_result = self.database_service.select_from_table(ocr, "*", as_dict=True)
                db_results_all.append(db_result)
            else:
                for item in sub_search_paths:
                    db_result = self.database_service.select_from_table(ocr, "*", condition="path = %s", params=[item], as_dict=True)
                    db_results_all.append(db_result)

        # create dictionary with all texts and the matching image path
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

        # create dict with the keyword the label was found with as key and corresponding path as value
        intersection_dict = {}
        for key, text in path_text_dict.items():
            for keyword in search_text_keywords:
                text_intersection = DataProcessService.find_text_intersections(keyword, text)
                #print(text_intersection)
                if text_intersection:
                    text_intersection_str = next(iter(text_intersection))
                    if text_intersection_str in intersection_dict:
                        intersection_dict[text_intersection_str].add(key)
                    else:
                        intersection_dict[text_intersection_str] = {key}

        return intersection_dict
