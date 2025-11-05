### Users tracking app
Teach stack: python3 with Flet, SQLite, pandas, xlsxwriter, ReportLab

Overview: Currently we are using telegram as communication between team and leader. Every day each team sub-leader always send report. That report can be only text, sometimes image(s) follow by caption, sometimes file(s) follow by caption. By this action of sub-leader, as me I want to convert these users reports to table of content that can searchable, editable, markable and some more extra actions on each of their report in a system. Because telegram will be long and long scroll if there are many many sub-leader of each team drop report in chat. So I want to create a modern ui system that will list users report as table, can be summery and track which team has been sent report which not, click the row to see detail of that report. Yeah, table can be filterable, search and ....(Please analyze more possible and human needed)

Task1: Create UI for storing configure app settings. 
Configurable:
+ Appearance:
- theme dark mode light mode
- language khmer and English
- ... (As you analyse)
+ Telegram auth:
- AppId
- Api Key
- user phone (user to be used for fetching data from telegram group)
- ... (As you analyse)
+ Fetch setting:
- dowload root directory
- to download message media or not
- Max size of file of message to be dowload
- Delay in second (telegram may block us, because fetching too quick, give it some delay)
- media download (mutiple seletion, )
- ... (As you analyzis more)


Task2: Build a system to fetch user message data from a telegram group. This system connect to telegram (Yes Using Pyrogram) api then fetch group history by date rang, or user message. Like in overview above, user may send some media follow by caption (if user has send media, please save user media, defualt root directory can be adjust/set from .env file (User can setting this in app, if user change, popover to ask them sure? If yes, one more pop as user to move current existing folders or not? (any subtitle tell them, it will block usage for a while during moving, should show progress, maybe at bottom) if user yes => block user use a while. (And this change only available when no progressing read/write to that dir) ). 

and folder structure should be: {rootDir}/{group_id}/{username}/{date}/{messageIdAndtime}/*
rootdir: the root dir provided in app setting
group_id: the telegram group id that I want to fetch report (this will provide in fetching UI user input)
username: can be telegram's username, who sent the message // if not have take their fullname, also replace space by underscore _
date: message sent date format as 2025-10-25 
messageIdAndTime: sent telegram's message ID + _ + sentHours.


+ UI: Ui that user can input their's phone number (after they put their phone number, will call the telgram api for authorization, yes it may sent 6 OTP code to user telegram, maybe telegram prompt the two factor password) (You need to aware this)
  - User can save their login or not, if save next time they open app auto choose the first credential if they are not yet selected the specific one.
  - When user input groupId, we also save this info for next time user needed.
+ Dashboard the best dashboard showing data as you analyze
+ Report, user can export to pdf, excel
+ For table show user messages data:
  - Table header should selectable group (drop down show group that user used to save.)
  - Telegram unique by userName, right? But if user not has username => take teir name as username, but users may have the same name, so maybe at index to it.
  - Click on a row will popup mesasge detail. (And also can be CRUD on this detail):
    . Show sender profile
    . messageId
    . link to that actual message
    . ...
  - Column:
    . No
    . UserPic
    . Full Name
    . phone (if avalibale, user may hide their phone by telegram feature)
    . message
    . date sent
    . media (if image, just display it should be mini one) If video show as video icon
    . ...
    . action (this drop down action three dot), delete it. (For delete it is solf delete, because when user try to fetch messages from this group again with the same date it may got the same data, so we can check and ignore, (You may create another db table for store deleted message (telegram may unique by messageId) for fast search))
  - ... (You can suggests more)

+ For users inside a group table:
   - Click on a row will popup user detail. (And also can be CRUD on this detail):
   - can delete user profile, if deleted => profile will be dowload again (This idea for if user has new profile picture , and our system is the old one)
   - Column:
    . No
    . UserPic ()
    . Full Name
    . phone (if avalibale, user may hide their phone by telegram feature)
    . short bio
    . ...
    . action (this drop down action three dot), delete this user. (For delete it is solf delete, because when user try to fetch messages from this group again, it may got the same user, so we can check and ignore this deleted user,(You may create another db table for store deleted telegram user ((telegram may unique by userId)for fast search)). Please note, if user deleted, => all message from this user also filter out.

+ These two tables (users, users messages) should the same page, may be using tabs. Each table has it own filter, export report, .... and default select current month date rang
+ The top of tables header may group selection (above filter)
+ There is a button for user to start fetch fetching data (Maybe put it at the side bar) 
+ Yes, sidebar only show icons: 
  - Dashboard
  - Telegram (that two tables, default is show message table)
  - Setting
  - Profile (Current login user)

+ Connect to firebase for credential Login to this app, one user can only login to one device.
  - Email, Password

.. Maybe I missing some usefull features please add. 

And you also can ask me infinite questions you want to confirm for the best app ever.
Current project dir is empty now, plan me for the best python app achiture, reusable, rliable, scalable, maintain, ... 
My color theme is #082f49

Like rounded corner (configurable radius of card, ... )
Note: Modern, cross platform