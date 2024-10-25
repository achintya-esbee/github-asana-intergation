# GitHub-Asana Integration

This Django-based integration connects GitHub and Asana, automatically creating tasks in Asana for each new issue opened in a specified GitHub repository. The integration uses GitHub webhooks to listen for issue creation events and the Asana API to create tasks with relevant details.

## Features

- **Automatic Task Creation**: Each new GitHub issue generates a corresponding task in Asana.
- **Assignee Handling**: If the GitHub issue has an assignee, the integration attempts to retrieve their email for assigning the task in Asana.
- **GitHub Webhook Verification**: Validates incoming webhook requests with HMAC to ensure secure communication.

## Prerequisites

- Python 3.x
- Django
- Ngrok
- GitHub API token
- Asana Personal Access Token
- Asana workspace and project

## Setup

### 1. Clone the Repository
```bash
git clone <repository-url>
cd <repository-directory>
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configuration
Add your API credentials and other required configurations to `settings.py`:

```python
# settings.py

ALLOWED_HOSTS = ['ngrok-given-url.ngrok-free.app']    # Needs to be updated everytime ngrok is restarted

ASANA_ACCESS_TOKEN = 'your_asana_access_token'
WORKSPACE_ID = 'your_workspace_id'    # https://app.asana.com/api/1.0/workspaces/
PROJECT_ID = 'your_project_id'      # https://app.asana.com/0/<project-id>/<task-id>/
GITHUB_TOKEN = 'your_github_token'
GITHUB_API_BASE_URL = "https://api.github.com"
ASANA_API_TASK_URL = "https://app.asana.com/api/1.0/tasks"
GITHUB_WEBHOOK_SECRET = 'your_github_webhook_secret'
```

### 4. Set Up the GitHub Webhook

1. Go to your GitHub repository > **Settings** > **Webhooks**.
2. **Start ngrok on the same port as the Django server (default: 8000)
   ```bash
   ngrok http 8000
   ```
3. Add the URL for the webhook (e.g., `https://yourdomain.com/github-webhook/`).
4. Use the `GITHUB_WEBHOOK_SECRET` to secure the webhook.
5. Select the "Let me select individual events" option, then choose "Issues" and set it to listen for the "opened" action.

## Usage

1. **Start the Django server**:
    ```bash
    python manage.py runserver
    ```
2. **Open a new GitHub Issue** in the configured repository.
3. The Django app will process the GitHub webhook and create a task in Asana for each new issue.

## Project Structure

After creating a Django project (e.g., named `git-sana`), Django generates several default files and directories to support the project’s structure:

- **`git-sana/`**: Root project directory containing configuration files.
  - **`settings.py`**: Holds all global variables and configurations for the project, including API tokens and other credentials.
  - **`urls.py`**: Contains URL routing for the project, including the endpoint setup for the GitHub webhook.
  - **`manage.py`**: Utility for managing the Django project, used to start the Django development server and execute other commands.

- **`integration/`**: Django app created within the project to handle GitHub-Asana integration.
  - **`views.py`**: Contains all the core logic for processing the webhook events, verifying GitHub signatures, and creating tasks in Asana.

## Key Functions

- **`verify_github_signature(request)`**: Ensures the GitHub webhook payload is valid.
- **`github_webhook(request)`**: Listens for incoming GitHub issue events and triggers task creation.
- **`create_asana_task(issue, assignee_email=None)`**: Sends a request to Asana's API to create a new task based on GitHub issue details.
- **`get_github_user_email(username)`**: Fetches the GitHub user’s email if available, using the GitHub API.

## Troubleshooting

- **Webhook Signature Verification Error**: Ensure the `GITHUB_WEBHOOK_SECRET` in GitHub matches the one in `settings.py`.
- **Rate Limits**: If GitHub or Asana API requests fail, ensure your API tokens have sufficient permissions and are not rate-limited.
- **Missing Assignee**: If a GitHub assignee’s email is not publicly available, the Asana task will default to "me" as the assignee.
