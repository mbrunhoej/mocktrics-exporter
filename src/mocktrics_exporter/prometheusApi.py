import fnmatch
from datetime import datetime

import httpx


class PrometheisApi:

    def __init__(self, adress: str = "", tenant: int | None = None):

        self.base_address = adress
        self.headers: dict[str, str] = {}

        if tenant != None:
            self.headers.update({"X-Scope-OrgID": str(tenant)})

    def get_available_metrics(self) -> list[str]:
        response = httpx.get(
            self.base_address + "/api/v1/label/__name__/values",
            headers=self.headers,
            follow_redirects=True,
            verify=False,
        )
        if response.status_code != 200:
            raise ValueError(f"Request returned status code {response.status_code}")
        metrics = response.json()["data"]
        return metrics

    def query_metric(
        self,
        metric: str,
        start: str,
        end: str = "",
        constraints: dict[str, str] = {},
        step: str = "30s",
    ) -> list:
        constraint = ""
        if constraints:
            _constraints = []
            for key, value in constraints.items():
                _constraints.append(f'{key}="{value}"')
            constraint = "{" + ",".join(_constraints) + "}"
        query = metric + constraint
        response = httpx.get(
            self.base_address + "/api/v1/query_range",
            headers=self.headers,
            follow_redirects=True,
            verify=False,
            params={
                "query": query,
                "start": str(int(datetime.fromisoformat(start).timestamp())),
                "end": str(int(datetime.fromisoformat(end).timestamp())),
                "step": step,
            },
        )
        if response.status_code != 200:
            raise ValueError(f"Request returned status code {response.status_code}")

        results = []
        for _metric in response.json()["data"]["result"]:

            results.append({"labels": _metric["metric"], "series": _metric["values"]})

        return results

    def query_metrics(
        self,
        metrics: str,
        start: str,
        end: str = "",
        constraints: dict[str, str] = {},
        step: str = "30s",
    ) -> dict:

        _metrics = fnmatch.filter(self.get_available_metrics(), metrics)

        f = {}

        for _metric in _metrics:
            f.update({_metric: self.query_metric(_metric, start, end, constraints, step)})

        return f
