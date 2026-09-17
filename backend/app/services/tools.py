from app.api.incidents import incidents
from app.api.users import users


def check_service_incidents(service: str):

    service_incidents = [
        incident
        for incident in incidents.values()
        if incident["service"] == service
    ]

    return service_incidents


def get_user(user_id: str):

    return users.get(user_id)


def get_user_permissions(user_id: str):

    user = users.get(user_id)

    if not user:
        return None

    return user["permissions"]


if __name__ == "__main__":

    print(check_service_incidents("vpn"))

    print(get_user("user_001"))

    print(get_user_permissions("user_001"))