from api.wattics_base import WatticsBaseClient


class WatticsMeterClient(WatticsBaseClient):

    def get_meters_for_site(self, organization_id, site_id):
        print(f"Fetching meters for organization ID {organization_id}, site ID {site_id}...")

        params = {
            "organization_id": organization_id,
            "site_id": site_id
        }

        data = self.get("/meters", params=params)

        if data is None:
            return []

        print(f"Found {len(data)} meters for site ID {site_id}.")
        return data

    def get_electricity_meters_for_site(self, organization_id, site_id):
        meters = self.get_meters_for_site(
            organization_id=organization_id,
            site_id=site_id
        )

        electricity_meters = []

        for meter in meters:
            if meter.get("type") == "electricity":
            #if meter.get("type") == "electricity" and meter.get("real_meter") == True:
                electricity_meters.append(meter)

        print(f"Found {len(electricity_meters)} electricity meters for site ID {site_id}.")

        return electricity_meters

    def get_electricity_meters_for_sites(self, organization_id, sites):
        all_electricity_meters = []

        for site in sites:
            site_id = site["id"]
            site_name = site["name"]

            print(f"Processing site: {site_name} | ID: {site_id}")

            electricity_meters = self.get_electricity_meters_for_site(
                organization_id=organization_id,
                site_id=site_id
            )

            for meter in electricity_meters:
                meter["site_id"] = site_id
                meter["site_name"] = site_name

            all_electricity_meters.extend(electricity_meters)

        print(f"Total electricity meters found: {len(all_electricity_meters)}")

        return all_electricity_meters

    def get_meter_ids(self, meters):
        meter_ids = [meter["id"] for meter in meters]

        print(f"Electricity meter IDs: {meter_ids}")

        return meter_ids # return a dictionary with the meter ids and their corresponding site names