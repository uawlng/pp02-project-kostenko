import os
import sys
from datetime import datetime
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QIcon, QFont
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                               QComboBox, QScrollArea, QMessageBox, QStackedWidget)
from database import Database
from discount import calculate_price_sad_ogorod 

def create_card(product):
    card = QWidget()
    card.setObjectName("productCard")

    total_quantity = product[5] if len(product) > 5 else 1
    base_price = float(product[2]) if product[2] else 0.0
    
    final_price, discount_amount = calculate_price_sad_ogorod(product[0], base_price)
    if final_price is None:
        final_price = base_price
        discount_amount = 0.0

    if total_quantity <= 3:
        bg_color, border_color = "#FF8080", "#FF8080"
    else:
        bg_color, border_color = "#FFFFFF", "#000000"

    card.setStyleSheet(f"#productCard {{ border: 1px solid {border_color}; border-radius: 4px; background-color: {bg_color}; }} #productCard QLabel {{ background-color: transparent; font-family: Calibri; }}")

    main_layout = QHBoxLayout(card)
    main_layout.setContentsMargins(10, 10, 10, 10)
    main_layout.setSpacing(15)

    image_label = QLabel()
    image_label.setFixedSize(100, 100)
    image_label.setAlignment(Qt.AlignCenter)
    image_label.setStyleSheet("border: 1px solid #000000; background-color: #FFFFFF;")

    name = product[1] if product[1] else "Наименование"
    file_name = product[3]
    manufacturer = product[4] if product[4] else "Неизвестный производитель"
    category_name = product[6] if len(product) > 6 else "Без категории"

    placeholder_path = os.path.join("resources", "picture.png")
    image_path = os.path.join("images", file_name) if file_name else placeholder_path

    pixmap = QPixmap(image_path)
    if pixmap.isNull():
        pixmap = QPixmap(placeholder_path)

    if pixmap.isNull():
        image_label.setText("IMG")
    else:
        image_label.setPixmap(pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation))
    main_layout.addWidget(image_label)

    text_layout = QVBoxLayout()
    text_layout.setSpacing(5)
    text_style = "font-size: 14px; border: none; color: #000000; font-family: Calibri;"

    title = QLabel(f"<b>{manufacturer} | {name}</b>")
    title.setStyleSheet(text_style)
    
    category_label = QLabel(f"Категория: {category_name}")
    category_label.setStyleSheet(text_style)

    quantity_text = f"Количество: {total_quantity} шт." if total_quantity > 0 else "Нет в наличии"
    quantity_label = QLabel(quantity_text)
    if total_quantity == 0:
        quantity_label.setStyleSheet("font-size: 14px; border: none; color: #d9534f; font-weight: bold; font-family: Calibri;")
    else:
        quantity_label.setStyleSheet(text_style)

    text_layout.addWidget(title)
    text_layout.addWidget(category_label)
    text_layout.addWidget(quantity_label)
    text_layout.addStretch()
    main_layout.addLayout(text_layout, 1)

    price_layout = QVBoxLayout()
    price_layout.setAlignment(Qt.AlignTop | Qt.AlignRight)
    
    if discount_amount > 0:
        old_price_label = QLabel(f"<s>{base_price:.2f} ₽</s>")
        old_price_label.setAlignment(Qt.AlignRight)
        old_price_label.setStyleSheet("color: red; font-size: 14px; border: none; font-family: Calibri;")
        price_layout.addWidget(old_price_label)
    
    new_price_label = QLabel(f"<b>{final_price:.2f} ₽</b>")
    new_price_label.setAlignment(Qt.AlignRight)
    new_price_label.setStyleSheet("color: black; font-weight: bold; font-size: 16px; border: none; font-family: Calibri;")

    price_layout.addWidget(new_price_label)
    main_layout.addLayout(price_layout)
    
    return card


