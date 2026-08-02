# backend/main.py
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import nibabel as nib
import numpy as np
import tempfile
import json
import os

app = FastAPI()

# Enable CORS for Vercel
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL", "http://localhost:3000")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/process-groups")
async def process_groups(
    files: list[UploadFile] = File(...),
    # Json string format: {"sub-01.func.gii": "GroupA", "sub-02.func.gii": "GroupB"}
    group_mapping: str = Form(...) 
):
    try:
        mapping = json.loads(group_mapping)
        group_a_data = []
        group_b_data = []

        # Temp directory to hold uploaded files
        with tempfile.TemporaryDirectory() as tmpdir:
            for file in files:
                file_path = os.path.join(tmpdir, file.filename)
                with open(file_path, "wb") as f:
                    f.write(await file.read())
                
                # Load GIFTI with Nibabel
                gii = nib.load(file_path)
                # Stack time-series arrays (Shape: [Vertices, Timepoints])
                time_series = np.column_stack([darray.data for darray in gii.darrays])
                
                # Group assignment
                group = mapping.get(file.filename)
                if group == "GroupA":
                    group_a_data.append(time_series)
                elif group == "GroupB":
                    group_b_data.append(time_series)

            if not group_a_data or not group_b_data:
                raise HTTPException(status_code=400, detail="Both groups must have at least 1 file.")

            # Compute group averages across subjects: (Axis 0 = Subject dimension)
            group_a_mean = np.mean(np.array(group_a_data), axis=0) # [Vertices, TRs]
            group_b_mean = np.mean(np.array(group_b_data), axis=0)
            
            # Compute differential map (Group A - Group B)
            diff_map = group_a_mean - group_b_mean

            # Convert result back to a GIFTI image
            darrays = [nib.gifti.GiftiDataArray(data=diff_map[:, t].astype(np.float32)) 
                       for t in range(diff_map.shape[1])]
            output_gii = nib.gifti.GiftiImage(darrays=darrays)
            
            output_path = os.path.join(tmpdir, "group_diff_4d.func.gii")
            nib.save(output_gii, output_path)

            return FileResponse(
                path=output_path, 
                filename="group_diff_4d.func.gii", 
                media_type="application/octet-stream"
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
