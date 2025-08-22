from flask import Blueprint, render_template, session, redirect, url_for
import uuid

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    # Ensure user has a session ID
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    
    return render_template('index.html')

@main_bp.route('/toggle-theme')
def toggle_theme():
    current_theme = session.get('theme', 'light')
    session['theme'] = 'dark' if current_theme == 'light' else 'light'
    return redirect(request.referrer or url_for('main.index'))
