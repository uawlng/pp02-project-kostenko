import psycopg
from psycopg_pool import ConnectionPool


class Database:
    def __init__(self):
        self.connection_pool = None
        try:
            self.connection_pool = ConnectionPool(
                conninfo="host=localhost port=5432 dbname=sad_i_ogorod user=postgres password=123",
                min_size=1,
                max_size=5,
                open=True
            )
            print("Пул соединений создан")
        except psycopg.Error as e:
            print(f"Ошибка БД: {e}")
            self.connection_pool = None

    def get_connection(self):
        if self.connection_pool is not None:
            return self.connection_pool.getconn()
        return None

    def release_connection(self, conn):
        if self.connection_pool is not None and conn is not None:
            self.connection_pool.putconn(conn)

    def close_all(self):
        if self.connection_pool is not None:
            self.connection_pool.close()
            print("Пул закрыт")

    def get_variants(self):
        conn = self.get_connection()
        if conn is None:
            return []
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='variants'
                """)
                columns = [row[0] for row in cursor.fetchall()]
                name_col = 'variant_name'
                if 'variant_name' not in columns:
                    if 'name' in columns:
                        name_col = 'name'
                    elif 'title' in columns:
                        name_col = 'title'
                    else:
                        name_col = columns[1] if len(columns) > 1 else columns[0]
                query = f"SELECT variant_id, {name_col} FROM variants ORDER BY variant_id"
                cursor.execute(query)
                return cursor.fetchall()
        except psycopg.Error as e:
            print(f"Ошибка запроса вариантов: {e}")
            return []
        finally:
            self.release_connection(conn)

    def get_variants_for_product(self, product_id):
        conn = self.get_connection()
        if conn is None:
            return []
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='variants'
                """)
                columns = [row[0] for row in cursor.fetchall()]
                name_col = 'variant_name'
                if 'variant_name' not in columns:
                    if 'name' in columns:
                        name_col = 'name'
                    elif 'title' in columns:
                        name_col = 'title'
                    else:
                        name_col = columns[1] if len(columns) > 1 else columns[0]
                query = f"""
                    SELECT DISTINCT v.variant_id, v.{name_col}
                    FROM variants v
                    JOIN stock_items si ON si.variant_id = v.variant_id
                    WHERE si.product_id = %s
                    ORDER BY v.variant_id
                """
                cursor.execute(query, (product_id,))
                return cursor.fetchall()
        except psycopg.Error as e:
            print(f"Ошибка запроса вариантов товара: {e}")
            return []
        finally:
            self.release_connection(conn)

    def get_stock_quantity(self, product_id, variant_id):
        conn = self.get_connection()
        if conn is None:
            return 0
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT quantity FROM stock_items WHERE product_id = %s AND variant_id = %s",
                    (product_id, variant_id)
                )
                row = cursor.fetchone()
                return row[0] if row else 0
        except psycopg.Error as e:
            print(f"Ошибка запроса остатка: {e}")
            return 0
        finally:
            self.release_connection(conn)

    def get_order_date(self, order_id):
        conn = self.get_connection()
        if conn is None:
            return ""
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT order_date FROM orders WHERE order_id = %s", (order_id,))
                row = cursor.fetchone()
                return row[0].strftime("%d.%m.%Y %H:%M") if row else ""
        except psycopg.Error as e:
            print(f"Ошибка запроса даты заказа: {e}")
            return ""
        finally:
            self.release_connection(conn)

    def get_categories(self):
        conn = self.get_connection()
        if conn is None:
            return []
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT name FROM categories ORDER BY name")
                return [row[0] for row in cursor.fetchall()]
        except psycopg.Error as e:
            print(f"Ошибка запроса категорий: {e}")
            return []
        finally:
            self.release_connection(conn)

    def get_products(self, search="", category="Все категории", sort_order="Без сортировки"):
        conn = self.get_connection()
        if conn is None:
            return []
        try:
            with conn.cursor() as cursor:
                search_pattern = f"%{search}%"
                order_map = {
                    "Цена: по возрастанию": "p.price ASC",
                    "Цена: по убыванию": "p.price DESC",
                }
                order_clause = ""
                if sort_order in order_map:
                    order_clause = f"ORDER BY {order_map[sort_order]}"
                query = f"""
                    SELECT p.product_id, p.name, p.price, p.image,
                           COALESCE(m.name, 'Неизвестно') AS manufacturer,
                           COALESCE(SUM(si.quantity), 0) AS total_quantity,
                           COALESCE(c.name, 'Без категории') AS category_name,
                           COALESCE(mat.name, '') AS material,
                           'Описание отсутствует' AS description
                    FROM products p
                    LEFT JOIN manufacturers m ON p.manufacturer_id = m.manufacturer_id
                    LEFT JOIN categories c ON p.category_id = c.category_id
                    LEFT JOIN materials mat ON p.material_id = mat.material_id
                    LEFT JOIN stock_items si ON p.product_id = si.product_id
                    WHERE p.name ILIKE %s
                    AND (c.name = %s OR %s = 'Все категории')
                    GROUP BY p.product_id, p.name, p.price, p.image,
                             m.name, c.name, mat.name
                    {order_clause}
                """
                cursor.execute(query, (search_pattern, category, category))
                return cursor.fetchall()
        except psycopg.Error as e:
            print(f"Ошибка запроса: {e}")
            return []
        finally:
            self.release_connection(conn)

    def search_products_for_order(self, search_text):
        conn = self.get_connection()
        if conn is None:
            return []
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT p.product_id, p.name, p.price,
                           COALESCE(SUM(si.quantity), 0) AS total_quantity
                    FROM products p
                    LEFT JOIN stock_items si ON p.product_id = si.product_id
                    WHERE p.name ILIKE %s
                    GROUP BY p.product_id, p.name, p.price
                    ORDER BY p.name
                """, (f"%{search_text}%",))
                return cursor.fetchall()
        except psycopg.Error as e:
            print(f"Ошибка поиска товаров: {e}")
            return []
        finally:
            self.release_connection(conn)

    def create_order_safe(self, user_id, status_name, items):
        conn = self.get_connection()
        if conn is None:
            return None, "Нет соединения с БД"
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT status_id FROM order_statuses WHERE name = %s", (status_name,))
                status_res = cursor.fetchone()
                if not status_res:
                    raise Exception(f"Статус '{status_name}' не найден в БД")
                status_id = status_res[0]
                cursor.execute(
                    "INSERT INTO orders (user_id, status_id, order_date) VALUES (%s, %s, CURRENT_TIMESTAMP) RETURNING order_id",
                    (user_id, status_id)
                )
                order_id = cursor.fetchone()[0]
                for item in items:
                    product_id = item['product_id']
                    variant_id = item['variant_id']
                    qty = item['quantity']
                    price = item['price']
                    cursor.execute(
                        "SELECT stock_item_id FROM stock_items WHERE product_id = %s AND variant_id = %s",
                        (product_id, variant_id)
                    )
                    stock_res = cursor.fetchone()
                    if not stock_res:
                        raise Exception(f"Товар с ID {product_id} и вариантом {variant_id} не найден на складе.")
                    stock_item_id = stock_res[0]
                    cursor.execute(
                        "UPDATE stock_items SET quantity = quantity - %s WHERE stock_item_id = %s AND quantity >= %s",
                        (qty, stock_item_id, qty)
                    )
                    if cursor.rowcount != 1:
                        raise Exception("Недостаточно товара на складе для выбранного варианта")
                    cursor.execute(
                        "INSERT INTO order_items (order_id, stock_item_id, quantity, price) VALUES (%s, %s, %s, %s)",
                        (order_id, stock_item_id, qty, price)
                    )
            conn.commit()
            return order_id, None
        except Exception as e:
            conn.rollback()
            return None, str(e)
        finally:
            self.release_connection(conn)

    def get_orders_for_table(self):
        conn = self.get_connection()
        if conn is None:
            return []
        try:
            with conn.cursor() as cursor:
                query = """
                    SELECT o.order_id, 
                           TO_CHAR(o.order_date, 'DD.MM.YYYY HH24:MI') AS order_date,
                           CONCAT_WS(' ', u.last_name, u.first_name, u.middle_name) AS full_name,
                           COALESCE(SUM(oi.quantity * oi.price), 0) AS total,
                           COALESCE(s.name, 'Неизвестно') AS status
                    FROM orders o
                    LEFT JOIN users u ON o.user_id = u.user_id
                    LEFT JOIN order_items oi ON o.order_id = oi.order_id
                    LEFT JOIN order_statuses s ON o.status_id = s.status_id
                    GROUP BY o.order_id, o.order_date, u.last_name, u.first_name, u.middle_name, s.name
                    ORDER BY o.order_date DESC
                """
                cursor.execute(query)
                return cursor.fetchall()
        except psycopg.Error as e:
            print(f"Ошибка получения заказов: {e}")
            return []
        finally:
            self.release_connection(conn)

    def get_order_details(self, order_id):
        conn = self.get_connection()
        if conn is None:
            return []
        try:
            with conn.cursor() as cursor:
                query = """
                    SELECT COALESCE(p.name, 'Товар удален') AS name,
                           oi.quantity, oi.price, (oi.quantity * oi.price) AS total
                    FROM order_items oi
                    LEFT JOIN stock_items si ON oi.stock_item_id = si.stock_item_id
                    LEFT JOIN products p ON si.product_id = p.product_id
                    WHERE oi.order_id = %s
                """
                cursor.execute(query, (order_id,))
                return cursor.fetchall()
        except psycopg.Error as e:
            print(f"Ошибка получения состава заказа: {e}")
            return []
        finally:
            self.release_connection(conn)

    def get_order_total(self, order_id):
        conn = self.get_connection()
        if conn is None:
            return 0
        try:
            with conn.cursor() as cursor:
                query = """
                    SELECT COALESCE(SUM(quantity * price), 0) AS total
                    FROM order_items
                    WHERE order_id = %s
                """
                cursor.execute(query, (order_id,))
                row = cursor.fetchone()
                return row[0] if row else 0
        except psycopg.Error as e:
            print(f"Ошибка получения суммы заказа: {e}")
            return 0
        finally:
            self.release_connection(conn)

    def delete_order_item(self, order_id, product_name):
        conn = self.get_connection()
        if conn is None:
            return False
        try:
            with conn.cursor() as cursor:
                query = """
                    DELETE FROM order_items 
                    WHERE order_id = %s AND stock_item_id IN (
                        SELECT si.stock_item_id 
                        FROM stock_items si 
                        JOIN products p ON si.product_id = p.product_id 
                        WHERE p.name = %s
                    )
                """
                cursor.execute(query, (order_id, product_name))
                conn.commit()
                return True
        except psycopg.Error as e:
            print(f"Ошибка удаления позиции: {e}")
            conn.rollback()
            return False
        finally:
            self.release_connection(conn)

    def get_clients(self):
        conn = self.get_connection()
        if conn is None:
            return []
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT user_id, CONCAT_WS(' ', last_name, first_name, middle_name) 
                    FROM users WHERE role_id = 3
                """)
                return cursor.fetchall()
        except psycopg.Error as e:
            print(f"Ошибка получения клиентов: {e}")
            return []
        finally:
            self.release_connection(conn)

    def add_order_simple(self, user_id, status_name):
        conn = self.get_connection()
        if conn is None:
            return None, "Нет соединения с БД"
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT status_id FROM order_statuses WHERE name = %s", (status_name,))
                status_res = cursor.fetchone()
                if not status_res:
                    raise Exception(f"Статус '{status_name}' не найден")
                status_id = status_res[0]
                cursor.execute(
                    "INSERT INTO orders (user_id, status_id, order_date) VALUES (%s, %s, CURRENT_TIMESTAMP) RETURNING order_id",
                    (user_id, status_id)
                )
                order_id = cursor.fetchone()[0]
            conn.commit()
            return order_id, None
        except Exception as e:
            conn.rollback()
            return None, str(e)
        finally:
            self.release_connection(conn)