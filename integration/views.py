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

def verify_github_signature(request):
    
    """
    Verify the authenticity of GitHub webhook requests using HMAC signature.
    
    Args:
        request: The Django HTTP request object containing the webhook payload
        
    Returns:
        bool: True if signature is valid, False otherwise
    """
    
    signature_header = request.headers.get("X-Hub-Signature-256")
    if signature_header is None:
        return False

    secret = settings.GITHUB_WEBHOOK_SECRET.encode()
    body = request.body
    expected_signature = "sha256=" + hmac.new(secret, body, hashlib.sha256).hexdigest()

    return hmac.compare_digest(expected_signature, signature_header)

@csrf_exempt
def github_webhook(request):
    
    """
    Handle GitHub webhook events, specifically for issue creation.
    Creates corresponding Asana tasks when new GitHub issues are opened.
    
    Args:
        request: The Django HTTP request object containing the webhook payload
        
    Returns:
        JsonResponse: Response indicating success, failure, or ignored status
    """
    
    if not verify_github_signature(request):
        return HttpResponseBadRequest("Invalid signature.")

    if request.method == 'POST':
        try:
            payload = json.loads(request.body)

            if 'issue' in payload and payload['action'] == 'opened':
                issue = payload['issue']
                assignee_username = issue['assignee']['login'] if issue.get('assignee') else None

                if assignee_username:
                    assignee_email = get_github_user_email(assignee_username)
                else:
                    assignee_email = None

                asana_task = create_asana_task(issue, assignee_email)
                return JsonResponse({'status': 'success', 'asana_task': asana_task}, status=201)

            return JsonResponse({'status': 'ignored'}, status=200)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid payload'}, status=400)

    return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)

def create_asana_task(issue, assignee_email=None):
    
    """
    Create a new task in Asana based on GitHub issue details.
    
    Args:
        issue (dict): GitHub issue data containing title, body, and other metadata
        assignee_email (str, optional): Email of the GitHub issue assignee
        
    Returns:
        dict: Response data from Asana API containing created task details
    """
    
    url = ASANA_API_TASK_URL
    headers = {
        "Authorization": f"Bearer {ASANA_ACCESS_TOKEN}"
    }

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

    try:
        response = requests.post(url, headers=headers, json=task_data)
        response_data = response.json()

        if response.status_code == 201:
            print("Task created successfully on Asana")
        else:
            print(f"Failed to create task. Status Code: {response.status_code}, Response: {response_data}")

        return response_data

    except requests.RequestException as e:
        print(f"An error occurred while making the POST request: {e}")
        return {'error': str(e)}

def get_github_user_email(username):
    
    """
    Fetch a GitHub user's public email address using the GitHub API.
    
    Args:
        username (str): GitHub username
        
    Returns:
        str or None: User's public email if available, None otherwise
    """
    
    url = f"{GITHUB_API_BASE_URL}/users/{username}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}"
    }

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            user_data = response.json()

            if 'email' in user_data and user_data['email']:
                return user_data['email']
            print(f"No public email available for user: {username}")
            return None
        
        print(f"Failed to fetch user data from GitHub. Status Code: {response.status_code}")
        return None
        
    except requests.RequestException as e:
        print(f"Error fetching GitHub user data: {e}")
        return None
