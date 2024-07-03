from Services.DataProcessService import DataProcessService


data = DataProcessService()
test = data.is_word_correct_check("Tst", language="de_DE")

print(test[0])