from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import FileResponse
from pydantic import BaseModel
from fpdf import FPDF
import pandas as pd
import os

# Load your DataFrame here
df = pd.read_csv('format_dataset.csv')
# For the sake of this example, let's assume that the CSV is already loaded into a DataFrame called 'df'

app = FastAPI()


class MedicationInput(BaseModel):
    medications: list[str]


class DiseaseInput(BaseModel):
    disease: str


# Existing code for calculate_medicine_similarity and guess_disease endpoint ...

def calculate_medicine_similarity(disease_medications: str, patient_medicines: list[str]) -> int:
    disease_medications_list = disease_medications.strip("[]").replace("'", "").split(', ')
    return len(set(disease_medications_list).intersection(set(patient_medicines)))


@app.post("/guess_disease")
async def guess_disease(medication_input: MedicationInput):
    df['medicine_similarity'] = df['commonMedications'].apply(
        lambda meds: calculate_medicine_similarity(meds, medication_input.medications))
    df_sorted_by_similarity = df.sort_values(by='medicine_similarity', ascending=False)
    df_with_similarity = df_sorted_by_similarity[df_sorted_by_similarity['medicine_similarity'] > 0]

    if df_with_similarity.empty:
        raise HTTPException(status_code=404, detail="No matching diseases found")

    diseases = df_with_similarity[['disease', 'medicine_similarity']].to_dict(orient='records')
    return {"diseases": diseases}

@app.post("/get_disease_description")
async def get_disease_description(disease_input: DiseaseInput):
    # Find the disease in the dataframe
    disease_row = df[df['disease'].str.lower() == disease_input.disease.lower()]
    if disease_row.empty:
        raise HTTPException(status_code=404, detail="Disease not found")

    # Get the description of the disease
    disease_description = disease_row.iloc[0]['reason']

    # Generate PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, txt=disease_description)

    # Save the PDF to a temporary file
    temp_filename = f"temp_disease_description_{disease_input.disease}.pdf"
    pdf.output(temp_filename)

    # Return the generated PDF file as a response
    response = FileResponse(path=temp_filename, filename=temp_filename, media_type='application/pdf')

    # Schedule the temporary file for removal after sending
    response.background = BackgroundTask(remove_temp_file, filename=temp_filename)

    return response


# Helper function to remove the temporary PDF file
def remove_temp_file(filename: str):
    try:
        os.remove(filename)
    except Exception as e:
        print(f"Error removing temporary file: {e}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

