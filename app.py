import os
import time
import random
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import OperationalError
from prometheus_flask_exporter import PrometheusMetrics
from prometheus_client import Counter, Histogram

app = Flask(__name__)

# --- 1. SRE METRICS CONFIGURATION ---
metrics = PrometheusMetrics(app)

# Custom Metric: Counters (Always go up)
# Tracks business value: How many tasks are users actually making?
task_created_counter = Counter('todo_tasks_created_total', 'Total number of tasks created')
task_deleted_counter = Counter('todo_tasks_deleted_total', 'Total number of tasks deleted')

# Custom Metric: Histogram (Buckets of time)
# Tracks performance: How long does the Database take to save/delete?
# We want to catch slow queries before users complain.
db_latency = Histogram('todo_db_operation_latency_seconds', 'Time spent processing DB operations', ['operation'])

# CONFIGURATION
DB_USER = os.getenv('POSTGRES_USER', 'user')
DB_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'pass')
DB_HOST = os.getenv('POSTGRES_HOST', 'db')
DB_NAME = os.getenv('POSTGRES_DB', 'todo_db')

app.config['SQLALCHEMY_DATABASE_URI'] = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:5432/{DB_NAME}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)

    def to_dict(self):
        return {"id": self.id, "content": self.content}

with app.app_context():
    db.create_all()

# --- ENDPOINTS ---

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "up"}), 200

@app.route('/tasks', methods=['GET'])
def get_tasks():
    # Measure how long the SELECT takes
    with db_latency.labels(operation='select').time():
        tasks = Task.query.all()
    return jsonify([t.to_dict() for t in tasks])

@app.route('/task', methods=['POST'])
def create_task():
    data = request.get_json()
    if not data or 'content' not in data:
        return jsonify({"error": "Content is required"}), 400
    
    # Measure DB Write Time
    with db_latency.labels(operation='insert').time():
        new_task = Task(content=data['content'])
        db.session.add(new_task)
        db.session.commit()
    
    # Increment our custom business metric
    task_created_counter.inc()
    
    return jsonify(new_task.to_dict()), 201

@app.route('/task', methods=['DELETE'])
def delete_task():
    task_id = request.args.get('id')
    
    with db_latency.labels(operation='select_for_delete').time():
        task = Task.query.get(task_id)
        
    if task:
        with db_latency.labels(operation='delete').time():
            db.session.delete(task)
            db.session.commit()
        
        # Increment deleted metric
        task_deleted_counter.inc()
        return jsonify({"message": "Deleted"}), 200
        
    return jsonify({"error": "Task not found"}), 404

# --- NEW: CHAOS ENDPOINT ---
# Hit this to prove your Alerting works!
@app.route('/simulate-error', methods=['GET'])
def simulate_error():
    # 50% chance of failure
    if random.choice([True, False]):
        # This 500 error will show up in Grafana
        raise Exception("Random Chaos Failure Triggered!")
    return jsonify({"message": "You got lucky! No error this time."}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)