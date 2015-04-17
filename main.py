#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
from google.appengine.api import users, mail, images
from google.appengine.ext import ndb, db
import webapp2, random, pickle, urllib, datetime, locale
locale.setlocale(locale.LC_ALL, '')
class Debate(ndb.Model):
    title=ndb.StringProperty()
    desc=ndb.TextProperty()
    levels=ndb.IntegerProperty()
class Opinion(ndb.Model):
    debate=ndb.KeyProperty()
    decision=ndb.BooleanProperty()
    comment=ndb.StringProperty()
    user=ndb.UserProperty()
class Chat(ndb.Model):
    debate=ndb.KeyProperty()
    when=ndb.DateTimeProperty(auto_now_add=True)
    msg=ndb.StringProperty()
    user=ndb.UserProperty()
class MainHandler(webapp2.RequestHandler):
    def get(self):
        debates=Debate.query().fetch(100)
        user = users.get_current_user()
        if self.request.get("alert")=="Yes":
            self.response.write("""<script>
        var x = alert("Your opinion/chat has been registered.");
        window.location.replace("/");
        </script>""")
        if not user:
            self.redirect(users.create_login_url(self.request.uri))
        admin=users.is_current_user_admin()
        for debate in debates:
            self.response.write("<h1>"+debate.title+"</h1><br>")
            self.response.write("<p>"+debate.desc+"</p><br>")
            
            
            if debate.levels>1 or admin:
                ayes=len(Opinion.query(Opinion.debate==debate.key, Opinion.decision==True).fetch(100))
                nays=len(Opinion.query(Opinion.debate==debate.key, Opinion.decision==False).fetch(100))
                self.response.write("%s people have answered:<br>" %(ayes+nays))
                self.response.write("   %s people said yes<br>" %(ayes))
                self.response.write("   %s people said no<br>" %(nays))
                if debate.levels>2 or admin:
                    for opinion in Opinion.query(Opinion.debate==debate.key).fetch(100):
                        self.response.write("<h2>"+opinion.user.nickname() + " chose " + ("Yes" if opinion.decision else "No")+":</h2><br>")
                        self.response.write("<p>"+opinion.comment+"</p><hr>")
                    if debate.levels>3 or admin:
                        for chat in Chat.query(Chat.debate==debate.key):
                            self.response.write("<h1>"+chat.user.nickname() + "said:</h1><br>")
                            self.response.write("<p>"+chat.msg+"</p><hr>")
                        self.response.write("""<form action="/chat" method="post" enctype="multipart/form-data"><input type="hidden" name="debate" value=\""""+debate.title+"""">
                        <textarea rows="4" cols="50" name="msg"""+debate.title+"""">Your chat message</textarea><br><input type="submit" value="Send Message"></form>""")
                        

                            
                        
            user_choice=Opinion.query(Opinion.user==user).get()
            if user_choice==None:
                self.response.write("You have not made a choice.<br>")
            else:
                self.response.write("Your choice is currently "+("Yes" if user_choice.decision else "No")+"<br>")
            self.response.write(("""Submit an opinion:
<form action="/opinion" method="post" enctype="multipart/form-data"><input type="hidden" name="debate" value="%s">
<input type="radio" name="decision" value="yes" selected>Yes<br>
<input type="radio" name="decision value="no">No<br>
<div><textarea rows="4" cols="50" name="comment">
Why you chose what you chose(500 characters or less)
</textarea><br></div>
<input type="submit" value="Submit Opinion"></form><br>""") %(debate.title))
            if admin:
                self.response.write(("""Change settings:<br>
<form action="/settings" method="post" enctype="multipart/form-data">><input type="hidden" name="debate" value="%s">
<input type="radio" name="level" value="1" selected>Level 1(no data)<br>
<input type="radio" name="level" value="2">Level 2(how many users chose each answer)<br>
<input type="radio" name="level" value="3">Level 3(each answer with comments)<br>
<input type="radio" name="level" value="4">Level 4(chats)<br>
<input type="submit" value="Change Settings"></form>""") %(debate.title))
        if admin:
            self.response.write("""<form action="/add" enctype="multipart/form-data" method="post">
<div><textarea rows="1" cols="50" name="name">
Enter the title of your debate here
</textarea><br></div>
<div><textarea rows="4" cols="50" name="desc">
Enter a description of your debate here
</textarea><br>
<input type="submit" value="Add Debate"></div></form>""")
class ChatHandler(webapp2.RequestHandler):
    def post(self):
        user = users.get_current_user()
        if not user:
            self.redirect(users.create_login_url(self.request.uri))
        
        o=Chat()
        o.user=user
        debate=Debate.query(Debate.title==self.request.get("debate")).get()
        o.debate=debate.key
        o.msg=self.request.get("msg")
        o.put()
        self.redirect('/?alert=Yes')
class RegisterHandler(webapp2.RequestHandler):
    def post(self):
        user = users.get_current_user()
        if not user:
            self.redirect(users.create_login_url(self.request.uri))
        
        o=Opinion()
        o.user=user
        debate=Debate.query(Debate.title==self.request.get("debate")).get()
        o.debate=debate.key
        o.decision=self.request.get("decision")=="yes"
        o.comment=self.request.get("comment")
        opinion=Opinion.query(Opinion.user==user, Opinion.debate==o.debate).get()
        if (opinion != None) and opinion.debate.get().title==self.request.get("debate"):
            self.response.write("""<script>
        var x = alert("Your previous opinion was deleted.");
        </script>""")
            opinion.key.delete()
        o.put()
        self.redirect('/?alert=Yes')
        
class AddHandler(webapp2.RequestHandler):
    def post(self):
        d=Debate()
        d.title=self.request.get("name")
        d.levels=1
        d.desc=self.request.get("desc")
        d.put()
        self.redirect('/')
        
class Settings(webapp2.RequestHandler):
    def post(self):
        d=Debate.query(Debate.title==self.request.get("debate")).get()
        d.levels=int(self.request.get("level"))
        d.put()
        self.redirect('/')
class Opinions(webapp2.RequestHandler):
    def get(self):
        opinions=Opinion.query().fetch(100)
        for opinion in opinions:
            self.response.write(opinion.debate.get().title+"<br>")
            self.response.write(opinion.user.nickname()+"<br>")
            self.response.write(("Yes" if opinion.decision else "No")+"<br>")
            self.response.write(opinion.comment+"<br>")
            
class ClearHandler(webapp2.RequestHandler):
    def get(self):
        opinions=Opinion.query().fetch(100)
        debates=Debate.query().fetch(100)
        chats=Chat.query().fetch(100)
        for i in opinions:i.key.delete()
        for i in debates:i.key.delete()
        for i in chats:i.key.delete()
app = webapp2.WSGIApplication([
    ('/', MainHandler), ('/opinion', RegisterHandler), ('/settings', Settings), ('/add', AddHandler), ('/debug', Opinions), ('/clear', ClearHandler), ('/chat', ChatHandler)
], debug=True)
