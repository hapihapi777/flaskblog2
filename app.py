from flask import Flask
from flask import render_template, request, redirect, url_for
import psycopg2
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pytz
 
app = Flask(__name__)
# app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://localhost/fblog"
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://hcrrnqrjoezdpt:561263e6bcbfc2d99e39c56c0d67816eecedfcc6362cd0d7daaa7523d3166fad@ec2-3-225-110-188.compute-1.amazonaws.com:5432/d78h3uhegfieod"
db = SQLAlchemy(app)

class BlogArticle(db.Model):
    __tablename__ = "article"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(), nullable=False)
    body = db.Column(db.String(), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now(pytz.timezone('Asia/Tokyo')))


# app.config['PASSWORD'] = "7890"
  
 
@app.route('/', methods=['GET'])
def blog():
    if request.method == 'GET':
        blogarticles = BlogArticle.query.all()
        return render_template('index.html', blogarticles=blogarticles)

@app.route('/create', methods=['GET', 'POST'])
def create():
    if request.method == "POST":
        title = request.form.get('title')
        body = request.form.get('body')
        blogarticle = BlogArticle(title=title, body=body)
        db.session.add(blogarticle)
        db.session.commit()
        return redirect('/')
    else:
        return render_template('create.html')

@app.route('/update', methods=['GET'])
def update(id):
    blogarticle = BlogArticle.query.get(id)
    return render_template('index.html', blogarticle=blogarticle)


@app.route('/update', methods=['POST'])
def upde():
    post_id = request.form.get("post_id")
    blogarticle = BlogArticle.query.filter(BlogArticle.id == post_id)
    blogarticle.title = request.form.get('title')
    blogarticle.body = request.form.get('body')
    return render_template('master.html', blogarticle=blogarticle)

@app.route('/delete', methods=['POST'])
def delete():
    post_id = request.form.get("post_id")
    blogarticle = BlogArticle.query.filter(BlogArticle.id == post_id).one()
    db.session.delete(blogarticle)
    db.session.commit()
    return redirect('/')

@app.route('/master', methods=['GET'])
def master_get():
    blogarticles = BlogArticle.query.all()
    return render_template('index.html', blogarticles=blogarticles)

@app.route('/master', methods=['POST'])
def login():
#   password = request.form.get("possword")
#   if password == "7890":
    blogarticles = BlogArticle.query.all()
    return render_template('/master.html', blogarticles=blogarticles)

# デバッグモード用
if __name__ == "__main__":
    app.run(debug=True)

# 8/22(月)
