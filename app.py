import os
from datetime import datetime, timedelta

# from turtle import pos
# import datetime
import cv2
import numpy as np
import psycopg2
import pytz
from flask import (Flask, flash, make_response, redirect, render_template,
                   request, session, url_for)
from flask_bootstrap import Bootstrap
from flask_login import (LoginManager, UserMixin, login_required, login_user,
                         logout_user)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
# app.config['SECRET_KEY'] = "abcdefghijklmn"
bootstrap = Bootstrap(app)
app.permanent_session_lifetime = timedelta(minutes=60)

# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sqliteblog.db'
# app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://localhost/fblog2"
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://hcrrnqrjoezdpt:561263e6bcbfc2d99e39c56c0d67816eecedfcc6362cd0d7daaa7523d3166fad@ec2-3-225-110-188.compute-1.amazonaws.com:5432/d78h3uhegfieod"
db = SQLAlchemy(app)

# ログイン用
login_manager = LoginManager()
login_manager.init_app(app)

class BlogArticle(db.Model):
    __tablename__ = "article"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text, nullable=False)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now(pytz.timezone('Asia/Tokyo')))
    img_path = db.Column(db.Text, nullable=True)
  
class User(UserMixin, db.Model):
    __tablename__ = "signup"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(100))


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))



# ---ログイン前ページ---
# topページ
# logoutの時にPOSTで来る為POST残し
@app.route('/', methods=['GET', 'POST'])
def blog():
    blogarticles = BlogArticle.query.all()
    # flash("Flashテスト")
    return render_template('index.html', blogarticles=blogarticles)

# signupページに飛ぶだけ
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    return render_template('/signup.html')

# loginページに飛ぶだけ
@app.route('/login', methods=['GET', 'POST'])
def login():
    return render_template('/login.html')

# signupページ内でuser登録をする為の関数
@app.route('/do_signup', methods=['GET', 'POST'])
def do_signup():
    if request.method == "POST":
        username = request.form.get('register_user')
        password = request.form.get('register_pass')
        if username != "" and password != "":
            # Userのインスタンスを作成
            user = User(username=username, password=generate_password_hash(password, method='sha256'))
            db.session.add(user)
            db.session.commit()
            flash('登録に成功')
            return redirect(url_for('login'))
        if username == "":
            flash('usernameが空欄です')
        if password == "":
            flash('passwordが空欄です')
        return redirect(url_for('signup'))
    else:
     flash('登録に失敗')
     return redirect(url_for('signup'))

# 登録済みのuserが入力された場合にのみmasterページに飛ぶ関数
# ログインに必要なデータ入力もあるのでPOSTに限定
# cookieとsessionを設定する
@app.route('/do_login', methods=['GET', 'POST'])
def do_login():
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')

        # Userテーブルからusernameに一致するユーザを取得
        user = User.query.filter_by(username=username).first()
        if check_password_hash(user.password, password):
            login_user(user)
            session.permanent = True
            session["l_username"] = username
            res = make_response(redirect(url_for('master')))
            res.set_cookie('l_username', username)
            return res
        else:
            flash('入力に失敗')
            return redirect(url_for('login'))
    else:
        return redirect(url_for('logout'))




# ---ログイン後ページ---
# 編集可能なmasterページ
# ログイン中ならGET,POST共に接続可能にする
@app.route('/master', methods=['GET', 'POST'])
@login_required
def master():
    l_username = request.cookies.get('l_username')
    blogarticles = BlogArticle.query.all()
    # img_path = BlogArticle.img_path
    return render_template('/master.html', blogarticles=blogarticles, username=l_username)


# 新規作成画面
# 飛ぶだけなのでログイン中ならGET,POST共に接続可能にする
@app.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    l_username = request.cookies.get('l_username')
    today = datetime.now(pytz.timezone('Asia/Tokyo')).strftime("%Y%m%d%H%M%S%f")

    day_of_week = ("月", "火", "水", "木", "金", "土", "日")
    return render_template('create.html', 
    username=l_username, today=today, day_of_week=day_of_week
    )

# 新規作成メソッド
# データを扱う作業なので、接続中でもPOSTメソッドのみ
@app.route('/do_create', methods=['GET', 'POST'])
@login_required
def do_create():
    if request.method == "POST":
        
        title = request.form.get('title')
        body = request.form.get('body')
        
        if title != "" and body != "": # タイトルと記事が空欄じゃなかった場合
            if str(request.files['img']) != "<FileStorage: '' ('application/octet-stream')>": #imgが空欄じゃなかった場合、アップロードする(無理矢理設定した)
                img_dir = "static/images/"
                stream = request.files['img'].stream
                img_array = np.asarray(bytearray(stream.read()), dtype=np.uint8)
                img = cv2.imdecode(img_array, 1)
                dt_now = datetime.now(pytz.timezone('Asia/Tokyo')).strftime("%Y%m%d%H%M%S%f")
                img_path = img_dir + str(dt_now) + ".jpg"
                cv2.imwrite(img_path, img)
            else:
                img_path=None
            blogarticle = BlogArticle(title=title, body=body, img_path=img_path)
            db.session.add(blogarticle)
            db.session.commit()
            return redirect(url_for('master'))
        if title == "":
            flash("タイトルが空欄です")
        if body == "":
            flash("記事が空欄です")
        return redirect(url_for('create'))
    else:
        return redirect(url_for('logout'))

# updateに飛ぶだけ
# GET,POST共に接続可能
@app.route('/update', methods=['GET', 'POST'])
@login_required
def update():
    blog_id = request.form.get("blog_id")
    blogarticle = BlogArticle.query.filter(BlogArticle.id == blog_id).one()
    l_username = request.cookies.get('l_username')
    res = make_response(render_template('update.html', blogarticle=blogarticle, username=l_username))
    # res.set_cookie("blog_id", blog_id)
    return res

# updateページから更新する場合
# データ扱うのでPOSTのみ
@app.route('/do_update', methods=['GET', 'POST'])
@login_required
def do_update():
    if request.method == "POST":
        blog_id = request.form.get("blog_id")
        
        blogarticle = BlogArticle.query.filter(BlogArticle.id == blog_id).one()
        title = request.form.get('title')
        body = request.form.get('body')
        if title != "" and body != "":
            blogarticle.title = title
            blogarticle.body = body
            db.session.add(blogarticle)
            db.session.commit()

            return redirect(url_for('master'))
        if title == "":
            flash("タイトルが空欄です")
        if body == "":
            flash("記事が空欄です")
        return redirect(url_for('update'))
    else:
        return redirect(url_for('logout'))


# 削除する場合(現状一発で削除されてしまう)
# POSTのみ、GETで来たら強制ログアウトさせる
@app.route('/delete', methods=['GET', 'POST'])
@login_required
def delete():
    if request.method == "POST":
        blog_id = request.form.get("blog_id")
        blogarticle = BlogArticle.query.filter(BlogArticle.id == blog_id).one()
        db.session.delete(blogarticle)
        db.session.commit()
        return redirect(url_for('master'))
    else:
        return redirect(url_for('logout'))

# ログアウト用
# GETで来てもPOSTで来てもログアウトさせる
# 持ってる情報、cookie,session共に消す
@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    session.pop('username', None)
    session.clear()
    res = make_response(redirect(url_for('blog')))
    res.delete_cookie('l_username')
    res.delete_cookie('blog_id')
    return res