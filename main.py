import time

from flask import Flask,request,render_template,redirect,session
import requests
import pymongo
import json
import datetime
from bson.objectid import ObjectId

myclient = pymongo.MongoClient("mongodb://localhost:27017/")
mydb = myclient["weatherapp"]
usersTable = mydb["users"]
weatherTable=mydb['weather_history']
app=Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'

@app.route("/",methods=['GET','POST'])
def login():
    user_id = session.get('user_email')
    if user_id is not None:
        return redirect("/get_weather")

    if request.method=='POST':
        email=request.form["email"]
        password = request.form["password"]
        user=usersTable.find_one(dict(request.form))
        if user is None:
            error="Invalid credentiat"
        else:
            session['user_name'] = user['name']
            session['user_email'] = user['email']
            return redirect("/get_weather")
    return render_template("login.html",**locals())

@app.route("/signout",methods=["GET","POST"])
def logout():
    if request.method=="POST":
        session.clear()
        return redirect("/")

@app.route("/register",methods=['GET','POST'])
def register():
    error=None
    if request.method=='POST':
        name=request.form['name']
        email = request.form['email']
        password = request.form['password']
        if name and email and password:
            data=usersTable.find_one({"email":email})
            if data is None:
                usersTable.insert_one(dict(request.form))
                return redirect("/")
            else:
                error="User already exists."

        else:
            error="please fill all the fields"
    return render_template("register.html",**locals())


@app.route("/get_weather",methods=['GET','POST'])
def get_weather():
    user_id = session.get('user_email')
    if user_id is None:
        return redirect("/")
    success=False
    city=""
    if request.method=="POST":
        city=request.form['city']
        res=requests.get("https://api.openweathermap.org/data/2.5/weather?q="+city+"&appid=3bfcd6ea57901b6ce028b6cb6917c8d0&units=metric")


        if res.status_code!=200:
            error="City not found"
        else:
            data = json.loads(res.text)
            name=data['name']
            temp=data['main']['temp']
            feels_like=data['main']['feels_like']
            humidity=data['main']['humidity']
            country=data['sys']['country']
            success=True
            now = datetime.datetime.now()
            time_str = now.strftime("%Y-%m-%d %H:%M:%S")
            d={
                "user":session['user_email'],
                "city":name,
                "temp":temp,
                "time":time_str
            }
            weatherTable.insert_one(d)

    return render_template("getweather.html",**locals())

@app.route("/history", defaults={'city1': None})
@app.route("/history/<city1>",methods=['GET','POST'])
def get_history(city1=None):
    user_id = session.get('user_email')
    if user_id is None:
        return redirect("/")
    if city1 is None:
        weather_history=weatherTable.find({'user':session['user_email']})
        historyList=[]
        unique_cities=set()
        for i in weather_history:
            historyList.append(i)
        for i in historyList:
            unique_cities.add(i['city'])
        length=len(historyList)
    else:
        weather_history = weatherTable.find({'user': session['user_email'], 'city':city1})
        historyList = []
        unique_cities = set()
        weather = weatherTable.find({'user': session['user_email']})
        for i in weather_history:
            historyList.append(i)
        for i in weather:
            unique_cities.add(i['city'])
        length = len(historyList)

    return render_template("history.html",**locals())

@app.route("/delete_history/<id>",methods=['GET','POST'])
def delete_history(id):
    weatherTable.delete_one({"_id":ObjectId(id)})
    return redirect("/history")


app.run(port=5004)