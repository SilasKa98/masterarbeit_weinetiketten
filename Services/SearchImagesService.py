import hashlib
import itertools
import random
import re
import os
import pickle
import pprint

import nltk
import numpy as np
import torch
from transformers import BertTokenizer, BertModel
from annoy import AnnoyIndex
from deep_translator import GoogleTranslator
import spacy
from spacy.matcher import PhraseMatcher
from Services.DatabaseService import DatabaseService
from Services.DataProcessService import DataProcessService
from Services.DetailFinderService import DetailFinderService
from collections import defaultdict

from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import ProcessPoolExecutor, as_completed


class SearchImagesService:

    def __init__(self, semantic_vector_cache_file='vector_cache.pkl',
                 country_cache_file="country_cache.pkl",
                 province_cache_file="province_cache.pkl",
                 annoy_index_cache_file="annoy_cache.ann"):
        self.database_service = DatabaseService()

        self.semantic_vector_cache_file = semantic_vector_cache_file
        self.annoy_index_cache_file = annoy_index_cache_file
        self.country_cache_file = country_cache_file
        self.province_cache_file = province_cache_file

        self.semantic_vector_cache = self.load_cache(self.semantic_vector_cache_file)
        self.annoy_index_cache = self.load_annoy_cache(self.annoy_index_cache_file)
        self.country_list_cache = self.load_cache(self.country_cache_file)
        self.province_list_cache = self.load_cache(self.province_cache_file)

        self.semantic_vector_cache_hash = self._compute_cache_hash()
        self.additional_country_infos = []
        self.entity_search_dict_with_adds = {}
        self.search_for_province = False
        self.search_for_country = False

    @staticmethod
    def load_cache(cache_file):
        if os.path.exists(cache_file):
            with open(cache_file, 'rb') as f:
                return pickle.load(f)
        return {}

    @staticmethod
    def save_cache(cache_file, cache_data):
        with open(cache_file, 'wb') as f:
            pickle.dump(cache_data, f)

    def update_cache_semantic_search(self, db_results, tokenizer, model):
        for result in db_results:
            key = (result['path'], result['ocr_model'], result['column'])
            text = result['text']
            if key not in self.semantic_vector_cache:
                vector = self.aggregate_text_vector(text, tokenizer, model)
                self.semantic_vector_cache[key] = vector
        self.save_cache(self.semantic_vector_cache_file, self.semantic_vector_cache)
        self.semantic_vector_cache_hash = self._compute_cache_hash()


    def load_annoy_cache(self, cache_file):
        if os.path.exists(cache_file):
            vectors = list(self.semantic_vector_cache.values())
            f = len(vectors[0]) if vectors else 0
            annoy_index = AnnoyIndex(f, 'angular')
            annoy_index.load(cache_file)
            return annoy_index
        return None

    @staticmethod
    def save_annoy_cache(cache_file, annoy_index):
        annoy_index.save(cache_file)

    def _compute_cache_hash(self):
        # calc hash value for vectors in cache
        vector_data = pickle.dumps(self.semantic_vector_cache)
        return hashlib.md5(vector_data).hexdigest()

    def update_annoy_index_cache(self):
        if not self.semantic_vector_cache:
            print("No semantic vectors to build the Annoy index.")
            return

        current_hash = self._compute_cache_hash()
        print(f"Current hash: {current_hash}")
        print(f"Stored hash: {self.semantic_vector_cache_hash}")
        if self.semantic_vector_cache_hash == current_hash:
            print("No changes detected in semantic vectors. Annoy index is up to date.")
            return

        annoy_index = self.build_annoy_index()

        self.save_annoy_cache(self.annoy_index_cache_file, annoy_index)
        self.annoy_index_cache = annoy_index
        self.semantic_vector_cache_hash = current_hash

    def update_cache_details_label_search(self):
        if self.country_list_cache == {} or self.province_list_cache == {}:
            details = DetailFinderService(init_path_text_dict=False)
            self.country_list_cache = details.get_all_countries_with_infos()
            self.save_cache(self.country_cache_file, self.country_list_cache)

            self.province_list_cache = details.get_provinces()
            self.save_cache(self.province_cache_file, self.province_list_cache)

    def search_algorithm(self, search_text, search_logic_combined, percentage_matching_range, number_of_used_db_entries):

        entity_search_dict = self.named_entity_recognition(search_text)
        entity_search_text = " ".join(ent for ents in entity_search_dict.values() for ent in ents)
        query = entity_search_text.strip() or search_text

        print("entity_search_dict")
        print(entity_search_dict)

        found_paths_semantic = self.semantic_search(query)
        label_details_result = self.search_with_db_label_details(entity_search_dict, number_of_used_db_entries)
        text_based_result = self.text_based_keyword_search(entity_search_dict, search_text, percentage_matching_range, number_of_used_db_entries)
        # TODO check for double entries here, so no labels are redundant in this dict
        text_based_x_label_details = {}
        for key in set(text_based_result.keys()).union(label_details_result.keys()):
            if key in text_based_result and key in label_details_result:
                text_based_x_label_details[key] = text_based_result[key].union(label_details_result[key])
            elif key in text_based_result:
                text_based_x_label_details[key] = text_based_result[key]
            elif key in label_details_result:
                text_based_x_label_details[key] = label_details_result[key]

        text_based_result = text_based_x_label_details

        # if search for country combine all provinces of the country in one dict key
        if self.search_for_province is False and self.search_for_country is True and search_logic_combined is False:
            country_summed_text_based_result = {}
            for key, item in text_based_result.items():
                found_country = next((inner_key for inner_key, inner_list in self.additional_country_infos.items() if key in inner_list), None)

                if found_country and key in self.additional_country_infos[found_country]:
                    new_key = GoogleTranslator(source='en', target='de').translate(found_country).lower()
                    if new_key not in country_summed_text_based_result:
                        country_summed_text_based_result[new_key] = list(set())
                    for inner_item in item:
                        country_summed_text_based_result[new_key].append(inner_item)
                else:
                    country_summed_text_based_result[key] = list(set(item))

            text_based_result = country_summed_text_based_result

        found_paths_only = [path for path, _, _ in found_paths_semantic]
        #top_hits = self.text_based_keyword_search(search_text, sub_search=True, sub_search_paths=found_paths_only)
        top_hits = {key: set(pfad for pfad in pfade if pfad in found_paths_only) for key, pfade in text_based_result.items()}

        if search_logic_combined:
            # doing result adjustment for normal textbased results if combined box is checked
            text_based_result_combinations = self.combined_search_result_adjustment(text_based_result, self.entity_search_dict_with_adds)
            if text_based_result_combinations:
                text_based_result = text_based_result_combinations
                text_based_result = {key: list(set(value)) for key, value in text_based_result.items()}

            # doing result adjustments for top hits if combined box is checked
            top_hits_combinations = self.combined_search_result_adjustment(top_hits, self.entity_search_dict_with_adds)

            if top_hits_combinations:
                top_hits = top_hits_combinations
                top_hits = {key: list(set(value)) for key, value in top_hits.items()}

        # limit top hits to 24 items
        data_processing = DataProcessService()
        top_hits = data_processing.limit_dict_items(top_hits, 24)

        # extend all values from top_hits in a new list set to create second_choice_hits out of it
        sub_search_values_list = list(set())
        for value_set in top_hits.values():
            sub_search_values_list.extend(value_set)

        # create second_choice_hits without already seen items and limit it to max 32 items
        second_choice_hits = list(filter(lambda x: x not in sub_search_values_list, found_paths_only))
        second_choice_hits = second_choice_hits[:32]

        # remove all paths from text_based_results that are already in top hits
        top_hits_values = set(v for values in top_hits.values() for v in values)
        if len(top_hits_values) > 0:
            for key, values in text_based_result.items():
                text_based_result[key] = {value for value in values if value not in top_hits_values}

        print("Search DONE !")
        return top_hits, second_choice_hits, text_based_result

    def combined_search_result_adjustment(self, input_result, entity_dict):

        def is_valid_combination(inner_comb, types_dict):

            # get categories with 0 as placeholder value
            category_count = {inner_key: 0 for inner_key in types_dict}

            # now actually count for existing values
            for c_key, values in types_dict.items():
                category_count[c_key] = sum(1 for item in inner_comb if item in values)

            # check if there are multiple values for one category for this combination
            if any(count > 1 for count in category_count.values()):
                return False

            # check if every category has one elem in the current combination
            # so no incomplete combinations are made
            if not all(count > 0 for count in category_count.values()):
                return False

            return True

        all_values_for_comb = []
        for res in input_result.keys():
            all_values_for_comb.append(res)

        # if there is only 1 val there is no need to do combinations, so just return initial input dictionary
        if len(all_values_for_comb) == 1:
            return input_result

        combinations = []
        if entity_dict != {}:
            for r in range(2, len(entity_dict.keys()) + 1):
                for combo in itertools.combinations(all_values_for_comb, r):
                    print("combo:")
                    print(combo)
                    if is_valid_combination(combo, entity_dict):
                        combinations.append(combo)
        else:
            for r in range(2, len(input_result.keys()) + 1):
                for combo in itertools.combinations(all_values_for_comb, r):
                    print("combo:")
                    print(combo)
                    combinations.append(combo)

        combination_text_based_result = {}
        print("combinations: ")
        print(combinations)
        for combs in combinations:
            all_paths = [input_result[comb_key] for comb_key in combs]
            common_paths = all_paths[0]
            for s in all_paths[1:]:
                common_paths = common_paths.intersection(s)
            common_key = ' '.join(combs)
            combination_text_based_result[common_key] = common_paths

        if self.search_for_province is False and self.search_for_country is True:
            country_combined_dict = {}
            for key, item in combination_text_based_result.items():
                country_infos = self.additional_country_infos

                #current_country = next((inner_key for inner_key, inner_list in country_infos.items() if any(word in inner_list for word in key.split())), None)
                for c_key, c_info in self.additional_country_infos.items():
                    if bool([ele for ele in c_info if(ele in key)]):
                        current_country = c_key
                        break
                    else:
                        current_country = None

                if current_country is not None:
                    non_country_words = key.split()
                    country_infos_words = [word for item in country_infos[current_country] for word in item.split()]

                    filtered_non_country_words = [word for word in non_country_words if word not in country_infos_words]
                    non_country_words = " ".join(filtered_non_country_words)

                    current_country = GoogleTranslator(source='en', target='de').translate(current_country).lower()
                    new_dict_key = non_country_words+" "+current_country

                    if new_dict_key not in country_combined_dict:
                        country_combined_dict[new_dict_key] = list(set())
                    for txt_based_item in item:
                        country_combined_dict[new_dict_key].append(txt_based_item)
                else:
                    country_combined_dict[key] = item

            combination_text_based_result = country_combined_dict

        return combination_text_based_result

    @staticmethod
    def named_entity_recognition(search_text):
        nlp_de = spacy.load('de_core_news_lg')
        nlp_en = spacy.load('en_core_web_md')

        def create_matcher_for_additional_entities(filename, matcher_name, used_attr="LOWER"):
            matcher = PhraseMatcher(nlp_de.vocab, attr=used_attr)
            directory_path = os.getenv("DICTIONARY_FOLDER")
            with open(f"{directory_path}{filename}.txt", "r", encoding="utf-8") as file:
                new_data = [item.strip().lower() for item in file]

            if used_attr == "LEMMA":
                patterns = [nlp_de(text).to_array([spacy.attrs.LEMMA]) for text in new_data]
            else:
                patterns = [nlp_de(text) for text in new_data]

            matcher.add(matcher_name, patterns)
            return matcher

        matcher_names = create_matcher_for_additional_entities("wine_names", "WINENAMES", used_attr="LOWER")
        matcher_types = create_matcher_for_additional_entities("wine_types", "WINETYPES", used_attr="LOWER")
        matcher_attributes = create_matcher_for_additional_entities("wine_attributes", "WINEATTRIBUTES", used_attr="LEMMA")

        non_accent_search_text = DataProcessService.remove_accent_chars(search_text)

        doc_de = nlp_de(non_accent_search_text.lower())
        matches_names = matcher_names(doc_de)
        matches_types = matcher_types(doc_de)
        matches_attributes = matcher_attributes(doc_de)
        wine_name_matches = [doc_de[start:end].text for match_id, start, end in matches_names]
        # if statement ignores all values that are already present in wine_name_matches
        # -> this shouldn`t be necessary, however its to make sure that no double entries are generated
        wine_type_matches = [doc_de[start:end].text for match_id, start, end in matches_types if doc_de[start:end].text not in wine_name_matches]
        wine_attributes_matches = [doc_de[start:end].text for match_id, start, end in matches_attributes]

        # en model is used for date recognition
        doc_en = nlp_en(search_text)
        found_dates = [ent.text for ent in doc_en.ents if ent.label_ == "DATE"]

        date_pattern = re.compile(r'\b\d{1,4}\b')
        dates_from_regex = date_pattern.findall(search_text)
        found_dates.extend(dates_from_regex)
        found_dates = list(set(found_dates))

        # search for centuries
        century_regex = r'(\d{1,2})\s*\.?\s*jahrhundert'
        centuries = re.findall(century_regex, search_text, re.IGNORECASE)
        for century in centuries:
            century = int(century)
            start_year = (century - 1) * 100 + 1
            end_year = century * 100
            found_dates.append(f'{start_year}-{end_year}')

        entities_dict = {}
        if wine_name_matches:
            entities_dict["wine_names"] = wine_name_matches
        if wine_type_matches:
            entities_dict["wine_types"] = wine_type_matches
        if wine_attributes_matches:
            entities_dict["wine_attributes"] = wine_attributes_matches

        for ent in doc_de.ents:
            if ent.label_ in ["LOC", "GPE"]:
                if "loc" not in entities_dict:
                    entities_dict["loc"] = []

                # ignore possible found location if its already found as wine_name or wine_type
                # eg. chardonnay. Otherwise there will be problems later
                if "wine_names" in entities_dict and "wine_types" in entities_dict:
                    if ent.text not in entities_dict["wine_names"] and ent.text not in entities_dict["wine_types"]:
                        entities_dict["loc"].append(ent.text)
                elif "wine_names" in entities_dict:
                    if ent.text not in entities_dict["wine_names"]:
                        entities_dict["loc"].append(ent.text)
                elif "wine_types" in entities_dict:
                    if ent.text not in entities_dict["wine_types"]:
                        entities_dict["loc"].append(ent.text)
                else:
                    entities_dict["loc"].append(ent.text)
        if found_dates:
            entities_dict["date"] = found_dates
        # this code is especially targeting the loc entity. If the list of loc is created but remained empty, remove it
        # all other keys with empty lists will get removed too. Its to be save that no empty list remains, which would
        # conflict with the combination logic
        entities_dict = {key: value for key, value in entities_dict.items() if value}

        # filter for duplikates
        entities_dict = {key: list(set(value)) for key, value in entities_dict.items()}

        return entities_dict

    # sub function for semantic search
    @staticmethod
    def encode_text(text, tokenizer, model):
        inputs = tokenizer(text, return_tensors='pt', truncation=True, padding=True, max_length=512)
        #outputs = model(**inputs)
        #return outputs.last_hidden_state.mean(dim=1).squeeze().detach().numpy()
        with torch.no_grad():
            outputs = model(**inputs)
        return outputs.last_hidden_state.mean(dim=1).squeeze().cpu().numpy()

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

    # sub function for semantic search
    def build_annoy_index(self):
        vectors = list(self.semantic_vector_cache.values())
        f = len(vectors[0]) if vectors else 0
        t = AnnoyIndex(f, 'angular')

        for i, (key, vector) in enumerate(self.semantic_vector_cache.items()):
            t.add_item(i, vector)

        t.build(100000)
        return t

    def semantic_search(self, search_text, used_ocrs={"doctr": ["text_final", "text_pure_modified_images"],
                                                      "tesseract": ["text_final", "text_pure_modified_images"],
                                                      "easyocr": ["text_final", "text_pure_modified_images"],
                                                        }):
        tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
        model = BertModel.from_pretrained('bert-base-uncased')

        db_results_all = []
        for ocr_model, columns in used_ocrs.items():
            for column in columns:
                db_result = self.database_service.select_from_table(ocr_model, f"path, {column} as text", as_dict=True)
                for res in db_result:
                    res['ocr_model'] = ocr_model
                    res['column'] = column
                db_results_all.extend(db_result)

        # update sematic_search cache
        self.update_cache_semantic_search(db_results_all, tokenizer, model)
        # update annoy_index cache
        self.update_annoy_index_cache()

        #t = self.build_annoy_index()
        if not self.annoy_index_cache:
            self.annoy_index_cache = self.build_annoy_index()
            self.save_annoy_cache(self.annoy_index_cache_file, self.annoy_index_cache)
        else:
            vectors = list(self.semantic_vector_cache.values())
            f = len(vectors[0]) if vectors else 0
            #self.annoy_index_cache = AnnoyIndex(
                #self.semantic_vector_cache[list(self.semantic_vector_cache.keys())[0]].shape[0], 'angular')
            self.annoy_index_cache = AnnoyIndex(f, 'angular')
            self.annoy_index_cache.load(self.annoy_index_cache_file)

        query = search_text
        query_vector = self.encode_text(query, tokenizer, model)
        #indices = t.get_nns_by_vector(query_vector, 50)
        indices = self.annoy_index_cache.get_nns_by_vector(query_vector, 600)

        found_paths = [list(set(self.semantic_vector_cache.keys()))[i] for i in indices]

        return found_paths

    def text_based_keyword_search(self, entity_search_dict, search_text, percentage_matching_range, number_of_used_db_entries,
                                  used_ocrs=["easyocr", "tesseract", "doctr"], sub_search=False, sub_search_paths=[]):
        if len(self.additional_country_infos) > 0:
            values_to_add = set()
            for value_list in self.additional_country_infos.values():
                values_to_add.update(value_list)
            entity_search_dict["loc"].extend(values_to_add)
            entity_search_dict["loc"] = list(set(entity_search_dict["loc"]))

        search_text_keywords = set()
        if entity_search_dict:
            for v in entity_search_dict.values():
                search_text_keywords.update(v)
        else:
            search_text_keywords = set(
                DataProcessService.create_keywords_of_scentence(search_text, "de", 4, 6, 0.9)[0][0].split()
            )

        db_results_all = []
        for ocr in used_ocrs:
            if not sub_search:
                db_result = self.database_service.select_from_table(ocr, "*", as_dict=True)
                db_results_all.append(db_result)
            else:
                for item in sub_search_paths:
                    db_result = self.database_service.select_from_table(ocr, "*", condition="path = %s", params=[item], as_dict=True)
                    db_results_all.append(db_result)

        if number_of_used_db_entries is not None:
            #number_of_used_db_entries = round(number_of_used_db_entries / len(used_ocrs))
            for i in range(len(db_results_all)):
                db_results_all[i] = random.choices(db_results_all[i], k=number_of_used_db_entries)

        path_text_dict = defaultdict(list)
        for inner_list in db_results_all:
            for item in inner_list:
                current_path = item.get("path")
                if current_path:
                    # join all texts of the current path
                    texts = " ".join(v for k, v in item.items() if k != "path")
                    path_text_dict[current_path].append(texts)

        # create final path_text_dict string
        path_text_dict = {k: " ".join(v) for k, v in path_text_dict.items()}

        print("path_text_dict_len: ", len(path_text_dict))

        # load lists for find_text_intersection logic
        def load_file(file_path):
            with open(file_path, "r", encoding="utf-8") as file:
                return [item.strip().lower() for item in file]

        blacklisted_words = load_file(os.getenv("BLACKLISTED_WORDS_FILE"))
        wine_names = load_file(os.getenv("WINE_NAMES_FILE"))
        wine_types = load_file(os.getenv("WINE_TYPES_FILE"))

        def create_doc_tokens(text_doc):
            tokens = nltk.word_tokenize(text_doc.lower())
            filtered_tokens = set(token for token in tokens if len(token) >= 5)
            return filtered_tokens

        doc_tokens_dict = {k: create_doc_tokens(v) for k, v in path_text_dict.items()}

        print("search_threshold: ",percentage_matching_range)
        intersection_dict = defaultdict(set)
        for key, text in path_text_dict.items():
            for keyword in search_text_keywords:
                text_intersection = DataProcessService.find_text_intersections(keyword, doc_tokens_dict[key], wine_names, wine_types,
                                                                               blacklisted_words, threshold=percentage_matching_range)
                if text_intersection:
                    text_intersection_str = next(iter(text_intersection))
                    intersection_dict[text_intersection_str].add(key)

        return intersection_dict

    def search_with_db_label_details(self, search_entity_dict, number_of_used_db_entries):
        self.update_cache_details_label_search()

        db_details_result = self.database_service.select_from_table("etiketten_infos", "path, country, provinces, anno, vol, wine_type", as_dict=True)

        if number_of_used_db_entries is not None:
            db_details_result = random.choices(db_details_result, k=number_of_used_db_entries)

        entity_list = list()

        for key, item in search_entity_dict.items():
            for item_text in item:
                entity_list.append(item_text)

        # check if the search_entity aka search text has common words with the countries dict
        country_entity_relation_list = {}
        found_country_keys = []
        for key, value in self.country_list_cache.items():

            if any(i.lower() in (s.lower() for s in entity_list) for i in value):
                # a province/country name was found for
                found_country_key = key
                if found_country_key not in country_entity_relation_list:
                    country_entity_relation_list[found_country_key] = list(set())
                country_entity_relation_list[found_country_key].extend(value)

        country_entity_relation_list = {key: [inner_item.lower() for inner_item in item] for key, item in country_entity_relation_list.items()}

        if len(country_entity_relation_list) > 0:
            found_provinces_list = {}
            for country_name in country_entity_relation_list.keys():
                found_provinces_list[country_name] = [province_name.lower() for province_name in self.province_list_cache[country_name]]
            self.search_for_country = True

            # check if searchentitys/searchwords are provinces. If so, remove the found provinces from the provinces -
            # list now the provinces list can be used to remove the remaining provinces from the country_entity_relation_list
            # with this logic, its only searched for the specific province and not for other provinces,
            # which arent desired to be shown
            found_provinces_intersection = {}
            for key, item in found_provinces_list.items():
                if len(set(item).intersection(entity_list)) > 0:
                    found_provinces_intersection[key] = list(set(item).intersection(entity_list))

            if len(found_provinces_intersection) > 0:
                self.search_for_province = True
                country_entity_relation_list = found_provinces_intersection

            self.additional_country_infos = country_entity_relation_list
            for item in country_entity_relation_list.values():
                search_entity_dict["loc"].extend(item)

        self.entity_search_dict_with_adds = search_entity_dict

        detail_search_findings = {}
        for elem in db_details_result:
            for key, item in elem.items():
                if key in {"anno", "vol"} and str(item) in entity_list:
                    if str(item) in detail_search_findings:
                        detail_search_findings[str(item)].add(elem["path"])
                    else:
                        detail_search_findings[str(item)] = {elem["path"]}
                if key in {"wine_type"}:
                    found_weiß = any("weiß" in word for word in entity_list)
                    found_weiss = any("weiss" in word for word in entity_list)
                    found_red = any("rot" in word for word in entity_list)
                    if found_red and str(item) == "red wine":
                        if "rotwein" in detail_search_findings:
                            detail_search_findings["rotwein"].add(elem["path"])
                        else:
                            detail_search_findings["rotwein"] = {elem["path"]}
                    if (found_weiß or found_weiss) and str(item) == "white wine":
                        if found_weiß:
                            dict_key = "weißwein"
                        else:
                            dict_key = "weisswein"
                        if dict_key in detail_search_findings:
                            detail_search_findings[dict_key].add(elem["path"])
                        else:
                            detail_search_findings[dict_key] = {elem["path"]}
                if key in {"country", "provinces"}:
                    for c_p_item in country_entity_relation_list.values():
                        if str(item.lower()) in c_p_item:
                            if str(item.lower()) in detail_search_findings:
                                detail_search_findings[str(item.lower())].add(elem["path"])
                            else:
                                detail_search_findings[str(item.lower())] = {elem["path"]}

        return detail_search_findings





