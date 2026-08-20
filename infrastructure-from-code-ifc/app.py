"""
app.py - Codigo de aplicacion de ejemplo (equivalente Python del ejemplo
Nitric/TypeScript del post).

El desarrollador NO define infraestructura aqui: solo declara que recursos
necesita su aplicacion. ifc_analyzer.py analiza este archivo (sin
ejecutarlo) y deduce automaticamente que infraestructura hay que provisionar.
"""

from ifc_sdk import api, bucket, queue

image_api = api("image-processor")
uploaded_images = bucket("uploaded-images").allow("read", "write")
resize_jobs = queue("resize-jobs").allow("send", "receive")


def upload_handler(ctx):
    """Handler HTTP: sube una imagen y encola un job de resize."""
    file_name = f"{ctx.timestamp}-image.jpg"
    uploaded_images.file(file_name).write(ctx.body)
    resize_jobs.send({"fileName": file_name})
    return {"message": "Image uploaded successfully", "fileName": file_name}
