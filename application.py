from flask import Flask ,render_template,request, session, redirect, flash, send_file
import sys
import os
import re
from werkzeug.utils import secure_filename
from pymongo import MongoClient
from flask_bcrypt import Bcrypt
from flask_mail import Mail, Message
import pyrebase
import pandas as pd
import numpy as np 
from scipy import stats as st 
import xlsxwriter
import csv
from datetime import date
import math
from pathlib import Path

app = Flask(__name__)
bcrypt = Bcrypt()

client = MongoClient("mongodb+srv://*****:*****@graco-pg6jo.mongodb.net/test?retryWrites=true&w=majority")
db = client.get_database('Graco')
user = db.user

app.debug=True
UPLOAD_FOLDER = './marksheet_folder'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER 

app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = '*****'
app.config['MAIL_PASSWORD'] = '*****'
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False

mail = Mail(app)

config= {
    "apiKey": "AIzaSyBEeB8M0_f6r53yenxF_7TPYnRqnp-GO8Y",
    "authDomain": "graco-f6d67.firebaseapp.com",
    "databaseURL": "https://graco-f6d67.firebaseio.com",
    "projectId": "graco-f6d67",
    "storageBucket": "graco-f6d67.appspot.com",
    "messagingSenderId": "113899851380",
    "appId": "1:113899851380:web:25deb6a6ab4e135e6dcb21",
    "measurementId": "G-PGL15Q9ZDB"
}

firebase = pyrebase.initialize_app(config);
storage = firebase.storage()

# Home Page
@app.route('/',methods=['GET'])
def start():
    session['logged_in']=False
    session['username'] = None
    return redirect('/home')

@app.route('/home',methods=['GET'])
def index():
    if session['logged_in']:
        flash('You are logged in as ' + session['username'],'danger')
    return render_template('homepage.html')

# Login Page
@app.route('/login',methods=['GET','POST'])
def login():
    if request.method=='POST':
        userDetails=request.form
        username=userDetails['username']
        password=userDetails['password']
        login_user = user.find_one({'username' : request.form['username']})
        if login_user:
            if bcrypt.check_password_hash(login_user['password'],password):
                session['logged_in'] = True
                session['username'] = username
                if login_user['type']=='Student':
                    session['type']='Student'
                    flash('You are now logged in','success')
                    return redirect('/student')
                else:
                    session['type']='Faculty'
                    flash('You are now logged in','success')
                    return redirect('/faculty')
            flash('Invalid username/password combination','danger')
            return redirect('/login')
        flash('Username does not exist. Register First!!','danger')
        return redirect('/login')
    else:
        if session['logged_in']:
            flash('You are logged in as ' + session['username'],'warning')
        return render_template('login.html')

#forgot password
@app.route('/sendmail',methods=['GET','POST'])
def sendmail():
    if request.method=='POST':
        mailid = request.form['mailid']
        existing_user = user.find_one({'email' : mailid})
        if existing_user == None:
            flash('User with this email does not exist','danger') 
            return redirect('/sendmail')
        username = existing_user['username']
        mess = 'GRACO : Reset Your Password.'
        msg = Message(mess, sender = 'wox.csti1@gmail.com', recipients = [mailid])
        # link = 'http://gradegrace-nngdt.run-us-west2.goorm.io/forgotpass/'+username
        link = 'http://graco-project.herokuapp.com/forgotpass/'+username
        msg.body = "Click this link to reset your password. " + link
        mail.send(msg)
        flash('Mail sent Successfully!! Click the link in your email to reset your password','success')
        return render_template('sendmail.html')
    return render_template('sendmail.html')

