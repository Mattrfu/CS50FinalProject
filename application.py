import os

#export API_KEY=pk_dfdca7bddc384ef799f0b69eea6622c7
#http://64576243-034a-403a-97d7-83cc427ffe06-ide.cs50.xyz/login


from datetime import datetime
from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///attendance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")

@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    #The index function displays the index page when a user is logged in.
    lastLogin = db.execute("SELECT lastlogin FROM users WHERE id=:user_id", user_id = session["user_id"])[0]["lastlogin"]
    position = db.execute("SELECT position FROM users WHERE id=:user_id", user_id = session["user_id"])[0]["position"]
    hours = db.execute("SELECT hours FROM users WHERE id=:user_id", user_id = session["user_id"])[0]["hours"]
    minutes = db.execute("SELECT minutes FROM users WHERE id=:user_id", user_id = session["user_id"])[0]["minutes"]
    #approved = db.execute("SELECT approved FROM users WHERE id=:user_id", user_id = session["user_id"])[0]["approved"]
    if request.method == "GET":
        #DISPLAY PAGE
        if position == "admin":
            return redirect("/confirmation")
        else:
            if lastLogin is not None:
                #!! Since lastlogin is an id, we're going to pass in the time stamp of last login to the html to be more user-friendly !!
                lastLoginTS = db.execute("SELECT LITimeStamp FROM checks WHERE id=:lastLogin", lastLogin=lastLogin)[0]["LITimeStamp"]
                return render_template("checkout.html", HOURS=hours, MINUTES=minutes, LASTLOGIN=lastLoginTS)
            #Need to checkin, just logged in, set up a check in page but not record anything
            return render_template("checkin.html", HOURS=hours, MINUTES=minutes)
    #If the method passed was post, that means the checkIn or checkOut button hit.
    if request.method == "POST":
        #ACTION CODE then return to appropriate display page
        if lastLogin is not None:
            #Need to checkout, CHECKOUT CODE
            db.execute("UPDATE checks SET LOTimeStamp=:LOTimeStamp WHERE id=:lastLogin", LOTimeStamp=datetime.now(), lastLogin=lastLogin)
            db.execute("UPDATE users SET lastlogin=:lastlogin WHERE id=:user_id", lastlogin=None, user_id=session["user_id"])
            return redirect("/")
        #CHECK IN CODE
        db.execute("INSERT INTO checks (user_id, LITimeStamp) VALUES (:user_id, :LITimeStamp)", user_id = session["user_id"], LITimeStamp = datetime.now())
        LIid = db.execute("SELECT id FROM checks WHERE user_id=:user_id GROUP BY user_id", user_id=session["user_id"])[0]["id"]
        db.execute("UPDATE users SET lastlogin=:lastlogin WHERE id=:user_id", lastlogin=LIid, user_id=session["user_id"])
        #db.execute("UPDATE users SET approved=:temp WHERE id=:user_id", temp=False)
        return redirect("/")

#If there is an error, an user-friendly apology is thrown.
def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)

#This function is based on the one in the Finance project. This function allows users to log in to their account.
#similar to CS50's finance website
@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

