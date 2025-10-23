# server_api.py
import os
from flask import Flask, request, jsonify, send_from_directory
from db_models import get_engine, get_session, Student, ScheduleItem, Homework, Grade, Base
from werkzeug.utils import secure_filename
from datetime import datetime
import config

UPLOAD_DIR = getattr(config, 'UPLOAD_DIR', 'uploads')
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = Flask(__name__)
engine = get_engine()
Base.metadata.create_all(engine)

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    if not data:
        return jsonify({'error': 'Нет данных'}), 400
    name = data.get('full_name')
    program = data.get('program')
    year = data.get('year')
    password = data.get('password')
    if not all([name, program, year, password]):
        return jsonify({'error': 'Поля full_name, program, year, password обязательны'}), 400
    sess = get_session(engine)
    existing = sess.query(Student).filter(Student.full_name == name).first()
    if existing:
        return jsonify({'error': 'Пользователь с таким ФИО уже существует'}), 400
    s = Student(full_name=name, program=program, year=int(year))
    s.set_password(password)
    sess.add(s)
    sess.commit()
    return jsonify({'id': s.id, 'full_name': s.full_name})

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    if not data:
        return jsonify({'error': 'Нет данных'}), 400
    name = data.get('full_name')
    password = data.get('password')
    if not all([name, password]):
        return jsonify({'error': 'full_name и password обязательны'}), 400
    sess = get_session(engine)
    st = sess.query(Student).filter(Student.full_name == name).first()
    if not st or not st.check_password(password):
        return jsonify({'error': 'Неверные учетные данные'}), 401
    return jsonify({'id': st.id, 'full_name': st.full_name})

@app.route('/students/<int:student_id>/schedule', methods=['GET'])
def get_schedule(student_id):
    day = request.args.get('day')
    sess = get_session(engine)
    st = sess.get(Student, student_id)
    if not st:
        return jsonify({'error': 'student not found'}), 404
    query = sess.query(ScheduleItem).filter(ScheduleItem.program == st.program)
    if day and day != 'All':
        query = query.filter(ScheduleItem.week_day == day)
    rows = query.all()
    out = []
    for r in rows:
        out.append({'week_day': r.week_day, 'time': r.time, 'subject': r.subject, 'classroom': r.classroom, 'teacher': r.teacher})
    return jsonify(out)

@app.route('/students/<int:student_id>/homework', methods=['GET', 'POST'])
def student_homework(student_id):
    sess = get_session(engine)
    st = sess.get(Student, student_id)
    if not st:
        return jsonify({'error': 'student not found'}), 404
    if request.method == 'GET':
        rows = sess.query(Homework).filter((Homework.student_id == student_id) | (Homework.program == st.program)).all()
        return jsonify([{
            'id': h.id,
            'title': h.title,
            'description': h.description,
            'due_date': h.due_date,
            'pushed': h.pushed,
            'attachment': h.attachment
        } for h in rows])
    else:
        if request.content_type and 'multipart/form-data' in request.content_type:
            title = request.form.get('title')
            description = request.form.get('description')
            due_date = request.form.get('due_date')
            file = request.files.get('file')
        else:
            body = request.get_json(force=True)
            title = body.get('title')
            description = body.get('description')
            due_date = body.get('due_date')
            file = None

        if not title:
            return jsonify({'error': 'title required'}), 400

        attachment_filename = None
        if file:
            filename = secure_filename(file.filename)
            timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
            filename_saved = f"{timestamp}_{filename}"
            save_path = os.path.join(UPLOAD_DIR, filename_saved)
            file.save(save_path)
            attachment_filename = filename_saved

        hw = Homework(student_id=student_id, program=st.program, title=title, description=description, due_date=due_date, pushed=1, attachment=attachment_filename)
        sess.add(hw)
        sess.commit()
        return jsonify({'id': hw.id, 'title': hw.title, 'attachment': hw.attachment})

@app.route('/homework/<int:hw_id>/download', methods=['GET'])
def download_attachment(hw_id):
    sess = get_session(engine)
    hw = sess.get(Homework, hw_id)
    if not hw or not hw.attachment:
        return jsonify({'error': 'attachment not found'}), 404
    return send_from_directory(UPLOAD_DIR, hw.attachment, as_attachment=True)

@app.route('/students/<int:student_id>/grades', methods=['GET'])
def get_grades(student_id):
    sess = get_session(engine)
    st = sess.get(Student, student_id)
    if not st:
        return jsonify({'error': 'student not found'}), 404
    rows = sess.query(Grade).filter(Grade.student_id == student_id).all()
    return jsonify([{'id': g.id, 'subject': g.subject, 'grade': g.grade, 'comment': g.comment} for g in rows])

@app.route('/admin/push_homework', methods=['POST'])
def push_homework_all():
    data = request.json
    program = data.get('program')
    title = data.get('title')
    description = data.get('description')
    due_date = data.get('due_date')
    if not all([program, title]):
        return jsonify({'error': 'program and title required'}), 400
    sess = get_session(engine)
    hw = Homework(program=program, title=title, description=description, due_date=due_date, pushed=1)
    sess.add(hw)
    sess.commit()
    return jsonify({'ok': True, 'id': hw.id})

if __name__ == '__main__':
    print('Run API server: http://127.0.0.1:5000')
    app.run(debug=True, host='0.0.0.0', port=5000)
