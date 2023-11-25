from datetime import datetime

from flask import jsonify, request, Blueprint
from flasgger import swag_from
from models import db, ChatHistory, Users, Robots
from constants.http_status_codes import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_409_CONFLICT,
    HTTP_500_INTERNAL_SERVER_ERROR,
)



from dtos import DTOMessage, DTOConversationMessage
import os
from dotenv import load_dotenv
import openai

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
chat_bp = Blueprint("chat_bp", __name__, url_prefix="/api/v1")

@chat_bp.route("/store_message", methods=["POST"])
def store_message():
    '''
    Y. Liu Updated models based on new ER Model

    Please validate and test the following
    Sample Request JSON body:

    data = {
        "message": "Hello, this is a chat message",
        "conversation_id": 123,
        "user_id": 456,
        "robot_id": 789,
        "is_robot": False
    }

    :return:
    200 OK / 500 Error
    '''
    data = request.get_json()
    message = data.get("message")
    conversation_id = data.get("conversation_id")
    user_id = data.get("user_id")
    robot_id = data.get("robot_id")
    is_robot = data.get("is_robot")

    if is_robot is None or message is None or user_id is None or robot_id is None:
        return jsonify({"error": "Incomplete data"}), HTTP_400_BAD_REQUEST

    chat_history = ChatHistory(
        message=message,
        conversation_id=conversation_id,
        user_id=user_id,
        robot_id=robot_id,
        is_robot=is_robot
    )

    try:
        db.session.add(chat_history)
        db.session.commit()
        return jsonify({"message": "Chat history stored successfully"}), HTTP_200_OK
    except Exception as e:
        print(e)
        db.session.rollback()
        return (
            jsonify({"error": "Failed to store chat history"}),
            HTTP_500_INTERNAL_SERVER_ERROR,
        )


@chat_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Incomplete data"}), HTTP_400_BAD_REQUEST

    existing_user = Users.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({"error": "User already exists", "user_id": existing_user.id}), HTTP_409_CONFLICT

    new_user = Users(email=email, password=password)

    try:
        db.session.add(new_user)
        db.session.flush()
        user_id = new_user.id
        db.session.commit()
        return jsonify({"message": "User registered successfully", "user_id": user_id}), HTTP_201_CREATED
    except Exception as e:
        db.session.rollback()
        return (
            jsonify({"error": "Failed to register user"}),
            HTTP_500_INTERNAL_SERVER_ERROR,
        )


@chat_bp.route("/robot/create", methods=["POST"])
def create_robot():
    data = request.get_json()
    robot_name = data.get("name")
    personality_description = data.get("personality")

    new_robot = Robots(robot_name=robot_name, description=personality_description)

    try:
        db.session.add(new_robot)
        db.session.commit()
        return jsonify(new_robot), HTTP_201_CREATED
    except Exception as e:
        db.session.rollback()
        return (
            jsonify({"error": "Failed to create New Robot"}),
            HTTP_500_INTERNAL_SERVER_ERROR,
        )


@chat_bp.route("/robot/<int:robot_id>")
@swag_from("./docs/robot.yaml")
def get_robot(robot_id: int):
    robot_info = Robots.query.get(robot_id)
    if robot_info:
        return jsonify(robot_info), HTTP_200_OK
    return jsonify({"error": f"Robot id: {robot_id} not found"}), HTTP_404_NOT_FOUND


# @chat_bp.route("/get_rooms_history")
# def get_room_history():
#     room_ids = request.get_json()

#     if room_ids:
#         response = {}
#         room_ids_list = [item["room_id"] for item in room_ids]
#         for room_id in room_ids_list:
#             response[room_id] = ChatHistory.query.get(room_id).message
#         return response
#     return (
#         jsonify({"error": f"error: Room_ids {room_ids} not found"}),
#         HTTP_404_NOT_FOUND,
#     )


@chat_bp.route("/rooms/get_history")
@swag_from("./docs/get_history.yaml")
def get_rooms_history():
    """
    Sample request body json:
    {
        "user_id": 2,
        "conversation_id_list": [
            23
            ,22
        ]
    }
    :return:
    [
        {
            "conversation_id": 22,
            "message_list": [
                {
                    "content": "Hello, this is a new chat message",
                    "sender": "robot",
                    "update_time": "2023-07-31 05:21:04.574198"
                },
                {
                    "content": "Hello, this is a new user chat message",
                    "sender": "user",
                    "update_time": "2023-07-31 05:21:14.781730"
                }
            ]
        },
        {
            "conversation_id": 23,
            "message_list": [
                {
                    "content": "Hello, again for the 2-1",
                    "sender": "user",
                    "update_time": "2023-07-31 16:53:16"
                },
                {
                    "content": "Hello, this is a test chat message",
                    "sender": "user",
                    "update_time": "2023-07-31 21:24:40.578768"
                }
            ]
        }
    ]
    """
    request_ids = request.get_json()
    user_id = request_ids.get("user_id", -1)
    conversation_id_list = request_ids.get("conversation_id_list", [])
    if user_id <= 0 and not conversation_id_list:
        return jsonify({"error": "Incomplete request data"}), HTTP_400_BAD_REQUEST
    elif not isinstance(conversation_id_list, list):
        return jsonify({"error": "Invalid request data"}), HTTP_400_BAD_REQUEST

    history = ChatHistory.query.filter(
        ChatHistory.user_id == user_id,
        ChatHistory.conversation_id.in_(conversation_id_list),
    ).all()
    history.sort(key=lambda c: c.update_time)

    # Construct the response with mapped conversation_id dict
    dto_conversations = dict()
    for h in history:
        c_id = h.conversation_id
        cur = dto_conversations.get(c_id, DTOConversationMessage(c_id))
        cur.message_list.append(DTOMessage(chat_history=h))
        dto_conversations[c_id] = cur
    print(dto_conversations)
    response = list(dto_conversations.values())

    return jsonify(response)


