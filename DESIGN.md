We wanted to create an attendance tracker. For building this project, as a general note, we did not strictly follow the good, better, best model outlined in our proposal. Instead, we programmed the entire project from the start wanting to fulfill the best model, with a few adjustments along the way.
Just a little about implementation “quirks” to note, so that I don’t have to explain repeatedly. Every table with a changing number of lines in the project was built using dictionaries. Let’s say we wanted to display the name, subteam, and hours of every user, we would create a dictionary with keys “name,” “subteam,” and “hours.” we then set a value to each key. This dictionary was then placed within an array of dictionaries that can be displayed in the html. The list was sent to a table in the html in which each row of the list is read individually. On the basis of the keys, we were able to fill in items for each entry using the keys.

----

myItem = {
    "subteam": s,
    "hours": tempHours,
    "minutes": tempMinutes
}
returnSubteamList.append(myItem)

----

Above is an example of a dictionary we created called myItem. That dictionary was then added to a list of dictionaries. This list was then implemented in the HTML as follows:

----

<tbody>
  {% for row in subteamList %}
    <tr>
      <td>{{row["subteam"]}}</td>
      <td>{{row["hours"]}}</td>
      <td>{{row["minutes"]}}</td>
    </tr>
  {% endfor %}
</tbody>

----

Using the key associated with the row items in the row, we are able to display a changing size of table in the HTML. This process was used in every instance of a changing table size.

We next went with the issue of registering, logging in, logging out, and updating user information. Login and logout were simply taken from finance as they were the same. Registration was also similar, with a few small items. First, we did not assume a table existed within the database. Any time a user was created, we checked quickly if the users and checks tables existed. If not, we created them. We have both a checks table as well as a users table in order to be efficient. We didn’t want to store, for example, the password every time we added something to the checks.Otherwise, we also put in a password strength tester. If the password did not fit the necessary criteria, we had them put a new one in. Finally, we created implementation that allowed user to change their password.

The users table is as follows:

CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, username TEXT NOT NULL, hash TEXT NOT NULL, hours INTEGER NOT NULL, minutes INTEGER NOT NULL, subteam TEXT, position TEXT, lastlogin INTEGER, approved BOOLEAN)

The if not exists ensures it is not yet there. The primary key is simply to allow us to have an id associated. Username is given by the user. Hash is from the generate hash. Hours keeps track of the total horus a user has been logged in. Minutes does the same but for minutes. Subteam stores the subteam of the user. Position stores their position (admin, subteam leader, admin). Last login is was used to keep track of whether there was a login before a logout.

CREATE TABLE IF NOT EXISTS checks (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, user_id INTEGER NOT NULL, LITimeStamp TIMESTAMP, LOTimeStamp TIMESTAMP, approved BOOLEAN, hours INTEGER, minutes INTEGER)

The id allows us to easily access a specific line within the history. User_id relates us to the user id of the main users table. The timestamps are for login/logout times. Hours/minutes keeps track of either the difference between timestamps or a custom input. Approved lets us know if it’s been approved.

After registering, etc, we wanted to tackle the core of our project: checking in and checking out. This was relatively easy. To begin, someone is sent to the check in page. This page had current hours and minute. It also has a button that says check in. When check in is clicked, a new entry is added to checks that includes a log in time for a user. That entry also use a unique identifier (so it is easy to return to the line to edit it). Each entry, initially, also has a null logout time. There are also a few other small null items. For example, the history page stores the hours logged in (which may become more apparent why in the confirmation page.) The user, once logged in, stores the unique ID of the check entry. This was done to ensure that the check in of a user was easily accessible and not ever lost. When a user has a unique ID stored, the code knows that the user has logged in, but has not logged out. When logged in, the user is sent to a log out page. On this page is the number of hours/minutes the user has recorded is displayed (just like login page). However, there is also a timestamp for the last login. This timestamp was found using the unique identifier stored in the user table. Once a user hits the log out button, the unique identifier of the last login is set to null (thus showing that the user is logged out). In turn, the checks slot is filled with a logout time. This cycle repeats indefinitely.

----

if lastLogin is not None:
#Need to checkout, CHECKOUT CODE
db.execute("UPDATE checks SET LOTimeStamp=:LOTimeStamp WHERE id=:lastLogin", LOTimeStamp=datetime.now(), lastLogin=lastLogin)
db.execute("UPDATE users SET lastlogin=:lastlogin WHERE id=:user_id", lastlogin=None, user_id=session["user_id"])

----

This is an example of last login. We use lastLogin to keep track of whether the user is currently checked in. If the user is checked in, we don’t want to present the user with another opportunity to check in, as they should stay in the same session even if they log out. Thus, we can keep track of the status of the user. lastLogin is also the id of the last check-in. This allows for easy access.

