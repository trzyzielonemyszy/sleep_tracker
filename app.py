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
        
        records = SleepRecord.query.filter(
            SleepRecord.sleep_time >= start_of_day,
            SleepRecord.sleep_time <= end_of_day
        ).order_by(SleepRecord.sleep_time.desc()).all()

        time_since_last = None
        naps_today = len(records)
        
        # Calculate time since last nap only for today
        if today == selected_date and records:
            last_wake = records[0].wake_time
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
        
        # Policz dzisiejsze drzemki
        today = get_current_warsaw_time().date()
        naps_today = SleepRecord.query.filter(
            SleepRecord.sleep_time >= today,
            SleepRecord.sleep_time < today + timedelta(days=1)
        ).count()
        
        notes = f"Drzemka nr {naps_today + 1}"
        
        record = SleepRecord(
            sleep_time=sleep_time,
            wake_time=wake_time,
            notes=notes
        )
        
        db.session.add(record)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Drzemka zapisana'
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
            
            if record.wake_time <= record.sleep_time:
                return render_template('edit.html', record=record, error="Czas pobudki musi być późniejszy niż czas zaśnięcia.")
            
            db.session.commit()
            return redirect(url_for('index'))
        except Exception as e:
            app.logger.error(f"Error editing record: {str(e)}")
            db.session.rollback()
            return render_template('edit.html', record=record, error="Wystąpił błąd podczas edycji wpisu.")
    
    return render_template('edit.html', record=record)

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