@app.route('/forgotpass/<username>',methods=['GET','POST'])
def forgotpass(username):
    if request.method=='POST':
        newpass = request.form['newpass']
        #check password
        e=0
        regex = re.compile('[@_!#$%^&*()<>?/\|}{~:]')    
        if regex.search(newpass) == None: 
            e+=1 
            flash('Password should contain a special character!!','warning')
        if not any(x.isupper() for x in newpass):
            e+=1
            flash('Password should contain atleast one UpperCase letter!!','warning')     
        if not any(x.isdigit() for x in newpass):
            e+=1
            flash('Password should contain atleast one number!!','warning')
        if e==0:
            dob = request.form['dob']
            existing_user = user.find_one({'username' : username})
            if existing_user['dob']==dob:
                user.update_one( {"username":username}, {"$set": { "password":bcrypt.generate_password_hash(newpass)}}) 
                flash('Your password is reset successfully!!','success')
                return redirect('/login')
            else:
                flash('Incorrect Date of Birth','danger')
                return redirect('/forgotpass/'+username)
        else:
            return redirect('/forgotpass/'+username)
    return render_template('resetpass.html',username = username)
    
    
#Register Page
def validate(user):
    e=0
    #check password
    regex = re.compile('[@_!#$%^&*()<>?/\|}{~:]')    
    if(regex.search(user['password']) == None): 
        e+=1 
        flash('Password should contain a special character!!','warning')
    if not any(x.isupper() for x in user['password']):
        e+=1
        flash('Password should contain atleast one UpperCase letter!!','warning')     
    if not any(x.isdigit() for x in user['password']):
        e+=1
        flash('Password should contain atleast one number!!','warning')
    #check email
    regex = '^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$'
    if not re.search(regex,user['email']):  
        e+=1
        flash('Not a Vaild Email!!','warning')

    if e==0:
        return True
    else:
        return False


@app.route('/register',methods=['GET'])
def register():
    if session['logged_in']:
        flash('You are logged in as ' + session['username'],'warning')
        return redirect('/home')
    return render_template('register.html')

@app.route('/regstu',methods=['GET','POST'])
def register_student():
    if request.method == 'POST':
        existing_user = user.find_one({'username' : request.form['username']})
        if existing_user is None:
            if validate(request.form):
                username = request.form['username']
                password = request.form['password']
                hashpass = bcrypt.generate_password_hash(password)
                email = request.form['email']
                dob = request.form['dob']
                batch = request.form['batch']
                dept = request.form['dept']
                section = request.form['section']
                types = 'Student'
                comments = []
                user.insert_one({'username' : username, 'password' : hashpass,'email':email, 'dob':dob, 'batch':batch, 'dept':dept, 'section':section, 'type':types, 'comments':comments})
                session['logged_in'] = True
                session['username'] = username
                flash('You are now logged in','success')
                return redirect('/student')
            else:
                return redirect('regstu')
            
        flash('That username already exists!','danger')
        return redirect('/regstu')
    
    if session['logged_in']:
            flash('You are logged in as ' + session['username'],'warning')
    return render_template('regstu.html')

@app.route('/regfac',methods=['GET','POST'])
def register_faculty():
    if request.method == 'POST':
        existing_user = user.find_one({'username' : request.form['username']})
        if existing_user is None:
            if validate(request.form):
                username = request.form['username']
                password = request.form['password']
                hashpass = bcrypt.generate_password_hash(password)
                email = request.form['email']
                dob = request.form['dob']
                types = 'Faculty'
                comments = []
                user.insert_one({'username' : username, 'password' : hashpass, 'email':email, 'dob':dob, 'type':types,'comments':comments})
                session['logged_in'] = True
                session['username'] = username
                flash('You are now logged in','success')
                return redirect('/faculty')
            else:
                return redirect('regfac')
        flash('That username already exists!','danger')
        return redirect('/regfac')
    
    if session['logged_in']:
            flash('You are logged in as ' + session['username'],'warning')
    return render_template('regfac.html')

