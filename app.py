from flask import Flask, render_template, url_for, jsonify, redirect, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import joblib
import pandas as pd

db = SQLAlchemy()
app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

try:
    awarded_model = joblib.load('awarded_model_pipeline.pkl')
except Exception as e:
    print(f"Критическая ошибка: Не удалось загрузить awarded_model_pipeline.pkl: {e}")
    awarded_model = None

db.init_app(app)

class Record(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    google_scholar = db.Column(db.Float, default=0.0)
    scopus = db.Column(db.Float, default=0.0)
    web_of_science = db.Column(db.Float, default=0.0)
    rinc = db.Column(db.Float, default=0.0)
    vak = db.Column(db.Float, nullable=True)
    vklad = db.Column(db.Float, nullable=True)
    vid_deyatelnosti = db.Column(db.String(100), nullable=True)
    vid_dostizheniya = db.Column(db.String(100), nullable=True)
    uroven_meropriyatiya = db.Column(db.String(100), nullable=True)
    uroven_uchastiya = db.Column(db.String(100), nullable=True)
    autori = db.Column(db.Text, nullable=True)
    naimenovanie_stati = db.Column(db.Text, nullable=True)
    podpisant = db.Column(db.String(100), nullable=True)
    ssilki_na_novosti = db.Column(db.Text, nullable=True)
    nomer_patenta = db.Column(db.String(50), nullable=True)
    nomer_udostovereniya = db.Column(db.String(50), nullable=True)
    stupen = db.Column(db.String(50), nullable=True)
    data_vidachi = db.Column(db.String(50), nullable=True)
    awarded_prediction = db.Column(db.String(10), nullable=False)
    awarded_probability = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'google_scholar': self.google_scholar,
            'scopus': self.scopus,
            'web_of_science': self.web_of_science,
            'rinc': self.rinc,
            'vak': self.vak,
            'vklad': self.vklad,
            'vid_deyatelnosti': self.vid_deyatelnosti,
            'vid_dostizheniya': self.vid_dostizheniya,
            'uroven_meropriyatiya': self.uroven_meropriyatiya,
            'uroven_uchastiya': self.uroven_uchastiya,
            'autori': self.autori,
            'naimenovanie_stati': self.naimenovanie_stati,
            'podpisant': self.podpisant,
            'ssilki_na_novosti': self.ssilki_na_novosti,
            'nomer_patenta': self.nomer_patenta,
            'nomer_udostovereniya': self.nomer_udostovereniya,
            'stupen': self.stupen,
            'data_vidachi': self.data_vidachi,
            'awarded_prediction': self.awarded_prediction,
            'awarded_probability': self.awarded_probability,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f'<Record {self.id} -> Awarded: {self.awarded_prediction}>'


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/history')
def history():
    records = Record.query.order_by(Record.id.desc()).all()
    return render_template('history.html', records=records)


@app.route('/prediction')
def prediction():
    record_id = request.args.get('edit', None)
    record = None
    if record_id:
        record = db.session.get(Record, int(record_id))
    return render_template('prediction.html', record=record)


@app.route('/predict', methods=["POST"])
def predict():
    if not awarded_model:
        return jsonify({"error": "Модель предсказания отсутствует"}), 500

    try:
        record_id = request.form.get('record_id')
        existing_record = None
        if record_id:
            existing_record = db.session.get(Record, int(record_id))
            if not existing_record:
                return jsonify({"error": "Запись не найдена"}), 404

        custom_id_str = request.form.get('custom_id')
        custom_id = None
        if not existing_record and custom_id_str and custom_id_str.strip():
            try:
                custom_id = int(custom_id_str.strip())
            except ValueError:
                return jsonify({"error": "ID должен быть целым числом"}), 400
            if custom_id <= 0:
                return jsonify({"error": "ID должен быть положительным целым числом"}), 400
            if db.session.get(Record, custom_id):
                return jsonify({"error": f"Запись с ID {custom_id} уже существует"}), 400

        raw_autori = request.form.get('autori') or None
        raw_stati = request.form.get('naimenovanie_stati') or None
        raw_podpisant = request.form.get('podpisant') or None
        raw_novosti = request.form.get('ssilki_na_novosti') or None
        raw_patenta = request.form.get('nomer_patenta') or None
        raw_udostovereniya = request.form.get('nomer_udostovereniya') or None
        raw_stupen = request.form.get('stupen') or None
        raw_data = request.form.get('data_vidachi') or None

        def check_val(x):
            return 0 if pd.isna(x) or str(x).strip() in ['', '-', '<NULL>', 'None'] else 1

        form_data = {
            'Google Scholar': float(1 if request.form.get('google_scholar') == 'да' else 0),
            'Scopus': float(1 if request.form.get('scopus') == 'да' else 0),
            'Web of science': float(1 if request.form.get('web_of_science') == 'да' else 0),
            'РИНЦ': float(1 if request.form.get('rinc') == 'да' else 0),
            'ВАК': float(1 if request.form.get('vak') == 'да' else 0),
            'Вклад %': float(request.form.get('vklad')) if request.form.get('vklad') and request.form.get('vklad').strip() else None,
            'Вид деятельности': request.form.get('vid_deyatelnosti') or None,
            'Вид достижения': request.form.get('vid_dostizheniya') or None,
            'Уровень мероприятия': request.form.get('uroven_meropriyatiya') or None,
            'Уровень участия': request.form.get('uroven_uchastiya') or None,
            'Авторы (Соавторы)_has_value': check_val(raw_autori),
            'Наименование статьи_has_value': check_val(raw_stati),
            'Подписант_has_value': check_val(raw_podpisant),
            'Ссылки на новости_has_value': check_val(raw_novosti),
            'Номер патента_has_value': check_val(raw_patenta),
            'Номер удостоверения_has_value': check_val(raw_udostovereniya),
            'Ступень_has_value': check_val(raw_stupen),
            'Дата выдачи_has_value': check_val(raw_data)
        }

        df_new = pd.DataFrame([form_data])
        probabilities = awarded_model.predict_proba(df_new)
        prob_yes = round(float(probabilities[0][1]) * 100, 2)
        prediction_code = int(awarded_model.predict(df_new)[0])
        verdict = "Да" if prediction_code == 1 else "Нет"

        if existing_record:
            existing_record.google_scholar = form_data['Google Scholar']
            existing_record.scopus = form_data['Scopus']
            existing_record.web_of_science = form_data['Web of science']
            existing_record.rinc = form_data['РИНЦ']
            existing_record.vak = form_data['ВАК']
            existing_record.vklad = form_data['Вклад %']
            existing_record.vid_deyatelnosti = form_data['Вид деятельности']
            existing_record.vid_dostizheniya = form_data['Вид достижения']
            existing_record.uroven_meropriyatiya = form_data['Уровень мероприятия']
            existing_record.uroven_uchastiya = form_data['Уровень участия']
            existing_record.autori = raw_autori
            existing_record.naimenovanie_stati = raw_stati
            existing_record.podpisant = raw_podpisant
            existing_record.ssilki_na_novosti = raw_novosti
            existing_record.nomer_patenta = raw_patenta
            existing_record.nomer_udostovereniya = raw_udostovereniya
            existing_record.stupen = raw_stupen
            existing_record.data_vidachi = raw_data
            existing_record.awarded_prediction = verdict
            existing_record.awarded_probability = prob_yes
            new_record = existing_record  
        else:
            new_kwargs = dict(
                google_scholar=form_data['Google Scholar'],
                scopus=form_data['Scopus'],
                web_of_science=form_data['Web of science'],
                rinc=form_data['РИНЦ'],
                vak=form_data['ВАК'],
                vklad=form_data['Вклад %'],
                vid_deyatelnosti=form_data['Вид деятельности'],
                vid_dostizheniya=form_data['Вид достижения'],
                uroven_meropriyatiya=form_data['Уровень мероприятия'],
                uroven_uchastiya=form_data['Уровень участия'],
                autori=raw_autori,
                naimenovanie_stati=raw_stati,
                podpisant=raw_podpisant,
                ssilki_na_novosti=raw_novosti,
                nomer_patenta=raw_patenta,
                nomer_udostovereniya=raw_udostovereniya,
                stupen=raw_stupen,
                data_vidachi=raw_data,
                awarded_prediction=verdict,
                awarded_probability=prob_yes
            )
            if custom_id is not None:
                new_kwargs['id'] = custom_id
            new_record = Record(**new_kwargs)
            db.session.add(new_record)

        db.session.commit()

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Ошибка при расчете и сохранении: {str(e)}"}), 500

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({
            "awarded_prediction": verdict,
            "awarded_probability": prob_yes,
            "record_id": new_record.id
        })

    return redirect(url_for("index"))


@app.route("/delete/<int:record_id>", methods=["POST"])
def delete_record(record_id):
    record = Record.query.get_or_404(record_id)
    try:
        db.session.delete(record)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Ошибка удаления: {str(e)}"}), 500
    return redirect(url_for("history"))


@app.route("/api/records/<int:record_id>", methods=["GET", "DELETE"])
def manage_record(record_id):
    record = db.session.get(Record, record_id)
    if not record:
        return jsonify({"error": f"Запись с ID {record_id} не найдена"}), 404

    if request.method == "GET":
        return jsonify(record.to_dict())

    if request.method == "DELETE":
        try:
            db.session.delete(record)
            db.session.commit()
            return jsonify({"message": f"Запись {record_id} успешно удалена", "id": record_id})
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": f"Ошибка при удалении: {str(e)}"}), 500


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=False)