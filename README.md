# The Observable Todo API: End-to-End DevSecOps Pipeline

![DevOps](https://img.shields.io/badge/DevOps-Pipeline-blue?style=for-the-badge&logo=jenkins)
![Terraform](https://img.shields.io/badge/Terraform-Infrastructure-purple?style=for-the-badge&logo=terraform)
![Docker](https://img.shields.io/badge/Docker-Containerization-blue?style=for-the-badge&logo=docker)
![AWS](https://img.shields.io/badge/AWS-Cloud-orange?style=for-the-badge&logo=amazon-aws)
![Prometheus](https://img.shields.io/badge/Prometheus-Monitoring-orange?style=for-the-badge&logo=prometheus)
![Grafana](https://img.shields.io/badge/Grafana-Visualization-orange?style=for-the-badge&logo=grafana)
![Python](https://img.shields.io/badge/Python-3.9-yellow?style=for-the-badge&logo=python)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-13-blue?style=for-the-badge&logo=postgresql)

## 📖 Project Overview

The **Observable Todo API** is a comprehensive reference implementation of a modern, secure, and observable DevSecOps pipeline. It demonstrates the full lifecycle of a software project, from infrastructure provisioning as code to automated deployment and deep system observability.

In the modern landscape of software engineering, deploying an application is only half the battle. The ability to monitor, debug, and secure that application in a hostile environment is what separates a "toy project" from a production-grade system. This project is not just a "Hello World" application; it is a battle-tested architecture designed to solve real-world challenges such as:

*   **Security-First Networking:** How to monitor applications without exposing sensitive ports (like 9090 or 3000) to the public internet, using SSH Bastion tunneling.
*   **Infrastructure as Code (IaC):** Eliminating manual server configuration and configuration drift by defining the entire environment (VPC, Security Groups, EC2) in Terraform.
*   **Automated CI/CD:** Using Jenkins to orchestrate build, test, and deploy cycles with zero manual intervention, including dynamic secret injection.
*   **Container Orchestration:** Managing multi-container dependencies (App, DB, Monitoring) using Docker Compose, ensuring that the database is healthy before the app starts.
*   **Deep Observability:** Implementing a full monitoring stack (Prometheus & Grafana) to visualize application health, request rates, and error budgets.

---

## 📑 Table of Contents

1.  [Architecture & Design Principles](#-architecture--design-principles)
2.  [Prerequisites & Local Setup](#-prerequisites--local-setup)
3.  [Phase 1: Infrastructure Provisioning (Terraform)](#phase-1-infrastructure-provisioning-security-configuration)
    *   [1.1 Deep Dive: Security Groups](#11-deep-dive-security-groups)
    *   [1.2 Infrastructure Automation](#12-infrastructure-automation-with-terraform)
    *   [1.3 Solving the "Permission Denied" Challenge](#13-solving-the-permission-denied-challenge)
4.  [Phase 2: CI/CD Pipeline & Container Orchestration](#phase-2-cicd-pipeline-configuration--container-orchestration)
    *   [2.1 Jenkins Initialization](#21-jenkins-initialization--security-setup)
    *   [2.2 Container Orchestration (Docker Compose)](#22-container-orchestration-docker-compose)
    *   [2.3 The Pipeline Execution Strategy](#23-the-pipeline-execution-strategy)
5.  [Phase 3: Deep Dive: The Application Logic](#phase-3-deep-dive-the-application-logic)
6.  [Phase 4: Secure Remote Access (SSH Tunneling)](#phase-4-secure-remote-access--network-tunneling)
    *   [4.1 The "Black Box" Problem](#41-the-black-box-problem)
    *   [4.2 The Tunneling Solution](#42-the-solution-ssh-local-port-forwarding)
7.  [Phase 5: Internal Network Discovery](#phase-5-monitoring-architecture--internal-service-discovery)
    *   [5.1 The "Split Network" Challenge](#51-the-split-network-challenge)
    *   [5.2 The "Name Game" DNS Fix](#52-the-name-game-dns-resolution-failure)
8.  [Phase 6: Dashboard Engineering & Visualization](#phase-6-dashboard-engineering--custom-metrics)
    *   [6.1 PromQL Deep Dive](#61-implementing-custom-panels-promql)
9.  [Phase 7: Load Testing & System Validation](#phase-7-load-testing--system-validation)
10. [Phase 8: Cost Management & Teardown](#phase-8-infrastructure-teardown-cost-management)
11. [Appendix A: Operational Cheatsheet](#appendix-a-operational-cheatsheet)
12. [Appendix B: Troubleshooting FAQ](#appendix-b-troubleshooting-faq)

---

## 🏗 Architecture & Design Principles

The system is built on **AWS** using **EC2** for compute. The architecture follows a **"Zero Trust"** model where only essential ports (SSH, HTTP) are exposed. All internal tools (Jenkins, Prometheus, Grafana) are accessed via encrypted SSH tunnels.

### Core Components & Technology Stack

*   **Application Logic:** A Python Flask API served via WSGI. It includes `prometheus_flask_exporter` middleware to automatically expose RED (Rate, Errors, Duration) metrics.
*   **Database Layer:** PostgreSQL 13 (Alpine edition) for persistent storage. It is configured with a persistent Docker volume to survive container restarts.
*   **Infrastructure Layer:** Terraform (AWS Provider) manages the VPC, Subnets, Internet Gateways, Route Tables, and EC2 instances.
*   **Orchestration Layer:** Docker Compose manages the lifecycle of the application stack. Jenkins manages the deployment pipeline.
*   **Observability Layer:**
    *   **Prometheus:** A time-series database that scrapes metrics from the App and Node Exporter every 5 seconds.
    *   **Grafana:** A visualization engine that queries Prometheus to build real-time dashboards.
    *   **Node Exporter:** A daemon that exposes hardware-level metrics (CPU, RAM, Disk I/O) to Prometheus.

---

## 🛠 Prerequisites & Local Setup

Before starting, ensure you have the following installed on your local machine. This project assumes a Windows or Linux environment, but Mac users can follow along with minor adjustments to the SSH commands.

1.  **Terraform** (v1.0+): [Download Here](https://www.terraform.io/downloads). Verify with `terraform --version`.
2.  **AWS CLI**: [Download Here](https://aws.amazon.com/cli/). Verify with `aws --version`.
    *   *Configuration:* Run `aws configure` and enter your Access Key, Secret Key, and default region (e.g., `ap-southeast-1`).
3.  **Git**: For version control.
4.  **Python 3.9+**: Required to run the `traffic_generator.py` script locally.
5.  **An AWS Account**: A standard AWS account. Note that while this project uses `t3.small` (which is not free-tier eligible), it costs very little (cents) if destroyed immediately after use.

---

## Phase 1: Infrastructure Provisioning & Security Configuration

### 1.1 Deep Dive: Security Groups
The primary objective of Phase 1 was to establish a secure, reproducible infrastructure foundation for the DevSecOps pipeline. Instead of manually creating servers in the AWS Console, we utilized Terraform (Infrastructure as Code) to define our resources. This ensures that the environment can be destroyed and recreated instantly with zero configuration drift.

A critical design decision in this phase was to adopt a **"Security First"** network architecture. We deliberately restricted the AWS Security Group to block all incoming traffic on monitoring ports:
*   **Port 9090:** Prometheus (Metrics)
*   **Port 3000:** Grafana (Dashboards)
*   **Port 5000:** Flask App (API)

**The Firewall Rules:**
We only allowed the following:
*   **Inbound Rule 1:** Allow Port 22 (SSH) – Restricted to admin access.
*   **Inbound Rule 2:** Allow Port 80 (HTTP) – Public web traffic (future proofing for Nginx).

**Reasoning:** Monitoring tools expose sensitive metric data and system details. They should never be exposed directly to the public internet, as they can be vectors for reconnaissance attacks.

### 1.2 Infrastructure Automation with Terraform
We defined our infrastructure in a `main.tf` file. This file is the "source of truth" for our cloud environment.

**Key Terraform Resources:**
*   **`aws_instance`**: We chose `t3.small` because running Jenkins, Docker, Postgres, Prometheus, and Grafana simultaneously requires more than the 1GB RAM provided by `t2.micro`.
*   **`aws_key_pair`**: Dynamically uploads your local public key (`~/.ssh/aws_key.pub`) to AWS, so you can SSH in without passwords.
*   **`user_data`**: A bash script that runs on the *first boot* of the instance to install Docker and Git automatically.

**Execution Commands**
The following Terraform lifecycle commands were used to provision the environment:

```bash
# 1. Initialize the Terraform backend and download AWS providers
terraform init

# 2. Generate an execution plan to preview changes (Sanity Check)
terraform plan

# 3. Apply the infrastructure changes (Auto-approve to bypass manual confirmation)
terraform apply --auto-approve
```

**Outcome:** Terraform provisioned the EC2 instance and downloaded the private key (`aws_key`) locally for access.

### 1.3 Solving the "Permission Denied" Challenge
**The Problem:** Upon installing Docker and Jenkins, we encountered a critical error when the pipeline tried to build an image. Jenkins failed with the message:
`dial unix /var/run/docker.sock: connect: permission denied`

**Root Cause:** By default, the Docker daemon binds to a Unix socket that is owned by `root`. The `ec2-user` and the `jenkins` user do not have permission to access this socket, meaning they cannot run any docker commands.

**The Solution:** We had to modify the user groups and file permissions to grant access to the Docker socket.

**Fix Commands:**
```bash
# 1. Add the current user (ec2-user) to the 'docker' group
# This allows running docker commands without 'sudo'
sudo usermod -aG docker ec2-user

# 2. (CRITICAL FIX) Grant Read/Write permissions to the Docker Socket
# This allows the Jenkins user (which runs the pipeline) to communicate
# with the Docker daemon to spawn sibling containers.
sudo chmod 666 /var/run/docker.sock
```
*Note:* In a strict enterprise production environment, adding the Jenkins user to the `docker` group is the preferred method over `chmod 666`. However, for this educational setup, modifying the socket permissions guarantees immediate access for all service users without complex re-login procedures.

---

## Phase 2: CI/CD Pipeline Configuration & Container Orchestration

### 2.1 Jenkins Initialization & Security Setup
Although Jenkins was installed via our setup scripts, it remained in a "locked" state. To begin building pipelines, we needed to unlock the administrative console.

**Retrieving the Initial Admin Credential**
Jenkins generates a temporary cryptographic password upon first launch. Since our server has no GUI, we retrieved it via the CLI:

```bash
# Retrieve the initial administrator password
# This password is required to unlock the Jenkins UI at http://localhost:8080
sudo cat /var/lib/jenkins/secrets/initialAdminPassword
```

**Configuration Steps Taken:**
1.  **Unlock:** Pasted the retrieved password into the Jenkins portal.
2.  **Plugins:** Installed the "Suggested Plugins" pack (Git, Pipeline, Credentials Binding).
3.  **Admin User:** Created the primary admin user (`admin`).

### 2.2 Container Orchestration (Docker Compose)
Instead of running disjointed `docker run` commands, we adopted an **Orchestration Strategy** using `docker-compose.yml`. This file serves as the "Blueprint" for our application.

**The Architecture Definition:**
We defined a microservices stack:

1.  **`app` (The Todo App):**
      *   **Build Context:** Built from the local `Dockerfile`.
      *   **Port Mapping:** `5000:5000` (Maps host port 5000 to container port 5000).
      *   **Dependency:** Depends on the `db` service.
2.  **`db` (PostgreSQL):**
      *   **Image:** `postgres:13-alpine` (Lightweight production database).
      *   **Volume:** `postgres_data:/var/lib/postgresql/data`. This persists data so tasks aren't lost when containers restart.
      *   **Healthcheck:** A command `pg_isready` ensures the DB is actually accepting connections before the App tries to connect.

### 2.3 The Pipeline Execution Strategy
We defined the automation logic in a `Jenkinsfile` using Groovy script. This pipeline creates an immutable build artifact and deploys it consistently.

**The "Sibling Container" Mechanics**
Because we fixed the socket permissions in Phase 1 (`chmod 666 /var/run/docker.sock`), Jenkins was able to execute the following commands *inside* the pipeline without `sudo`. This is known as the "Docker-outside-of-Docker" pattern (accessing the host's Docker socket).

```groovy
// Snippet from Jenkinsfile
stage('Deploy to EC2') {
    steps {
        sshagent(['ec2-ssh-key']) {
            script {
                sh "docker-compose up -d --build"
            }
        }
    }
}
```

The `sshagent` plugin is crucial here: it securely injects the SSH private key (stored in Jenkins Credentials) into the agent's session, allowing the script to `scp` files to the target server and run commands via `ssh`.

---

## Phase 3: Deep Dive: The Application Logic

The core application `app.py` is a Flask web server designed to be observable from day one.

### 3.1 SQLAlchemy Integration
We use `flask_sqlalchemy` to interact with the PostgreSQL database. The model is simple:

```python
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
```

### 3.2 Prometheus Middleware
The most critical part of the code for this project is the metric exposure:

```python
from prometheus_flask_exporter import PrometheusMetrics
metrics = PrometheusMetrics(app)

# Custom Business Metric
task_created_counter = Counter('todo_tasks_created_total', 'Total tasks created')
```

This middleware automatically creates a `/metrics` endpoint. When Prometheus hits this endpoint, the app responds with:
*   `flask_http_request_total`: How many requests have come in.
*   `flask_http_request_duration_seconds`: How long they took.
*   `process_cpu_seconds_total`: CPU usage of the Python process.

This "Code-as-Instrumentation" approach allows us to see exactly what the code is doing without installing external agents.

---

## Phase 4: Secure Remote Access & Network Tunneling

### 4.1 The "Black Box" Problem
With the infrastructure provisioning (Phase 1) and application deployment (Phase 2) complete, our application was running successfully on the AWS server. However, a major operational challenge remained: **Observability.**

We had installed Prometheus (Port 9090) and Grafana (Port 3000) inside the server, but we could not see them due to our strict Security Group.

**The Architectural Dilemma:**
*   **Option A (Insecure):** Open Ports 9090 and 3000 in the AWS Security Group to `0.0.0.0/0`. This allows anyone on the internet to view our server metrics.
*   **Option B (Secure):** Keep all ports blocked and use an encrypted tunnel.

We chose **Option B**.

### 4.2 The Solution: SSH Local Port Forwarding
SSH Tunneling allows us to "wrap" arbitrary TCP traffic (like a web request to Grafana) inside the encrypted SSH protocol (Port 22).

**The Tunneling Command:**
We ran this command from a local PowerShell/Terminal window (kept running in the background):

```powershell
# Establish the Encrypted Tunnel
ssh -i "C:\Users\Ashish\.ssh\aws_key" \
    -L 9090:127.0.0.1:9090 \
    -L 3000:127.0.0.1:3000 \
    -L 5001:127.0.0.1:5000 \
    ec2-user@47.128.226.87
```

**Command Breakdown:**
*   **`-i "...\aws_key"`**: Identity file.
*   **`-L [LocalPort]:[RemoteHost]:[RemotePort]`**: The core tunneling flag.
    *   **`-L 9090:127.0.0.1:9090`**: "Take traffic from my laptop's port 9090 and forward it to the server's port 9090."
    *   **`-L 5001:127.0.0.1:5000`**: Forwarding local 5001 to remote 5000 (app). Note we used 5001 locally to avoid port conflicts.

**Access Verification:**
Once the tunnel was established, we were able to access the internal tools using `localhost` URLs:
*   **Prometheus:** `http://localhost:9090`
*   **Grafana:** `http://localhost:3000`
*   **App API:** `http://localhost:5001/health`

This setup allowed us to maintain a "Zero Trust" network posture on AWS while retaining full observability access for the development team.

---

## Phase 5: Internal Network Discovery

### 5.1 The "Split Network" Challenge
**The Problem:** When Jenkins deployed the application using `docker-compose`, it automatically created a new, isolated network (e.g., `ec2-user_default`). However, our Monitoring Stack (Prometheus/Grafana) was running on the default Docker `bridge` network because they were started manually or separately.

**The Consequence:** Docker containers on different networks are strictly isolated. Prometheus was shouting out to the App, but the firewall between them dropped the packets. They were in "different rooms" and could not see each other.

### 5.2 The "Name Game" DNS Resolution Failure
**The Problem:** Our `prometheus.yml` configuration file was originally written to look for a host named **`app`**. However, Jenkins named the container **`todo-app`**. This caused a `no such host` DNS error.

**The Solution:**
We manually bridged the networks and updated the DNS names.

```bash
# 1. Retrieve the network name of the running application
NETWORK_NAME=$(docker inspect todo-app -f '{{range $k, $v := .NetworkSettings.Networks}}{{$k}}{{end}}')

# 2. Connect Monitoring containers to the App's network
docker network connect $NETWORK_NAME ec2-user-prometheus-1
docker network connect $NETWORK_NAME ec2-user-grafana-1
docker network connect $NETWORK_NAME node-exporter

# 3. Update Prometheus Config dynamically
cat <<EOF > /home/ec2-user/prometheus.yml
global:
  scrape_interval: 5s
scrape_configs:
  - job_name: 'todo_app'
    static_configs:
      - targets: ['todo-app:5000']  # <--- FIXED: Updated to real container name
  - job_name: 'node_exporter'
    static_configs:
      - targets: ['node-exporter:9100']
EOF

# 4. Restart Prometheus to reload config
docker restart ec2-user-prometheus-1
```

---

## Phase 6: Dashboard Engineering & Custom Metrics

### 6.1 Implementing Custom Panels (PromQL)
We designed three specific panels to monitor the **"Golden Signals"** of the application. We utilized the PromQL (Prometheus Query Language) to extract meaningful insights.

**Panel 1: Total Traffic (Requests Per Second)**
*   **Goal:** Measure the volume of traffic hitting the application.
*   **Metric:** `flask_http_request_total`
*   **The Query:**
    ```promql
    sum(rate(flask_http_request_total[1m]))
    ```
*   **Explanation:** Calculates the per-second rate of requests, averaged over a 1-minute window, and sums them across all instances.

**Panel 2: Error Rate % (Reliability)**
*   **Goal:** visualize what percentage of requests are failing (HTTP 500 status).
*   **The Query:**
    ```promql
    sum(rate(flask_http_request_total{status=~"5.."}[1m])) / sum(rate(flask_http_request_total[1m])) * 100
    ```
*   **Explanation:** (Rate of Errors / Total Rate of Traffic) * 100. This gives a clear percentage line (e.g., "5% Error Rate").

**Panel 3: CPU Usage % (Resource Monitoring)**
*   **Goal:** Monitor server load.
*   **The Query:**
    ```promql
    100 - (avg by (instance) (irate(node_cpu_seconds_total{mode="idle"}[1m])) * 100)
    ```
*   **Explanation:** Prometheus tracks how much time the CPU is *idle*. We calculate usage by inverting this: `100% - Idle% = Usage%`.

**Common Pitfalls We Solved:**
*   **"Smart Quote" Errors:** Copy-pasting from documents often converts straight quotes (`"`) into curly "smart quotes" (`”`). PromQL strictly requires straight quotes. We manually sanitized the queries.
*   **"No Data" issues:** Addressed by generating synthetic traffic in Phase 7.

---

## Phase 7: Load Testing & System Validation

A monitoring system is useless if it has nothing to monitor. To validate our dashboard, we needed to simulate a production environment with active users.

### 7.1 Traffic Simulation Script
We ran `traffic_generator.py` from our local machine. Thanks to the SSH Tunnel, it communicated securely with the remote AWS app.

**The Script Logic:**
```python
# traffic_generator.py snippet
while True:
    try:
        # Randomly choose an action
        action = random.choice(['read', 'create', 'delete', 'error'])
        
        if action == 'read':
            requests.get(f"{BASE_URL}/tasks")
        elif action == 'error':
            # Intentionally hit the chaos endpoint to trigger alerts
            requests.get(f"{BASE_URL}/simulate-error")
            
        time.sleep(random.uniform(0.1, 1.0))
    except Exception as e:
        print(f"Error: {e}")
```

### 7.2 Visual Verification
Once the script ran for ~2-3 minutes, we observed the "Heartbeat" of the system in Grafana:
1.  **RPS Panel:** Spiked from 0 to ~5-10 RPS.
2.  **Error Rate:** Showed intermittent spikes as the script hit failure endpoints, validating our PromQL math.
3.  **CPU Usage:** Increased slightly due to request processing and monitoring overhead.

---

## Phase 8: Cost Management & Teardown

### 8.1 The "Kill Switch"
Since this project utilized paid AWS resources (EC2 instances, EBS volumes), it was critical to shut down the environment to avoid unnecessary billing.

Instead of manually terminating instances in the AWS Console (which often leaves behind "Ghost Resources" like Security Groups or Key Pairs), we used Terraform to perform a clean sweep.

### 8.2 Execution Command
```bash
cd terraform
terraform destroy --auto-approve
```

**Outcome:**
*   Terminated the EC2 Instance.
*   Deleted the Security Group.
*   Removed the SSH Key Pair.
*   Deleted the ECR Repository.
*   **Result:** Zero active costs.

---

## Appendix A: Operational Cheatsheet

Here is a quick reference for the commands frequently used in this project.

### Terraform
| Command | Purpose |
| :--- | :--- |
| `terraform init` | Initialize the directory & download providers. |
| `terraform fmt` | Auto-format your `.tf` files to standard style. |
| `terraform validate` | Check for syntax errors. |
| `terraform plan` | Preview the changes AWS will make. |
| `terraform apply --auto-approve` | Create/Update resources without prompting. |
| `terraform destroy` | Delete all resources. |

### Docker & Compose
| Command | Purpose |
| :--- | :--- |
| `docker ps` | List running containers. |
| `docker ps -a` | List all containers (including stopped ones). |
| `docker-compose up -d --build` | Build and start containers in the background. |
| `docker-compose down` | Stop and remove containers and networks. |
| `docker logs -f <container_name>` | Follow the logs of a specific container. |
| `docker exec -it <container> sh` | Open a shell inside a running container. |

### SSH Tunneling
| Flag | Meaning |
| :--- | :--- |
| `-i "key.pem"` | Specify the private key file. |
| `-L 8080:localhost:80` | Forward local port 8080 to remote port 80. |
| `-v` | Verbose mode (use for debugging connection issues). |

---

## Appendix B: Troubleshooting FAQ

**Q: Why does my Terraform apply fail with "Error acquiring the state lock"?**
**A:** This happens if a previous Terraform command was interrupted. Locate the `.terraform.lock.hcl` file or use `terraform force-unlock <LOCK_ID>` if you are using a remote backend (S3/DynamoDB).

**Q: I can't SSH into the instance.**
**A:**
1.  Check the security group rules in the AWS Console. Is Port 22 open to your IP?
2.  Check the permissions of your key file. On Linux/Mac, it must be `400` (`chmod 400 aws_key`). On Windows, ensure your user is the only one with "Full Control".

**Q: The Jenkins pipeline fails at the "Build" stage.**
**A:**
1.  Check if Docker is running on the agent (`docker ps`).
2.  Check if the disk is full (`df -h`).
3.  Check the console output for "Permission denied" errors (refer to Phase 1.3).

**Q: Grafana shows "No Data" for my queries.**
**A:**
1.  Is the application generating traffic? Run the traffic generator.
2.  Is Prometheus scraping? Check `http://localhost:9090/targets`. If the target is RED, Prometheus can't reach the app.
3.  Did you select the correct time range in Grafana? (Top right corner -> "Last 5 minutes").

**Q: My "Error Rate" panel is always 0%."
**A:** Good! That means your app is working. To test the panel, you must generate errors. Use the `/simulate-error` endpoint or the traffic generator's error mode.

---
*Created by the DevOps Team. Saturday, 13 December 2025.*
