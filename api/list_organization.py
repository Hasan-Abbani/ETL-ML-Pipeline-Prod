from api.wattics_base import WatticsBaseClient


class WatticsOrganizationClient(WatticsBaseClient):

    def get_organizations(self):
        print("Fetching organizations...")

        data = self.get("/organizations")

        if data is None:
            return []

        print(f"Found {len(data)} organizations.")
        return data

    def get_organization_by_name(self, organization_name):
        organizations = self.get_organizations()

        for organization in organizations:
            if organization["name"].lower() == organization_name.lower():
                print(f"Found organization: {organization['name']} with ID {organization['id']}")
                return organization

        print(f"Organization not found: {organization_name}")
        return None