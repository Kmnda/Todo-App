import os
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import OperationalError
from prometheus_flask_exporter import PrometheusMetrics

app = Flask(__name__)
metrics = PrometheusMetrics(app) # Automatically exposes /metrics for Prometheus later

# CONFIGURATION: Load from Environment Variables (Secure)
DB_USER = os.getenv('POSTGRES_USER', 'user')
DB_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'pass')
DB_HOST = os.getenv('POSTGRES_HOST', 'db')
DB_NAME = os.getenv('POSTGRES_DB', 'todo_db')

app.config['SQLALCHEMY_DATABASE_URI'] = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:5432/{DB_NAME}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# DATABASE MODEL
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)

    def to_dict(self):
        return {"id": self.id, "content": self.content}

# Initialize DB (In production, you would use Flask-Migrate)
with app.app_context():
    db.create_all()

# ENDPOINTS
@app.route('/health', methods=['GET'])
def health_check():
    """Checks if the app is running and can connect to the DB"""
    try:
        # Perform a real query to check DB connection
        db.session.execute(db.text('SELECT 1'))
        return jsonify({"status": "up", "db_connection": True}), 200
    except Exception as e:
        return jsonify({"status": "down", "db_connection": False, "error": str(e)}), 500

@app.route('/tasks', methods=['GET'])
def get_tasks():
    tasks = Task.query.all()
    return jsonify([t.to_dict() for t in tasks])

@app.route('/task', methods=['POST'])
def create_task():
    data = request.get_json()
    if not data or 'content' not in data:
        return jsonify({"error": "Content is required"}), 400
    new_task = Task(content=data['content'])
    db.session.add(new_task)
    db.session.commit()
    return jsonify(new_task.to_dict()), 201

@app.route('/task', methods=['DELETE'])
def delete_task():
    task_id = request.args.get('id')
    task = Task.query.get(task_id)
    if task:
        db.session.delete(task)
        db.session.commit()
        return jsonify({"message": "Deleted"}), 200
    return jsonify({"error": "Task not found"}), 404

if __name__ == '__main__':
    # Host 0.0.0.0 is required for Docker
    app.run(host='0.0.0.0', port=5000)