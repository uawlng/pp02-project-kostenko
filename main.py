import os
import sys
import shutil
import uuid
from decimal import Decimal
from datetime import datetime
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QIcon, QFont
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                               QComboBox, QScrollArea, QMessageBox, QStackedWidget,
                               QDialog, QInputDialog, QFileDialog, QTableWidget, 
                               QTableWidgetItem, QHeaderView)
from database import Database
from discount import calculate_price_sad_ogorod 

class ProductCard(QDialog):
    def __init__(self, product, main_window):
        super().__init__()
        self.product = product
        self.main_window = main_window
        self.setWindowTitle("Карточка товара")
        self.resize(400, 650)
        self.setup_ui()

    def setup_ui(self):
        self.setStyleSheet("QDialog { background-color: #FFFFFF; }")
        
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)
        
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.update_image_label(self.product[3])
        
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

        btn_load_img = QPushButton("Загрузить изображение")
        btn_load_img.setStyleSheet("background-color: #555555; color: white; padding: 8px; border-radius: 5px; font-weight: bold;")
        btn_load_img.clicked.connect(self.load_image)

        btn_add = QPushButton("Добавить в корзину")
        btn_add.setStyleSheet("background-color: #70B2AF; color: white; padding: 10px; border-radius: 5px; font-weight: bold; font-size: 14px; border: none;")
        btn_add.clicked.connect(self.add_to_cart_click)

        layout.addWidget(self.image_label)
        layout.addWidget(self.name_label)
        layout.addWidget(desc_label)
        layout.addWidget(btn_load_img)
        layout.addStretch()
        layout.addWidget(lbl_variant)
        layout.addWidget(self.variant_combo)
        layout.addWidget(btn_add)

    def update_image_label(self, image_name):
        pixmap = QPixmap(os.path.join("images", image_name)) if image_name else QPixmap()
        if pixmap.isNull():
            self.image_label.setText("Фото отсутствует")
            self.image_label.setStyleSheet("border: 1px solid #ccc; padding: 40px; color: #888888; font-size: 14px;")
        else:
            self.image_label.setPixmap(pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def load_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выберите изображение", "", "Images (*.png *.jpg *.jpeg)"
        )
        
        if file_path:
            try:
                ext = os.path.splitext(file_path)[1]
                new_filename = f"{uuid.uuid4().hex}{ext}"
                dest_path = os.path.join("images", new_filename)

                shutil.copy(file_path, dest_path)

                conn = self.main_window.db.get_connection()
                if conn:
                    with conn.cursor() as cursor:
                        cursor.execute(
                            "UPDATE products SET image = %s WHERE product_id = %s",
                            (new_filename, self.product[0])
                        )
                    conn.commit()
                    self.main_window.db.release_connection(conn)

                self.update_image_label(new_filename)
                
                p_list = list(self.product)
                p_list[3] = new_filename
                self.product = tuple(p_list)

                QMessageBox.information(self, "Успех", "Изображение успешно загружено!")

            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить изображение:\n{e}")

    def add_to_cart_click(self):
        qty, ok = QInputDialog.getInt(self, "Количество", "Сколько штук добавить?", 1, 1, 100)
        if ok:
            variant_id = self.variant_combo.currentIndex() + 4 
            variant_name = self.variant_combo.currentText()
            display_name = f"{self.product[1]} ({variant_name})"
            self.main_window.add_to_cart(self.product[0], variant_id, display_name, qty, float(self.product[2]))
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
    def __init__(self, role_id=None, full_name=None, db=None, user_id=None):
        super().__init__()
        self.role_id = role_id
        self.full_name = full_name
        self.db = db if db is not None else Database()
        self.user_id = user_id if user_id else 3

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

        self.order_button = QPushButton("Перейти в корзину")
        self.manager_button = QPushButton("Заказы (менеджер)")
        self.admin_button = QPushButton("Админ-панель")
        
        self.order_button.clicked.connect(self.open_cart_page)
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

        self.page_cart = QWidget()
        cart_layout = QVBoxLayout(self.page_cart)
        
        self.cart_table = QTableWidget()
        self.cart_table.setColumnCount(5)
        self.cart_table.setHorizontalHeaderLabels(["Наименование", "Количество", "Цена", "Сумма", "ID"])
        self.cart_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.cart_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.cart_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.cart_table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        self.cart_table.setStyleSheet("""
            QTableWidget {
                background-color: #2b2b2b;
                color: #ffffff;
                gridline-color: #555555;
                font-size: 14px;
            }
            QHeaderView::section {
                background-color: #3c3f41;
                color: #ffffff;
                padding: 5px;
                border: 1px solid #555555;
                font-weight: bold;
            }
            QTableWidget::item {
                padding: 5px;
            }
        """)
        cart_layout.addWidget(self.cart_table)
        
        self.total_label = QLabel("Итого: 0.00 ₽")
        self.total_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50; margin-top: 10px;")
        self.total_label.setAlignment(Qt.AlignRight)
        cart_layout.addWidget(self.total_label)
        
        btn_remove = QPushButton("Удалить выбранный товар")
        btn_remove.clicked.connect(self.remove_from_cart)
        cart_layout.addWidget(btn_remove)

        btn_change_qty = QPushButton("Изменить количество")
        btn_change_qty.clicked.connect(self.change_quantity)
        cart_layout.addWidget(btn_change_qty)

        status_layout = QHBoxLayout()
        lbl_status = QLabel("<b>Статус заказа:</b>")
        lbl_status.setStyleSheet("font-size: 16px; color: #2c3e50;")
        status_layout.addWidget(lbl_status)
        
        self.status_combo = QComboBox()
        self.status_combo.addItems(["Новый", "В обработке", "Готов к выдаче"])
        self.status_combo.setStyleSheet("padding: 5px; font-size: 14px; border: 1px solid #ccc; background-color: #FFF; color: #000;")
        self.status_combo.setFixedWidth(200)
        status_layout.addWidget(self.status_combo)
        
        status_layout.addStretch()
        cart_layout.addLayout(status_layout)
        
        cart_layout.addSpacing(10)
        
        btn_checkout = QPushButton("Оформить заказ")
        btn_checkout.clicked.connect(self.confirm_order)
        cart_layout.addWidget(btn_checkout)

        self.stacked_widget.addWidget(self.page_catalog)
        self.stacked_widget.addWidget(self.page_orders)
        self.stacked_widget.addWidget(self.page_cart)
        
        main_layout.addWidget(self.stacked_widget)
        central.setLayout(main_layout)
        self.setCentralWidget(central)

    def open_cart_page(self):
        self.switch_page(2)
        self.update_total()

    def add_to_cart(self, product_id, variant_id, name, quantity, price):
        row = self.cart_table.rowCount()
        self.cart_table.insertRow(row)
        
        total = quantity * price
        self.cart_table.setItem(row, 0, QTableWidgetItem(name))
        self.cart_table.setItem(row, 1, QTableWidgetItem(str(quantity)))
        self.cart_table.setItem(row, 2, QTableWidgetItem(f"{price:.2f}"))
        self.cart_table.setItem(row, 3, QTableWidgetItem(f"{total:.2f}"))
        
        id_item = QTableWidgetItem(str(product_id))
        id_item.setData(Qt.UserRole, variant_id)
        self.cart_table.setItem(row, 4, id_item)
        
        self.update_total()

    def change_quantity(self):
        row = self.cart_table.currentRow()
        if row >= 0:
            try:
                new_qty, ok = QInputDialog.getInt(self, "Количество", "Введите новое количество:", 1, 1, 100)
                if ok:
                    price = float(self.cart_table.item(row, 2).text())
                    self.cart_table.setItem(row, 1, QTableWidgetItem(str(new_qty)))
                    self.cart_table.setItem(row, 3, QTableWidgetItem(f"{new_qty * price:.2f}"))
                    self.update_total()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка при изменении: {e}")

    def remove_from_cart(self):
        row = self.cart_table.currentRow()
        if row >= 0:
            self.cart_table.removeRow(row)
            self.update_total()
            QMessageBox.information(self, "Корзина", "Товар удален из корзины!")

    def update_total(self):
        total = Decimal('0.00')
        for row in range(self.cart_table.rowCount()):
            item = self.cart_table.item(row, 3)
            if item:
                total += Decimal(item.text())
        self.total_label.setText(f"Итого: {total:.2f} ₽")

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
            status_name = order[4] if len(order) > 4 else "Неизвестно"

            card = QWidget()
            card.setStyleSheet("border: 1px solid #000000; border-radius: 4px; background-color: #F4F9F9; margin-bottom: 5px;")
            layout = QHBoxLayout(card)
            
            lbl_info = QLabel(f"<b>Заказ №{order_id}</b> | {fio}")
            lbl_info.setStyleSheet("font-size: 14px; color: black; border: none;")
            
            lbl_details = QLabel(f"Статус: <b>{status_name}</b> | Позиций: {items_count} | Сумма: {total_sum:.2f} ₽")
            lbl_details.setStyleSheet("font-size: 14px; color: black; border: none;")
            
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
        titles = ["Сад и огород — Каталог", "Сад и огород — Заказы", "Сад и огород — Корзина"]
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
            self.order_button.show()
        elif self.role_id == 2:
            self.manager_button.show()
        elif self.role_id == 3:
            self.order_button.show()

    def confirm_order(self):
        if self.cart_table.rowCount() == 0:
            QMessageBox.warning(self, "Внимание", "Ваша корзина пуста!")
            return

        items_to_save = []
        for row in range(self.cart_table.rowCount()):
            item_id = self.cart_table.item(row, 4)
            if not item_id:
                continue

            product_id = int(item_id.text())
            variant_id = item_id.data(Qt.UserRole) 
            quantity = int(self.cart_table.item(row, 1).text())
            price = float(self.cart_table.item(row, 2).text())
            
            items_to_save.append({
                'product_id': product_id,
                'variant_id': variant_id,
                'quantity': quantity,
                'price': price
            })

        selected_status = self.status_combo.currentText()
        
        order_id, error_msg = self.db.create_order_safe(self.user_id, selected_status, items_to_save)
        
        if order_id:
            QMessageBox.information(self, "Успех", f"Заказ №{order_id} успешно оформлен!\nСтатус: {selected_status}")
            self.cart_table.setRowCount(0)
            self.update_total()
            self.load_products()
            self.switch_page(0)
        else:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить заказ:\n{error_msg}\n\nВсе изменения отменены.")

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