#from CS50 Finance project
@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    db.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, username TEXT NOT NULL, hash TEXT NOT NULL, hours INTEGER NOT NULL, minutes INTEGER NOT NULL, subteam TEXT, position TEXT, lastlogin INTEGER, approved BOOLEAN)")
    db.execute("CREATE TABLE IF NOT EXISTS checks (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, user_id INTEGER NOT NULL, LITimeStamp TIMESTAMP, LOTimeStamp TIMESTAMP, approved BOOLEAN, hours INTEGER, minutes INTEGER)")

    #display registration form on get
    if request.method == "GET":
        return render_template("register.html")

    #insert new user into users table
    if request.method == "POST":
        username = request.form.get("username")
        confirmation = request.form.get("confirmation")
        password = request.form.get("password")
        if password != confirmation:
            return apology("Your passwords must match.", 403)
        for name in db.execute("SELECT username FROM users"):
            if name["username"] == username:
                return apology("Your username already exists.", 403)

        # Ensure password is strong enough
        chars = set('!?*<>,.:()[]')
        nums = set('1234567890')
        if((len(password) < 8)):
            return apology("password must be at least length 8")

        if not any(c in chars for c in password):
            return apology("password must have some symbol (!,?,*,<,>,(,),[,],,,.,:)")

        if not any(n in nums for n in password):
            return apology("password must have some number (1,2,3,4,5,5,6,7,8,9,0)")


        #do it in a way safely
        phash = generate_password_hash(password)
        if len(db.execute("SELECT * FROM users")) == 0:
            db.execute("INSERT INTO users (username, hash, hours, minutes, position, subteam) VALUES (:username, :phash, 0, 0, :pos, :subteam)", username=username, phash=phash, pos="admin", subteam="admin")
        else:
            db.execute("INSERT INTO users (username, hash, hours, minutes, position, subteam) VALUES (:username, :phash, 0, 0, :pos, :subteam)", username=username, phash=phash, pos="student", subteam="noSubteam")
    return redirect("/")

#This allows the user to change user information in the users table.
@app.route("/changeAccountInfo", methods=["GET", "POST"])
@login_required
def changeAccountInfo():
    if request.method == "GET":
        return render_template("changeAccountInfo.html")
    if request.method == "POST":
        #obtain information from forms
        username = request.form.get("username")
        confirmation = request.form.get("confirmation")
        password = request.form.get("password")
        #password checks
        if password != confirmation:
            return apology("Your passwords must match.", 403)
        if password == None:
            return apology("Your password cannot be empty.", 403)
        phash = generate_password_hash(password)
        db.execute("UPDATE users SET hash=:phash, username=:username WHERE id=:unique_id", phash=phash, username=username, unique_id=session["user_id"])
        #ADD A ALERT THAT SAYS ACCOUNT INFORMATION SUCCESSFULLY CHANGED
    return redirect("/")

