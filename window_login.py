from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QLineEdit, 
                               QPushButton, QMessageBox)

class LoginWindow(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.setWindowTitle("Авторизация")
        self.resize(300, 200)
        
        layout = QVBoxLayout()
        
        self.label = QLabel("Логин:")
        self.login_input = QLineEdit()
        self.login_input.setPlaceholderText("Введите логин")
        
        self.btn_login = QPushButton("Войти")
        self.btn_login.clicked.connect(self.check_login)
        
        layout.addWidget(self.label)
        layout.addWidget(self.login_input)
        layout.addWidget(self.btn_login)
        
        self.setLayout(layout)

    def check_login(self):
        login = self.login_input.text().strip()
        
        if not login:
            QMessageBox.critical(self, "Ошибка", "Введите логин!")
            return
            
        conn = self.db.get_connection()
        if conn is None:
            QMessageBox.critical(self, "Ошибка", "Нет подключения к БД!")
            return
            
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id, role_id, last_name, first_name, middle_name FROM users WHERE login = %s", (login,))
            result = cursor.fetchone()
            cursor.close()
            self.db.release_connection(conn)
            
            if not result:
                QMessageBox.critical(self, "Ошибка", "Пользователь не найден!")
                return
            
            self.user_id = result[0]
            self.role_id = result[1]
            last_name = result[2]
            first_name = result[3]
            middle_name = result[4]
            
            if middle_name:
                self.full_name = f"{last_name} {first_name} {middle_name}"
            else:
                self.full_name = f"{last_name} {first_name}"
            
            from main import MainWindow
            self.main_window = MainWindow(role_id=self.role_id, full_name=self.full_name, db=self.db)
            self.main_window.show()
            self.close()
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка БД", str(e))