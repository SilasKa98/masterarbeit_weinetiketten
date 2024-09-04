from spellchecker import SpellChecker
from transformers import BertTokenizer, BertForMaskedLM
import torch

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

    def get_word_confidence(self, original_word, corrected_word):
        original_freq = self.spell.word_frequency[original_word]
        corrected_freq = self.spell.word_frequency[corrected_word]

        # pretend 0 division
        total_freq = original_freq + corrected_freq + 1e-9

        confidence = corrected_freq / total_freq

        if corrected_freq > 0 and original_freq > 0:
            confidence = 1 / (1 + (original_freq / corrected_freq))

        return confidence

    @staticmethod
    def get_word_confidence_with_BERT(sentence, target_word, corrected_word):
        print("sentence: ", sentence)
        print("target_word: ", target_word)
        print("corrected_word: ", corrected_word)

        # Überprüfe, ob das target_word im Satz vorkommt
        if target_word not in sentence:
            raise ValueError(f"'{target_word}' not found in the sentence.")

        model_name = 'bert-base-multilingual-cased'  # Oder 'bert-base-german-cased'
        tokenizer = BertTokenizer.from_pretrained(model_name)
        model = BertForMaskedLM.from_pretrained(model_name)

        # Ersetze das target_word durch [MASK]
        masked_sentence = sentence.replace(target_word, '[MASK]', 1)
        inputs = tokenizer(masked_sentence, return_tensors='pt')

        with torch.no_grad():
            outputs = model(**inputs)
            predictions = outputs.logits

        # Finde den Index des maskierten Tokens
        masked_index = torch.where(inputs['input_ids'][0] == tokenizer.mask_token_id)[0].item()

        # Extrahiere die Wahrscheinlichkeiten für das korrigierte Wort
        target_token_id = tokenizer.convert_tokens_to_ids(corrected_word)
        probability = torch.softmax(predictions[0, masked_index], dim=-1)[target_token_id].item()

        # Extrahiere die Top 5 Vorhersagen für das maskierte Wort
        top_predictions = predictions[0, masked_index].topk(5).indices.tolist()
        top_predicted_words = [tokenizer.decode([token_id]) for token_id in top_predictions]

        print(f"Top 5 Vorhersagen für das maskierte Wort: {top_predicted_words}")

        return corrected_word, probability, top_predicted_words

    def is_word_correct_check(self, word):
        is_correct = self.spell.known([word])

        if is_correct:
            is_correct = True
            suggestions = {}
        else:
            is_correct = False
            suggestions = self.spell.candidates(word)

        return is_correct, suggestions