#This function displays the history of yourself if you are a student and everyone on the team if you are an admin. It also gives an opportunity to delete entries if needed.
@app.route("/history", methods=["GET", "POST"])
@login_required
def history():
    if request.method == "GET":
        #Gets the position of the user
        position = db.execute("Select position FROM users WHERE id = :user_id", user_id = session["user_id"])
        pos = position[0]["position"]
        #Gets personal history
        database = db.execute("SELECT * FROM checks WHERE user_id = :user_id", user_id = session["user_id"])
        #turns personal history into a dictionary that can be used in html
        myList = []
        for row in database:
            LITimeStamp = row["LITimeStamp"]
            LOTimeStamp = row["LOTimeStamp"]
            approved = row["approved"]
            if LOTimeStamp is not None:
                hoursPlus = row["hours"]
                minutesPlus = row["minutes"]
                temp = {
                    "LITime": LITimeStamp,
                    "LOTime": LOTimeStamp,
                    "Hours": hoursPlus,
                    "Minutes": minutesPlus,
                    "approved": approved
                }
                #Appends the dictionary to a list that can be used in HTML
                myList.append(temp)
                #print(myList)

        #Prepares the return data
        returnData = db.execute("SELECT username, subteam FROM users WHERE id = :user_id", user_id = session["user_id"])
        #Prepares a list of usernames for admin history
        usernames = db.execute("SELECT username FROM users")
        #Check if the user's position is admin
        if pos == "admin":
            #Return adminHistory template with ncessary information
            username = returnData[0]["username"]
            subteamList = db.execute("Select * FROM users WHERE subteam = :user_subteam", user_subteam = returnData[0]["subteam"])
            return render_template("adminHistory.html", USERNAME = returnData[0]["username"], SUBTEAM = returnData[0]["subteam"], rows = myList, usernames = usernames)
        #Check if the user's position is subteam leader
        elif pos == "subteamLeader":
            #Returns necessary information for subteam leader
            username = returnData[0]["username"]
            subteamList = db.execute("Select * FROM users WHERE subteam = :user_subteam", user_subteam = returnData[0]["subteam"])
            return render_template("adminHistory.html", USERNAME = returnData[0]["username"], SUBTEAM = returnData[0]["subteam"], rows = myList)
        #Else in case the position is student
        else:
            #Returns personal history.
            return render_template("history.html", USERNAME = returnData[0]["username"], SUBTEAM = returnData[0]["subteam"], rows = myList)

    #If the post method is pressed
    else:
        #Checks to see if editmode is selected
        editMode = request.form.get('editMode')
        if editMode:
            #Gets the username of the edit
            currentUsername = request.form.get("username")
            if currentUsername == "Select Username":
                return apology("missing username selection", 400)
            #Gets the id of user you are looking at
            currentID = db.execute("Select id FROM users WHERE username = :username", username = currentUsername)
            currentID = currentID[0]["id"]
            #Gets the position of the user you are looking at.
            position = db.execute("Select position FROM users WHERE id = :user_id", user_id = currentID)
            pos = position[0]["position"]
            #Gets the necessary history information
            database = db.execute("SELECT * FROM checks WHERE user_id = :user_id", user_id = currentID)
            myList = []
            for row in database:
                #Gets login time
                LITimeStamp = row["LITimeStamp"]
                #Gets logout time
                LOTimeStamp = row["LOTimeStamp"]
                approved = row["approved"]
                #As long as the log out has occured, create a dictionary
                if LOTimeStamp is not None:
                    hoursPlus = row["hours"]
                    minutesPlus = row["minutes"]
                    checkID = "delete"+str(row["id"])
                    print(checkID)
                    #Dictionary as needed with all information.
                    temp = {
                        "LITime": LITimeStamp,
                        "LOTime": LOTimeStamp,
                        "Hours": hoursPlus,
                        "Minutes": minutesPlus,
                        "approved": approved,
                        "id": checkID
                    }
                    #Add dictionary to the list
                    myList.append(temp)
            #Gets neceesary return data
            returnData = db.execute("SELECT username, subteam FROM users WHERE id = :user_id", user_id = currentID)
            position1 = db.execute("Select position FROM users WHERE id = :user_id", user_id = session["user_id"])
            pos1 = position1[0]["position"]
            #checks position of the logged in user. If admin, submits items.
            if pos1 == "admin":
                username = returnData[0]["username"]
                subteamList = db.execute("Select * FROM users WHERE subteam = :user_subteam", user_subteam = returnData[0]["subteam"])
                return render_template("deleteHistory.html", USERNAME = returnData[0]["username"], SUBTEAM = returnData[0]["subteam"], rows = myList)
            else:
                return render_template("history.html", USERNAME = returnData[0]["username"], SUBTEAM = returnData[0]["subteam"], rows = myList)
        else:
            #Otherwise simply gives history of the person.
            currentUsername = request.form.get("username")
            if currentUsername == "Select Username":
                return apology("not in edit mode", 400)
            #Gets the id of the person you are looking at
            currentID = db.execute("Select id FROM users WHERE username = :username", username = currentUsername)
            currentID = currentID[0]["id"]
            position = db.execute("Select position FROM users WHERE id = :user_id", user_id = currentID)
            pos = position[0]["position"]
            #Gets necessary history from that person's id
            database = db.execute("SELECT * FROM checks WHERE user_id = :user_id", user_id = currentID)
            myList = []
            for row in database:
                #Gets login/logout time
                LITimeStamp = row["LITimeStamp"]
                LOTimeStamp = row["LOTimeStamp"]
                approved = row["approved"]
                #Ensures that person has logged out of timestamp before including it in history
                if LOTimeStamp is not None:
                    hoursPlus = row["hours"]
                    minutesPlus = row["minutes"]
                    #Cretes a dictionary
                    temp = {
                        "LITime": LITimeStamp,
                        "LOTime": LOTimeStamp,
                        "Hours": hoursPlus,
                        "Minutes": minutesPlus,
                        "approved": approved
                    }
                    myList.append(temp)
            #Get necessary return data
            usernames = db.execute("SELECT username FROM users")
            returnData = db.execute("SELECT username, subteam FROM users WHERE id = :user_id", user_id = currentID)
            #Check position of logged in user
            position1 = db.execute("Select position FROM users WHERE id = :user_id", user_id = session["user_id"])
            pos1 = position1[0]["position"]
            #Returns different items depending on the psoition of the user.
            #If admin, returns full
            if pos1 == "admin":
                username = returnData[0]["username"]
                subteamList = db.execute("Select * FROM users WHERE subteam = :user_subteam", user_subteam = returnData[0]["subteam"])
                return render_template("adminHistory.html", USERNAME = returnData[0]["username"], SUBTEAM = returnData[0]["subteam"], rows = myList, usernames=usernames, ID = currentID)
            #If subteamleader, allows for selection of members in the subteam
            elif pos1 == "subteamLeader":
                username = returnData[0]["username"]
                subteamList = db.execute("Select * FROM users WHERE subteam = :user_subteam", user_subteam = returnData[0]["subteam"])
                return render_template("adminHistory.html", USERNAME = returnData[0]["username"], SUBTEAM = returnData[0]["subteam"], rows = myList)
            #If student, you get personal history.
            else:
                return render_template("history.html", USERNAME = returnData[0]["username"], SUBTEAM = returnData[0]["subteam"], rows = myList)