We wanted to know how many hours people had logged, so roster was initially a simple table that included a line for every user and their total hours and minute. We used an sql line to get all the data for each user. We then created a “total hours/minutes” variable that stored the total hours/minutes for the whole team. Every time we went over a user, we added to this total. Thus, we also displayed total hours. Next, we wanted to display hours per subteam. As such, we selected subteam, sum(hours), and sum(minutes) on the basis of a grouped subteam. Then, we displayed a table with all this data. From this, our roster page displayed whole team data, individual subteam data, and user data with regard to login/logout times.

----

subteamSets = list(subteamSets)
for i in range(len(subteamSets)):
    s = subteamSets[i]
    returnSubteam = db.execute("SELECT subteam, SUM (hours), SUM (minutes) FROM users GROUP BY subteam")
    tempSubteam = returnSubteam[i]["subteam"]
    tempHours = returnSubteam[i]["SUM (hours)"]
    tempMinutes = returnSubteam[i]["SUM (minutes)"]

----

Shown here is the group by as well as the sum that we used.

Originally, history displayed a history of a user. We found all checks that are related to a certain user id. We then displayed this in table format. After, however, we wanted to be able to display any user if you were an admin. So, we created a dropdown menu that included every username. When a button was pressed, instead of using session[“user_id”], we created a “currentID” that was the id of the selected user. This currentID was used to display history.
One of the most complicated portion of the project was the confirmation page. Instead of a clock out immediately adding hours to the user, it had to be confirmed first. Every check line has a “confirmed” box. If null, it has not been confirmed or denied. If 0, it has been denied or deleted (more on deleted later). If 1, it has been confirmed. Our confirmation page allows you to view every confirmation in the whole team as an admin. You must confirm/deny everything when done confirming. Each entry that has to be confirmed as a dropdown menu for confirm/deny. There is also a custom entry in which an admin can input a custom number of hours. As there could be 1 or greater lines, we created a unique name for each input on the basis of the unique identifier of the check entry. Once a final button was preseed, each line was checked for confirm/deny. Deny set approved to 0 immediately. Confirm checked if there was anything in custom. If not, it was confirmed as is, and the difference between the two time stamps was both recorded in the checks line as well as updated in the user’s data. If there was a custom item, it was, once more, stored in both the checks line and the user’s data.

----

<select name = {{row['selectName']}} class="browser-default custom-select" style="max-width:65%">
    <option selected value="Confirm">Confirm</option>
    <option value="Deny">Deny</option>
</select>

----

This is the HTML for the confirm/deny button. As you can see, the name is set to a variable. This is done so that each dropdown menu has its only unique identifier in terms of its name. Thus, we can distinguish between a confirm and deny in a different line.

We soon updated the history page to allow for deletes. Because we did want to work two buttons, we added a check box that checked whether an admin wanted to edit. If that was checked, the functionality was sent to the delete() function. In the delete function, the history of a specific user is shown with a check box next to each item. If checked, the slot is deleted. Because custom hours was allowed in the confirmation page, we couldn’t just delete on the basis of the difference between time stamps. Hence, we stored the custom hours. Using the custom hours or difference between timestamps, we subtracted the deleted check from the user’s data. Furthermore, we switched the accepted value from 1 to 0, showing that it had been retroactively denied. Thus, we know that 0 represents a denial or a delete.

----

<td><div class="form-check">
    <input type="checkbox" class="form-check-input" id={{row['id']}} name={{row['id']}}>
    <label class="form-check-label" for={{row['id']}}></label>
</div></td>

----

Here, once more, we name on the basis of a key in a dictionary in order to give it a unique identifier.

We then updated the roster page. While previously the roster showed hours, we wanted admins to be able to use the roster page in order to change things like subteams as well as positions.To do so, we used implementation from previous work we had done in confirmation as well as delete. Each user was given a line in a table with a dropdown menu that included the different items they might need: admin, subteam lead, and student. Once could select the currently selected item or a new item for the user in order to change their position. In turn, one can add/drop new subteams. Finally, admins can place users on a dropdown menu of the set of all subteams. See previous for examples of how this looked in code
The last thing we did was implement permissions. Since the entire project was coded from the perspective of an admin, we implemented permissions to give people the ability to look at or edit items based on their position. For example, students do not have access to the confirmation page.

----

if pos1 == "admin":
    username = returnData[0]["username"]
    subteamList = db.execute("Select * FROM users WHERE subteam = :user_subteam", user_subteam = returnData[0]["subteam"])
    return render_template("deleteHistory.html", USERNAME = returnData[0]["username"], SUBTEAM = returnData[0]["subteam"], rows = myList)
else:
    return render_template("history.html", USERNAME = returnData[0]["username"], SUBTEAM = returnData[0]["subteam"], rows = myList)

----

Here, if the position of the session user is admin, we give full power in the history page to delete history. Otherwise, we redirect the user to the regular history page, as they do not have permissions to delete.
