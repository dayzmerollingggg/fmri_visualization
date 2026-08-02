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

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL", "http://localhost:3000")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/process-npy-groups")
async def process_npy_groups(
    files: list[UploadFile] = File(...),
    # Expecting JSON string mapping filenames to groups:
    # {"sub-control01_task-GoT_space-fsaverage5_hemi-L_denoised.npy": "GroupA", ...}
    group_mapping: str = Form(...)
):
    try:
        mapping = json.loads(group_mapping)
        group_a_mats = []
        group_b_mats = []

        with tempfile.TemporaryDirectory() as tmpdir:
            for file in files:
                file_path = os.path.join(tmpdir, file.filename)
                with open(file_path, "wb") as f:
                    f.write(await file.read())

                # 1. Load the 2D NumPy array [Vertices, Timepoints]
                arr = np.load(file_path)

                group = mapping.get(file.filename)
                if group == "GroupA":
                    group_a_mats.append(arr)
                elif group == "GroupB":
                    group_b_mats.append(arr)

            if not group_a_mats or not group_b_mats:
                raise HTTPException(status_code=400, detail="Both Group A and Group B require at least 1 .npy file.")

            # 2. Compute group averages across subjects (Axis 0)
            mean_a = np.mean(np.array(group_a_mats), axis=0)  # Shape: [10242, TRs]
            mean_b = np.mean(np.array(group_b_mats), axis=0)  # Shape: [10242, TRs]

            # 3. Compute differential signal map (Group A - Group B)
            diff_map = mean_a - mean_b

            # 4. Pack into a standard GIFTI 4D surface overlay
            darrays = [
                nib.gifti.GiftiDataArray(data=diff_map[:, t].astype(np.float32))
                for t in range(diff_map.shape[1])
            ]
            gii_img = nib.gifti.GiftiImage(darrays=darrays)

            output_path = os.path.join(tmpdir, "diff_fsaverage5_hemi-L.func.gii")
            nib.save(gii_img, output_path)

            return FileResponse(
                path=output_path,
                filename="diff_fsaverage5_hemi-L.func.gii",
                media_type="application/octet-stream"
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