#This function helps display the roster appropriately according to a member’s position on the team.
@app.route("/roster", methods=["GET", "POST"])
@login_required
def roster():
    if request.method == "GET":
        position = db.execute("Select position FROM users WHERE id = :user_id", user_id = session["user_id"])
        pos = position[0]["position"]
        if pos == "admin":
            members = db.execute("Select * FROM users")
            #total team's hours and minutes
            totalHours = 0
            totalMinutes = 0
            subteamSets = set()
            returnMemberList = []
            returnSubteamList = []

            #iterate through all the information per member
            for row in members:
                username = row["username"]
                subteam = row["subteam"]
                position = row["position"]
                hours = row["hours"]
                minutes = row["minutes"]
                totalHours += hours
                totalMinutes += minutes
                selectPosition = "selection" + str(row["id"])
                selectSubteam = "subteam" + str(row["id"])
                subteamSets.add(subteam)
                customSubteam = "custom" + str(row["id"])
                addDrop = "addDrop" + str(row["id"])
                myItem = {
                    "username": username,
                    "subteam": subteam,
                    "hours": hours,
                    "minutes": minutes,
                    "customSubteam": customSubteam,
                    "selectSubteam": selectSubteam,
                    "selectPosition": selectPosition,
                    "position": position,
                    "addDrop": addDrop
                }
                returnMemberList.append(myItem)

            #iterate through all the subteams to get total subteam data
            subteamSets = list(subteamSets)
            for i in range(len(subteamSets)):
                s = subteamSets[i]
                returnSubteam = db.execute("SELECT subteam, SUM (hours), SUM (minutes) FROM users GROUP BY subteam")
                tempSubteam = returnSubteam[i]["subteam"]
                tempHours = returnSubteam[i]["SUM (hours)"]
                tempMinutes = returnSubteam[i]["SUM (minutes)"]
                tempHours += tempMinutes // 60
                tempMinutes = tempMinutes % 60
                myItem = {
                    "subteam": s,
                    "hours": tempHours,
                    "minutes": tempMinutes
                }
                returnSubteamList.append(myItem)

            #total team data
            totalHours += totalMinutes // 60
            totalMinutes = totalMinutes % 60
            subteamList = db.execute("SELECT subteam FROM users GROUP BY subteam")
            positionList = ["admin", "subteamLeader", "student"]
            return render_template("roster.html", TTHOURS = totalHours, TTMINUTES = totalMinutes, subteamList = returnSubteamList, memberList = returnMemberList, subteams=subteamList, positions=positionList)

        if pos == "student":
            #no access if you are a student
            return render_template("noRoster.html")

        if pos == "subteamLeader":
            # members = db.execute("Select * FROM users")
            # totalHours = 0
            # totalMinutes = 0
            # subteamSets = set()
            # returnMemberList = []
            # returnSubteamList = []

            # for row in members:
            #     username = row["username"]
            #     subteam = row["subteam"]
            #     position = row["position"]
            #     hours = row["hours"]
            #     minutes = row["minutes"]
            #     totalHours += hours
            #     totalMinutes += minutes
            #     selectPosition = "selection" + str(row["id"])
            #     selectSubteam = "subteam" + str(row["id"])
            #     subteamSets.add(subteam)
            #     customSubteam = "custom" + str(row["id"])
            #     addDrop = "addDrop" + str(row["id"])
            #     myItem = {
            #         "username": username,
            #         "subteam": subteam,
            #         "hours": hours,
            #         "minutes": minutes,
            #         "customSubteam": customSubteam,
            #         "selectSubteam": selectSubteam,
            #         "selectPosition": selectPosition,
            #         "position": position,
            #         "addDrop": addDrop
            #     }
            #     returnMemberList.append(myItem)

            # subteamSets = list(subteamSets)
            # for i in range(len(subteamSets)):
            #     s = subteamSets[i]
            #     returnSubteam = db.execute("SELECT subteam, SUM (hours), SUM (minutes) FROM users GROUP BY subteam")
            #     tempSubteam = returnSubteam[i]["subteam"]
            #     tempHours = returnSubteam[i]["SUM (hours)"]
            #     tempMinutes = returnSubteam[i]["SUM (minutes)"]
            #     tempHours += tempMinutes // 60
            #     tempMinutes = tempMinutes % 60
            #     myItem = {
            #         "subteam": s,
            #         "hours": tempHours,
            #         "minutes": tempMinutes
            #     }
            #     returnSubteamList.append(myItem)

            # totalHours += totalMinutes // 60
            # totalMinutes = totalMinutes % 60
            # subteamList = db.execute("SELECT subteam FROM users GROUP BY subteam")
            # print(subteamList)
            # positionList = ["admin", "subteamLeader", "student"]
            # return render_template("roster.html", TTHOURS = totalHours, TTMINUTES = totalMinutes, subteamList = returnSubteamList, memberList = returnMemberList, subteams=subteamList, positions=positionList)

            #same idea as the code in "admin", except the visible rows are only those of that subteamLeader's subteam
            subteam = db.execute("Select subteam FROM users WHERE id = :user_id", user_id = session["user_id"])[0]["subteam"]
            members = db.execute("Select * FROM users WHERE subteam = :subteam", subteam = subteam)
            totalHours = 0
            totalMinutes = 0
            subteamSets = set()
            returnMemberList = []
            returnSubteamList = []

            for row in members:
                username = row["username"]
                subteam = row["subteam"]
                hours = row["hours"]
                minutes = row["minutes"]
                totalHours += hours
                totalMinutes += minutes
                selectPosition = "selection" + str(row["id"])
                selectSubteam = "subteam" + str(row["id"])
                subteamSets.add(subteam)
                customSubteam = "custom" + str(row["id"])
                addDrop = "addDrop" + str(row["id"])
                myItem = {
                    "username": username,
                    "subteam": subteam,
                    "hours": hours,
                    "minutes": minutes,
                    "customSubteam": customSubteam,
                    "selectSubteam": selectSubteam,
                    "selectPosition": selectPosition,
                    "addDrop": addDrop
                }
                returnMemberList.append(myItem)

            subteamSets = list(subteamSets)
            for i in range(len(subteamSets)):
                s = subteamSets[i]
                returnSubteam = db.execute("SELECT subteam, SUM (hours), SUM (minutes) FROM users GROUP BY subteam")
                tempSubteam = returnSubteam[i]["subteam"]
                tempHours = returnSubteam[i]["SUM (hours)"]
                tempMinutes = returnSubteam[i]["SUM (minutes)"]
                tempHours += tempMinutes // 60
                tempMinutes = tempMinutes % 60
                myItem = {
                    "subteam": s,
                    "hours": tempHours,
                    "minutes": tempMinutes
                }
                returnSubteamList.append(myItem)

            totalHours += totalMinutes // 60
            totalMinutes = totalMinutes % 60
            subteamList = db.execute("SELECT subteam FROM users GROUP BY subteam")
            #for subteam
            return render_template("subteamRoster.html", TTHOURS = totalHours, TTMINUTES = totalMinutes, subteamList = returnSubteamList, memberList = returnMemberList, subteams=subteamList)

        return apology("END OF ROSTER CODE", 405)

    #clicked change
    if request.method == "POST":
        members = db.execute("Select * FROM users")
        for row in members:
            #error when clicking change without doing something, position is set to none
            subteam = request.form.get("subteam" + str(row["id"]))
            if subteam is None:
                subteam = db.execute("SELECT subteam FROM users WHERE id = :user_id",user_id = row["id"])[0]["subteam"]
            customSubteam = request.form.get("custom" + str(row["id"]))
            position = request.form.get("selection" + str(row["id"]))
            db.execute("UPDATE users SET position=:position WHERE id=:user_id", position=position, user_id=row["id"])
            if not request.form.get("custom" + str(row["id"])) == "":
                #custom is not empty
                if request.form.get("addDrop" + str(row["id"])) == "add":
                    db.execute("UPDATE users SET subteam=:subteam WHERE id=:user_id", subteam=customSubteam, user_id=row["id"])
                else:
                    #want to delete subteam
                    #DONT DELETE IF SUBTEAM DOES NOT EXIST
                    deleteUserSubteamList = db.execute("SELECT id FROM users WHERE subteam=:subteam", subteam=customSubteam)
                    for user_id in deleteUserSubteamList:
                        db.execute("UPDATE users SET subteam=:subteam WHERE id=:user_id", subteam="noSubteam", user_id=row["id"])
            else:
                #custom is empty
                db.execute("UPDATE users SET subteam=:subteam WHERE id=:user_id", subteam=subteam, user_id=row["id"])


    #below code is to reprint the roster page/rerun the roster get code
    members = db.execute("Select * FROM users")
    totalHours = 0
    totalMinutes = 0
    subteamSets = set()
    returnMemberList = []
    returnSubteamList = []

    for row in members:
        # username = row["username"]
        # subteam = row["subteam"]
        # position = row["position"]
        # hours = row["hours"]
        # minutes = row["minutes"]
        # totalHours += hours
        # totalMinutes += minutes
        # selectName = "selection" + str(row["id"])
        # subteamSets.add(subteam)
        # customName = "custom" + str(row["id"])
        # myItem = {
        #     "username": username,
        #     "subteam": subteam,
        #     "hours": hours,
        #     "minutes": minutes,
        #     "customName": customName,
        #     "selectName": selectName,
        #     "position": position
        # }
        # returnMemberList.append(myItem)

        username = row["username"]
        subteam = row["subteam"]
        position = row["position"]
        hours = row["hours"]
        minutes = row["minutes"]
        totalHours += hours
        totalMinutes += minutes
        selectPosition = "selection" + str(row["id"])
        selectSubteam = "subteam" + str(row["id"])
        subteamSets.add(subteam)
        customSubteam = "custom" + str(row["id"])
        addDrop = "addDrop" + str(row["id"])
        myItem = {
            "username": username,
            "subteam": subteam,
            "hours": hours,
            "minutes": minutes,
            "customSubteam": customSubteam,
            "selectSubteam": selectSubteam,
            "selectPosition": selectPosition,
            "position": position,
            "addDrop": addDrop
        }
        returnMemberList.append(myItem)

    for s in subteamSets:
        returnSubteam = db.execute("SELECT subteam, SUM (hours), SUM (minutes) FROM users GROUP BY :subteam", subteam = s)
        tempSubteam = returnSubteam[0]["subteam"]
        tempHours = returnSubteam[0]["SUM (hours)"]
        tempMinutes = returnSubteam[0]["SUM (minutes)"]
        tempHours += tempMinutes // 60
        tempMinutes = tempMinutes % 60
        myItem = {
            "subteam": s,
            "hours": tempHours,
            "minutes": tempMinutes
        }
        returnSubteamList.append(myItem)

    totalHours += totalMinutes // 60
    totalMinutes = totalMinutes % 60
    subteamList = db.execute("SELECT subteam FROM users GROUP BY subteam")
    positionList = ["admin", "subteamLeader", "student"]
    return render_template("roster.html", TTHOURS = totalHours, TTMINUTES = totalMinutes, subteamList = returnSubteamList, memberList = returnMemberList, subteams=subteamList, positions=positionList)

