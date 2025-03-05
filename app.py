from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz
import os

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///sleep_tracker.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)

# Dodaj strefę czasową dla Polski
local_tz = pytz.timezone('Europe/Warsaw')

# Funkcja zwracająca aktualny czas w strefie czasowej warszawskiej
def get_current_warsaw_time():
    # Zamiast używać datetime.now(pytz.UTC), użyjmy datetime.utcnow()
    # i jawnie ustawmy strefę czasową UTC
    utc_now = datetime.utcnow().replace(tzinfo=pytz.UTC)
    
    # Konwertuj do strefy czasowej warszawskiej
    warsaw_time = utc_now.astimezone(local_tz)
    
    return warsaw_time

class SleepRecord(db.Model):
    """Model for sleep records"""
    __tablename__ = 'sleep_records'

    id = db.Column(db.Integer, primary_key=True)
    sleep_time = db.Column(db.DateTime, nullable=False)
    wake_time = db.Column(db.DateTime, nullable=False)
    notes = db.Column(db.String(200))
    sleep_rating = db.Column(db.Integer, nullable=True)  # Rating from 1-5 stars
    is_rated = db.Column(db.Boolean, default=False)  # Flag to track if sleep has been rated
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def sleep_duration(self):
        """Calculate sleep duration in hours"""
        duration = self.wake_time - self.sleep_time
        return round(duration.total_seconds() / 3600, 2)

