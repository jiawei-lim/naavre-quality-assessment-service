import requests

SEARCH_URL = "https://metadatacatalogue.lifewatch.eu/srv/api/search/records/_search"
RECORD_URL = "https://metadatacatalogue.lifewatch.eu/srv/api/records/"

def get_metadata_uuid(file:str) -> str:
    response = search_workflow_file(file)
    results = response.get("hits").get("hits")

    if len(results) == 0:
        raise LookupError("Metadata entry for file not found")
    elif len(results) > 1:
        raise ValueError("Multiple metadata entry for file found")

    return results[0]["_id"]
    

def search_workflow_file(filename:str) -> dict:
    body =  {
        "query":{"bool":{
        "must":[{"query_string":{"query":f"*{filename}*",
                                 "fields":["complexComponents.*"],
                                 "analyze_wildcard":True}}],
        "filter":[{"term":{"resourceType":"workflow"}}]}}}
    return search_records(body)


def search_records(body: dict, bucket: str = "metadata") -> dict:
    response = requests.post(
        SEARCH_URL,
        params={"bucket": bucket},
        json=body,
        headers={"Accept": "application/json"},
    )
    response.raise_for_status()
    return response.json()
