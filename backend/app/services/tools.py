import requests



BASE_URL = "http://127.0.0.1:8000"


def check_service_incidents(service):
    try:
        response = requests.get(
            f"{BASE_URL}/api/incidents/{service}",
            timeout=5
        )

        response.raise_for_status()

        return response.json()

    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": f"Incident service is unavailable: {str(e)}"
        }


def get_user(user_id):
    try:
        response = requests.get(
            f"{BASE_URL}/api/users/{user_id}",
            timeout=5
        )

        response.raise_for_status()

        return response.json()

    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": f"User service is unavailable: {str(e)}"
        }


def get_user_permissions(user_id):
    try:
        response = requests.get(
            f"{BASE_URL}/api/users/{user_id}/permissions",
            timeout=5
        )

        response.raise_for_status()

        return response.json()

    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": f"Permission service is unavailable: {str(e)}"
        }


def create_ticket(user_id, category, description):
    try:
        response = requests.post(
            f"{BASE_URL}/api/tickets",
            json={
                "user_id": user_id,
                "category": category,
                "description": description
            },
            timeout=5
        )

        response.raise_for_status()

        return response.json()

    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": f"Ticket service is unavailable: {str(e)}"
        }

def get_ticket(ticket_id, requester_user_id):
    try:
        response = requests.get(
            f"{BASE_URL}/api/tickets/{ticket_id}",
            params={
                "requester_id": requester_user_id
            },
            timeout=5
        )

        response.raise_for_status()
        return response.json()

    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": f"Ticket service is unavailable: {str(e)}"
        }

def get_my_tickets(user_id):
    try:
        response = requests.get(
            f"{BASE_URL}/api/tickets",
            params={"user_id": user_id},
            timeout=5
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": f"Ticket service is unavailable: {str(e)}"
        }


def get_team_tickets(user_id):
    try:
        response = requests.get(
            f"{BASE_URL}/api/tickets/team",
            params={"requester_id": user_id},
            timeout=5
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": f"Ticket service is unavailable: {str(e)}"
        }

def get_employee_tickets(employee_id, requester_id):
    try:
        response = requests.get(
            f"{BASE_URL}/api/tickets/employee/{employee_id}",
            params={"requester_id": requester_id},
            timeout=5
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": f"Ticket service is unavailable: {str(e)}"
        }

def get_all_tickets(user_id):
    try:
        response = requests.get(
            f"{BASE_URL}/api/tickets/all",
            params={"requester_id": user_id},
            timeout=5
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": f"Ticket service is unavailable: {str(e)}"
        }
    
def get_employee(target_user_id, requester_user_id):
    try:
        response = requests.get(
            f"{BASE_URL}/api/users/admin/{target_user_id}",
            params={
                "requester_id": requester_user_id
            },
            timeout=5
        )

        response.raise_for_status()
        return response.json()

    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": f"User service is unavailable: {str(e)}"
        }

def get_all_employees(requester_user_id):
    try:
        response = requests.get(
            f"{BASE_URL}/api/users/admin",
            params={
                "requester_id": requester_user_id
            },
            timeout=5
        )

        response.raise_for_status()
        return response.json()

    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": f"User service is unavailable: {str(e)}"
        }
        


    
if __name__ == "__main__":

    print(check_service_incidents("vpn"))

    print(get_user("user_001"))

    print(get_user_permissions("user_001"))

    print(
        create_ticket(
            user_id="user_002",
            category="VPN",
            description="VPN is not connecting."
        )
    )