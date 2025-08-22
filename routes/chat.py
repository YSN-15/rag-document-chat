from flask import Blueprint, render_template, request, jsonify, session, flash, redirect, url_for
from models import Document, ChatMessage
from services.document_processor import DocumentProcessor
from app import db
import uuid
import json

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/')
def chat_interface():
    # Ensure user has a session ID
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    
    session_id = session['session_id']
    
    # Get user's documents for context
    documents = Document.query.filter_by(
        session_id=session_id, 
        status='indexed'
    ).order_by(Document.upload_date.desc()).all()
    
    # Get chat history
    messages = ChatMessage.query.filter_by(
        session_id=session_id
    ).order_by(ChatMessage.timestamp.asc()).all()
    
    return render_template('chat.html', documents=documents, messages=messages)

@chat_bp.route('/ask', methods=['POST'])
def ask_question():
    if 'session_id' not in session:
        return jsonify({'error': 'No session'}), 400
    
    session_id = session['session_id']
    
    try:
        data = request.get_json()
        if not data or 'question' not in data:
            return jsonify({'error': 'No question provided'}), 400
        
        question = data['question'].strip()
        if not question:
            return jsonify({'error': 'Empty question'}), 400
        
        # Check if user has any indexed documents
        indexed_docs = Document.query.filter_by(
            session_id=session_id, 
            status='indexed'
        ).count()
        
        if indexed_docs == 0:
            return jsonify({
                'response': 'Please upload and process some documents first before asking questions.',
                'sources': [],
                'context_used': 0
            })
        
        # Save user message
        user_message = ChatMessage(
            session_id=session_id,
            message_type='user',
            content=question
        )
        db.session.add(user_message)
        
        # Get document filters if specified
        document_filters = None
        if 'document_names' in data and data['document_names']:
            document_filters = {'document_names': data['document_names']}
        
        # Process the question
        processor = DocumentProcessor()
        result = processor.search_and_answer(question, session_id, document_filters)
        
        # Save assistant message
        assistant_message = ChatMessage(
            session_id=session_id,
            message_type='assistant',
            content=result['response'],
            sources=json.dumps(result['sources'])
        )
        db.session.add(assistant_message)
        db.session.commit()
        
        return jsonify(result)
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error processing question: {str(e)}'}), 500

@chat_bp.route('/clear', methods=['POST'])
def clear_chat():
    if 'session_id' not in session:
        return jsonify({'error': 'No session'}), 400
    
    session_id = session['session_id']
    
    try:
        # Delete all chat messages for this session
        ChatMessage.query.filter_by(session_id=session_id).delete()
        db.session.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error clearing chat: {str(e)}'}), 500

@chat_bp.route('/export')
def export_chat():
    if 'session_id' not in session:
        flash('No session found', 'error')
        return redirect(url_for('chat.chat_interface'))
    
    session_id = session['session_id']
    
    # Get all messages for this session
    messages = ChatMessage.query.filter_by(
        session_id=session_id
    ).order_by(ChatMessage.timestamp.asc()).all()
    
    # Create export data
    export_data = []
    for message in messages:
        export_data.append({
            'type': message.message_type,
            'content': message.content,
            'timestamp': message.timestamp.isoformat(),
            'sources': json.loads(message.sources) if message.sources else []
        })
    
    from flask import Response
    import json
    
    response_data = json.dumps(export_data, indent=2)
    
    return Response(
        response_data,
        mimetype='application/json',
        headers={
            'Content-Disposition': f'attachment; filename=chat_export_{session_id[:8]}.json'
        }
    )
