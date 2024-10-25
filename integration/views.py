from django.shortcuts import render
from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
import json
import requests
import hmac
import hashlib
import datetime
from django.conf import settings

ASANA_ACCESS_TOKEN = settings.ASANA_ACCESS_TOKEN
WORKSPACE_ID = settings.WORKSPACE_ID
PROJECT_ID = settings.PROJECT_ID
GITHUB_TOKEN = settings.GITHUB_TOKEN
GITHUB_API_BASE_URL = settings.GITHUB_API_BASE_URL
ASANA_API_TASK_URL = settings.ASANA_API_TASK_URL

# Github webhook validation
def verify_github_signature(request):
    # Retrieve the signature from the headers
    signature_header = request.headers.get("X-Hub-Signature-256")
    if signature_header is None:
        return False

    # Prepare the actual signature
    secret = settings.GITHUB_WEBHOOK_SECRET.encode()
    body = request.body
    expected_signature = "sha256=" + hmac.new(secret, body, hashlib.sha256).hexdigest()

    # Compare the expected signature with the one received from GitHub
    if not hmac.compare_digest(expected_signature, signature_header):
        return False

    return True

# Catching issues created in Github repo
@csrf_exempt
def github_webhook(request):

    # Verify the GitHub signature first
    if not verify_github_signature(request):
        return HttpResponseBadRequest("Invalid signature.")

    if request.method == 'POST':
        try:
            payload = json.loads(request.body)

            # Check if the event is an issue creation event
            if 'issue' in payload and payload['action'] == 'opened':
                print("Processing issue creation event")
                issue = payload['issue']

                # Get the assignee's GitHub username
                assignee_username = issue['assignee']['login'] if issue.get('assignee') else None

                # Getting the assignee's email as it is not in the webhook data
                if assignee_username:
                    assignee_email = get_github_user_email(assignee_username)
                else:
                    assignee_email = None

                # Pass issue details and assignee email to create Asana task
                asana_task = create_asana_task(issue, assignee_email)
                return JsonResponse({'status': 'success', 'asana_task': asana_task}, status=201)

            # Return 200 OK for other events that you are not interested in
            return JsonResponse({'status': 'ignored'}, status=200)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid payload'}, status=400)

    return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)

# Creating corresponding tasks in Asana
def create_asana_task(issue, assignee_email=None):
    # Prepare the data for the new task in Asana
    url = ASANA_API_TASK_URL
    headers = {
        "Authorization": f"Bearer {ASANA_ACCESS_TOKEN}"
    }

    # Use the assignee email if available; otherwise, use a default assignee
    assignee = assignee_email if assignee_email else "me"

    task_data = {
        "data": {
            "name": issue['title'], 
            "notes": issue['body'], 
            "workspace": str(WORKSPACE_ID),
            "projects": [str(PROJECT_ID)],  
            "assignee": assignee,
            "due_on": datetime.datetime.now().strftime("%Y-%m-%d")
        }
    }

    # Send the request to Asana API
    try:
        response = requests.post(url, headers=headers, json=task_data)
        response_data = response.json()

        # Check if the task creation was successful
        if response.status_code == 201:
            print("Task created successfully on Asana")
        else:
            print(f"Failed to create task. Status Code: {response.status_code}, Response: {response_data}")

        return response_data

    except requests.RequestException as e:
        print(f"An error occurred while making the POST request: {e}")
        return {'error': str(e)}

# Function to fetch GitHub user's email (if public), using authentication
def get_github_user_email(username):
    url = f"{GITHUB_API_BASE_URL}/users/{username}"

    headers = {
        "Authorization": f"token {GITHUB_TOKEN}"
    }

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            user_data = response.json()

            # Check if the email is available
            if 'email' in user_data and user_data['email']:
                return user_data['email']
            else:
                print(f"No public email available for user: {username}")
                return None
        else:
            print(f"Failed to fetch user data from GitHub. Status Code: {response.status_code}")
            return None
    except requests.RequestException as e:
        print(f"Error fetching GitHub user data: {e}")
        return None
