Setup instructions:

1. Set up sourcecode management

brew install heroku/brew/heroku
heroku login
git clone https://github.com/nseidl/Ripe.git
git remote add staging https://git.heroku.com/ripe-staging.git
git remote add production https://git.heroku.com/ripe-production.git


2. Set up PyCharm and virtualenv

    cd Ripe-Booty
virtualenv venv
pip install -r requirements.txt
deactivate

In PyCharm:
PyCharm -> Preferences -> Project: ripe -> Project Interpreter
Make sure Project Interpreter is set to ripe/venv
If you want to use custom environment variables for app settings:
Edit Run Configurations -> app -> Environment Variables


3. Set up Mongo

brew install mongodb
cd ripe

Following command runs mongo live in a terminal window
mongod --dbpath mongo/ --config mongo/mongod.conf

Interact with that mongo instance with this:
mongo --host 127.0.0.1:27018

Create 'ripe' database, 'ripe-users' and 'ripe-media' collections
> use ripe
> db.createCollection("ripe-users")
> db.createCollection("ripe-media")

4. POSTing data to mongo

Use the add_content script


~~~~~
WORKFLOW:

For development work, always pull from and push to ripe
- this should be where most of the code changes happen

After you're done testing code you've edited off of ripe, push it to staging

If it works on staging, great! Leave it on staging.
DO NOT PUSH TO PRODUCTION unless it's a big feature - no reason to clutter the production space

~~~~~

git remote -v
- this shows information of branches you're tracking

git push <remote name> <branch name>
- branch name defaults to whichever branch you're on (which defaults to master)
- remote name should be one of:
  - staging
    - this one is where you should push AFTER YOU VERIFY THAT NOTHING IS BROKEN WHEN RUNNING LOCALLY
  - production
    - the "production" instance of the api, please only push to this after you're done with a major feature
  - origin
    - pretty sure this gets added by default whenever you just git clone a repo
  - booty
    - where we should push and pull source

~~~~~

API Endpoints:

GET /mongo/<object_type>/
- <object_type>
  - type of object you're trying to query for (users|media)

GET /mongo/<object_type>/<object_id>
- <object_type>
  - type of object you're trying to query for (users|media)
- <object_id>
  - mongo assigned _id

POST /mongo/<object_type>/
- <object_type>
  - type of object you're trying to query for (users|media)
- payload
  - see add_object.py for python example of how to add an object
  - just send json

