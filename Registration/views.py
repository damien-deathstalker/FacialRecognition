import json, logging
from pathlib import PurePath
from statistics import mode
from typing import Dict, List, Text
from PIL import Image
import cv2
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_protect
import numpy as np
from FacialRecognitonModule.recognition import (
	backup_encodings,
	train_face,
	face_detect_stream,
	base64_to_img,
	SYSTEM_LOGS,
)
from .models import Visitor, VisitorLog

logger = logging.getLogger("registration_handler")
logger.setLevel(logging.INFO)
file_handler = logging.FileHandler(PurePath(SYSTEM_LOGS, "Registration.log"), mode="a+")
logger.addHandler(file_handler)

# Create your views here.


@csrf_protect
def submit(request):
	return_data = dict(status="fail", message="Nothing is happening")
	try:
		formData: Dict = request.POST
		name = formData.get("name", None)
		telephone = formData.get("telephone", None)
		personToSee = formData.get("person_to_see", None)
		purpose = formData.get("purpose", None)
		facialFeatures = formData.get("facial_features", None)
		if all([name, telephone, personToSee, purpose, facialFeatures]):
			try:
				facialFeatures = json.loads(facialFeatures)
				newVisitorData = dict(
					name=name,
					telephone=telephone,
					purpose=purpose,
					images_collected=json.dumps(facialFeatures),
				)
				try:
					newVisitor, _ = Visitor.objects.update_or_create(
						telephone=telephone, defaults=newVisitorData
					)
					VisitorLog(
						**dict(
							person_to_see=personToSee,
							visitor_fk=newVisitor,
							vistor_name=newVisitor.name,
						),
					).save()
					VisitorLog.objects.filter(visitor_fk=newVisitor).update(
						vistor_name=newVisitor.name
					)
					return_data.update(
						status="ok",
						message=f"Visitor data saved. Processing Facial Features.",
					)
					try:
						person = analyze_facialFeatures(facialFeatures)
						if person:
							return_data.update(
								message=f"Visitor data saved.",
							)
						else:
							trigger_face_training(newVisitor.name, facialFeatures)
							return_data.update(
								message=f"Visitor data & facial features saved. Vistor can now be recognized",
							)
					except Exception as e:
						logger.exception("ERROR: recognize_face(request)")
						return_data.update(
							message=f"Something went wrong in face training: {e.__str__()}"
						)
				except Exception as e:
					logger.exception("ERROR: recognize_face(request)")
					return_data.update(
						message=f"Something went wrong saving: {e.__str__()}"
					)
			except Exception as e:
				logger.exception("ERROR: recognize_face(request)")
				return_data.update(
					message=f"There's something wrong with the collected features: {e.__str__()}"
				)
		else:
			return_data.update(
				message="Some info hasn't been collected. Please ensure too that at least 4 Facial Features have been collected"
			)
	except Exception as e:
		logger.exception("ERROR: submit(request)")
		return_data.update(message=e.__repr__())
	return JsonResponse(return_data)


def trigger_face_training(vistorName: Text, base64List: List[Text]):
	backup_encodings()
	for base64Image in base64List:
		train_face(vistorName, base64Image)
	return


@csrf_protect
def recognize_face(request):
	return_data = dict(status="fail", message="Nothing is happening")
	try:
		formData: Dict = request.POST
		facialFeatures = formData.get("facial_features", None)
		if facialFeatures:
			facialFeatures = json.loads(facialFeatures)
			person = analyze_facialFeatures(facialFeatures)
			if person:
				return_data.update(
					status="recognized", message=f"Hello {person.title()}. Welcome."
				)
				try:
					visitorObj:Visitor = Visitor.objects.get(name__iexact=person)
					return_data.update(
						visitor_name = visitorObj.name,
						visitor_telephone = visitorObj.telephone
					)
				except Exception as e:
					return_data.update(message=e.__repr__())
			else:
				return_data.update(
					status="not_recognized",
					message="System can't identify you. Either the image is bad or you have not been registered.",
				)
	except Exception as e:
		logger.exception("ERROR: recognize_face(request)")
		return_data.update(message=e.__repr__())
	return JsonResponse(return_data)


def develop_frame(facialFeature):
	image = base64_to_img(facialFeature)
	pimg = Image.open(image)
	frame = cv2.cvtColor(np.array(pimg), cv2.COLOR_RGB2BGR)
	return frame


def analyze_facialFeatures(facialFeatures: List):
	detections: List[Text] = list()
	person = None
	for facialFeature in facialFeatures:
		frame = develop_frame(facialFeature)
		detections, _ = face_detect_stream(frame, detections)
	if len(detections) > 2:
		person = mode(detections)
	return person
