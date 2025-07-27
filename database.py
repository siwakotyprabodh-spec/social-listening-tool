import mysql.connector
import bcrypt
import os
from mysql.connector import Error

class DatabaseManager:
    def __init__(self):
        self.connection = None
        self.cursor = None
    
    def connect(self):
        """Connect to MySQL database"""
        try:
            # Get database configuration from environment variables or use defaults
            host = os.getenv('MYSQL_HOST', 'localhost')
            user = os.getenv('MYSQL_USER', 'root')
            password = os.getenv('MYSQL_PASSWORD', '')  # Default XAMPP password is empty
            database = os.getenv('MYSQL_DATABASE', 'social_listening')
            port = int(os.getenv('MYSQL_PORT', '3306'))
            
            self.connection = mysql.connector.connect(
                host=host,
                user=user,
                password=password,
                database=database,
                port=port
            )
            self.cursor = self.connection.cursor()
            return True
        except Error as e:
            print(f"Error connecting to MySQL: {e}")
            return False
    
    def disconnect(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
    
    def check_login(self, username, password):
        """Check if username and password match"""
        try:
            if not self.connect():
                return False
            
            # First try with role column
            try:
                self.cursor.execute("SELECT id, password_hash, role FROM users WHERE username=%s AND is_active=TRUE", (username,))
                result = self.cursor.fetchone()
                
                if result:
                    user_id, stored_hash, role = result
                    # Check if password matches the stored hash
                    if bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8')):
                        # Update last login
                        self.cursor.execute("UPDATE users SET last_login=CURRENT_TIMESTAMP WHERE id=%s", (user_id,))
                        self.connection.commit()
                        return {'success': True, 'user_id': user_id, 'username': username, 'role': role}
            except Error as e:
                # If role column doesn't exist, try without it
                if "Unknown column 'role'" in str(e):
                    self.cursor.execute("SELECT id, password_hash FROM users WHERE username=%s", (username,))
                    result = self.cursor.fetchone()
                    
                    if result:
                        user_id, stored_hash = result
                        # Check if password matches the stored hash
                        if bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8')):
                            # Update last login
                            self.cursor.execute("UPDATE users SET last_login=CURRENT_TIMESTAMP WHERE id=%s", (user_id,))
                            self.connection.commit()
                            return {'success': True, 'user_id': user_id, 'username': username, 'role': 'user'}
                else:
                    raise e
            
            return {'success': False, 'message': 'Invalid credentials'}
        except Error as e:
            print(f"Error checking login: {e}")
            return {'success': False, 'message': 'Database error'}
        finally:
            self.disconnect()
    
    def create_user(self, username, password, email=None):
        """Create a new user"""
        try:
            if not self.connect():
                return False
            
            # Hash the password
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            
            # Insert new user
            self.cursor.execute(
                "INSERT INTO users (username, password_hash, email) VALUES (%s, %s, %s)",
                (username, password_hash.decode('utf-8'), email)
            )
            self.connection.commit()
            return True
        except Error as e:
            print(f"Error creating user: {e}")
            return False
        finally:
            self.disconnect()
    
    def user_exists(self, username):
        """Check if username already exists"""
        try:
            if not self.connect():
                return False
            
            self.cursor.execute("SELECT id FROM users WHERE username=%s", (username,))
            result = self.cursor.fetchone()
            return result is not None
        except Error as e:
            print(f"Error checking user existence: {e}")
            return False
        finally:
            self.disconnect()
    
    def get_user_preferences(self, user_id):
        """Get user preferences"""
        try:
            if not self.connect():
                return None
            
            self.cursor.execute("SELECT translation_quality, summary_length, max_crawl_pages, crawl_timeout FROM user_preferences WHERE user_id=%s", (user_id,))
            result = self.cursor.fetchone()
            
            if result:
                return {
                    'translation_quality': result[0],
                    'summary_length': result[1],
                    'max_crawl_pages': result[2],
                    'crawl_timeout': result[3]
                }
            return None
        except Error as e:
            print(f"Error getting user preferences: {e}")
            return None
        finally:
            self.disconnect()
    
    def save_user_preferences(self, user_id, preferences):
        """Save user preferences"""
        try:
            if not self.connect():
                return False
            
            # Check if preferences exist
            self.cursor.execute("SELECT id FROM user_preferences WHERE user_id=%s", (user_id,))
            exists = self.cursor.fetchone()
            
            if exists:
                # Update existing preferences
                self.cursor.execute("""
                    UPDATE user_preferences 
                    SET translation_quality=%s, summary_length=%s, max_crawl_pages=%s, crawl_timeout=%s 
                    WHERE user_id=%s
                """, (preferences['translation_quality'], preferences['summary_length'], 
                     preferences['max_crawl_pages'], preferences['crawl_timeout'], user_id))
            else:
                # Insert new preferences
                self.cursor.execute("""
                    INSERT INTO user_preferences (user_id, translation_quality, summary_length, max_crawl_pages, crawl_timeout)
                    VALUES (%s, %s, %s, %s, %s)
                """, (user_id, preferences['translation_quality'], preferences['summary_length'],
                     preferences['max_crawl_pages'], preferences['crawl_timeout']))
            
            self.connection.commit()
            return True
        except Error as e:
            print(f"Error saving user preferences: {e}")
            return False
        finally:
            self.disconnect()
    
    def save_crawl_session(self, user_id, session_name, keywords, search_logic, date_from=None, date_to=None):
        """Save a crawl session"""
        try:
            if not self.connect():
                return None
            
            import json
            keywords_json = json.dumps(keywords)
            
            self.cursor.execute("""
                INSERT INTO crawl_sessions (user_id, session_name, keywords, search_logic, date_from, date_to)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (user_id, session_name, keywords_json, search_logic, date_from, date_to))
            
            self.connection.commit()
            return self.cursor.lastrowid
        except Error as e:
            print(f"Error saving crawl session: {e}")
            return None
        finally:
            self.disconnect()
    
    def save_crawl_results(self, crawl_session_id, results):
        """Save crawl results"""
        try:
            if not self.connect():
                return False
            
            for result in results:
                self.cursor.execute("""
                    INSERT INTO crawl_results (crawl_session_id, url, date_found, raw_date, content)
                    VALUES (%s, %s, %s, %s, %s)
                """, (crawl_session_id, result['url'], result['date'], result['raw_date'], result.get('content')))
            
            self.connection.commit()
            return True
        except Error as e:
            print(f"Error saving crawl results: {e}")
            return False
        finally:
            self.disconnect()
    
    def get_user_crawl_sessions(self, user_id):
        """Get user's crawl sessions"""
        try:
            if not self.connect():
                return []
            
            self.cursor.execute("""
                SELECT id, session_name, keywords, search_logic, date_from, date_to, created_at
                FROM crawl_sessions 
                WHERE user_id=%s 
                ORDER BY created_at DESC
            """, (user_id,))
            
            sessions = []
            for row in self.cursor.fetchall():
                import json
                sessions.append({
                    'id': row[0],
                    'session_name': row[1],
                    'keywords': json.loads(row[2]),
                    'search_logic': row[3],
                    'date_from': row[4],
                    'date_to': row[5],
                    'created_at': row[6]
                })
            
            return sessions
        except Error as e:
            print(f"Error getting crawl sessions: {e}")
            return []
        finally:
            self.disconnect()

# Test connection function
def test_connection():
    """Test database connection"""
    db = DatabaseManager()
    if db.connect():
        print("✅ Database connection successful!")
        db.disconnect()
        return True
    else:
        print("❌ Database connection failed!")
        return False

if __name__ == "__main__":
    test_connection() 