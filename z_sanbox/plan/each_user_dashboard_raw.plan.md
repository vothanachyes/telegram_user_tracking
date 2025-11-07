I want another feature.
this feature for see user detail and data. (Look similar to user_detail_dialog).
I can filter date rang to see this user's messages sent to a group (This user may has multiple group joined, you may check our database has handle it or yet, if yet, make sure handle it. Because a user can joined many telegram group)
By this feature,  I can specific user to see their activities inside group, So I can report this user or analyze their message to final see this user is very active in a group.


Plan: 
- Has a page that can detail to a user. Should has another button at sidebar

In that page, layout should be:
+ Top Header: 
    - Left: Searchable field (For search a user), show suggestion dropdown matching user, this search box also can search by FullName, Phone, username (user must use @ as prefix to search by user name). Suggested drop down show 3 data, FullName, username, phone
    - Right: 
        . Telegram button (this is link, click to nevigate to telegram app, this button only can click after )
        . Menu: the same to Telegram page, that has export menu to export this user data.
+ Above Messages table: User detail (the same to user_detail_dialog at Profile photo section)
    - There has button click to see this user detail at the right corner (Yes pop-up full user_detail_dialog for editable info)
+ Content: there are 2 tabs
    - General: 
        . Will show all report: All the things a user sent to group. reaction total, messages total (in message total may, total stickers, total videos, links, photo, ...
    - Message tab: show all messages sent by this user (the same ui to Message Table, but it specific by this user, and select the first group and date range is current month)