def save_chat_history(chat_history):
    db.session.add(chat_history)
    db.session.commit()


@chat_bp.route("/user/<int:user_id>")
def get_user(user_id: int):
    '''
    Experiment get end-point just for testing
    :param user_id:
    :return:
    '''
    user = Users.query.get(user_id)
    delattr(user, 'password') # Patch the password to be None
    return jsonify(user)


@chat_bp.route("/get_response", methods=["post"])
def get_response():
    """
    conversation_id == 111 contains coherent test conversation

    Sample query:
    {
        "message": "Hi tell me a little about yourself",
        "user_id": 4,
        "robot_id": 8,
        "conversation_id": 111
    }

    :return:
    200 OK:
    {
        "response": "Hello! My name is Alex, and I'm a warm and caring individual..."
    }
    500 Error
    """
    data = request.get_json()
    message = data.get("message")
    user_id = data.get("user_id")
    robot_id = data.get("robot_id")
    conversation_id = data.get("conversation_id")

    # Personality retrieval
    robot_info = Robots.query.get(robot_id)
    if robot_info:
        robot_personality = robot_info.description
    else:
        return jsonify({"error": f"Robot id: {robot_id} not found"}), 404

    # tell chatGPT what role it takes on by assigning it "system"
    messages = [{"role": "system", "content": robot_personality}]

    history = ChatHistory.query.filter(
        ChatHistory.user_id == user_id,
        ChatHistory.conversation_id == conversation_id
    ).all()
    history.sort(key=lambda c: c.update_time)

    for h in history:
        role = "user"
        if h.is_robot:
            role = "assistant"
        messages.append({
            "role": role,
            "content": h.message
        })

    try:
        messages.append({
            "role": "user",
            "content": message
        })
        chat = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages
        )
        reply = chat.choices[0].message.content
    except Exception as e:
        print(e)
        return jsonify({"error": "Failed to get chatGPT response"}), 500

    user_message = ChatHistory(
        message=message,
        conversation_id=conversation_id,
        user_id=user_id,
        robot_id=robot_id,
        is_robot=False
    )

    robot_response = ChatHistory(
        message=reply,
        conversation_id=conversation_id,
        user_id=user_id,
        robot_id=robot_id,
        is_robot=True
    )

    try:
        db.session.add(user_message)
        db.session.add(robot_response)
    except Exception as e:
        print(e)
        db.session.rollback()
        return jsonify({"error": "Failed to store user message or response, please try again"}), 500
    else:
        db.session.commit()
        return jsonify({"response": reply}), 200
      
      
      
      
@chat_bp.route("/rooms/get_history")
def get_rooms_history():
    '''
    Sample request body json:
    {
        "user_id": 2,
        "conversation_id_list": [
            23
            ,22
        ]
    }

    :return:
    [
        {
            "conversation_id": 22,
            "message_list": [
                {
                    "content": "Hello, this is a new chat message",
                    "sender": "robot",
                    "update_time": "2023-07-31 05:21:04.574198"
                },
                {
                    "content": "Hello, this is a new user chat message",
                    "sender": "user",
                    "update_time": "2023-07-31 05:21:14.781730"
                }
            ]
        },
        {
            "conversation_id": 23,
            "message_list": [
                {
                    "content": "Hello, again for the 2-1",
                    "sender": "user",
                    "update_time": "2023-07-31 16:53:16"
                },
                {
                    "content": "Hello, this is a test chat message",
                    "sender": "user",
                    "update_time": "2023-07-31 21:24:40.578768"
                }
            ]
        }
    ]
    '''
    request_ids = request.get_json()
    user_id = request_ids.get('user_id', -1)
    conversation_id_list = request_ids.get('conversation_id_list', [])
    if user_id <= 0 and not conversation_id_list:
        return jsonify({"error": "Incomplete request data"}), 400
    elif not isinstance(conversation_id_list, list):
        return jsonify({"error": "Invalid request data"}), 400

    history = ChatHistory.query.filter(
        ChatHistory.user_id == user_id,
        ChatHistory.conversation_id.in_(conversation_id_list)
    ).all()
    history.sort(key=lambda c: c.update_time)

    # Construct the response with mapped conversation_id dict
    dto_conversations = dict()
    for h in history:
        c_id = h.conversation_id
        cur = dto_conversations.get(c_id, DTOConversationMessage(c_id))
        cur.message_list.append(DTOMessage(
            chat_history=h
        ))
        dto_conversations[c_id] = cur
    print(dto_conversations)
    response = list(dto_conversations.values())


    return jsonify(response)

