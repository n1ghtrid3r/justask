from multiprocessing.connection import Client
from flask import render_template, request, redirect, url_for, session, flash
from flask_session import Session
from flask_classful import FlaskView, route
from Client import ClientModel
from Utility import Utility
from SharedContext import *
from Client import ClientAttribute



class JustAskHTTPServer(FlaskView):
    
    default_methods = ['GET', 'POST']
    route_base = "/"

    def __init__(self):
        super().__init__()

        db.create_all()
        app.config["SESSION_PERMANENT"] = False
        app.config["SESSION_TYPE"] = "filesystem"
        Session(app)

    def UpdateSessionInformation(self, client_attribute, arg, updateDB = False, auto_commit = True):
        client_attribute = ClientAttribute(client_attribute)
        session[client_attribute.name] = arg

        if updateDB:
            # if we just replaced the username in our session, perform search by email.
            SEARCH_PRED = ClientAttribute(ClientAttribute.EMAIL if client_attribute == ClientAttribute.USERNAME else ClientAttribute.USERNAME)
            current_user = ClientModel.query.filter_by(**{SEARCH_PRED.name : session[SEARCH_PRED.name]}).first()
            setattr(current_user, client_attribute.name, arg)
            if auto_commit: db.session.commit()

    def GetUser(self, client_attributes):
        return ClientModel.query.filter_by(**client_attributes).first()

    def GetSessionInformation(self, client_attribute):
        return session[ClientAttribute(client_attribute).name]

    # This should be on SocketServer.py
    def KickUser(self, username):
        user = self.GetUser({ClientAttribute.USERNAME.name : username})
        if user is not None:
            user.ACTIVE_SESSION = ""
            user.ADMIN = 0
            
        return redirect("/profile")
    
    def IsUserLoggedIn(self):
        return session
    
    def CreateUser(self, user_information):
        user = ClientModel(**user_information)
        db.session.add(user)
        db.session.commit()
        return user

    def UserExists(self, username, email):
        return ClientModel.query.filter_by(EMAIL = email).first() != None or ClientModel.query.filter_by(USERNAME = username).first() != None

    @route("/signout", endpoint="signout")
    def ROUTE_SIGNOUT(self):
        if self.IsUserLoggedIn():
            if session["ACTIVE_SESSION"]: self.UpdateSessionInformation(ClientAttribute.ACTIVE_SESSION, "", updateDB=True)
            session.clear()
        return redirect("/landingpage")

    @route("/landingpage", endpoint="landingpage")
    @route("/", endpoint="landingpage")
    def ROUTE_LANDING_PAGE(self):
        return redirect("profile") if self.IsUserLoggedIn() else render_template("landingpage.html")

    @route("/leave_session", endpoint="leave_session",methods=["POST", "GET"])
    def ROUTE_LEAVE_SESSION(self):
        if request.method == "GET" and not self.IsUserLoggedIn(): return redirect("landingpage")
        if session["ACTIVE_SESSION"]: self.UpdateSessionInformation(ClientAttribute.ACTIVE_SESSION, "", updateDB=True)
        return redirect("/session")

    def PROFILE_CHANGE_ASSIGNMENT(self, change_exists, client_attribute, form_input, default):
        if change_exists:
            self.UpdateSessionInformation(client_attribute, form_input, updateDB=True) 
            return form_input
        return default

    def CHANGE_PERSONAL_INFORMATION(self, default_args):
        form_firstname = request.form.get("firstname")
        form_lastname = request.form.get("lastname")
        form_aboutme =  request.form.get("about-me-text-edit")

        default_args["FIRSTNAME_EXISTS"] = bool(form_firstname)
        default_args["LASTNAME_EXISTS"] = bool(form_lastname)
        default_args["ABOUTME_EXISTS"] = bool(form_aboutme)

        default_args[ClientAttribute.FIRSTNAME.name] = self.PROFILE_CHANGE_ASSIGNMENT(default_args["FIRSTNAME_EXISTS"], ClientAttribute.FIRSTNAME, form_firstname, default_args[ClientAttribute.FIRSTNAME.name])
        default_args[ClientAttribute.LASTNAME.name] = self.PROFILE_CHANGE_ASSIGNMENT(default_args["LASTNAME_EXISTS"], ClientAttribute.LASTNAME, form_lastname, default_args[ClientAttribute.LASTNAME.name])
        default_args[ClientAttribute.ABOUT_ME.name] = self.PROFILE_CHANGE_ASSIGNMENT(default_args["ABOUTME_EXISTS"], ClientAttribute.ABOUT_ME, form_aboutme, default_args[ClientAttribute.ABOUT_ME.name])

        return default_args
        
    def CHANGE_LOGIN_INFORMATION(self, default_args):
        #print("CHANGING PROFILE INFORMATION")
        form_username = request.form.get("username")
        form_email = request.form.get("email")

        # I don't understand why these need to be stored
        # The change I made is: If a change happened, then existence is true otherwise its false
        default_args["USERNAME_EXISTS"] = bool(form_username) and ClientModel.query.filter_by(USERNAME = form_username).all() == []
        default_args["EMAIL_EXISTS"] = bool(form_email) and ClientModel.query.filter_by(EMAIL = form_email).all() == [] and Utility.IsEmailAddress(form_email)
        
        default_args[ClientAttribute.USERNAME.name] = self.PROFILE_CHANGE_ASSIGNMENT(default_args["USERNAME_EXISTS"], ClientAttribute.USERNAME, form_username, default_args[ClientAttribute.USERNAME.name])
        default_args[ClientAttribute.EMAIL.name] = self.PROFILE_CHANGE_ASSIGNMENT(default_args["EMAIL_EXISTS"], ClientAttribute.EMAIL, form_email, default_args[ClientAttribute.EMAIL.name])
        return default_args

    def CHANGE_MEDIA_INFORMATION(self, default_args):
        #print("CHANGING PROFILE INFORMATION")
        form_instagram = request.form.get("instagram")
        form_facebook = request.form.get("facebook")
        form_twitter = request.form.get("twitter")
        form_linkedin = request.form.get("linkedin")

        # I don't understand why these need to be stored
        # The change I made is: If a change happened, then existence is true otherwise its false
        default_args["INSTAGRAM_EXISTS"] = bool(form_instagram)
        default_args["FACEBOOK_EXISTS"] = bool(form_facebook)
        default_args["TWITTER_EXISTS"] = bool(form_twitter)
        default_args["LINKEDIN_EXISTS"] = bool(form_linkedin)
        
        default_args[ClientAttribute.INSTAGRAM_PAGE.name] = self.PROFILE_CHANGE_ASSIGNMENT(default_args["INSTAGRAM_EXISTS"], ClientAttribute.INSTAGRAM_PAGE, form_instagram, default_args[ClientAttribute.INSTAGRAM_PAGE.name])
        default_args[ClientAttribute.FACEBOOK_PAGE.name] = self.PROFILE_CHANGE_ASSIGNMENT(default_args["FACEBOOK_EXISTS"], ClientAttribute.FACEBOOK_PAGE, form_facebook, default_args[ClientAttribute.FACEBOOK_PAGE.name])
        default_args[ClientAttribute.TWITTER_PAGE.name] = self.PROFILE_CHANGE_ASSIGNMENT(default_args["TWITTER_EXISTS"], ClientAttribute.TWITTER_PAGE, form_twitter, default_args[ClientAttribute.TWITTER_PAGE.name])
        default_args[ClientAttribute.LINKEDIN_PAGE.name] = self.PROFILE_CHANGE_ASSIGNMENT(default_args["LINKEDIN_EXISTS"], ClientAttribute.LINKEDIN_PAGE, form_linkedin, default_args[ClientAttribute.LINKEDIN_PAGE.name])

        return default_args
    
    def CHANGE_PASSWORD_INFORMATION(self, default_args):
        old_password = Utility.EncryptSHA256(request.form.get("old_password"))
        new_password = request.form.get("new_password")
        new_password_confirm = request.form.get("new_password_confirm")
        # check if old password entry matches password in db.
        if new_password != new_password_confirm:
            return default_args

        if old_password != self.GetSessionInformation(ClientAttribute.PASSWORD):
            return default_args
        
        if not Utility.IsStrongPassword(new_password):
            return default_args

        new_password = Utility.EncryptSHA256(new_password)
        self.UpdateSessionInformation(ClientAttribute.PASSWORD, new_password, updateDB=True)
        default_args[ClientAttribute.PASSWORD.name] = new_password
        return default_args
    
    def CHANGE_ABOUTME_INFORMATION(self, default_args):
        print("ok")
        default_args[ClientAttribute.ABOUT_ME.name] = self.PROFILE_CHANGE_ASSIGNMENT(True, ClientAttribute.ABOUT_ME, request.form.get("about-me-text-edit"), default_args[ClientAttribute.ABOUT_ME.name])

        return default_args


    @route("/profile", endpoint="profile",methods=["GET", "POST"])
    def ROUTE_PROFILE(self):
        default_args = {key.name : session[key.name] for key in ClientAttribute}
        if request.method == "GET":
            if not self.IsUserLoggedIn(): return render_template("landingpage.html")
            return render_template("profile.html", **default_args)
        

        if "personal-information-submit" in request.form:
            default_args = self.CHANGE_PERSONAL_INFORMATION(default_args)
        elif "login-information-submit" in request.form:
            default_args = self.CHANGE_LOGIN_INFORMATION(default_args)
        elif "password-information-submit" in request.form:
            default_args = self.CHANGE_PASSWORD_INFORMATION(default_args)
        elif "social-media-information-submit" in request.form:
            default_args = self.CHANGE_MEDIA_INFORMATION(default_args)
    
        try: db.session.commit()
        except Exception as e: print(e)
        return render_template("profile.html", **default_args)
    
    def LOGIN_CONFIRMATION(self, user):
        self.UpdateSessionInformation(ClientAttribute.EMAIL, user.EMAIL)
        self.UpdateSessionInformation(ClientAttribute.USERNAME, user.USERNAME)
        self.UpdateSessionInformation(ClientAttribute.FIRSTNAME, user.FIRSTNAME)
        self.UpdateSessionInformation(ClientAttribute.LASTNAME, user.LASTNAME)
        self.UpdateSessionInformation(ClientAttribute.PASSWORD, user.PASSWORD)
        self.UpdateSessionInformation(ClientAttribute.ACTIVE_SESSION, user.ACTIVE_SESSION)
        self.UpdateSessionInformation(ClientAttribute.ADMIN, user.ADMIN)
        
        self.UpdateSessionInformation(ClientAttribute.PROFILE_PICTURE, user.PROFILE_PICTURE)
        self.UpdateSessionInformation(ClientAttribute.INSTAGRAM_PAGE, user.INSTAGRAM_PAGE)
        self.UpdateSessionInformation(ClientAttribute.FACEBOOK_PAGE, user.FACEBOOK_PAGE)
        self.UpdateSessionInformation(ClientAttribute.LINKEDIN_PAGE, user.LINKEDIN_PAGE)
        self.UpdateSessionInformation(ClientAttribute.TWITTER_PAGE, user.TWITTER_PAGE)
        self.UpdateSessionInformation(ClientAttribute.ABOUT_ME, user.ABOUT_ME)
        self.UpdateSessionInformation(ClientAttribute.ANONYMOUS, user.ANONYMOUS)

        return redirect("/profile")

    @route("/", endpoint="/")
    @route("/login/", endpoint="login", methods=['POST', 'GET'])
    def ROUTE_LOGIN(self):
        if request.method == "GET" and not self.IsUserLoggedIn(): return redirect("landingpage")
        form_email = request.form.get("email")
        form_password = request.form.get("password")
        form_fields = [form_email, form_password]
        user = self.GetUser({ClientAttribute.EMAIL.name : form_email, ClientAttribute.PASSWORD.name : Utility.EncryptSHA256(form_password)})
        if not self.LOGIN_VALIDATION(form_fields, user == None):
            return render_template("landingpage.html")
        return self.LOGIN_CONFIRMATION(user)


    @route("/registration/",endpoint="registration", methods = ["GET", "POST"])
    def ROUTE_REGISTRATION(self):
        if self.IsUserLoggedIn() and request.method == "GET": return redirect("/profile")
        new_user_details = {
            ClientAttribute.EMAIL.name : request.form.get("email"), 
            ClientAttribute.USERNAME.name : request.form.get("username"), 
            ClientAttribute.FIRSTNAME.name : request.form.get("firstname"), 
            ClientAttribute.LASTNAME.name : request.form.get("lastname"), 
            ClientAttribute.PASSWORD.name : request.form.get("password"),
            ClientAttribute.ACTIVE_SESSION.name : "",
            ClientAttribute.ADMIN.name : 0,
            ClientAttribute.PROFILE_PICTURE.name : "",
            ClientAttribute.INSTAGRAM_PAGE.name : "",
            ClientAttribute.FACEBOOK_PAGE.name : "",
            ClientAttribute.TWITTER_PAGE.name : "",
            ClientAttribute.LINKEDIN_PAGE.name : "",
            ClientAttribute.ABOUT_ME.name : "",
            ClientAttribute.ANONYMOUS.name : False
            }
            
        test_list = [
            new_user_details[ClientAttribute.EMAIL.name], 
            new_user_details[ClientAttribute.USERNAME.name], 
            new_user_details[ClientAttribute.FIRSTNAME.name], 
            new_user_details[ClientAttribute.LASTNAME.name], 
            new_user_details[ClientAttribute.PASSWORD.name]
        ]
        user_exists = self.UserExists(username=new_user_details[ClientAttribute.USERNAME.name], email=new_user_details[ClientAttribute.EMAIL.name])
        if not self.REGISTERATION_VALIDATION(test_list, user_exists, new_user_details[ClientAttribute.EMAIL.name], new_user_details[ClientAttribute.PASSWORD.name]):
            return redirect("/landingpage") 
        
        new_user_details[ClientAttribute.PASSWORD.name] = Utility.EncryptSHA256(new_user_details[ClientAttribute.PASSWORD.name])
        user = self.CreateUser(new_user_details)
        return self.LOGIN_CONFIRMATION(user)

    @route("/session", endpoint="session", methods=["GET", "POST"])
    def ROUTE_MANAGE_SESSIONS(self):
        if request.method == "POST":
            roomID = request.form.get("room")
            isAnon = session["ANONYMOUS"]
            matchingRoomClients = ClientModel.query.filter_by(ACTIVE_SESSION = roomID).all()
            
            if "joinsession" in request.form:
                matchingRoomClients = ClientModel.query.filter_by(ACTIVE_SESSION = roomID).all()
                
                if request.form.get("isAnon") == "anon":
                    isAnon = True
                else:
                    isAnon = False
                    
                if matchingRoomClients == []:
                    # todo make this nicer 
                    flash('Chatroom does not exist')
                    return redirect(url_for("session"))
            elif "createsession" in request.form:
                if matchingRoomClients != []:
                    # todo make this nicer
                    flash('Session id already exists')
                    return redirect(url_for("session"))

            self.UpdateSessionInformation(ClientAttribute.ACTIVE_SESSION, roomID, updateDB=True)
            self.UpdateSessionInformation(ClientAttribute.ANONYMOUS, isAnon, updateDB=True)
        return redirect(url_for("chat"))

    @route("/chat", endpoint="chat",methods=["GET"])
    def ROUTE_CHAT_SYSTEM(self):
        if not self.IsUserLoggedIn(): return redirect("landingpage")
        username = self.GetSessionInformation(ClientAttribute.USERNAME)
        active_session = self.GetSessionInformation(ClientAttribute.ACTIVE_SESSION)
        if active_session: return render_template("chat.html", username=username, room=active_session)
        return render_template("session.html")

    @route("/sketchpad", endpoint="sketchpad", methods=["GET", "POST"])
    def ROUTE_SKETCHPAD(self):
        if request.method == "GET" and not self.IsUserLoggedIn(): return redirect("landingpage")
        if request.method == "GET": return render_template("sketchpad.html")
    
    @route("/mcq", endpoint="mcq", methods=['POST', 'GET'])
    def ROUTE_MCQ(self):
        if request.method == "GET" and not self.IsUserLoggedIn(): return redirect("landingpage")
        username = self.GetSessionInformation(ClientAttribute.USERNAME)
        active_session = self.GetSessionInformation(ClientAttribute.ACTIVE_SESSION)
        if active_session: return render_template("mcq.html", username=username, room=active_session)
        return render_template("session.html")

    def LOGIN_VALIDATION(self, fields, invalid_existence_status):
        if self.EMPTY_FIELDS_CHECK(fields):
            # Print a message or return an indicator
            return False
        if invalid_existence_status:
            # Print a message or return an indicator
            return False
        return True
    
    def REGISTERATION_VALIDATION(self, fields, invalid_existence_status, email, password):
        if not self.LOGIN_VALIDATION(fields, invalid_existence_status):
            return False
        if not Utility.IsEmailAddress(email):
             # Print a message or return an indicator
            return False
        if not Utility.IsStrongPassword(password):
             # Print a message or return an indicator
            return False
        return True

    def EMPTY_FIELDS_CHECK(self, fields):
        for field in fields:
            if not field:
                return True
        return False


