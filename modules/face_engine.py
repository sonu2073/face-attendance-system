"""
face_engine.py
All OpenCV + face_recognition logic lives here.
"""

import cv2
import face_recognition
import numpy as np
from database import db


class FaceEngine:
    def __init__(self):
        self.known_ids       = []
        self.known_names     = []
        self.known_encodings = []
        self.cap             = None
        self.load_known_faces()

    # ─── Encoding DB ─────────────────────────────────────────────────────────

    def load_known_faces(self):
        """Load all student encodings from database."""
        self.known_ids       = []
        self.known_names     = []
        self.known_encodings = []
        for sid, name, enc in db.load_encodings():
            self.known_ids.append(sid)
            self.known_names.append(name)
            self.known_encodings.append(enc)

    def reload(self):
        self.load_known_faces()

    # ─── Registration ────────────────────────────────────────────────────────

    def capture_encoding_from_frame(self, frame):
        """
        Given a BGR frame, detect the largest face and return its encoding.
        Returns (encoding, annotated_frame, error_msg).
        """
        rgb  = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        locs = face_recognition.face_locations(rgb, model="hog")

        if not locs:
            return None, frame, "No face detected — look at the camera"
        if len(locs) > 1:
            return None, frame, "Multiple faces — only one person in frame"

        enc = face_recognition.face_encodings(rgb, locs)[0]

        # Draw box
        top, right, bottom, left = locs[0]
        annotated = frame.copy()
        cv2.rectangle(annotated, (left, top), (right, bottom), (0, 255, 136), 2)
        cv2.putText(annotated, "Face Detected", (left, top - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 136), 2)
        return enc, annotated, None

    # ─── Recognition ─────────────────────────────────────────────────────────

    def identify_faces(self, frame):
        """
        Identify all faces in frame.
        Returns list of dicts: {id, name, box:(top,right,bottom,left), confidence}
        """
        rgb    = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        small  = cv2.resize(rgb, (0, 0), fx=0.5, fy=0.5)
        locs   = face_recognition.face_locations(small, model="hog")
        encs   = face_recognition.face_encodings(small, locs)

        results = []
        for enc, loc in zip(encs, locs):
            top, right, bottom, left = [v * 2 for v in loc]

            if not self.known_encodings:
                results.append({"id": None, "name": "Unknown",
                                 "box": (top, right, bottom, left), "confidence": 0})
                continue

            distances = face_recognition.face_distance(self.known_encodings, enc)
            best_idx  = int(np.argmin(distances))
            best_dist = distances[best_idx]
            confidence = max(0, round((1 - best_dist) * 100))

            if best_dist < 0.50:
                results.append({
                    "id":         self.known_ids[best_idx],
                    "name":       self.known_names[best_idx],
                    "box":        (top, right, bottom, left),
                    "confidence": confidence,
                })
            else:
                results.append({"id": None, "name": "Unknown",
                                 "box": (top, right, bottom, left), "confidence": 0})
        return results

    def draw_results(self, frame, results):
        """Draw bounding boxes and labels onto frame."""
        for r in results:
            top, right, bottom, left = r["box"]
            known = r["id"] is not None
            color = (0, 255, 136) if known else (0, 80, 255)
            label = f"{r['name']}  {r['confidence']}%" if known else "Unknown"

            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
            # Corner accents
            cs = 14
            for (cx, cy, dx, dy) in [
                (left, top, 1, 1), (right, top, -1, 1),
                (left, bottom, 1, -1), (right, bottom, -1, -1)
            ]:
                cv2.line(frame, (cx, cy), (cx + dx * cs, cy), color, 3)
                cv2.line(frame, (cx, cy), (cx, cy + dy * cs), color, 3)

            # Label background
            cv2.rectangle(frame, (left, top - 28), (right, top), color, -1)
            cv2.putText(frame, label, (left + 5, top - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55,
                        (0, 0, 0) if known else (255, 255, 255), 1)
        return frame

    # ─── Camera ──────────────────────────────────────────────────────────────

    def open_camera(self, index=0):
        self.cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        return self.cap.isOpened()

    def read_frame(self):
        if self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            return frame if ret else None
        return None

    def release_camera(self):
        if self.cap:
            self.cap.release()
            self.cap = None