@app.route("/confirmation", methods=["GET", "POST"])
@login_required
def confirmation():
    if request.method == "GET":
        #get position of member
        position = db.execute("Select position FROM users WHERE id = :user_id", user_id = session["user_id"])
        pos = position[0]["position"]
        #admins are able to view the page
        if pos == "admin":
            returnRow = []
            rows = db.execute("SELECT * FROM checks WHERE approved is NULL AND LOTimeStamp IS NOT NULL AND NOT user_id=:user_id", user_id=session["user_id"])
            for row in rows:
                #getting the idfference between the timestamps
                s1 = row["LITimeStamp"]
                s2 = row["LOTimeStamp"]
                FMT = "%Y-%m-%d %H:%M:%S"
                tdelta = datetime.strptime(s2, FMT) - datetime.strptime(s1, FMT)
                daysPlus = tdelta.days
                hoursPlus = tdelta.seconds // 3600
                minutesPlus = tdelta.seconds // 60 % 60
                selectName = "selection" + str(row["id"])
                customName = "custom" + str(row["id"])
                #these are variables that will help the html page with values and names of objects
                myItem = {
                    "username": db.execute("SELECT username FROM users WHERE id=:user_id", user_id = row["user_id"])[0]["username"],
                    "hours": hoursPlus,
                    "minutes": minutesPlus,
                    "selectName": selectName,
                    "customName": customName
                }
                returnRow.append(myItem)

            #redirect to a different page so that there isn't an empty table, but rather a simple message that says there are no waiting confirmations
            if len(returnRow) == 0 or len(rows) == 0:
                return render_template("noChecks.html")
            #display the waiting confirmation table with information from returnRow which consists of information about each item (myItem)
            return render_template("confirmation.html", rows = returnRow)
        # some of the below commented parts ars part of best outcome that was not implemented
        # elif pos == "studentLeader":
        #     returnRow = []
        #     rows = db.execute("SELECT * FROM checks WHERE approved is NULL AND LOTimeStamp IS NOT NULL AND NOT user_id=:user_id", user_id=session["user_id"])
        #     for row in rows:
        #         s1 = row["LITimeStamp"]
        #         s2 = row["LOTimeStamp"]
        #         FMT = "%Y-%m-%d %H:%M:%S"
        #         tdelta = datetime.strptime(s2, FMT) - datetime.strptime(s1, FMT)
        #         daysPlus = tdelta.days
        #         hoursPlus = tdelta.seconds // 3600
        #         minutesPlus = tdelta.seconds // 60 % 60
        #         selectName = "selection" + str(row["id"])
        #         customName = "custom" + str(row["id"])
        #         myItem = {
        #             "username": db.execute("SELECT username FROM users WHERE id=:user_id", user_id = row["user_id"])[0]["username"],
        #             "hours": hoursPlus,
        #             "minutes": minutesPlus,
        #             "selectName": selectName,
        #             "customName": customName
        #         }
        #         returnRow.append(myItem)
        #     if len(returnRow) == 0 or len(rows) == 0:
        #         return render_template("noChecks.html")
        #     return render_template("confirmation.html", rows = returnRow)
        else:
            #the user does not have access to the page
            return render_template("noRoster.html")

    if request.method == "POST":
        rows = db.execute("SELECT * FROM checks WHERE approved is NULL")
        #returnRow will store ID's to approve
        returnRow = []
        #check whether the selection was confirmed or denied
        for row in rows:
            if request.form.get("selection" + str(row["id"])) == "Confirm":
                print("CONFIRMED")
                returnRow.append(row)
            elif request.form.get("selection" + str(row["id"])) == "Deny":
                #set to 0 using primary key
                db.execute("UPDATE checks SET hours=:hours, minutes=:minutes, approved=0 WHERE id=:row_id", hours = 0, minutes = 0, row_id=row["id"])
        for row in returnRow:
            hours = db.execute("SELECT hours FROM users WHERE id=:user_id", user_id = row["user_id"])[0]["hours"]
            minutes = db.execute("SELECT minutes FROM users WHERE id=:user_id", user_id = row["user_id"])[0]["minutes"]
            s1 = row["LITimeStamp"]
            s2 = row["LOTimeStamp"]
            FMT = "%Y-%m-%d %H:%M:%S"
            tdelta = datetime.strptime(s2, FMT) - datetime.strptime(s1, FMT)
            daysPlus = tdelta.days
            hoursPlus = tdelta.seconds // 3600
            minutesPlus = tdelta.seconds // 60 % 60
            #check whether the custom hours box was used
            if request.form.get("custom" + str(row["id"])) == "":
                #operates if custom is blank
                minutes += minutesPlus
                if minutes >= 60:
                    hoursPlus += (minutes//60)
                    minutes = minutes % 60
                hoursPlus += daysPlus * 24
            else:
                #confirmed with something
                hoursPlus = int(request.form.get("custom" + str(row["id"])))
                minutesPlus = 0

            hours += hoursPlus
            #update tables
            db.execute("UPDATE users SET minutes=:minutes WHERE id=:user_id", minutes=minutes, user_id=row["user_id"])
            db.execute("UPDATE users SET hours=:hours WHERE id=:user_id", hours=hours, user_id=row["user_id"])
            db.execute("UPDATE checks SET hours=:hours, minutes=:minutes, approved=1 WHERE id=:row_id", hours=hoursPlus, minutes=minutesPlus, row_id=row["id"])
    rows = db.execute("SELECT * FROM checks WHERE approved is NULL AND LOTimeStamp IS NOT NULL")
    if len(rows) == 0:
        return render_template("noChecks.html")
    return redirect("/confirmation")
#allow option to not confirm or deny

@app.route("/delete", methods=["GET", "POST"])
@login_required
def delete():
    #Gets every item that may have been deleted
    database = db.execute("SELECT * FROM checks WHERE approved = 1")
    currentID = None
    tempHour = 0
    tempMinute = 0
    #Checks to see whether there has been a deletion
    for row in database:
        #Gets the name of the object
        checkID = 'delete'+str(row["id"])
        deleted = request.form.get(checkID)
        #If there has been a deletion, continue
        if deleted:
            db.execute("UPDATE checks SET approved = 0 WHERE id = :checkID", checkID = row["id"])
            currentID = row["user_id"]
            #Gets the numbers of hours and minutes that were added from the line
            s1 = row["hours"]
            s2 = row["minutes"]
            if s2 > tempMinute:
                tempMinute += 60
                tempHour -= 1
            #Keeps track of the difference of hours and minutes total
            tempHour -= s1
            tempMinute -= s2
        #As long as there was a deletion
        if currentID is not None:
            #Gets the original time so that time can be subtracted.
            time = db.execute("SELECT * FROM users WHERE id = :user_id", user_id = currentID)
            tempHour += time[0]["hours"]
            tempMinute += time[0]["minutes"]
            db.execute("UPDATE users SET hours = :setHours, minutes = :setMinutes WHERE id = :user_id", setHours = tempHour, setMinutes = tempMinute, user_id = currentID)
    return redirect("/history")



# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)