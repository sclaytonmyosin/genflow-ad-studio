import requests

def trigger_generation_pipeline(product_name: str, brand_guidelines: str, target_audience: str) -> str:
    """
    Triggers the full automated video generation pipeline for a given product.
    Use this when the user asks to generate a video for a product.
    
    Args:
        product_name: Name of the product (e.g., 'blue dress', 'running shoes')
        brand_guidelines: Any specific styling or mood requested (e.g., 'energetic and beachy')
        target_audience: The intended audience (e.g., 'young adults', 'athletes')
    """
    payload = {
        "product_name": product_name,
        "brand_guidelines": brand_guidelines,
        "target_audience": target_audience,
        "num_scenes": 3
    }
    # Call the local FastAPI endpoint
    try:
        resp = requests.post("http://127.0.0.1:8000/api/v1/pipeline/start", json=payload)
        if resp.status_code == 200:
            data = resp.json()
            return f"Successfully triggered pipeline. Job ID: {data.get('job_id')}. Tell the user the job has started."
        return f"Failed to trigger pipeline: {resp.text}"
    except Exception as e:
        return f"Error connecting to backend: {str(e)}"


def list_running_jobs() -> str:
    """
    Returns a list of all jobs currently running or completed in the system.
    Use this when a user asks for the status of a video or campaign.
    """
    try:
        resp = requests.get("http://127.0.0.1:8000/api/v1/jobs")
        if resp.status_code == 200:
            return str(resp.json())
        return "Failed to fetch jobs."
    except Exception as e:
        return f"Error connecting to backend: {str(e)}"
