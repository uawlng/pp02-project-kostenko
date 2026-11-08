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

    def get_categories(self):
        conn = self.get_connection()
        if conn is None:
            return []
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT name FROM categories ORDER BY name")
                categories = cursor.fetchall()
                return [row[0] for row in categories]
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
                    "Количество: по возрастанию": "total_quantity ASC",
                    "Количество: по убыванию": "total_quantity DESC",
                }
                order_clause = ""
                if sort_order in order_map:
                    order_clause = f"ORDER BY {order_map[sort_order]}"

                query = f"""
                    SELECT p.product_id, p.name, p.price, p.image,
                           COALESCE(m.name, 'Неизвестно') AS manufacturer,
                           COALESCE(SUM(si.quantity), 0) AS total_quantity,
                           COALESCE(c.name, 'Без категории') AS category_name
                    FROM products p
                    LEFT JOIN manufacturers m ON p.manufacturer_id = m.manufacturer_id
                    LEFT JOIN categories c ON p.category_id = c.category_id
                    LEFT JOIN stock_items si ON p.product_id = si.product_id
                    WHERE (p.name ILIKE %s OR COALESCE(m.name, '') ILIKE %s)
                    AND (c.name = %s OR %s = 'Все категории')
                    GROUP BY p.product_id, p.name, p.price, p.image, m.name, c.name
                    {order_clause}
                """

                cursor.execute(query, (search_pattern, search_pattern, category, category))
                return cursor.fetchall()
        except psycopg.Error as e:
            print(f"Ошибка запроса: {e}")
            return []
        finally:
            self.release_connection(conn)

    def create_order(self, user_id, items):
        conn = self.get_connection()
        if conn is None:
            return False
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO orders (user_id) VALUES (%s) RETURNING order_id",
                    (user_id,)
                )
                order_id = cursor.fetchone()[0]

                for item in items:
                    cursor.execute(
                        "INSERT INTO order_items (order_id, stock_item_id, quantity, price) VALUES (%s, %s, %s, %s)",
                        (order_id, item['product_id'], item['quantity'], item['price'])
                    )
            conn.commit()
            return True
        except psycopg.Error as e:
            print(f"Ошибка при создании заказа: {e}")
            conn.rollback()
            return False
        finally:
            self.release_connection(conn)

    def get_all_orders(self):
        conn = self.get_connection()
        if conn is None:
            return []
        try:
            with conn.cursor() as cursor:
                query = """
                    SELECT o.order_id, 
                           COALESCE(u.last_name, '') || ' ' || COALESCE(u.first_name, '') || ' ' || COALESCE(u.middle_name, '') AS fio,
                           COUNT(oi.id) AS items_count,
                           SUM(oi.quantity * oi.price) AS total_sum
                    FROM orders o
                    LEFT JOIN users u ON o.user_id = u.user_id
                    LEFT JOIN order_items oi ON o.order_id = oi.order_id
                    GROUP BY o.order_id, u.last_name, u.first_name, u.middle_name
                    ORDER BY o.order_id DESC
                """
                cursor.execute(query)
                return cursor.fetchall()
        except psycopg.Error as e:
            print(f"Ошибка получения заказов: {e}")
            return []
        finally:
            self.release_connection(conn)