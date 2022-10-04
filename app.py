# from curses import flash
import os, psycopg2, pytz
from flask import Flask, render_template, request, make_response, session, redirect, url_for
from flask_login import UserMixin, LoginManager, login_user, logout_user, login_required
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
 
app = Flask(__name__)
# app.config['SECRET_KEY'] = os.urandom(24)
app.config['SECRET_KEY'] = "secret"


# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sqliteblog.db'
# app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://localhost/fblog2"
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://hcrrnqrjoezdpt:561263e6bcbfc2d99e39c56c0d67816eecedfcc6362cd0d7daaa7523d3166fad@ec2-3-225-110-188.compute-1.amazonaws.com:5432/d78h3uhegfieod"
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
# ログイン用

class BlogArticle(db.Model):
    __tablename__ = "article"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text, nullable=False)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now(pytz.timezone('Asia/Tokyo')))
  
class User(UserMixin, db.Model):
    __tablename__ = "signup"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(100))


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))




# topページ
@app.route('/', methods=['GET', 'POST'])
def blog():
    blogarticles = BlogArticle.query.all()
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
        # Userのインスタンスを作成
        user = User(username=username, password=generate_password_hash(password, method='sha256'))
        db.session.add(user)
        db.session.commit()
        # flash('登録に成功')
        return redirect(url_for('login'))
    else:
        # flash('登録に失敗')
        return redirect(url_for('logout'))

# 登録済みのuserが入力された場合にのみmasterページに飛ぶ関数
@app.route('/do_login', methods=['GET', 'POST'])
def do_login():
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')

        # Userテーブルからusernameに一致するユーザを取得
        user = User.query.filter_by(username=username).first()

        if check_password_hash(user.password, password):
            login_user(user)
            res = make_response(redirect(url_for('master')))
            res.set_cookie('l_username', username)
            return res
        else:
            # flash('入力に失敗')
            return render_template('/login.html')
    else:
        return redirect(url_for('logout'))





# 編集可能なmasterページにPOSTで来た場合(正常動作)とそれ以外に設定
@app.route('/master', methods=['GET', 'POST'])
@login_required
def master():
    l_username = request.cookies.get('l_username')
    blogarticles = BlogArticle.query.all()
    return render_template('/master.html', blogarticles=blogarticles, username=l_username)

# 新規作成画面
@app.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    l_username = request.cookies.get('l_username')
    return render_template('create.html', 
    username=l_username
    )

# 新規作成メソッド
@app.route('/do_create', methods=['GET', 'POST'])
@login_required
def do_create():
    if request.method == "POST":
        title = request.form.get('title')
        body = request.form.get('body')
        if title == "":
            return redirect(url_for('create'))
        else:
            blogarticle = BlogArticle(title=title, body=body)
            db.session.add(blogarticle)
            db.session.commit()
            return redirect(url_for('master'))
    else:
        return redirect(url_for('logout'))

# updateにPOSTで来た場合
# とそれ以外に設定
@app.route('/update', methods=['GET', 'POST'])
@login_required
def update():
    post_id = request.form.get("post_id")
    blogarticle = BlogArticle.query.filter(BlogArticle.id == post_id).one()
    l_username = request.cookies.get('l_username')
    return render_template('update.html', blogarticle=blogarticle, username=l_username)

# updateページから更新する場合
@app.route('/do_update', methods=['GET', 'POST'])
@login_required
def do_update():
    if request.method == "POST":
        post_id = request.form.get("post_id")
        username = request.form.get('username')
        blogarticle = BlogArticle.query.filter(BlogArticle.id == post_id).one()
        if request.form.get('title') == "":
            return render_template('update.html', blogarticle=blogarticle, username=username, comment="＊タイトルを入れてください")
        else:
            blogarticle.title = request.form.get('title')
            blogarticle.body = request.form.get('body')
            db.session.add(blogarticle)
            db.session.commit()
            return redirect(url_for('master'))
    else:
        return redirect(url_for('logout'))

# 削除する場合(現状一発で削除されてしまう)
@app.route('/delete', methods=['GET', 'POST'])
@login_required
def delete():
    if request.method == "POST":
        post_id = request.form.get("post_id")
        blogarticle = BlogArticle.query.filter(BlogArticle.id == post_id).one()
        db.session.delete(blogarticle)
        db.session.commit()
        return redirect(url_for('master'))
    else:
        return redirect(url_for('logout'))

# ログアウト用
@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    res = make_response(redirect(url_for('blog')))
    res.delete_cookie('l_username')
    return res