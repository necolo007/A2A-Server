from flask import Flask, request, jsonify, Response

app = Flask('a2a-server')
@app.route('/index')
def hello_world():
    age = request.args.get('age')
    return 'Hello, World!' + str(age)

@app.route('/add', methods=['POST'])
def add() -> Response:
    data = request.get_json()
    xx = request.form.get('xx')
    uu = request.json['uu'] # 这是字典形式
    a = data.get('a', 0)
    b = data.get('b', 0)
    return jsonify({'result': a + b, 'xx': xx, 'uu': uu})

def main():
    print("Hello from a2a-server!")



if __name__ == "__main__":
    main()
    app.run()
