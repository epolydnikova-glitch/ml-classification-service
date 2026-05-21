import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
import joblib

df = pd.read_csv('ds.csv')

df['target'] = df['awarded'].map({'Да': 1, 'Нет': 0})

num_cols = ['Google Scholar', 'Scopus', 'Web of science', 'РИНЦ', 'ВАК', 'Вклад %']

cat_cols = ['Вид деятельности', 'Вид достижения', 'Уровень мероприятия', 'Уровень участия']

text_cols = ['Авторы (Соавторы)', 'Наименование статьи', 'Подписант', 'Ссылки на новости', 
             'Номер патента', 'Номер удостоверения', 'Ступень', 'Дата выдачи']

for col in text_cols:
    df[f'{col}_has_value'] = df[col].apply(lambda x: 0 if pd.isna(x) or str(x).strip() in ['', '-', '<NULL>'] else 1)

binary_cols = [f'{col}_has_value' for col in text_cols]

X = df[num_cols + cat_cols + binary_cols]
y = df['target']

num_transformer = Pipeline(steps=[
    ('imputer', SimpleImputer(strategy='constant', fill_value=0)),
    ('scaler', StandardScaler())
])
cat_transformer = Pipeline(steps=[
    ('imputer', SimpleImputer(strategy='constant', fill_value='unknown')),
    ('onehot', OneHotEncoder(handle_unknown='ignore', sparse_output=False))
])

preprocessor = ColumnTransformer(
    transformers=[
        ('num', num_transformer, num_cols),
        ('cat', cat_transformer, cat_cols),
        ('bin', 'passthrough', binary_cols)
    ])
model_pipeline = Pipeline(steps=[
    ('preprocessor', preprocessor),
    ('classifier', RandomForestClassifier(n_estimators=100, class_weight='balanced', random_state=42))
])
model_pipeline.fit(X, y)
encoded_cat_cols = model_pipeline.named_steps['preprocessor']\
                                 .named_transformers_['cat']\
                                 .named_steps['onehot']\
                                 .get_feature_names_out(cat_cols).tolist()

all_features = num_cols + encoded_cat_cols + binary_cols
importances = model_pipeline.named_steps['classifier'].feature_importances_
weights_df = pd.DataFrame({
    'Признак': all_features,
    'Вес': importances
}).sort_values(by='Вес', ascending=False)
print("\nВеса признаков для будущих предсказаний")
print(weights_df.to_string(index=False))
joblib.dump(model_pipeline, 'awarded_model_pipeline.pkl')
print("Модель успешно экспортирована в файл 'awarded_model_pipeline.pkl'")