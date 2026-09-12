from app.api.incidents import incidents



def check_service_incidents(service: str):
    service_incidents = []

    for incident in incidents.values():
        if incident["service"] == service:
            service_incidents.append(incident)

    return service_incidents

if __name__ == "__main__":

    result = check_service_incidents("vpn")

    print(result)