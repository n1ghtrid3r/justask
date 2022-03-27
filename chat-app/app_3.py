from flask import Flask, render_template, request, redirect, url_for, session
from flask_session import Session
from flask_socketio import SocketIO, join_room, leave_room
import sqlite3
from datetime import datetime
from flask_classful import FlaskView, route
from flask import Response
import os

# app = Flask(__name__)
# socketio = SocketIO(app)

# def insert_data(command_SQL, data):
#     cursor.execute(command_SQL, data)
#     connection.commit()

# def search_data( command_SQL, data):
#     return cursor.execute(command_SQL, data).fetchall()

    

class JustAsk(FlaskView):
    default_methods = ['GET', 'POST']
    route_base = "/"
    
    def __init__(self):
        pass

    def create_app(self, dbname):
        self.app = Flask(__name__)
        self.socketio = SocketIO(self.app)

        self.app.config["SESSION_PERMANENT"] = False
        self.app.config["SESSION_TYPE"] = "filesystem"
        Session(self.app)

        self.socketio.on_event("send_message", self.handle_send_message_event)
        self.socketio.on_event("join_room", self.handle_join_room_event)
        self.socketio.on_event("leave_room", self.handle_leave_room_event)
        self.socketio.on_event("clientmsg", self.handle_my_custom_event)
        
        self.connection, self.cursor = self.connect_db(dbname)
        
        JustAsk.register(self.app)


    def start_app(self):
        self.socketio.run(self.app)


    def connect_db(self, dbName):
        CLIENT_SQL_INJECTION = """
        CREATE TABLE IF NOT EXISTS users (
            email TEXT NOT NULL PRIMARY KEY,
            username TEXT NOT NULL,
            firstname TEXT NOT NULL,
            lastname TEXT NOT NULL,
            password TEXT NOT NULL,
            active_session TEXT NOT NULL);
        """
        connection = sqlite3.connect(dbName, check_same_thread=False)
        cursor = connection.cursor()
        cursor.execute(CLIENT_SQL_INJECTION)
        connection.commit()
        return connection, cursor     

    def disconnect(self):
        self.cursor.close()
        self.connection.close()

    def insert_data(self, command_SQL, data):
        self.cursor.execute(command_SQL, data)
        self.connection.commit()

    def search_data(self, command_SQL, data):
        return self.cursor.execute(command_SQL, data).fetchall()

    @route("/landingpage", endpoint="landingpage")
    @route("/", endpoint="landingpage")
    def landingpage(self):
        return render_template("landingpage.html")

    # @route("/", endpoint="/")
    @route("/profile", endpoint="profile",methods=["GET", "POST"])
    def profile(self):
        # If no user session, redirect to login page. Else render the user profile page.
        if not session.get("email"):
            return redirect("/login")
        return render_template("profile.html")

    @route("/", endpoint="/")
    @route("/login/", endpoint="login", methods=['POST', 'GET'])
    def login(self):
        if request.method == "GET":
            return render_template("landingpage.html")

        # Get user login details
        email = request.form.get("email")
        password = request.form.get("password")

        # Validate submission
        login_details = [email, password]
        for field in login_details:
            if not field:
                #todo handle this
                return render_template("login.html")
        # If the user provided details stored in the database, add these details to the session, 
        # and send them to their profile page
        user = self.search_data("SELECT * FROM users WHERE email= ? AND password = ?",(email, password))[0]
        print(user)
        if  user == None:
            #todo handle this. Invalid login credentials.
            print("INVALID LOGIN CREDENTIALS")
            return render_template("landingpage.html")
            # return render_template("landingpage.html")

        session["email"] = user[0]
        session["username"] = user[1]
        session["firstname"] = user[2]
        session["lastname"] = user[3]
        session["password"] = user[4]
        session["active_session"] = ""

        return redirect("/profile")

    @route("/registration/",endpoint="registration", methods = ["GET", "POST"])
    def registration(self):
        if request.method == "GET":
            return render_template("registration.html")

        # Get user submission
        email = request.form.get("email")
        username = request.form.get("username")
        first_name = request.form.get("firstname")
        last_name = request.form.get("lastname")
        password = request.form.get("password")
        active_session = "0"

        data = [email, username,first_name,last_name,password, active_session]
        for field in data:
            if not field:
                #todo handle this
                return render_template("404.html")


        # If the user provided valid info, and they were not already registered, store data in database
        email_present = self.cursor.execute("SELECT * FROM users WHERE email= ?", (email,)).fetchall()
        if email_present != []:
            #todo handle this. User is already registered.
            return render_template("userexists.html")

        
        self.insert_data("INSERT INTO users VALUES (?,?,?,?,?,?)", data)

        # maybe we should have a registration succesful page, that can then link to the login?
        return redirect("/login")

    @route("/chat_logout/", endpoint="chat_logout")
    def chat_logout(self):
        session["room"] = None
        return redirect("/newsession")

    @route("/logout", endpoint="logout")
    def logout():
        session["email"] = None
        return redirect("/login")

    @route("/joinsession", endpoint="joinsession", methods = ["GET", "POST"])
    def joinsession(self):
        # need to validate the session id string.
        if request.method == "GET":
            return render_template("joinsession.html")

        # get the room id from the form.
        roomID = request.form.get("room")

        # clients = cursor.execute("SELECT * FROM users WHERE username = ?",("jas",)).fetchall()

        matchingRoomClients = self.search_data("SELECT * FROM users WHERE active_session= ?", (roomID,))
        # if the room ID does not exist among any other user, then we cannot join the session.
        if matchingRoomClients == []:
            return "room id does not exist"

        session["active_session"] = roomID

        self.insert_data("UPDATE users SET active_session = ? WHERE username = ?", (roomID, session["username"]))
        print("UPDATED")

        # ???
        # cursor.execute('''SELECT active_session FROM users WHERE username=?''', (session["username"],))

        return redirect(url_for("chat"))

    @route("/newsession", endpoint="newsession")
    def newsession(self):
        if request.method == "GET":
            return render_template("newsession.html")


    @route("/chat", endpoint="chat")
    def chat(self):
        username = session.get('username')
        room = session.get('active_session')
        if username and room:
            return render_template('chat.html', username=username, room=room)
        else:
            return redirect(url_for('newsession'))

    def handle_send_message_event(self,data):
        self.app.logger.info("{} has sent message to the room {}: {}".format(data['username'],
                                                                        data['room'],
                                                                        data['message']))
        data["time"] = datetime.now().strftime("%H:%M")                                                               
        self.socketio.emit('receive_message',data, room=data['room'])

    def handle_join_room_event(self,data):
        self.app.logger.info("{} has joined the room {}".format(data['username'], data['room']))
        join_room(data['room'])
        data["time"] = datetime.now().strftime("[%H:%M]")
        self.socketio.emit('join_room_announcement',data, room=data['room'])

    def handle_leave_room_event(self,data):
        self.app.logger.info("{} has left the room {}".format(data['username'], data['room']))
        leave_room(data['room'])
        self.socketio.emit('leave_room_announcement', data, room=data['room'])

    @route('/sketchpad', endpoint="sketchpad")
    def sessions(self):
        return render_template('sketchpad.html')
    
    @route('/MCQ', endpoint="MCQ")
    def mcq(self):
        return render_template('MCQ.html')

    def messageReceived(self,methods=['GET', 'POST']):
        print('message was received!!!')

    def handle_my_custom_event(self,json, methods=['GET', 'POST']):
        print('received my event: ' + str(json))
        self.socketio.emit('servermsg', json, callback=self.messageReceived)

if __name__ == '__main__':
    application = JustAsk()
    application.create_app("clients.db")
    application.start_app()