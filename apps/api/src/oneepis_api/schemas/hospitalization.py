from oneepis_api.schemas.clinical_record import ClinicalEncounterRead
from oneepis_api.schemas.common import APIModel
from oneepis_api.schemas.patient import PatientRead


class HospitalizationBoardItem(APIModel):
    patient: PatientRead
    encounter: ClinicalEncounterRead
