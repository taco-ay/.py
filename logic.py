import sqlite3
from config import DATABASE

# Varsayılan veriler
skills = [(_,) for _ in ['Python', 'SQL', 'API', 'Discord']]
statuses = [(_,) for _ in [
    'Prototip Oluşturma',
    'Geliştirme Aşamasında',
    'Tamamlandı, kullanıma hazır',
    'Güncellendi',
    'Tamamlandı, ancak bakımı yapılmadı'
]]

class DB_Manager:
    def __init__(self, database):
        self.database = database

    def create_tables(self):
        conn = sqlite3.connect(self.database)
        with conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS projects (
                project_id INTEGER PRIMARY KEY,
                user_id INTEGER,
                project_name TEXT NOT NULL,
                description TEXT,
                url TEXT,
                status_id INTEGER,
                screenshot TEXT,
                FOREIGN KEY(status_id) REFERENCES status(status_id)
            )''')
            conn.execute('''CREATE TABLE IF NOT EXISTS skills (
                skill_id INTEGER PRIMARY KEY,
                skill_name TEXT
            )''')
            conn.execute('''CREATE TABLE IF NOT EXISTS project_skills (
                project_id INTEGER,
                skill_id INTEGER,
                FOREIGN KEY(project_id) REFERENCES projects(project_id),
                FOREIGN KEY(skill_id) REFERENCES skills(skill_id)
            )''')
            conn.execute('''CREATE TABLE IF NOT EXISTS status (
                status_id INTEGER PRIMARY KEY,
                status_name TEXT
            )''')
            conn.commit()

    def add_screenshot_column(self):
        """Tabloya ekran görüntüsü sütunu ekler (zaten varsa hata vermez)."""
        conn = sqlite3.connect(self.database)
        with conn:
            try:
                conn.execute("ALTER TABLE projects ADD COLUMN screenshot TEXT")
                print("✅ screenshot sütunu başarıyla eklendi!")
            except sqlite3.OperationalError:
                print("⚠️ screenshot sütunu zaten var, tekrar eklenmedi.")

    def __executemany(self, sql, data):
        conn = sqlite3.connect(self.database)
        with conn:
            conn.executemany(sql, data)
            conn.commit()

    def __select_data(self, sql, data=tuple()):
        conn = sqlite3.connect(self.database)
        with conn:
            cur = conn.cursor()
            cur.execute(sql, data)
            return cur.fetchall()

    def default_insert(self):
        sql = 'INSERT OR IGNORE INTO skills (skill_name) VALUES(?)'
        self.__executemany(sql, skills)
        sql = 'INSERT OR IGNORE INTO status (status_name) VALUES(?)'
        self.__executemany(sql, statuses)

    def insert_project(self, user_id, project_name, description, url, status_name, screenshot=None):
        status_id = self.get_status_id(status_name)
        if not status_id:
            raise ValueError("Geçersiz durum adı!")
        sql = '''INSERT INTO projects (user_id, project_name, description, url, status_id, screenshot)
                 VALUES (?, ?, ?, ?, ?, ?)'''
        self.__executemany(sql, [(user_id, project_name, description, url, status_id, screenshot)])

    def insert_skill(self, user_id, project_name, skill):
        res = self.__select_data(
            'SELECT project_id FROM projects WHERE project_name = ? AND user_id = ?',
            (project_name, user_id)
        )
        if not res:
            raise ValueError("Proje bulunamadı!")
        project_id = res[0][0]

        res = self.__select_data('SELECT skill_id FROM skills WHERE skill_name = ?', (skill,))
        if not res:
            raise ValueError("Beceri bulunamadı!")
        skill_id = res[0][0]

        sql = 'INSERT OR IGNORE INTO project_skills VALUES (?, ?)'
        self.__executemany(sql, [(project_id, skill_id)])

    def get_statuses(self):
        sql = 'SELECT status_name FROM status'
        return self.__select_data(sql)

    def get_status_id(self, status_name):
        sql = 'SELECT status_id FROM status WHERE status_name = ?'
        res = self.__select_data(sql, (status_name,))
        return res[0][0] if res else None

    def get_projects(self, user_id):
        sql = 'SELECT * FROM projects WHERE user_id = ?'
        return self.__select_data(sql, (user_id,))

    def get_project_id(self, project_name, user_id):
        sql = 'SELECT project_id FROM projects WHERE project_name = ? AND user_id = ?'
        return self.__select_data(sql, (project_name, user_id))[0][0]

    def get_skills(self):
        return self.__select_data('SELECT * FROM skills')

    def get_project_skills(self, project_name):
        sql = '''SELECT skill_name FROM projects 
                 JOIN project_skills ON projects.project_id = project_skills.project_id 
                 JOIN skills ON skills.skill_id = project_skills.skill_id 
                 WHERE project_name = ?'''
        res = self.__select_data(sql, (project_name,))
        return ', '.join([x[0] for x in res])

    def get_project_info(self, user_id, project_name):
        sql = '''SELECT project_name, description, url, status_name, screenshot FROM projects 
                 JOIN status ON status.status_id = projects.status_id 
                 WHERE project_name = ? AND user_id = ?'''
        return self.__select_data(sql, (project_name, user_id))

    def update_projects(self, column, value, project_id):
        if column not in ("project_name", "description", "url", "status_id", "screenshot"):
            raise ValueError("Geçersiz alan!")
        sql = f'UPDATE projects SET {column} = ? WHERE project_id = ?'
        self.__executemany(sql, [(value, project_id)])

    def delete_project(self, user_id, project_id):
        sql = 'DELETE FROM project_skills WHERE project_id = ?'
        self.__executemany(sql, [(project_id,)])
        sql = 'DELETE FROM projects WHERE user_id = ? AND project_id = ?'
        self.__executemany(sql, [(user_id, project_id)])


if __name__ == '__main__':
    manager = DB_Manager(DATABASE)
    manager.create_tables()
    manager.add_screenshot_column()  # Yeni sütunu ekle
    manager.default_insert() 
