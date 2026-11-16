from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QLineEdit,
                               QPushButton, QMessageBox)


class LoginWindow(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.setWindowTitle("Авторизация")
        self.resize(300, 250)

        layout = QVBoxLayout()

        self.label = QLabel("Логин:")
        self.login_input = QLineEdit()
        self.login_input.setPlaceholderText("Введите логин")

        self.btn_login = QPushButton("Войти")
        self.btn_login.clicked.connect(self.check_login)
        
        self.btn_guest = QPushButton("Войти как гость")
        self.btn_guest.setStyleSheet("background-color: #888888; color: white; border-radius: 4px; padding: 8px;")
        self.btn_guest.clicked.connect(self.login_as_guest)

        layout.addWidget(self.label)
        layout.addWidget(self.login_input)
        layout.addWidget(self.btn_login)
        layout.addWidget(self.btn_guest)
        
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
            with conn.cursor() as cursor:
                # ИСПРАВЛЕНО: используем role_id, так как в БД столбец называется так
                cursor.execute(
                    """SELECT user_id, role_id, last_name, first_name, middle_name
                       FROM users WHERE login = %s""",
                    (login,)
                )
                result = cursor.fetchone()
        finally:
            self.db.release_connection(conn)

        if not result:
            QMessageBox.critical(
                self, "Пользователь не найден",
                f"Логин «{login}» отсутствует в списке пользователей.\n"
                "Проверьте написание логина или войдите как гость."
            )
            return

        self.user_id = result[0]
        self.role_id = result[1] # ИСПРАВЛЕНО: здесь уже число, поэтому маппинг не нужен
        last_name, first_name, middle_name = result[2], result[3], result[4]

        if middle_name:
            self.full_name = f"{last_name} {first_name} {middle_name}"
        else:
            self.full_name = f"{last_name} {first_name}"

        self.open_main_window(self.role_id, self.full_name, self.user_id)

    def login_as_guest(self):
        self.open_main_window(0, "Гость", None)

    def open_main_window(self, role_id, full_name, user_id):
        from main import MainWindow
        self.main_window = MainWindow(
            role_id=role_id,
            full_name=full_name,
            db=self.db,
            user_id=user_id
        )
        self.main_window.show()
        self.close()