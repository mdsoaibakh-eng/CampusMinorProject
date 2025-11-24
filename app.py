import os
from flask import Flask, render_template, redirect, url_for, request
from dotenv import load_dotenv
from models import db, Item
from markupsafe import Markup, escape

load_dotenv()
def create_app():
    app = Flask(__name__, template_folder='templates', static_folder='static')
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', '123456')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


    



    db.init_app(app)

    with app.app_context():
        db.create_all()

    @app.template_filter('nl2br')    
    def nl2br_filter(s):
        if s is None:
            return ''
        
    return Markup('<br>'.join(escape(s).splitlines()))


if __name__=='__main__':
    create_app().run(debug=True)   
















































   # @app.route('/')
   # def index():
    #    items = Item.query.all()
    #    return render_template('index.html', items=items)

   # @app.route('/add', methods=['POST'])
   # def add_item():
   #     title = request.form.get('title')
   #     description = request.form.get('description')
   #     new_item = Item(title=title, description=description)
   #     db.session.add(new_item)
   ##     db.session.commit()
    #    return redirect(url_for('index'))

    #@app.route('/delete/<int:item_id>')
   # def delete_item(item_id):
    #    item = Item.query.get_or_404(item_id)
     #   db.session.delete(item)
      #  db.session.commit()
       # return redirect(url_for('index'))

   # return app

    
