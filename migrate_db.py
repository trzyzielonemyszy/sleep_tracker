import sqlite3
import os

# Ścieżka do bazy danych
db_path = 'instance/sleep_tracker.db'

def migrate_database():
    """Migracja bazy danych - dodanie kolumn sleep_rating i is_rated"""
    print("Rozpoczynam migrację bazy danych...")
    
    # Sprawdź, czy baza danych istnieje
    if not os.path.exists(db_path):
        print(f"Baza danych {db_path} nie istnieje!")
        return
    
    # Połącz z bazą danych
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Sprawdź, czy kolumny już istnieją
        cursor.execute("PRAGMA table_info(sleep_records)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Dodaj kolumnę sleep_rating, jeśli nie istnieje
        if 'sleep_rating' not in columns:
            print("Dodaję kolumnę sleep_rating...")
            cursor.execute("ALTER TABLE sleep_records ADD COLUMN sleep_rating INTEGER")
        else:
            print("Kolumna sleep_rating już istnieje.")
        
        # Dodaj kolumnę is_rated, jeśli nie istnieje
        if 'is_rated' not in columns:
            print("Dodaję kolumnę is_rated...")
            cursor.execute("ALTER TABLE sleep_records ADD COLUMN is_rated BOOLEAN DEFAULT 0")
        else:
            print("Kolumna is_rated już istnieje.")
        
        # Zatwierdź zmiany
        conn.commit()
        print("Migracja zakończona pomyślnie!")
    
    except Exception as e:
        print(f"Błąd podczas migracji: {str(e)}")
        conn.rollback()
    
    finally:
        # Zamknij połączenie
        conn.close()

if __name__ == "__main__":
    migrate_database() 