class MainWindow(QMainWindow):
    def __init__(self, role_id=None, full_name=None, db=None):
        super().__init__()
        self.role_id = role_id
        self.full_name = full_name
        self.db = db if db is not None else Database()

        self.setWindowTitle("Сад и огород — Каталог")
        self.resize(900, 700)
        self.setWindowIcon(QIcon("resources/icon.ico"))

        font = QFont("Calibri", 10)
        self.setFont(font)

        self.setStyleSheet("""
            QMainWindow { background-color: #FFFFFF; font-family: Calibri; }
            QLabel { font-family: Calibri; }
            #HeaderLabel { font-size: 28px; font-weight: bold; color: #2c3e50; margin: 20px; }
            QPushButton { padding: 10px; margin: 5px; font-size: 14px; background-color: #70B2AF; color: white; border: none; border-radius: 5px; font-family: Calibri; }
            QPushButton:hover { background-color: #5a9a97; }
            QComboBox, QLineEdit { padding: 5px; font-size: 14px; font-family: Calibri; border: 1px solid #ccc; border-radius: 3px; }
        """)

        self.setup_ui()
        self.setup_role_interface()
        self.load_products()

    def setup_ui(self):
        central = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

        header_widget = QWidget()
        header_widget.setStyleSheet("background-color: #D2F6E7; border-radius: 5px;")
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(10, 10, 10, 10)

        logo_header = QLabel()
        pixmap_logo = QPixmap("resources/logo.png")
        if not pixmap_logo.isNull():
            logo_header.setPixmap(pixmap_logo.scaledToHeight(50, Qt.SmoothTransformation))
        header_layout.addWidget(logo_header)

        header_layout.addStretch()

        name_text = f"ФИО: {self.full_name}" if self.full_name else "ФИО: —"
        name_label = QLabel(name_text)
        name_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #2c3e50; background-color: transparent;")
        header_layout.addWidget(name_label)

        self.logout_button = QPushButton("Выход")
        self.logout_button.clicked.connect(self.logout)
        header_layout.addWidget(self.logout_button)
        main_layout.addWidget(header_widget)

        nav_layout = QHBoxLayout()
        self.back_button = QPushButton("Назад")
        self.back_button.clicked.connect(self.go_back)
        self.back_button.hide()
        nav_layout.addWidget(self.back_button)
        
        self.title_label = QLabel("Сад и огород — Каталог")
        self.title_label.setObjectName("HeaderLabel")
        self.title_label.setAlignment(Qt.AlignCenter)
        nav_layout.addWidget(self.title_label, 1)
        main_layout.addLayout(nav_layout)

        self.stacked_widget = QStackedWidget()

        self.page_catalog = QWidget()
        catalog_layout = QVBoxLayout(self.page_catalog)

        controls_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск...")
        self.search_input.textChanged.connect(self.load_products)
        controls_layout.addWidget(self.search_input, 2)

        self.filter_combo = QComboBox()
        self.filter_combo.addItem("Все категории")
        categories = self.db.get_categories()
        for cat in categories: self.filter_combo.addItem(cat)
        self.filter_combo.currentIndexChanged.connect(self.load_products)
        controls_layout.addWidget(self.filter_combo, 1)

        catalog_layout.addLayout(controls_layout)

        self.order_button = QPushButton("Оформить заказ")
        self.manager_button = QPushButton("Заказы (менеджер)")
        self.admin_button = QPushButton("Админ-панель")
        
        self.order_button.clicked.connect(self.confirm_order)
        self.manager_button.clicked.connect(lambda: self.switch_page(2))
        
        self.test_delete_btn = QPushButton("Удалить заказ (тест)")
        self.test_delete_btn.clicked.connect(lambda: self.delete_order(1))
        
        catalog_layout.addWidget(self.order_button)
        catalog_layout.addWidget(self.manager_button)
        catalog_layout.addWidget(self.admin_button)
        catalog_layout.addWidget(self.test_delete_btn)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("border: none; background-color: #FFFFFF")
        self.container = QWidget()
        self.list_layout = QVBoxLayout(self.container)
        self.list_layout.setAlignment(Qt.AlignTop)
        self.scroll.setWidget(self.container)
        catalog_layout.addWidget(self.scroll)

        self.page_product = QWidget()
        product_layout = QVBoxLayout(self.page_product)
        product_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        
        form_title = QLabel("Добавление нового товара")
        form_title.setStyleSheet("font-size: 20px; font-weight: bold; margin-bottom: 20px;")
        product_layout.addWidget(form_title)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Введите наименование товара")
        product_layout.addWidget(self.name_input)

        self.price_input = QLineEdit()
        self.price_input.setPlaceholderText("Введите цену (например, 1500)")
        product_layout.addWidget(self.price_input)

        self.quantity_input = QLineEdit()
        self.quantity_input.setPlaceholderText("Введите количество (например, 10)")
        product_layout.addWidget(self.quantity_input)

        self.date_input = QLineEdit()
        self.date_input.setPlaceholderText("Дата заказа (ДД.ММ.ГГГГ)")
        product_layout.addWidget(self.date_input)

        self.save_product_btn = QPushButton("Сохранить товар")
        self.save_product_btn.clicked.connect(self.add_product)
        product_layout.addWidget(self.save_product_btn)
        
        product_layout.addStretch()

        self.page_orders = QWidget()
        orders_layout = QVBoxLayout(self.page_orders)
        orders_layout.addWidget(QLabel("Здесь будет список заказов", alignment=Qt.AlignCenter))

        self.stacked_widget.addWidget(self.page_catalog)
        self.stacked_widget.addWidget(self.page_product)
        self.stacked_widget.addWidget(self.page_orders)
        
        main_layout.addWidget(self.stacked_widget)
        central.setLayout(main_layout)
        self.setCentralWidget(central)

    def switch_page(self, index):
        self.stacked_widget.setCurrentIndex(index)
        self.update_title_and_back_button(index)

    def go_back(self):
        current_index = self.stacked_widget.currentIndex()
        if current_index > 0:
            self.switch_page(current_index - 1)

    def update_title_and_back_button(self, index):
        titles = ["Сад и огород — Каталог", "Сад и огород — Карточка товара", "Сад и огород — Заказы"]
        if 0 <= index < len(titles):
            self.title_label.setText(titles[index])
            self.setWindowTitle(titles[index])
        if index == 0: self.back_button.hide()
        else: self.back_button.show()

    def load_products(self):
        for i in reversed(range(self.list_layout.count())):
            widget = self.list_layout.itemAt(i).widget()
            if widget: widget.setParent(None)

        search = self.search_input.text()
        category = self.filter_combo.currentText()

        self.products = self.db.get_products(search, category, "")
        if not self.products:
            self.list_layout.addWidget(QLabel("Товары не найдены."))
        else:
            for product in self.products:
                self.list_layout.addWidget(create_card(product))

    def setup_role_interface(self):
        self.order_button.hide()
        self.manager_button.hide()
        self.admin_button.hide()
        self.test_delete_btn.hide()

        if self.role_id == 1:
            self.admin_button.show()
            self.manager_button.show()
            self.test_delete_btn.show()
        elif self.role_id == 2:
            self.manager_button.show()
        elif self.role_id == 3:
            self.order_button.show()

    def delete_order(self, order_id):
        reply = QMessageBox.warning(
            self, "Предупреждение", "Вы уверены, что хотите удалить заказ?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            pass

    def confirm_order(self):
        QMessageBox.information(self, "Информация", "Заказ успешно оформлен!")

    def add_to_cart(self):
        qty_text = self.quantity_input.text().strip()
        if not qty_text:
            QMessageBox.critical(self, "Ошибка", "Введите количество")
            return
            
        if not qty_text.isdigit():
            QMessageBox.critical(self, "Ошибка", "Введите число")
            return
            
        quantity = int(qty_text)
        if quantity <= 0:
            QMessageBox.critical(self, "Ошибка", "Количество должно быть положительным")
            return

    def add_product(self):
        price_text = self.price_input.text().strip()
        if not price_text:
            QMessageBox.critical(self, "Ошибка", "Введите цену")
            return
            
        try:
            price = float(price_text)
        except ValueError:
            QMessageBox.critical(self, "Ошибка", "Введите число")
            return
            
        if price <= 0:
            QMessageBox.critical(self, "Ошибка", "Цена должна быть положительной")
            return

        name = self.name_input.text().strip()
        if not name:
            QMessageBox.critical(self, "Ошибка", "Введите наименование")
            return
            
        date_str = self.date_input.text().strip()
        if not date_str:
            QMessageBox.critical(self, "Ошибка", "Введите дату")
            return
            
        try:
            date = datetime.strptime(date_str, "%d.%m.%Y")
        except ValueError:
            QMessageBox.critical(self, "Ошибка", "Введите дату в формате ДД.ММ.ГГГГ")
            return

        QMessageBox.information(self, "Успех", "Товар успешно добавлен!")
        self.name_input.clear()
        self.price_input.clear()
        self.quantity_input.clear()
        self.date_input.clear()

    def logout(self):
        reply = QMessageBox.question(self, "Выход", "Вы уверены, что хотите выйти?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            from window_login import LoginWindow
            self.login_window = LoginWindow(self.db)
            self.login_window.show()
            self.close()

    def closeEvent(self, event):
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    db = Database()
    from window_login import LoginWindow
    login_window = LoginWindow(db)
    login_window.show()
    exit_code = app.exec()
    db.close_all()
    sys.exit(exit_code)