import base64, logging, shutil, pickle, cv2, io, pandas, csv, numpy as np, os, face_recognition
from typing import Dict
from pathlib import PurePath
from datetime import datetime

# from flask_socketio import emit
from PIL import Image
import cv2
import random
from .sqlite_handler import clock_out_update, clock_in_insert
from . import CSV_LOGS, SYSTEM_LOGS, FACES, ENCODINGS_PATH

logger = logging.getLogger("recognition_handler")
logger.setLevel(logging.INFO)
file_handler = logging.FileHandler(PurePath(SYSTEM_LOGS, "recognition.log"), mode="a+")
logger.addHandler(file_handler)

CURRENT_ENCODINGS_PATH = PurePath(ENCODINGS_PATH, "current.pickle")
NOT_RECOGNIZED = []
TOLERANCE = 0.4


def recognize_face(face_encoding, tolerance: float = TOLERANCE):
    name = "not_recognized"
    try:
        faces_pickle = open(CURRENT_ENCODINGS_PATH, "rb")
        faces_dict: Dict = pickle.load(faces_pickle)
        faces_pickle.close()
        known_face_encodings = list(faces_dict.values())
        matches = face_recognition.compare_faces(
            known_face_encodings, face_encoding, tolerance
        )
        face_distances = face_recognition.face_distance(
            known_face_encodings, face_encoding
        )
        best_match_index = np.argmin(face_distances)
        if matches[best_match_index]:
            name = list(faces_dict.keys())[best_match_index]
            # name = "".join(re.findall("[a-zA-Z]+", name))
            name = name.rsplit("_")[0]
    except FileNotFoundError:
        logger.exception("ERROR:Encodings Not Found")
    except:
        logger.exception("ERROR:Recognize Face Function")
    return name


def face_detect_stream(frame, detections_array: list):
    global NOT_RECOGNIZED
    rgb_frame = frame[:, :, ::-1]
    face_locations = face_recognition.face_locations(rgb_frame)
    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
    for _, face_encoding in zip(face_locations, face_encodings):
        try:
            name = recognize_face(face_encoding)
            if name == "not_recognized":
                NOT_RECOGNIZED.append(1)
            else:
                detections_array.append(name)
                NOT_RECOGNIZED = []
        except Exception as e:
            logger.exception("recognize_face(face_encoding)")
    return detections_array, NOT_RECOGNIZED


def facial_csv_writer(csv_name: str, person_recongnized: str, time: datetime):
    CSV_PATH = PurePath(CSV_LOGS, csv_name)
    did_write = False
    clock_type = "clockin"
    fieldnames = ["staff_id", "clock_in", "clock_out"]
    clock_in_dict = dict(
        staff_id=person_recongnized,
        clock_in=f'{time.strftime("%Y-%m-%d %H:%M:%S")}',
        clock_out="",
    )
    if os.path.isfile(CSV_PATH) is False:
        csv_file = open(CSV_PATH, "w")
        writer = csv.DictWriter(csv_file, fieldnames)
        writer.writeheader()
        csv_file.close()
    df = pandas.read_csv(CSV_PATH, dtype=str)
    df.fillna("Null", inplace=True)
    names = df["staff_id"].tolist()
    if person_recongnized in names:
        clock_type = "clockout"
        records = df.loc[df["staff_id"] == person_recongnized]
        clock_in = datetime.strptime(records["clock_in"].values[0], "%Y-%m-%d %H:%M:%S")
        if (time - clock_in).total_seconds() < 5 * 60:
            return did_write, clock_type
        else:
            if records["clock_out"].values[0] != "Null":
                clock_out = datetime.strptime(
                    records["clock_out"].values[0], "%Y-%m-%d %H:%M:%S"
                )
                if (time - clock_out).total_seconds() < 5 * 60:
                    return did_write, clock_type
            df.loc[
                df["staff_id"] == person_recongnized, "clock_out"
            ] = f'{time.strftime("%Y-%m-%d %H:%M:%S")}'
            df.to_csv(CSV_PATH, mode="w", index=False)
            did_write = True
            clock_out_update(person_recongnized, time)
    else:
        with open(CSV_PATH, "a") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames)
            writer.writerow(clock_in_dict)
            did_write = True
            clock_in_insert(person_recongnized, time)
    return did_write, clock_type


def train_face(staff_id: str, base64_img):
    try:
        image = base64_to_img(base64_img)
        loaded_image = Image.open(image)
        loaded_image = loaded_image.convert("RGB")
        random_num = random.randint(0, 99999)
        os.makedirs(PurePath(FACES, staff_id), exist_ok=True)
        filepath = PurePath(
            FACES, f"{staff_id}/{staff_id}_{random_num}.jpeg"
        ).as_posix()
        loaded_image.save(fp=filepath, format="JPEG")
        loaded_image = cv2.imread(filepath)
        rgb = cv2.cvtColor(loaded_image, cv2.COLOR_BGR2RGB)
        fac_locations = face_recognition.face_locations(
            rgb, model="hog", number_of_times_to_upsample=2
        )
        faces = face_recognition.face_encodings(
            rgb, fac_locations, model="large", num_jitters=2
        )
        if len(faces) == 1:
            face_encoding_to_store = faces[0]
            faces_dict = dict()

            if os.path.isfile(CURRENT_ENCODINGS_PATH):
                current_pickle = open(CURRENT_ENCODINGS_PATH, "rb")
                faces_dict = pickle.load(current_pickle)
                current_pickle.close()

                person = recognize_face(
                    face_encoding_to_store, tolerance=0.30
                )
                if person != "not_recognized":
                    person = f"{person}_{random_num}"
                    staff_id = person

            faces_dict[staff_id] = face_encoding_to_store
            new_pickle = open(CURRENT_ENCODINGS_PATH, "wb")
            pickle.dump(faces_dict, new_pickle)
            new_pickle.close()
            return dict(ErrorCode=0, message="face added")
        return dict(ErrorCode=1, message="no faces found")
    except Exception as e:
        logger.exception("Training Faces")
        return dict(ErrorCode=2, message=f"exception in training faces {e}")


def backup_encodings():
    if os.path.isfile(CURRENT_ENCODINGS_PATH):
        backup_encodings_path = PurePath(
            ENCODINGS_PATH, f"backup-{datetime.now().date()}.pickle"
        )
        shutil.copy(CURRENT_ENCODINGS_PATH.as_posix(), backup_encodings_path.as_posix())
    return


def base64_to_img(base64_img):
    _, image = base64_img.split(",", 1)
    b = io.BytesIO(base64.b64decode(image))
    return b


def check_image(base64_img, is_file: bool = False):
    if is_file is False:
        image = base64_to_img(base64_img)
    else:
        image = base64_img
    pimg = Image.open(image)
    frame = cv2.cvtColor(np.array(pimg), cv2.COLOR_RGB2BGR)
    rgb_frame = frame[:, :, ::-1]
    face_locations = face_recognition.face_locations(
        rgb_frame, model="hog", number_of_times_to_upsample=2
    )
    face_encodings = face_recognition.face_encodings(
        rgb_frame, face_locations, num_jitters=2, model="large"
    )
    response = dict(ErrorCode=2, message="No face detected")
    if len(face_encodings) > 0:
        face_encoding = face_encodings[0]
        person = recognize_face(face_encoding, enable_socket=False)
        if person == "not_recognized":
            response = dict(ErrorCode=1, message="Person not recognized")
        else:
            response = dict(ErrorCode=0, message=person)
        return response
    return response
