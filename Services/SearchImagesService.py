import hashlib
import itertools
import re
import os
import pickle
import pprint
import numpy as np
import torch
from transformers import BertTokenizer, BertModel
from annoy import AnnoyIndex
import spacy
from spacy.matcher import PhraseMatcher
from Services.DatabaseService import DatabaseService
from Services.DataProcessService import DataProcessService
from Services.DetailFinderService import DetailFinderService

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

    def search_algorithm(self, search_text, search_logic_combined):

        entity_search_dict = self.named_entity_recognition(search_text)
        entity_search_text = " ".join(ent for ents in entity_search_dict.values() for ent in ents)

        query = entity_search_text.strip() or search_text
        print("########################(query)##################################")
        print(query)
        found_paths_semantic = self.semantic_search(query)
        label_details_result = self.search_with_db_label_details(entity_search_dict)
        text_based_result = self.text_based_keyword_search(search_text)
        # WIP check for double entries here, so no labels are redundant in this dict
        text_based_x_label_details = {}
        for key in set(text_based_result.keys()).union(label_details_result.keys()):
            if key in text_based_result and key in label_details_result:
                text_based_x_label_details[key] = text_based_result[key].union(label_details_result[key])
            elif key in text_based_result:
                text_based_x_label_details[key] = text_based_result[key]
            elif key in label_details_result:
                text_based_x_label_details[key] = label_details_result[key]

        text_based_result = text_based_x_label_details
        print("label_details_result")
        print(label_details_result)

        print("########################(text_based_result)##################################")
        pprint.pp(text_based_result)

        found_paths_only = [path for path, _, _ in found_paths_semantic]
        top_hits = self.text_based_keyword_search(search_text, sub_search=True, sub_search_paths=found_paths_only)
        print("entity_search_dict")
        print(entity_search_dict)
        if search_logic_combined:
            # doing result adjustment for normal textbased results if combined box is checked
            text_based_result_combinations = self.combined_search_result_adjustment(text_based_result, self.entity_search_dict_with_adds)
            if text_based_result_combinations:
                text_based_result = text_based_result_combinations

            # doing result adjustments for top hits if combined box is checked
            top_hits_combinations = self.combined_search_result_adjustment(top_hits, self.entity_search_dict_with_adds)
            print("top_hits_combinations")
            print(top_hits_combinations)
            if top_hits_combinations:
                top_hits = top_hits_combinations

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

        print("---------------------------new text based result------------------------------------------------")
        pprint.pp(text_based_result)
        pprint.pp(top_hits)

        # remove all paths from text_based_results that are already in top hits
        top_hits_values = set(v for values in top_hits.values() for v in values)
        if len(top_hits_values) > 0:
            for key, values in text_based_result.items():
                text_based_result[key] = {value for value in values if value not in top_hits_values}

        print("Search DONE !")
        return top_hits, second_choice_hits, text_based_result

    def combined_search_result_adjustment(self, input_result, entity_dict):

        def is_valid_combination(inner_comb, types_dict):

            print("types_dict_inner")
            print(types_dict)
            # get categories with 0 as placeholder value
            category_count = {inner_key: 0 for inner_key in types_dict}

            print("category_count1")
            print(category_count)

            # now actually count for existing values
            for c_key, values in types_dict.items():
                category_count[c_key] = sum(1 for item in inner_comb if item in values)

            print("category_count2")
            print(category_count)

            # check if there are multiple values for one category for this combination
            if any(count > 1 for count in category_count.values()):
                print("return false")
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

        print("all vals for comb")
        print(all_values_for_comb)

        combinations = []
        for r in range(2, len(all_values_for_comb) + 1):
            for combo in itertools.combinations(all_values_for_comb, r):
                print("combo:")
                print(combo)
                print(is_valid_combination(combo, entity_dict))
                if is_valid_combination(combo, entity_dict):
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

        print("combination_text_based_result")
        print(combination_text_based_result)
        if self.search_for_province is False and self.search_for_country is True:
            country_combined_dict = {}
            for key, item in combination_text_based_result.items():
                print("combination_text_based_resultkey")
                print(key)
                if any(word in entity_dict["loc"] for word in key.split()):
                    print("rein in neues dict")
                    new_dict_key = ""
                    for entity_item in entity_dict.values():
                        new_dict_key += entity_item[0] + " "

                    if new_dict_key not in country_combined_dict:
                        country_combined_dict[new_dict_key] = list(set())
                    for txt_based_item in combination_text_based_result[key]:
                        country_combined_dict[new_dict_key].append(txt_based_item)
                else:
                    country_combined_dict[key] = combination_text_based_result[key]
            combination_text_based_result = country_combined_dict

        return combination_text_based_result

    @staticmethod
    def named_entity_recognition(search_text):
        nlp_de = spacy.load('de_core_news_md')
        nlp_en = spacy.load('en_core_web_md')

        def create_matcher_for_additional_entities(filename, matcher_name):
            matcher = PhraseMatcher(nlp_de.vocab, attr='LOWER')
            with open(f"C:\\Masterarbeit_ocr_env\\dictionary_files\\{filename}.txt", "r", encoding="utf-8") as file:
                new_data = [item.strip().lower() for item in file]
            patterns = [nlp_de(text) for text in new_data]
            matcher.add(matcher_name, patterns)
            return matcher

        matcher_names = create_matcher_for_additional_entities("wine_names", "WINENAMES")
        matcher_types = create_matcher_for_additional_entities("wine_types", "WINETYPES")

        non_accent_search_text = DataProcessService.remove_accent_chars(search_text)

        doc_de = nlp_de(non_accent_search_text.lower())
        matches_names = matcher_names(doc_de)
        matches_types = matcher_types(doc_de)
        wine_name_matches = [doc_de[start:end].text for match_id, start, end in matches_names]
        # if statement ignores all values that are already present in wine_name_matches
        # -> this shouldn`t be necessary, however its to make sure that no double entries are generated
        wine_type_matches = [doc_de[start:end].text for match_id, start, end in matches_types if doc_de[start:end].text not in wine_name_matches]

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

        print("--------------semantic search text:------------")
        print(search_text)

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
        print(indices)

        found_paths = [list(set(self.semantic_vector_cache.keys()))[i] for i in indices]
        print(found_paths)

        return found_paths

    def text_based_keyword_search(self, search_text, used_ocrs=["easyocr", "tesseract", "doctr"], sub_search=False, sub_search_paths=[]):
        if len(self.additional_country_infos) > 0:
            additional_country_infos_str = " ".join(self.additional_country_infos)
            search_text = search_text+" "+additional_country_infos_str
        search_entitys = self.named_entity_recognition(search_text)
        search_text_keywords = list(set())
        if search_entitys:
            for k, v in search_entitys.items():
                search_text_keywords.extend(v)
        else:
            search_text_keywords = DataProcessService.create_keywords_of_scentence(search_text, "de", 4, 6, 0.9)[0].split()

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

    def search_with_db_label_details(self, search_entity_dict):
        self.update_cache_details_label_search()

        db_details_result = self.database_service.select_from_table("etiketten_infos", "path, country, provinces, anno, vol, wine_type", as_dict=True)
        entity_list = list()

        for key, item in search_entity_dict.items():
            for item_text in item:
                entity_list.append(item_text)

        # check if the search_entity aka search text has common words with the countries dict
        country_entity_relation_list = list(set())
        for key, value in self.country_list_cache.items():
            print(entity_list)
            print(value)
            #if bool(set(entity_list) & set(item)):
            if any(i.lower() in (s.lower() for s in entity_list) for i in value):
                # a province/country name was found for
                found_country_key = key
                country_entity_relation_list.extend(value)
        country_entity_relation_list = [item.lower() for item in country_entity_relation_list]

        if len(country_entity_relation_list) > 0:
            found_provinces_list = [item.lower() for item in self.province_list_cache[found_country_key]]
            self.search_for_country = True
            # check if searchentitys/searchwords are provinces. If so, remove the found provinces from the provinces -
            # list now the provinces list can be used to remove the remaining provinces from the country_entity_relation_list
            # with this logic, its only searched for the specific province and not for other provinces,
            # which arent desired to be shown
            found_provinces_intersection = set(found_provinces_list).intersection(entity_list)
            print("found_provinces_intersection")
            print(found_provinces_intersection)
            if len(found_provinces_intersection) > 0:
                self.search_for_province = True
                found_provinces_list = [element for element in found_provinces_list if element not in found_provinces_intersection]
                country_entity_relation_list = [element for element in country_entity_relation_list if element not in found_provinces_list]

            self.additional_country_infos = country_entity_relation_list
            search_entity_dict["loc"].extend(country_entity_relation_list)

        self.entity_search_dict_with_adds = search_entity_dict

        print("country_entity_relation_list")
        print(country_entity_relation_list)
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
                if key in {"country", "provinces"} and str(item.lower()) in country_entity_relation_list:
                    if str(item.lower()) in detail_search_findings:
                        detail_search_findings[str(item.lower())].add(elem["path"])
                    else:
                        detail_search_findings[str(item.lower())] = {elem["path"]}

        return detail_search_findings





