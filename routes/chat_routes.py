from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import or_
from datetime import datetime

from extensions import db
from models import User, Message

chat_bp = Blueprint('chat_bp', __name__)

@chat_bp.route('/messages', methods=['POST'])
@jwt_required()
def send_message():
    user_id = get_jwt_identity()
    sender = User.query.get(user_id)

    if not sender:
        return jsonify({'error': 'User not found'}), 404

    data = request.get_json()
    recipient_id = data.get('recipient_id')
    message_text = data.get('message_text')

    if not recipient_id or not message_text:
        return jsonify({'error': 'Recipient ID and message text are required'}), 400

    recipient = User.query.get(recipient_id)
    if not recipient:
        return jsonify({'error': 'Recipient not found'}), 404

    # Create the message
    message = Message(
        sender_id=sender.id,
        recipient_id=recipient.id,
        message_text=message_text,
        sent_at=datetime.utcnow()
    )

    db.session.add(message)

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error sending message: {e}")
        return jsonify({'error': 'An error occurred while sending the message'}), 500

    return jsonify({'message': 'Message sent successfully', 'message_id': message.id}), 201

@chat_bp.route('/conversations', methods=['GET'])
@jwt_required()
def get_conversations():
    user_id = get_jwt_identity()

    # Get all users that the current user has had conversations with
    messages = Message.query.filter(
        or_(Message.sender_id == user_id, Message.recipient_id == user_id)
    ).order_by(Message.sent_at.desc()).all()

    # Extract unique user IDs from messages
    user_ids = set()
    conversations = []
    for message in messages:
        other_user_id = message.recipient_id if message.sender_id == user_id else message.sender_id
        if other_user_id not in user_ids:
            user_ids.add(other_user_id)
            other_user = User.query.get(other_user_id)
            conversations.append({
                'user_id': other_user.id,
                'username': other_user.username,
                'first_name': other_user.first_name,
                'last_name': other_user.last_name,
                'profile_picture_url': other_user.profile_picture_url,
            })

    return jsonify({'conversations': conversations}), 200

@chat_bp.route('/messages/<int:other_user_id>', methods=['GET'])
@jwt_required()
def get_messages(other_user_id):
    user_id = get_jwt_identity()

    # Check if the other user exists
    other_user = User.query.get(other_user_id)
    if not other_user:
        return jsonify({'error': 'User not found'}), 404

    # Get messages between the current user and the other user
    messages = Message.query.filter(
        or_(
            (Message.sender_id == user_id) & (Message.recipient_id == other_user_id),
            (Message.sender_id == other_user_id) & (Message.recipient_id == user_id)
        )
    ).order_by(Message.sent_at.asc()).all()

    messages_data = []
    for message in messages:
        messages_data.append({
            'message_id': message.id,
            'sender_id': message.sender_id,
            'recipient_id': message.recipient_id,
            'message_text': message.message_text,
            'sent_at': message.sent_at.isoformat(),
            'seen_at': message.seen_at.isoformat() if message.seen_at else None
        })

    return jsonify({'messages': messages_data}), 200

