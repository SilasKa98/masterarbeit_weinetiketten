import yake
kw_extractor = yake.KeywordExtractor()
text = """Freiburger kabinette trocken aus 1990"""
language = "de"
max_ngram_size = 3
deduplication_threshold = 0.4
numOfKeywords = 4
custom_kw_extractor = yake.KeywordExtractor(lan=language, n=max_ngram_size, dedupLim=deduplication_threshold, top=numOfKeywords, features=None)
keywords = custom_kw_extractor.extract_keywords(text)
for kw in keywords:
  print(kw)