#Student Dashboard
@app.route('/student',methods=['GET','POST'])
def student_dash():
    if request.method == 'POST':
        comment = str(date.today())+"_"+session['username']+"_"+request.form['comment'];
        existing_user = user.find_one({'username' : request.form['facultyid']})
        if existing_user:
            user.update_one( {"username":request.form['facultyid']}, {"$push": { "comments":comment}}) 
            flash('Your comment is sent successfully!!','success')
            return redirect('/student')
        flash('Username does not exist!!','danger')
        return redirect('/student')
    
    existing_user = user.find_one({'username' : session['username']})
    if session['logged_in'] and existing_user['type']=='Student':
        return render_template('studentdash.html')
    else:
        flash("You cannot access the Student dashboard!! Login as a Student","danger")
        return redirect("/home")
    
@app.route('/viewmarks',methods=['GET','POST'])
def view_marks():
    if request.method == 'POST':
        stu = user.find_one({'username':session['username']})
        filename = stu['batch']+stu['dept']+stu['section']+".csv"
        path = "upload/"+filename
        download_path = "./marksheet_folder/"+filename
        storage.child(path).download(download_path)
        df=pd.read_csv(download_path)
        stu_grades = []
        for rollno,name,subject,marks,grade,finalgrade in zip(df.rollno,df.name,df.subject,df.marks,df.grade,df.final_grade): 
            if str(rollno)==str(session['username'][11:]):
                stu_grades.append([rollno,name,subject,marks,grade,finalgrade])
        flash("Here is your Marks :)","success")
        return render_template('studentdash.html',arr=stu_grades)
    existing_user = user.find_one({'username' : session['username']})
    if session['logged_in'] and existing_user['type']=='Student':
        return redirect('/student')
    elif not session['logged_in']:
        flash("You need to be Logged in","danger")
        return redirect("/home")
    elif not existing_user['type']=='Student':
        flash("You Cannot View the marks!! Login as a Student","danger")
        return redirect("/home")
    
#Faculty Dashboard
@app.route('/faculty',methods=['GET','POST'])
def faculty_dash():
    if request.method == 'POST':
        print(request.form['comment'])
        user.update_one( {"username":session['username']}, {"$pull": {"comments":request.form['comment']}})
        return redirect('/faculty')
    existing_user = user.find_one({'username' : session['username']})
    if session['logged_in'] and existing_user['type']=='Faculty':
        comments = existing_user['comments']
        return render_template('facultydash.html',comments=comments)
    elif not session['logged_in']:
        flash("You are not Logged in","danger")
        return redirect("/home")
    else:
        flash("You cannot access the faculty dashboard!! Login as a Faculty","danger")
        return redirect("/home")

def calc_grades(sub):
    l=[]
    for a in sub:
        a=int(a)
        l.append(a) 
        
    zscores=st.zscore(l) 
    
    ans=[]
    for val in zscores:
        ans.append(st.norm.cdf(val)*100) #ans contains the z score percenile of the each mark
        
    grades=[]
    for use in ans:
        c=use*1.0
        if(c>85):
            grades.append('O')
        elif(c>75):
            grades.append('A+')
        elif(c>65):
            grades.append('A')
        elif(c>60):
            grades.append('B+')
        elif(c>55):
            grades.append('B')
        elif(c>50):
            grades.append('C')
        elif(c>40):
            grades.append('P')
        else:
            grades.append('F') 
            
    return grades
        
def grace(req,grades):
    filename = request.form['u_batch']+request.form['u_dept']+request.form['u_section']+"grace.csv"
    path = "upload/"+filename
    download_path = "./marksheet_folder/"+filename
    print(storage.child(path))
    storage.child(path).download(download_path)
    my_file = Path(download_path)
    if my_file.is_file():
        grace = pd.read_csv(download_path)
        y1=grace["amma"]
        y2=grace["sports"]
        y3=grace["nss"]
        glist=[]
        for i in range(10):
            temp=math.ceil((int(y1[i]) + int(y2[i]) + int(y3[i])))
            glist.append(temp)
        print(glist)
        new_grades = grades[:]
        for i in range(0,10):
            k=i
            while glist[i]>0 and k<=29:
                if grades[k] == "F":
                    new_grades[k]="P"
                    glist[i]-=10
                elif (grades[k] =='P'):
                    new_grades[k]="C"
                    glist[i]-=10
                elif (grades[k]=='C') :
                    new_grades[k]="B"
                    glist[i]-=10
                elif (grades[k] =='B') :
                    new_grades[k]="B+"
                    glist[i]-=10
                elif (grades[k] =='B+') :
                    new_grades[k]="A"
                    glist[i]-=10
                elif (grades[k]=='A') :
                    new_grades[k]="A+"
                    glist[i]-=10
                elif (grades[k]=='A+'):
                    new_grades[k]="O"
                    glist[i]-=10
                else:
                    new_grades[k]="O"
                    glist[i]-=10
                k += 10       
        print("old grades",grades)
        print("new_grades",new_grades)            
        return new_grades
    else:
        flash("Grace Mark Uploaded Successfully","success")
        return redirect('/faculty')
    
