import pandas as pd
from sklearn.model_selection import train_test_split
from keras.preprocessing.text import Tokenizer
from keras.preprocessing.sequence import pad_sequences
from keras.models import Model
from keras.layers import Embedding, LSTM, Dense, Input, concatenate, Flatten

# Daten laden und vorbereiten
wine_data = pd.read_csv("data/winemag-data-130k-v2.csv")
wine_data = wine_data.dropna()

# Ausgewählte Spalten für das Modell
selected_columns = ['country', 'description', 'designation', 'price', 'province', 'region_1', 'region_2']

# Extrahiere numerische Daten
numeric_columns = ['price']
numerical_data = wine_data[numeric_columns].values

# Normalisiere die numerischen Daten (optional)
mean = numerical_data.mean(axis=0)
std = numerical_data.std(axis=0)
numerical_data = (numerical_data - mean) / std

# Tokenisiere und padde die textuellen Daten
tokenizer = Tokenizer(oov_token="<OOV>")
tokenizer.fit_on_texts(wine_data['description'])
vocab_size = len(tokenizer.word_index) + 1
max_length = 50
data_sequences = tokenizer.texts_to_sequences(wine_data['description'])
data_padded = pad_sequences(data_sequences, maxlen=max_length, padding='post', truncating='post')

# Aufteilen der Daten in Trainings- und Testsets
X_numerical_train, X_numerical_test, X_text_train, X_text_test, y_train, y_test = train_test_split(
    numerical_data, data_padded, wine_data['points'], test_size=0.2, random_state=42
)

# Modell erstellen
numerical_input = Input(shape=(numerical_data.shape[1],), name='numerical_input')
text_input = Input(shape=(max_length,), name='text_input')
embedding_dim = 50  # Beispielwert, du kannst dies anpassen
embedding_layer = Embedding(input_dim=vocab_size, output_dim=embedding_dim, input_length=max_length)(text_input)
lstm_layer_text = LSTM(units=100)(embedding_layer)  # LSTM für textuelle Daten
flattened_numerical = Flatten()(numerical_input)  # Flatten für numerische Daten
combined_input = concatenate([flattened_numerical, lstm_layer_text])  # Kombination der beiden Eingänge
output_layer = Dense(units=1, activation='linear')(combined_input)

model = Model(inputs=[numerical_input, text_input], outputs=output_layer)
model.compile(optimizer='adam', loss='mean_squared_error')

# Modell trainieren
num_epochs = 10  # Beispielwert, anpassen nach Bedarf
model.fit([X_numerical_train, X_text_train], y_train, epochs=num_epochs, validation_data=([X_numerical_test, X_text_test], y_test))

# Modell evaluieren
mse = model.evaluate([X_numerical_test, X_text_test], y_test)
print(f"Mean Squared Error on Test Set: {mse}")

# Vorhersagen für neue Daten
new_data_description = ["Ein Rotwein aus der Toskana."]
new_data_price = [50]
new_data_sequences = tokenizer.texts_to_sequences(new_data_description)
new_data_padded = pad_sequences(new_data_sequences, maxlen=max_length, padding='post', truncating='post')

# Reshape der numerischen Daten
import numpy as np
new_data_price = np.array(new_data_price).reshape(-1, 1)

prediction = model.predict([new_data_price, new_data_padded])
print(f"Predicted Points: {prediction[0]}")