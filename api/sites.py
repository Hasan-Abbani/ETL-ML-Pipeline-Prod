from api.wattics_base import WatticsBaseClient


class WatticsSiteClient(WatticsBaseClient):

    def get_sites_for_organization(self, organization_id):
        print(f"Fetching sites for organization ID {organization_id}...")

        params = {
            "organization_id": organization_id
        }

        data = self.get("/sites", params=params)

        if data is None:
            return []

        print(f"Found {len(data)} sites.")
        return data