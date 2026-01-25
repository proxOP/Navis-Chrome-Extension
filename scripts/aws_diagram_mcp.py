from fastapi import FastAPI
from diagrams import Diagram
from diagrams.aws.compute import EC2
import uuid
import os

app = FastAPI()

@app.post("/generate")
def generate_diagram(spec: dict):
    name = f"aws_diagram_{uuid.uuid4().hex}"
    out_dir = os.path.abspath("outputs")
    os.makedirs(out_dir, exist_ok=True)

    with Diagram(
        name,
        filename=os.path.join(out_dir, name),
        show=False,
        direction="LR"
    ):
        EC2("Example EC2")

    return {
        "status": "ok",
        "file": f"{name}.png",
        "path": out_dir
    }
