from curses import flash
import os
from flask import Flask
from flask import render_template, request, redirect
from flask_login import UserMixin, LoginManager, login_user, logout_user, login_required
import psycopg2
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pytz
from werkzeug.security import generate_password_hash, check_password_hash
 
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://localhost/fblog"
# app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://hcrrnqrjoezdpt:561263e6bcbfc2d99e39c56c0d67816eecedfcc6362cd0d7daaa7523d3166fad@ec2-3-225-110-188.compute-1.amazonaws.com:5432/d78h3uhegfieod"
db = SQLAlchemy(app)

# デバッグモード用
if __name__ == "__main__":
    app.run(debug=True)

login_manager = LoginManager()
login_manager.init_app(app)
# ログイン用 製作中

class BlogArticle(db.Model):
    __tablename__ = "article"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(), nullable=False)
    body = db.Column(db.String(), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now(pytz.timezone('Asia/Tokyo')))
  
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(10))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# topページ
@app.route('/', methods=['GET', 'POST'])
def blog():
    # if request.method == 'GET':
        blogarticles = BlogArticle.query.all()
        return render_template('index.html', blogarticles=blogarticles)

# 編集可能なmasterページにPOSTで来た場合(正常動作)とそれ以外に設定
@app.route('/master', methods=['POST'])
@login_required
def master():
    if request.method == "POST":
    # and request.form.get("possword") == "7890":
        blogarticles = BlogArticle.query.all()
        return render_template('/master.html', blogarticles=blogarticles)
    else:
        return redirect('/')

# errorページに飛ぶ用
@app.route('/error', methods=['GET', 'POST'])
def error():
    return render_template('/error.html')

# signupページに飛ぶだけ
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == "POST":
        return render_template('/signup.html')
    else:
        return redirect('/')

# loginページに飛ぶだけ
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        return render_template('/login.html')
    else:
        return redirect('/')

# signupページ内でuser登録をする為の関数(全然上手くいかない)
@app.route('/do_signup', methods=['GET', 'POST'])
def do_signup():
    if request.method == "POST":
        username = request.form.get('register_user')
        password = request.form.get('register_pass')
        # Userのインスタンスを作成
        user = User(username=username, password=generate_password_hash(password, method='sha256'))
        
        db.session.add(user)
        db.session.commit()
        flash('登録に成功')
        return render_template('/login')
    else:
        flash('登録に失敗')
        return render_template('/error.html')

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
            return redirect('/master.html')
        else:
            flash('入力に失敗')
            render_template('/error.html')
    else:
        return render_template('/error.html')

# ログアウト用
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')

# 新規作成画面
@app.route('/create', methods=['GET', 'POST'])
@login_required
def craete():
    if request.method == "POST":
        return render_template('create.html')
    else:
        return redirect('/')

# 新規作成メソッド
@app.route('/do_create', methods=['GET', 'POST'])
@login_required
def do_create():
    if request.method == "POST":
        title = request.form.get('title')
        body = request.form.get('body')
        blogarticle = BlogArticle(title=title, body=body)
        db.session.add(blogarticle)
        db.session.commit()
        return redirect('/')
    else:
        return redirect('/')

# updateにPOSTで来た場合(正常動作)
# とそれ以外に設定
@app.route('/update', methods=['GET', 'POST'])
@login_required
def update():
    if request.method == "POST":
        post_id = request.form.get("post_id")
        blogarticle = BlogArticle.query.filter(BlogArticle.id == post_id).one()
        return render_template('update.html', blogarticle=blogarticle)
    else:
        return redirect('/')

# updateページから更新する場合
@app.route('/do_update', methods=['POST'])
@login_required
def do_update():
    post_id = request.form.get("post_id")
    blogarticle = BlogArticle.query.filter(BlogArticle.id == post_id).one()
    blogarticle.title = request.form.get('title')
    blogarticle.body = request.form.get('body')
    db.session.add(blogarticle)
    db.session.commit()
    return redirect('/')

# 削除する場合(現状一発で削除されてしまう)
@app.route('/delete', methods=['POST'])
@login_required
def delete():
    post_id = request.form.get("post_id")
    blogarticle = BlogArticle.query.filter(BlogArticle.id == post_id).one()
    db.session.delete(blogarticle)
    db.session.commit()
    return redirect('/')
