# server_console.py
import csv
import json
from db_models import get_engine, get_session, Student, Homework, ScheduleItem, Grade, Base

engine = get_engine()
Base.metadata.create_all(engine)

HELP = '''Команды консоли:
  help                    - показать это сообщение
  list_students           - список студентов
  list_homeworks          - список домашних заданий
  list_schedule           - расписание
  add_student             - добавить студента (с паролем)
  add_homework            - добавить домашнее задание
  add_schedule            - добавить пару в расписание
  add_grade               - поставить оценку
  export <table> <file>   - экспорт (students|homeworks|grades|schedule) -> .csv или .json
  exit
'''

def list_students(sess):
    rows = sess.query(Student).all()
    for r in rows:
        print(r.id, r.full_name, r.program, 'year', r.year)

def list_homeworks(sess):
    rows = sess.query(Homework).all()
    for r in rows:
        print(r.id, 'st_id=' + str(r.student_id), r.program, r.title, r.due_date, 'pushed=' + str(r.pushed), 'attachment=' + str(r.attachment))

def list_schedule(sess):
    rows = sess.query(ScheduleItem).all()
    for r in rows:
        print(r.id, r.program, r.week_day, r.time, r.subject, r.classroom, r.teacher)

def add_student(sess):
    name = input('Full name: ')
    program = input('Program: ')
    year = input('Year: ')
    pwd = input('Password (will be hashed): ')
    s = Student(full_name=name, program=program, year=int(year))
    s.set_password(pwd)
    sess.add(s)
    sess.commit()
    print('Added', s.id)

def add_homework(sess):
    sid = input('Student id (or leave empty to create program-level): ')
    program = None
    student_id = None
    if sid.strip() == '':
        program = input('Program for homework: ')
    else:
        student_id = int(sid)
    title = input('Title: ')
    desc = input('Description: ')
    due = input('Due date: ')
    hw = Homework(student_id=student_id, program=program, title=title, description=desc, due_date=due, pushed=0)
    sess.add(hw)
    sess.commit()
    print('Homework added id=', hw.id)

def add_schedule(sess):
    program = input('Program: ')
    week_day = input('Week day (e.g. Monday): ')
    time = input('Time (e.g. 09:00-10:30): ')
    subject = input('Subject: ')
    classroom = input('Classroom: ')
    teacher = input('Teacher: ')
    si = ScheduleItem(program=program, week_day=week_day, time=time, subject=subject, classroom=classroom, teacher=teacher)
    sess.add(si)
    sess.commit()
    print('Schedule item added, id=', si.id)

def add_grade(sess):
    sid = int(input('Student id: '))
    subject = input('Subject: ')
    grade = input('Grade: ')
    comment = input('Comment: ')
    g = Grade(student_id=sid, subject=subject, grade=grade, comment=comment)
    sess.add(g)
    sess.commit()
    print('Grade added')

def export_table(sess, table, filename):
    if table == 'students':
        rows = sess.query(Student).all()
        keys = ['id','full_name','program','year','created_at']
        data = [[r.id,r.full_name,r.program,r.year,str(r.created_at)] for r in rows]
    elif table == 'homeworks':
        rows = sess.query(Homework).all()
        keys = ['id','student_id','program','title','description','due_date','pushed','attachment','created_at']
        data = [[r.id,r.student_id,r.program,r.title,r.description,r.due_date,r.pushed,r.attachment,str(r.created_at)] for r in rows]
    elif table == 'grades':
        rows = sess.query(Grade).all()
        keys = ['id','student_id','subject','grade','comment','created_at']
        data = [[r.id,r.student_id,r.subject,r.grade,r.comment,str(r.created_at)] for r in rows]
    elif table == 'schedule':
        rows = sess.query(ScheduleItem).all()
        keys = ['id','program','week_day','time','subject','classroom','teacher']
        data = [[r.id,r.program,r.week_day,r.time,r.subject,r.classroom,r.teacher] for r in rows]
    else:
        print('Unknown table')
        return
    if filename.endswith('.csv'):
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(keys)
            writer.writerows(data)
        print('Exported to', filename)
    elif filename.endswith('.json'):
        arr = [dict(zip(keys,row)) for row in data]
        with open(filename,'w',encoding='utf-8') as f:
            json.dump(arr,f,ensure_ascii=False,indent=2)
        print('Exported to', filename)
    else:
        print('Use .csv or .json')

def repl():
    sess = get_session(engine)
    print('Console manager. Type help')
    while True:
        cmd = input('> ').strip()
        if cmd == 'help':
            print(HELP)
        elif cmd == 'list_students':
            list_students(sess)
        elif cmd == 'list_homeworks':
            list_homeworks(sess)
        elif cmd == 'list_schedule':
            list_schedule(sess)
        elif cmd == 'add_student':
            add_student(sess)
        elif cmd == 'add_homework':
            add_homework(sess)
        elif cmd == 'add_schedule':
            add_schedule(sess)
        elif cmd == 'add_grade':
            add_grade(sess)
        elif cmd.startswith('export'):
            parts = cmd.split()
            if len(parts) >= 3:
                export_table(sess, parts[1], parts[2])
            else:
                print('Usage: export <table> <file.csv|file.json>')
        elif cmd == 'exit':
            break
        else:
            print('Unknown command. Type help')

if __name__ == '__main__':
    repl()