@app.route('/')
def index():
    """Home page route"""
    try:
        # Get selected date from query parameters or use today
        selected_date_str = request.args.get('date')
        # Używamy aktualnego czasu w strefie czasowej warszawskiej
        today = get_current_warsaw_time().date()
        
        if selected_date_str:
            selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
        else:
            selected_date = today

        # Get records for selected date
        start_of_day = datetime.combine(selected_date, datetime.min.time())
        end_of_day = datetime.combine(selected_date, datetime.max.time())
        
        # Pobierz rekordy, które:
        # 1. Są drzemkami (krótsze niż 4h) i zaczynają się w wybranym dniu
        # 2. Są snem nocnym (dłuższe niż 4h) i kończą się w wybranym dniu
        records = []
        
        # Najpierw pobierz wszystkie rekordy, które mogą być związane z wybranym dniem
        all_possible_records = SleepRecord.query.filter(
            ((SleepRecord.sleep_time >= start_of_day) & (SleepRecord.sleep_time <= end_of_day)) |  # zaczynają się w wybranym dniu
            ((SleepRecord.wake_time >= start_of_day) & (SleepRecord.wake_time <= end_of_day))      # kończą się w wybranym dniu
        ).all()
        
        # Następnie przefiltruj je zgodnie z zasadami
        for record in all_possible_records:
            # Oblicz czas trwania snu w godzinach
            sleep_duration = (record.wake_time - record.sleep_time).total_seconds() / 3600
            
            # Jeśli to drzemka (krótszy niż 4h), sprawdź czy zaczyna się w wybranym dniu
            if sleep_duration <= 4 and record.sleep_time.date() == selected_date:
                records.append(record)
            # Jeśli to sen nocny (dłuższy niż 4h), sprawdź czy kończy się w wybranym dniu
            elif sleep_duration > 4 and record.wake_time.date() == selected_date:
                records.append(record)
        
        # Sortuj rekordy według czasu rozpoczęcia, od najnowszego
        records.sort(key=lambda x: x.sleep_time, reverse=True)
        
        time_since_last = None
        
        # Oblicz liczbę drzemek i sumę godzin drzemek dla wybranego dnia
        naps_today = 0
        total_nap_hours = 0
        total_nap_minutes = 0
        
        for record in records:
            sleep_duration = (record.wake_time - record.sleep_time).total_seconds()
            # Jeśli to drzemka (krótszy niż 4h)
            if sleep_duration <= 4 * 3600:
                naps_today += 1
                total_nap_hours += int(sleep_duration // 3600)
                total_nap_minutes += int((sleep_duration % 3600) // 60)
        
        # Konwertuj nadmiarowe minuty na godziny
        if total_nap_minutes >= 60:
            total_nap_hours += total_nap_minutes // 60
            total_nap_minutes = total_nap_minutes % 60
        
        # Calculate time since last nap only for today
        if today == selected_date and records:
            # Znajdź ostatni rekord (drzemkę lub sen nocny) zakończony dzisiaj
            today_records = [r for r in records if r.wake_time.date() == today]
            if today_records:
                last_wake = today_records[0].wake_time
                # Używamy aktualnego czasu w strefie czasowej warszawskiej
                current_time = get_current_warsaw_time().replace(tzinfo=None)
                time_diff = current_time - last_wake
                hours = int(time_diff.total_seconds() // 3600)
                minutes = int((time_diff.total_seconds() % 3600) // 60)
                time_since_last = {'hours': hours, 'minutes': minutes}
            
        return render_template('index.html', 
                             records=records, 
                             time_since_last=time_since_last,
                             naps_today=naps_today,
                             total_nap_hours=total_nap_hours,
                             total_nap_minutes=total_nap_minutes,
                             selected_date=selected_date,
                             today=today)
    except Exception as e:
        app.logger.error(f"Error fetching records: {str(e)}")
        return render_template('error.html', message="Nie udało się pobrać zapisów.")

@app.route('/add', methods=['GET', 'POST'])
def add_record():
    """Add new sleep record route"""
    if request.method == 'POST':
        try:
            sleep_time = datetime.strptime(request.form['sleep_time'], '%Y-%m-%dT%H:%M')
            wake_time = datetime.strptime(request.form['wake_time'], '%Y-%m-%dT%H:%M')
            notes = request.form['notes']

            if wake_time <= sleep_time:
                return render_template('add.html', error="Czas pobudki musi być późniejszy niż czas zaśnięcia.")
            
            # Oblicz czas trwania snu w godzinach
            sleep_duration = (wake_time - sleep_time).total_seconds() / 3600
            
            # Sprawdź, czy notatki są puste lub zawierają standardowy opis
            is_standard_note = not notes.strip() or notes.strip() == "Sen nocny" or notes.strip().startswith("Drzemka nr")
            
            # Jeśli notatki są puste lub zawierają standardowy opis, automatycznie określ typ snu
            if is_standard_note:
                if sleep_duration > 4:
                    notes = "Sen nocny"
                else:
                    # Dla drzemek liczymy drzemki z dnia rozpoczęcia
                    today = sleep_time.date()
                    # Policz dzisiejsze drzemki
                    naps_today = SleepRecord.query.filter(
                        SleepRecord.sleep_time >= datetime.combine(today, datetime.min.time()),
                        SleepRecord.sleep_time < datetime.combine(today, datetime.max.time()),
                        (SleepRecord.wake_time - SleepRecord.sleep_time) <= timedelta(hours=4)  # tylko drzemki
                    ).count()
                    
                    notes = f"Drzemka nr {naps_today + 1}"
            
            record = SleepRecord(
                sleep_time=sleep_time,
                wake_time=wake_time,
                notes=notes
            )
            db.session.add(record)
            db.session.commit()
            return redirect(url_for('index'))
        
        except Exception as e:
            app.logger.error(f"Error adding record: {str(e)}")
            db.session.rollback()
            return render_template('add.html', error="Wystąpił błąd podczas dodawania zapisu.")
    
    return render_template('add.html')

@app.route('/start_nap', methods=['POST'])
def start_nap():
    """Start new nap"""
    try:
        # Używamy aktualnego czasu w strefie czasowej warszawskiej
        start_time = get_current_warsaw_time()
        
        # Zwracamy czas w formacie ISO z informacją o strefie czasowej
        # Dzięki temu przeglądarka będzie wiedziała, że to czas w strefie warszawskiej
        return jsonify({
            'status': 'success',
            'start_time': start_time.isoformat()
        })
    except Exception as e:
        app.logger.error(f"Error starting nap: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/stop_nap', methods=['POST'])
def stop_nap():
    """Stop nap and save record"""
    try:
        data = request.get_json()
        
        # Konwertuj czasy do lokalnej strefy czasowej
        sleep_time_str = data['start_time']
        
        # Poprawiona konwersja czasu - zakładamy, że czas przychodzący jest już w strefie czasowej warszawskiej
        # ale został przekonwertowany do ISO format, więc musimy go prawidłowo zinterpretować
        if 'Z' in sleep_time_str:
            # Jeśli czas zawiera 'Z', oznacza to czas UTC
            sleep_time = datetime.fromisoformat(sleep_time_str.replace('Z', '+00:00'))
            sleep_time = sleep_time.astimezone(local_tz)
        elif '+' in sleep_time_str or '-' in sleep_time_str[-6:]:
            # Jeśli czas zawiera informację o strefie czasowej
            sleep_time = datetime.fromisoformat(sleep_time_str)
            sleep_time = sleep_time.astimezone(local_tz)
        else:
            # Jeśli czas nie zawiera informacji o strefie czasowej, zakładamy że jest w lokalnej strefie
            sleep_time = datetime.fromisoformat(sleep_time_str)
            sleep_time = sleep_time.replace(tzinfo=local_tz)
        
        # Używamy aktualnego czasu w strefie czasowej warszawskiej
        wake_time = get_current_warsaw_time()
        
        # Zapisujemy czas bez informacji o strefie czasowej, ale zachowujemy lokalny czas warszawski
        sleep_time = sleep_time.replace(tzinfo=None)
        wake_time = wake_time.replace(tzinfo=None)
        
        # Oblicz czas trwania snu w godzinach
        sleep_duration = (wake_time - sleep_time).total_seconds() / 3600
        
        # Określ opis na podstawie czasu trwania snu
        if sleep_duration > 4:
            notes = "Sen nocny"
            # Dla snu nocnego liczymy drzemki z dnia zakończenia
            today = wake_time.date()
        else:
            # Dla drzemek liczymy drzemki z dnia rozpoczęcia
            today = sleep_time.date()
            # Policz dzisiejsze drzemki
            naps_today = SleepRecord.query.filter(
                SleepRecord.sleep_time >= datetime.combine(today, datetime.min.time()),
                SleepRecord.sleep_time < datetime.combine(today, datetime.max.time()),
                (SleepRecord.wake_time - SleepRecord.sleep_time) <= timedelta(hours=4)  # tylko drzemki
            ).count()
            
            notes = f"Drzemka nr {naps_today + 1}"
        
        record = SleepRecord(
            sleep_time=sleep_time,
            wake_time=wake_time,
            notes=notes,
            is_rated=False  # Domyślnie sen nie jest oceniony
        )
        
        db.session.add(record)
        db.session.commit()
        
        # Jeśli to sen nocny, zwróć ID rekordu, aby można było przekierować do oceny
        if sleep_duration > 4:
            return jsonify({
                'status': 'success',
                'message': 'Sen nocny zapisany',
                'is_night_sleep': True,
                'record_id': record.id
            })
        else:
            return jsonify({
                'status': 'success',
                'message': 'Drzemka zapisana',
                'is_night_sleep': False
            })
    except Exception as e:
        app.logger.error(f"Error saving nap: {str(e)}")
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/delete_record/<int:record_id>', methods=['POST'])
def delete_record(record_id):
    """Delete sleep record"""
    try:
        record = SleepRecord.query.get_or_404(record_id)
        db.session.delete(record)
        db.session.commit()
        return redirect(url_for('index'))
    except Exception as e:
        app.logger.error(f"Error deleting record: {str(e)}")
        return render_template('error.html', message="Nie udało się usunąć wpisu.")

@app.route('/edit_record/<int:record_id>', methods=['GET', 'POST'])
def edit_record(record_id):
    """Edit sleep record"""
    record = SleepRecord.query.get_or_404(record_id)
    
    if request.method == 'POST':
        try:
            record.sleep_time = datetime.strptime(request.form['sleep_time'], '%Y-%m-%dT%H:%M')
            record.wake_time = datetime.strptime(request.form['wake_time'], '%Y-%m-%dT%H:%M')
            record.notes = request.form['notes']
            
            # Handle sleep rating if provided
            if 'rating' in request.form and request.form['rating']:
                try:
                    rating = int(request.form['rating'])
                    if 1 <= rating <= 5:
                        record.sleep_rating = rating
                        record.is_rated = True
                except ValueError:
                    pass
            
            if record.wake_time <= record.sleep_time:
                return render_template('edit.html', record=record, error="Czas pobudki musi być późniejszy niż czas zaśnięcia.")
            
            # Oblicz czas trwania snu w godzinach
            sleep_duration = (record.wake_time - record.sleep_time).total_seconds() / 3600
            
            # Sprawdź, czy notatki są puste lub zawierają standardowy opis
            is_standard_note = not record.notes.strip() or record.notes.strip() == "Sen nocny" or record.notes.strip().startswith("Drzemka nr")
            
            # Jeśli notatki są puste lub zawierają standardowy opis, automatycznie zaktualizuj opis
            if is_standard_note:
                if sleep_duration > 4:
                    record.notes = "Sen nocny"
                else:
                    # Dla drzemek liczymy drzemki z dnia rozpoczęcia
                    today = record.sleep_time.date()
                    # Policz dzisiejsze drzemki
                    naps_today = SleepRecord.query.filter(
                        SleepRecord.sleep_time >= datetime.combine(today, datetime.min.time()),
                        SleepRecord.sleep_time < datetime.combine(today, datetime.max.time()),
                        (SleepRecord.wake_time - SleepRecord.sleep_time) <= timedelta(hours=4),  # tylko drzemki
                        SleepRecord.id != record_id  # Wykluczamy aktualny rekord
                    ).count()
                    
                    record.notes = f"Drzemka nr {naps_today + 1}"
            
            db.session.commit()
            return redirect(url_for('index'))
        except Exception as e:
            app.logger.error(f"Error editing record: {str(e)}")
            db.session.rollback()
            return render_template('edit.html', record=record, error="Wystąpił błąd podczas edycji wpisu.")
    
    return render_template('edit.html', record=record)

@app.route('/rate_sleep/<int:record_id>', methods=['GET', 'POST'])
def rate_sleep(record_id):
    """Rate sleep quality"""
    record = SleepRecord.query.get_or_404(record_id)
    
    # Check if this is a night sleep (longer than 4 hours)
    sleep_duration = (record.wake_time - record.sleep_time).total_seconds() / 3600
    if sleep_duration <= 4:
        return render_template('error.html', message="Tylko sen nocny może być oceniony.")
    
    if request.method == 'POST':
        try:
            rating = int(request.form['rating'])
            if 1 <= rating <= 5:
                record.sleep_rating = rating
                record.is_rated = True
                db.session.commit()
                return redirect(url_for('index'))
            else:
                return render_template('rate_sleep.html', record=record, error="Ocena musi być w zakresie 1-5.")
        except Exception as e:
            app.logger.error(f"Error rating sleep: {str(e)}")
            db.session.rollback()
            return render_template('rate_sleep.html', record=record, error="Wystąpił błąd podczas oceny snu.")
    
    return render_template('rate_sleep.html', record=record)

@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors"""
    return render_template('error.html', message="Strona nie została znaleziona."), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    db.session.rollback()
    return render_template('error.html', message="Wystąpił błąd serwera."), 500

def init_db():
    """Initialize the database"""
    with app.app_context():
        db.create_all()

if __name__ == '__main__':
    init_db()
    app.run(
        host='0.0.0.0',
        port=int(os.getenv('PORT', 5000)),
        debug=os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    ) 