#Upload Excel File    
@app.route('/upload', methods = ['GET', 'POST'])
def upload_file():
    if request.method =='POST':
        if request.form['submit']=='marks':
            file = request.files['file']
            df=pd.read_csv(file)

            y=df.loc[:,"ROLLNO"]
            n=df["NAME"]
            num = 0
            x=df["MARKS"]
            s = df["SUBJECT"]
            req = request.form
            grades = []
            for i in range(3):
                sub = x.iloc[num:num+10]
                grades += calc_grades(sub)
                num+=10
            new_grades = grace(req,grades)
            df1 = pd.DataFrame({'rollno':y,'name':n,'subject':s,'marks':x,'grade':grades,'final_grade':new_grades})
            # print(df1)
            filename = request.form['u_batch']+request.form['u_dept']+request.form['u_section']+".csv"
            df1.to_csv("./marksheet_folder/"+filename)
            path = "upload/"+filename
            upload_path = "./marksheet_folder/"+filename
            storage.child(path).put(upload_path)
            flash("Marksheet Uploaded Successfully","success")
            return redirect('/faculty')
        else:
            file = request.files['file']
            df=pd.read_csv(file)
            filename = request.form['u_batch']+request.form['u_dept']+request.form['u_section']+"grace.csv"
            df.to_csv("./marksheet_folder/"+filename)
            path = "upload/"+filename
            upload_path = "./marksheet_folder/"+filename
            storage.child(path).put(upload_path)
            flash("Grace Mark Uploaded Successfully","success")
            return redirect('/faculty')
    existing_user = user.find_one({'username' : session['username']})
    if session['logged_in'] and existing_user['type']=='Faculty':
        return render_template('facultydash.html')
    elif not session['logged_in']:
        flash("You need to be Logged in","danger")
        return redirect("/home")
    elif not existing_user['type']=='Student':
        flash("You Cannot Upload the marks!! Login as a Faculty","danger")
        return redirect("/home")

#Download Excel File
@app.route('/download',methods = ['GET', 'POST'])
def download_file():
    if request.method =='POST':
        filename = request.form['d_batch']+request.form['d_dept']+request.form['d_section']+".csv"
        path = "upload/"+filename
        download_path = "./marksheet_folder/"+filename
        storage.child(path).download(download_path)
        flash("Marksheet Downloaded Successfully","success")
        return send_file(download_path, as_attachment=True)
        # return redirect('/fasculty')
    existing_user = user.find_one({'username' : session['username']})
    if session['logged_in'] and existing_user['type']=='Faculty':
        return render_template('facultydash.html')
    elif not session['logged_in']:
        flash("You need to be Logged in","danger")
        return redirect("/home")
    elif not existing_user['type']=='Student':
        flash("You Cannot Upload the marks!! Login as a Faculty","danger")
        return redirect("/home")
        
@app.route('/logout',methods=['GET'])
def logout():
    session['logged_in'] = False
    session['username'] = None
    flash('You are logged out','danger')
    return redirect('/home')


if __name__ == '__main__':
    app.secret_key = 'youcantseeme'
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
#     app.run(host='0.0.0.0', port=int(sys.argv[1]))
    
