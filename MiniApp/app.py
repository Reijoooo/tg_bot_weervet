from flask import Flask, render_template

app = Flask(__name__)

@app.route('/mini-app')
def mini_app():
    return render_template('/webapp/mini_app.html')

if __name__ == '__main__':
    app.run(debug=True)
