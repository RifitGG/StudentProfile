# db_init.py
from db_models import Base, get_engine, get_session, Student, ScheduleItem, Homework, Grade

def seed():
    engine = get_engine()
    print('Создаем таблицы (если нет)...')
    Base.metadata.create_all(engine)

    sess = get_session(engine)

    if sess.query(Student).count() > 0:
        print('Данные уже есть в базе — seed пропущен. Если хотите пересоздать — удалите таблицы вручную.')
        return

    s1 = Student(full_name='Иванов Иван Иванович', program='ИСиП', year=2)
    s1.set_password('password1')
    s2 = Student(full_name='Петрова Мария Сергеевна', program='Банковское дело', year=3)
    s2.set_password('password2')
    sess.add_all([s1, s2])
    sess.commit()

    sched = [
        ScheduleItem(program='ИСиП', week_day='Monday', time='09:00-10:30', subject='Программирование', classroom='A101', teacher='И. Сидоров'),
        ScheduleItem(program='ИСиП', week_day='Monday', time='10:45-12:15', subject='Математика', classroom='A102', teacher='П. Иванов'),
        ScheduleItem(program='ИСиП', week_day='Tuesday', time='09:00-10:30', subject='ОС', classroom='A103', teacher='О. Петров'),
    ]
    sess.add_all(sched)

    hw1 = Homework(student=s1, program='ИСиП', title='Лабораторная 1', description='Реализовать калькулятор', due_date='2025-10-10')
    hw2 = Homework(student=s2, program='Банковское дело', title='Реферат по банковскими операциями', description='10 стр.', due_date='2025-10-12')
    sess.add_all([hw1, hw2])

    g1 = Grade(student=s1, subject='Программирование', grade='A', comment='Отлично')
    g2 = Grade(student=s2, subject='Экономика', grade='B+', comment='Хорошо')
    sess.add_all([g1, g2])

    sess.commit()
    print('Seed finished. DB ready.')
    print('Sample student passwords: Иванов -> password1, Петрова -> password2')

if __name__ == '__main__':
    seed()
