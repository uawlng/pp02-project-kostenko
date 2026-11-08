import os
import sys
from datetime import datetime
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QIcon, QFont
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                               QComboBox, QScrollArea, QMessageBox, QStackedWidget,
                               QDialog, QInputDialog)
from database import Database
from discount import calculate_price_sad_ogorod 

class ProductCard(QDialog):
    def __init__(self, product, main_window):
        super().__init__()
        self.product = product
        self.main_window = main_window
        self.setWindowTitle("Карточка товара")
        self.resize(400, 550)
        self.setup_ui()

    def setup_ui(self):
        self.setStyleSheet("QDialog { background-color: #FFFFFF; }")
        
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)
        
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        pixmap = QPixmap(os.path.join("images", self.product[3])) if self.product[3] else QPixmap()
        if pixmap.isNull():
            self.image_label.setText("Фото отсутствует")
            self.image_label.setStyleSheet("border: 1px solid #ccc; padding: 40px; color: #888888; font-size: 14px;")
        else:
            self.image_label.setPixmap(pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        
        self.name_label = QLabel(f"{self.product[1]}")
        self.name_label.setAlignment(Qt.AlignCenter)
        self.name_label.setWordWrap(True)
        self.name_label.setStyleSheet("font-size: 22px; font-weight: bold; color: #2c3e50;")
        
        desc_label = QLabel(f"Производитель: {self.product[4]}\nКатегория: {self.product[6]}")
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setStyleSheet("color: #555555; font-size: 14px;")

        self.variant_combo = QComboBox()
        self.variant_combo.setStyleSheet("padding: 5px; font-size: 14px; border: 1px solid #ccc; color: #000000; background-color: #FFFFFF;")
        if "Лопатка" in self.product[1]:
            self.variant_combo.addItems(["Длина 25 см", "Длина 30 см", "Длина 35 см"])
        elif "Лейка" in self.product[1]:
            self.variant_combo.addItems(["Объём 3 л", "Объём 5 л", "Объём 8 л"])
        elif "Горшок" in self.product[1]:
            self.variant_combo.addItems(["Диаметр 12 см", "Диаметр 16 см", "Диаметр 20 см"])
        elif "Укрывной" in self.product[1]:
            self.variant_combo.addItems(["Плотность 17 г/м²", "Плотность 30 г/м²", "Плотность 60 г/м²"])
        else:
            self.variant_combo.addItem("Стандарт")

        lbl_variant = QLabel("Выберите вариант:")
        lbl_variant.setStyleSheet("font-weight: bold; color: #000000; font-size: 14px;")

        btn_add = QPushButton("Добавить в корзину")
        btn_add.setStyleSheet("background-color: #70B2AF; color: white; padding: 10px; border-radius: 5px; font-weight: bold; font-size: 14px; border: none;")
        btn_add.clicked.connect(self.add_to_cart_click)

        layout.addWidget(self.image_label)
        layout.addWidget(self.name_label)
        layout.addWidget(desc_label)
        layout.addStretch()
        layout.addWidget(lbl_variant)
        layout.addWidget(self.variant_combo)
        layout.addWidget(btn_add)

    def add_to_cart_click(self):
        qty, ok = QInputDialog.getInt(self, "Количество", "Сколько штук добавить?", 1, 1, 100)
        if ok:
            self.main_window.add_to_cart(self.product[0], float(self.product[2]), qty)
            self.accept()

def create_card(product, main_window):
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

    card.mousePressEvent = lambda event: ProductCard(product, main_window).exec()

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
        self.cart = []

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
        self.logout_button.setFixedSize(80, 30)
        self.logout_button.setStyleSheet("""
            QPushButton {
                background-color: #70B2AF; color: white; border: none; 
                border-radius: 4px; font-size: 13px; padding: 0px; margin: 0px;
            }
            QPushButton:hover { background-color: #5a9a97; }
        """)
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
        for cat in categories:
            self.filter_combo.addItem(cat)
        self.filter_combo.currentIndexChanged.connect(self.load_products)
        controls_layout.addWidget(self.filter_combo, 1)

        self.sort_combo = QComboBox()
        self.sort_combo.addItems([
            "Без сортировки",
            "Цена: по возрастанию",
            "Цена: по убыванию",
            "Количество: по возрастанию",
            "Количество: по убыванию",
        ])
        self.sort_combo.currentIndexChanged.connect(self.load_products)
        controls_layout.addWidget(self.sort_combo, 1)

        catalog_layout.addLayout(controls_layout)

        self.order_button = QPushButton("Оформить заказ")
        self.manager_button = QPushButton("Заказы (менеджер)")
        self.admin_button = QPushButton("Админ-панель")
        
        self.order_button.clicked.connect(self.confirm_order)
        self.manager_button.clicked.connect(self.open_orders_page)
        
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

        self.page_orders = QWidget()
        orders_layout = QVBoxLayout(self.page_orders)
        
        self.orders_scroll = QScrollArea()
        self.orders_scroll.setWidgetResizable(True)
        self.orders_scroll.setStyleSheet("border: none; background-color: #FFFFFF")
        self.orders_container = QWidget()
        self.orders_list_layout = QVBoxLayout(self.orders_container)
        self.orders_list_layout.setAlignment(Qt.AlignTop)
        self.orders_scroll.setWidget(self.orders_container)
        
        orders_layout.addWidget(self.orders_scroll)

        self.stacked_widget.addWidget(self.page_catalog)
        self.stacked_widget.addWidget(self.page_orders)
        
        main_layout.addWidget(self.stacked_widget)
        central.setLayout(main_layout)
        self.setCentralWidget(central)

    def open_orders_page(self):
        self.switch_page(1)
        self.load_orders()

    def load_orders(self):
        for i in reversed(range(self.orders_list_layout.count())):
            widget = self.orders_list_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        orders = self.db.get_all_orders()
        if not orders:
            lbl = QLabel("Заказов пока нет.")
            lbl.setStyleSheet("font-size: 18px; color: #555555; font-weight: bold;")
            self.orders_list_layout.addWidget(lbl)
            return

        for order in orders:
            order_id = order[0]
            fio = order[1].strip() if order[1] else "Неизвестный пользователь"
            items_count = order[2]
            total_sum = order[3] if order[3] else 0

            card = QWidget()
            card.setStyleSheet("border: 1px solid #000000; border-radius: 4px; background-color: #F4F9F9; margin-bottom: 5px;")
            layout = QHBoxLayout(card)
            
            lbl_info = QLabel(f"<b>Заказ №{order_id}</b> | {fio}")
            lbl_info.setStyleSheet("font-size: 14px; color: black; border: none;")
            
            lbl_details = QLabel(f"Позиций: {items_count} | Сумма: {total_sum:.2f} ₽")
            lbl_details.setStyleSheet("font-size: 14px; color: black; border: none; font-weight: bold;")
            
            layout.addWidget(lbl_info)
            layout.addStretch()
            layout.addWidget(lbl_details)
            
            self.orders_list_layout.addWidget(card)

    def switch_page(self, index):
        self.stacked_widget.setCurrentIndex(index)
        self.update_title_and_back_button(index)

    def go_back(self):
        current_index = self.stacked_widget.currentIndex()
        if current_index > 0:
            self.switch_page(current_index - 1)

    def update_title_and_back_button(self, index):
        titles = ["Сад и огород — Каталог", "Сад и огород — Заказы"]
        if 0 <= index < len(titles):
            self.title_label.setText(titles[index])
            self.setWindowTitle(titles[index])
        if index == 0:
            self.back_button.hide()
        else:
            self.back_button.show()

    def load_products(self):
        for i in reversed(range(self.list_layout.count())):
            widget = self.list_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        search = self.search_input.text()
        category = self.filter_combo.currentText()
        sort = self.sort_combo.currentText()

        self.products = self.db.get_products(search, category, sort)
        
        if not self.products:
            not_found_label = QLabel("Товары не найдены.")
            not_found_label.setStyleSheet("font-size: 18px; color: #555555; font-weight: bold; margin-top: 20px;")
            not_found_label.setAlignment(Qt.AlignCenter)
            self.list_layout.addWidget(not_found_label)
        else:
            for product in self.products:
                self.list_layout.addWidget(create_card(product, self))

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

    def add_to_cart(self, product_id, price, qty=1):
        self.cart.append({'product_id': product_id, 'quantity': qty, 'price': price})
        QMessageBox.information(self, "Корзина", f"Товар добавлен в корзину ({qty} шт.)!")

    def confirm_order(self):
        if not self.cart:
            QMessageBox.warning(self, "Внимание", "Ваша корзина пуста!")
            return

        test_user_id = 3
        success = self.db.create_order(test_user_id, self.cart)
        
        if success:
            QMessageBox.information(self, "Успех", f"Заказ на {len(self.cart)} позиций успешно оформлен!")
            self.cart.clear() 
            self.load_products() 
        else:
            QMessageBox.critical(self, "Ошибка", "Не удалось сохранить заказ в базу данных.")

    def delete_order(self, order_id):
        reply = QMessageBox.warning(
            self, "Предупреждение", "Вы уверены, что хотите удалить заказ?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            pass

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