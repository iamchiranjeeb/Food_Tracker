from flask import Flask,render_template,g,request,redirect,url_for
import sqlite3
from datetime import datetime
from database import connect_db,get_db

app = Flask(__name__)

@app.teardown_appcontext
def close_db(error):
    if hasattr(g,'sqlite_db'):
        g.sqlite_db.close()

@app.route('/',methods=["POST",'GET'])
def index():
    try:
        db = get_db()
        if request.method == 'POST':
            date = request.form['date']
            dt = datetime.strptime(date,'%Y-%m-%d')
            db_date = datetime.strftime(dt,'%Y%m%d')
            db.execute('insert into log_date (entry_date) values (?)',[db_date])
            db.commit()

        cur = db.execute('select log_date.entry_date,sum(food.protein) as protein,sum(food.carbohydrate) as carbohydrate, sum(food.fat) as fat, sum(food.calories)\
         as calories from log_date join food_date on food_date.log_date_id = log_date.id join food on food.id = food_date.food_id\
          group by log_date.id order by log_date.entry_date desc')
        result = cur.fetchall()
        date_res = []
        for i in result:
            single_date = {}
            single_date['entry_date'] = i['entry_date']
            single_date['protein'] = i['protein']
            single_date['carbohydrate'] = i['carbohydrate']
            single_date['fat'] = i['fat']
            single_date['calories'] = i['calories']

            d = datetime.strptime(str(i['entry_date']),'%Y%m%d')
            single_date['pretty_date'] = datetime.strftime(d,'%B %d, %Y')
            date_res.append(single_date)

        return render_template('home.html',rest = date_res)
    except Exception as e:
        return "<h1>Error Ocuured : {} </h1>".format(e)

@app.route('/view/<date>', methods=['GET', 'POST'])
def view(date):
    try:

        db = get_db()
        cur = db.execute('select id, entry_date from log_date where entry_date = ?', [date])
        date_result = cur.fetchone()
        if request.method == 'POST':
            db.execute('insert into food_date (food_id,log_date_id) values (?,?)',[request.form['food-select'],date_result['id']])
            db.commit()

        d = datetime.strptime(str(date_result['entry_date']), '%Y%m%d')
        pretty_date = datetime.strftime(d, '%B %d, %Y')

        food_cur = db.execute('select id, name from food')
        food_results = food_cur.fetchall()

        log_cur = db.execute('select food.name, food.protein, food.carbohydrate, food.fat, food.calories from log_date join food_date on food_date.log_date_id = log_date.id join food on food.id = food_date.food_id where log_date.entry_date = ?', [date])
        log_results = log_cur.fetchall()

        totals = {}
        totals['protein'] = 0
        totals['carbohydrate'] = 0
        totals['fat'] = 0
        totals['calories'] = 0

        for food in log_results:
            totals['protein'] += food['protein']
            totals['carbohydrate'] += food['carbohydrate']
            totals['fat'] += food['fat']
            totals['calories'] += food['calories']


        return render_template('day.html', entry_date= date_result['entry_date'] ,pretty_date=pretty_date,\
         food_results=food_results,log_results=log_results,totals=totals)
    except Exception as e:
        return "<h1>Error Ocuured : {} </h1>".format(e)

@app.route('/food',methods=['GET','POST'])
def food():
    try:
        db = get_db()
        if request.method == 'POST':
            name = request.form['food-name']
            protein = int(request.form['protein'])
            carbohydrate = int(request.form['carbohydrates'])
            fat = int(request.form['fat'])
            calories = protein*4 + carbohydrate*4 + fat*9

            db.execute('insert into food(name,protein,carbohydrate,fat,calories) values (?,?,?,?,?)',\
            [name, protein,carbohydrate,fat,calories])
            db.commit()

        cur = db.execute('select name,protein,carbohydrate,fat,calories from food')
        result = cur.fetchall()
        return render_template('add_food.html',result=result), 200
    except  Exception as e:
        return "<h1>Error Ocuured : {} </h1>".format(e),400

@app.route('/delete_food/<string:name>',methods=['POST'])
def delete_food(name):
    db = get_db()
    db.execute('delete from food where name = ?',[name])
    db.commit()
    return redirect('/food')

@app.route('/delete_date/<string:entry_date>')
def delete_date(entry_date):

    db = get_db()
    db.execute('delete from log_date where entry_date = ?',[entry_date])
    db.commit()
    return redirect('/')


if __name__ == '__main__':
    app.run(debug=True,port=4465)
